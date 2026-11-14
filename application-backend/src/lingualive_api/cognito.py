"""Cognito access-token verifier. Fails closed; never trusts unverified claims."""
from __future__ import annotations

import asyncio

import jwt
from jwt import PyJWKClient

from .auth import Identity
from .errors import ApiError, unavailable
#new
from .persistence.errors import Conflict
from .persistence.repository import Scope  # KHỚP: xem ghi chú dưới


class CognitoVerifier:
    ready = True

    def __init__(self, region: str, pool_id: str, client_id: str):
        self.issuer = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"
        self.client_id = client_id
        self._jwks = PyJWKClient(f"{self.issuer}/.well-known/jwks.json", cache_keys=True, lifespan=3600)

    @staticmethod
    def looks_like_jwt(token: str) -> bool:
        if token.count(".") != 2:
            return False
        try:
            return bool(jwt.get_unverified_header(token).get("kid"))
        except jwt.PyJWTError:
            return False

    def _verify(self, token: str) -> dict:
        key = self._jwks.get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=["RS256"], issuer=self.issuer,
                            options={"require": ["exp", "iss", "sub"], "verify_aud": False})
        if claims.get("token_use") != "access" or claims.get("client_id") != self.client_id:
            raise jwt.InvalidTokenError("wrong token_use or client_id")
        return claims

    async def verify_access_token(self, token: str) -> Identity:
        try:
            claims = await asyncio.to_thread(self._verify, token)
        except jwt.PyJWKClientConnectionError:
            raise unavailable() from None
        except jwt.PyJWTError:
            raise ApiError(401, "AUTH_REQUIRED", "The access token is invalid.") from None
        #roles = ("admin",) if "admin" in claims.get("cognito:groups", []) else ("user",)
        #return Identity("cognito:" + claims["sub"], roles)
        roles = ("admin",) if "admin" in claims.get("cognito:groups", []) else ("user",)
        return Identity("cognito:" + claims["sub"], roles), claims


class CombinedAuthenticator:
    """Cognito JWTs go to Cognito (no fallback to local); everything else to local auth."""

    def __init__(self, local, cognito, provisioner):
        self.local, self.cognito, self.provisioner = local, cognito, provisioner

    @property
    def ready(self):
        return self.local.ready

    def __getattr__(self, name):
        return getattr(self.local, name)

    async def verify_access_token(self, token):
        if self.cognito.looks_like_jwt(token):
            #return await self.cognito.verify_access_token(token)
            identity, claims = await self.cognito.verify_access_token(token)
            await asyncio.to_thread(self.provisioner.ensure, identity, claims)
            return identity
        #
        return await self.local.verify_access_token(token)
#new
class ProfileProvisioner:
    """Creates the profile row on a Cognito user's first verified request."""

    def __init__(self, storage):
        self.repo, self.store = storage.repository, storage.store
        self._known = set()

    def ensure(self, identity, claims):
        uid = identity.user_id
        if uid in self._known:
            return
        scope = Scope("user", uid)
        if self.repo.get(Identity(uid, ("user",)), scope, "profile", uid):
            self._known.add(uid)
            return
        username = claims.get("username", "")
        email = username if "@" in username else uid.split(":", 1)[1] + "@cognito.invalid"
        profile = {"user_id": uid, "display_name": email.split("@")[0][:60] or "User",
                   "email": email, "email_verified": False, "roles": ["user"],
                   "permissions": [], "status": "active", "locale": "vi",
                   "timezone": "Asia/Ho_Chi_Minh", "learning_language": "ja", "version": 1}
        row, reference, _ = self.repo.rows(scope, "profile", profile, 1)
        try:
            self.store.transact([self.store.put_action(item) for item in (row, reference)])
        except Conflict:
            pass
        self._known.add(uid)