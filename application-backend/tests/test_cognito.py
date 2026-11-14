import time
import unittest
from types import SimpleNamespace

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from lingualive_api.auth import Identity
from lingualive_api.cognito import CognitoVerifier, CombinedAuthenticator, ProfileProvisioner
from lingualive_api.errors import ApiError

REGION, POOL, CLIENT = "ap-southeast-1", "ap-southeast-1_Test12345", "client-abc"
ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{POOL}"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class FakeJwks:
    def get_signing_key_from_jwt(self, token):
        return SimpleNamespace(key=KEY.public_key())


def make_token(key=KEY, **override):
    claims = {"sub": "user-1", "iss": ISSUER, "client_id": CLIENT, "token_use": "access",
              "exp": int(time.time()) + 3600, "username": "user-1"}
    claims.update(override)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "k1"})


def verifier():
    v = CognitoVerifier(REGION, POOL, CLIENT)
    v._jwks = FakeJwks()
    return v


class CognitoVerifierTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_token_gives_cognito_identity(self):
        identity, claims = await verifier().verify_access_token(make_token())
        self.assertEqual(identity.user_id, "cognito:user-1")
        self.assertEqual(identity.roles, ("user",))

    async def test_admin_group_gives_admin_role(self):
        identity, _ = await verifier().verify_access_token(make_token(**{"cognito:groups": ["admin"]}))
        self.assertEqual(identity.roles, ("admin",))

    async def test_rejections(self):
        cases = {
            "wrong signature": make_token(key=OTHER_KEY),
            "wrong issuer": make_token(iss="https://evil.example.com/pool"),
            "expired": make_token(exp=int(time.time()) - 10),
            "id token": make_token(token_use="id"),
            "wrong client": make_token(client_id="other-client"),
            "missing sub": make_token(sub=None),
        }
        for name, token in cases.items():
            with self.subTest(name):
                with self.assertRaises(ApiError):
                    await verifier().verify_access_token(token)

    def test_looks_like_jwt(self):
        self.assertTrue(CognitoVerifier.looks_like_jwt(make_token()))
        self.assertFalse(CognitoVerifier.looks_like_jwt("abc.def.ghi"))
        self.assertFalse(CognitoVerifier.looks_like_jwt("x" * 64))


class FakeLocal:
    ready = True

    async def verify_access_token(self, token):
        return Identity("local:1", ("user",))


class FakeProvisioner:
    def __init__(self):
        self.calls = []

    def ensure(self, identity, claims):
        self.calls.append(identity.user_id)


class CombinedTests(unittest.IsolatedAsyncioTestCase):
    async def test_routing_and_no_fallback(self):
        provisioner = FakeProvisioner()
        auth = CombinedAuthenticator(FakeLocal(), verifier(), provisioner)
        self.assertEqual((await auth.verify_access_token(make_token())).user_id, "cognito:user-1")
        self.assertEqual(provisioner.calls, ["cognito:user-1"])
        self.assertEqual((await auth.verify_access_token("local-token-not-a-jwt")).user_id, "local:1")
        with self.assertRaises(ApiError):  # bad Cognito JWT must NOT fall back to local auth
            await auth.verify_access_token(make_token(key=OTHER_KEY))
        self.assertEqual(provisioner.calls, ["cognito:user-1"])


class FakeRepo:
    def __init__(self, existing=None):
        self.existing, self.saved = existing, None

    def get(self, identity, scope, kind, entity_id):
        return self.existing

    def rows(self, scope, kind, data, version):
        self.saved = data
        return ("row", "reference", None)


class FakeStore:
    def __init__(self):
        self.actions = None

    def put_action(self, item):
        return {"Put": item}

    def transact(self, actions):
        self.actions = actions


class ProvisionerTests(unittest.TestCase):
    def make(self, existing=None):
        repo, store = FakeRepo(existing), FakeStore()
        return ProfileProvisioner(SimpleNamespace(repository=repo, store=store)), repo, store

    def test_creates_profile_once(self):
        p, repo, store = self.make()
        identity = Identity("cognito:abc", ("user",))
        p.ensure(identity, {"username": "abc"})
        self.assertEqual(repo.saved["email"], "abc@cognito.invalid")
        self.assertEqual(repo.saved["roles"], ["user"])
        self.assertEqual(repo.saved["status"], "active")
        self.assertFalse(repo.saved["email_verified"])
        self.assertEqual(len(store.actions), 2)
        store.actions = None
        p.ensure(identity, {"username": "abc"})
        self.assertIsNone(store.actions)

    def test_email_username_and_existing_profile(self):
        p, repo, _ = self.make()
        p.ensure(Identity("cognito:abc", ("user",)), {"username": "a@b.com"})
        self.assertEqual(repo.saved["email"], "a@b.com")
        p2, repo2, store2 = self.make(existing=object())
        p2.ensure(Identity("cognito:abc", ("user",)), {})
        self.assertIsNone(store2.actions)


if __name__ == "__main__":
    unittest.main()