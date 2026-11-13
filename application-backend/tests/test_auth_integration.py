"""Group 3: real HTTP, real DynamoDB, synthetic accounts, local mailbox only."""
import asyncio
import json
import os
from pathlib import Path
import shutil
import stat
import time
from unittest.mock import patch

from lingualive_api.app import STATE
from lingualive_api.errors import ApiError
from lingualive_api.local_auth import COOKIE, SESSION_SECONDS
from lingualive_api.local_admin import LocalAdmin
from lingualive_api.persistence.errors import StorageUnavailable
from test_learning_integration import LocalIntegrationCase


class AuthIntegrationTests(LocalIntegrationCase):
    async def local(self, action, token=None, body=None, expected=200, method="POST"):
        headers = {"X-Local-Client": "browser"}
        if token:
            headers["Authorization"] = "Bearer " + token
        response = await self.client.request(method, "/local-auth/" + action, headers=headers, json=body)
        result = await response.json()
        self.assertEqual(response.status, expected, result)
        return result.get("data", result)

    def code(self, purpose, email):
        files = sorted((self.storage.objects.root.parent / "mailbox").glob("*.json"), key=lambda path: path.stat().st_mtime_ns, reverse=True)
        for path in files:
            message = json.loads(path.read_text())
            if message["purpose"] == purpose and message["to"] == email:
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
                self.assertEqual(message["delivery_mode"], "local_mailbox")
                return message["code"]
        self.fail("No local test mail was delivered")

    async def verified(self, email=None):
        data = await self.register(email)
        token, email = data["access_token"], data["profile"]["email"]
        await self.local("verification/request", token, {})
        profile = await self.local("verification/confirm", token, {"code": self.code("verify_email", email)})
        self.assertTrue(profile["email_verified"])
        return data

    async def admin(self):
        data = await self.verified()
        LocalAdmin(self.app[STATE]["authenticator"]).provision(data["profile"]["email"], grant=True, reason="Test administrator provisioning")
        return await self.auth("login", {"email": data["profile"]["email"], "password": self.password})

    def cookie(self):
        return self.client.session.cookie_jar.filter_cookies(self.client.make_url("/local-auth/session"))[COOKIE].value

    async def test_code_confirmation_is_one_time_and_not_exposed_by_api_or_db(self):
        data = await self.register(); token = data["access_token"]
        response = await self.local("verification/request", token, {})
        self.assertEqual(response, {"accepted": True, "delivery_mode": "local_mailbox"})
        code = self.code("verify_email", data["profile"]["email"])
        self.assertNotIn(code, json.dumps(list(self.store.export_items())))
        await self.local("verification/confirm", token, {"code": code})
        await self.local("verification/confirm", token, {"code": code}, 400)
        self.assertTrue((await self.api("GET", "/me", token))["email_verified"])

    async def test_wrong_code_attempts_cooldown_and_expiry_are_enforced(self):
        data = await self.register(); token = data["access_token"]
        await self.local("verification/request", token, {})
        await self.local("verification/request", token, {}, 429)
        correct = self.code("verify_email", data["profile"]["email"])
        wrong = "00000000" if correct != "00000000" else "11111111"
        for _ in range(5):
            await self.local("verification/confirm", token, {"code": wrong}, 400)
        await self.local("verification/confirm", token, {"code": correct}, 400)
        self.assertFalse((await self.api("GET", "/me", token))["email_verified"])
        auth = self.app[STATE]["authenticator"]
        key = auth.key("CHALLENGE", data["profile"]["user_id"] + ":verify_email")
        old = self.store.get(key)
        self.store.transact([self.store.put_action({**old, "expires_at_s": 1, "revision": old["revision"] + 1}, old["revision"])])
        await self.local("verification/confirm", token, {"code": correct}, 400)

    async def test_password_reset_revokes_all_access_and_refresh_sessions(self):
        data = await self.register(); email = data["profile"]["email"]
        second = await self.auth("login", {"email": email, "password": self.password})
        await self.local("password/forgot", body={"email": email})
        code = self.code("reset_password", email)
        await self.local("password/reset", body={"email": email, "code": code, "password": "A new secure password!"})
        for token in [data["access_token"], second["access_token"]]:
            await self.api("GET", "/me", token, expected=401)
        await self.local("session", method="GET", expected=401)
        await self.local("password/reset", body={"email": email, "code": code, "password": self.password}, expected=400)
        await self.auth("login", {"email": email, "password": self.password}, 401)
        login = await self.auth("login", {"email": email, "password": "A new secure password!"})
        self.assertEqual(login["profile"]["user_id"], data["profile"]["user_id"])

    async def test_unknown_forgot_response_matches_existing_and_does_not_create_account(self):
        data = await self.register()
        existing = await self.local("password/forgot", body={"email": data["profile"]["email"]})
        unknown = await self.local("password/forgot", body={"email": "unknown@example.invalid"})
        self.assertEqual(existing, unknown)
        self.assertIsNone(self.store.get(self.app[STATE]["authenticator"].account_key("unknown@example.invalid")))

    async def test_password_change_checks_current_password_and_revokes_other_sessions(self):
        data = await self.register(); token = data["access_token"]
        await self.local("password/change", token, {"current_password": "wrong password", "password": "New test password!"}, 400)
        await self.local("password/change", token, {"current_password": self.password, "password": "New test password!"})
        await self.api("GET", "/me", token, expected=401)
        await self.auth("login", {"email": data["profile"]["email"], "password": "New test password!"})

    async def test_password_change_invalidates_outstanding_confirmation_code(self):
        data = await self.register(); token = data["access_token"]; email = data["profile"]["email"]
        await self.local("verification/request", token, {})
        code = self.code("verify_email", email)
        await self.local("password/change", token, {"current_password": self.password, "password": "Changed secure password!"})
        login = await self.auth("login", {"email": email, "password": "Changed secure password!"})
        await self.local("verification/confirm", login["access_token"], {"code": code}, 400)

    async def test_refresh_rotates_cookie_and_expired_access_cannot_renew_itself(self):
        data = await self.register(); auth = self.app[STATE]["authenticator"]
        old_cookie = self.cookie()
        self.assertNotEqual(old_cookie, data["access_token"])
        self.assertLessEqual(data["expires_at_s"] - time.time(), SESSION_SECONDS)
        self.assertNotIn("_refresh_token", data)
        await self.local("refresh", body={"roles": ["admin"]}, expected=400)
        refreshed = await self.local("refresh", body={})
        self.assertNotEqual(self.cookie(), old_cookie)
        self.assertNotEqual(refreshed["access_token"], data["access_token"])
        self.assertIsNone(self.store.get(auth.key("REFRESH", old_cookie)))
        # Browser cookie accepts only a refresh token, never a current access token.
        self.client.session.cookie_jar.clear()
        self.client.session.cookie_jar.update_cookies({COOKIE: data["access_token"]}, response_url=self.client.make_url("/"))
        await self.local("refresh", body={}, expected=401)
        row = self.store.get(auth.session_key(data["access_token"]))
        self.store.transact([self.store.put_action({**row, "expires_at_s": 1, "revision": 2}, 1)])
        await self.api("GET", "/me", data["access_token"], expected=401)

    async def test_logout_revokes_access_tokens_issued_by_refresh(self):
        data = await self.register()
        fresh = await self.local("refresh", body={})
        await self.local("logout")
        for token in [data["access_token"], fresh["access_token"]]:
            await self.api("GET", "/me", token, expected=401)

    async def test_logout_all_revokes_every_login(self):
        data = await self.register()
        second = await self.auth("login", {"email": data["profile"]["email"], "password": self.password})
        await self.local("logout-all", second["access_token"], {})
        for token in [data["access_token"], second["access_token"]]:
            await self.api("GET", "/me", token, expected=401)

    async def test_legacy_cookie_and_account_upgrade_without_losing_words(self):
        data = await self.register(); token = data["access_token"]
        await self.word(token)
        auth = self.app[STATE]["authenticator"]
        account = self.store.get(auth.account_key(data["profile"]["email"]))
        old_account = {key: value for key, value in account.items() if key not in {"auth_epoch", "created_at", "last_sign_in_at"}}
        old_account["revision"] += 1
        legacy_token = "legacy-access-token-" + "A" * 32
        self.store.transact([self.store.put_action(old_account, account["revision"]), self.store.put_action({**auth.session_key(legacy_token), "revision": 1, "user_id": data["profile"]["user_id"], "expires_at_s": int(time.time()) + 3600})])
        self.client.session.cookie_jar.clear()
        self.client.session.cookie_jar.update_cookies({COOKIE: legacy_token}, response_url=self.client.make_url("/"))
        upgraded = await self.local("session", method="GET")
        self.assertIsNone(self.store.get(auth.session_key(legacy_token)))
        self.assertEqual((await self.api("GET", "/vocabulary", upgraded["access_token"]))["items"][0]["lemma"], "カフェ")

    async def test_user_cannot_self_promote_or_access_admin_and_unverified_cannot_be_provisioned(self):
        data = await self.register(); token = data["access_token"]
        await self.local("admin/users", token, method="GET", expected=403)
        await self.local("verification/confirm", token, {"code": "00000000", "roles": ["admin"]}, 400)
        await self.api("PATCH", "/me", token, {"roles": ["admin"], "expected_version": 1}, 400)
        with self.assertRaises(ApiError) as failure:
            LocalAdmin(self.app[STATE]["authenticator"]).provision(data["profile"]["email"], grant=True, reason="Test rejected provisioning")
        self.assertEqual(failure.exception.code, "USER_NOT_VERIFIED")

    async def test_admin_suspend_reactivate_is_versioned_audited_and_revokes_sessions(self):
        admin = await self.admin(); token = admin["access_token"]
        user = await self.register()
        page = await self.local("admin/users", token, method="GET")
        self.assertEqual(len(page["items"]), 2)
        body = {"user_id": user["profile"]["user_id"], "status": "suspended", "expected_version": 1, "reason": "Test account restriction"}
        await self.local("admin/status", token, {**body, "status": []}, 400)
        await self.local("admin/status", token, {**body, "expected_version": True}, 400)
        changed = await self.local("admin/status", token, body)
        self.assertEqual(changed["status"], "suspended")
        await self.api("GET", "/me", user["access_token"], expected=403)
        await self.auth("login", {"email": user["profile"]["email"], "password": self.password}, 403)
        await self.local("admin/status", token, body, 409)
        await self.local("admin/status", token, {**body, "status": "active", "expected_version": changed["version"]})
        await self.api("GET", "/me", user["access_token"], expected=401)
        await self.auth("login", {"email": user["profile"]["email"], "password": self.password})
        audit = await self.local("admin/audit", token, method="GET")
        self.assertEqual(len(audit["items"]), 3)
        self.assertTrue(all(item["outcome"] == "succeeded" for item in audit["items"]))

    async def test_self_suspend_and_last_admin_revocation_are_blocked(self):
        data = await self.admin()
        await self.local("admin/status", data["access_token"], {"user_id": data["profile"]["user_id"], "status": "suspended", "expected_version": data["profile"]["version"], "reason": "Test self suspension"}, 409)
        with self.assertRaises(ApiError) as failure:
            LocalAdmin(self.app[STATE]["authenticator"]).provision(data["profile"]["email"], grant=False, reason="Test last admin removal")
        self.assertEqual(failure.exception.code, "LAST_ADMIN_PROTECTED")

    async def test_concurrent_admin_suspensions_keep_one_active_admin(self):
        first, second = await self.admin(), await self.admin()
        async def suspend(caller, target):
            response = await self.client.post("/local-auth/admin/status", headers={"X-Local-Client": "browser", "Authorization": "Bearer " + caller["access_token"]}, json={"user_id": target["profile"]["user_id"], "status": "suspended", "expected_version": target["profile"]["version"], "reason": "Concurrent administration test"})
            await response.read()
            return response.status
        statuses = await asyncio.gather(suspend(first, second), suspend(second, first))
        self.assertEqual(statuses.count(200), 1, statuses)
        self.assertTrue(all(status in {200, 401, 403, 409} for status in statuses), statuses)
        from lingualive_api.local_admin import REGISTRY
        self.assertEqual(len(self.store.get(REGISTRY)["user_ids"]), 1)

    async def test_admin_audit_failure_rolls_back_status_and_revocation(self):
        admin = await self.admin(); user = await self.register()
        auth = self.app[STATE]["local_admin"]
        with patch.object(auth, "audit_actions", side_effect=StorageUnavailable("injected failure")):
            await self.local("admin/status", admin["access_token"], {"user_id": user["profile"]["user_id"], "status": "suspended", "expected_version": 1, "reason": "Test atomic audit"}, 503)
        self.assertEqual((await self.api("GET", "/me", user["access_token"]))["status"], "active")

    async def test_email_change_requires_password_code_uniqueness_and_revokes_sessions(self):
        data = await self.register(); token = data["access_token"]
        old_email, new_email = data["profile"]["email"], "changed@example.invalid"
        await self.local("email/request", token, {"email": new_email, "password": "wrong password"}, 400)
        await self.local("email/request", token, {"email": new_email, "password": self.password})
        self.assertEqual((await self.api("GET", "/me", token))["email"], old_email)
        code = self.code("change_email", new_email)
        await self.local("email/confirm", token, {"code": code})
        await self.api("GET", "/me", token, expected=401)
        await self.auth("login", {"email": old_email, "password": self.password}, 401)
        login = await self.auth("login", {"email": new_email, "password": self.password})
        self.assertEqual(login["profile"]["user_id"], data["profile"]["user_id"])
        self.assertTrue(login["profile"]["email_verified"])

    async def test_mailbox_failure_is_error_and_does_not_confirm_email(self):
        data = await self.register(); auth = self.app[STATE]["authenticator"]
        with patch.object(auth.mailbox, "deliver", side_effect=OSError("injected disk failure")):
            await self.local("verification/request", data["access_token"], {}, 503)
        self.assertFalse((await self.api("GET", "/me", data["access_token"]))["email_verified"])
        await self.local("verification/request", data["access_token"], {})

    async def test_login_lockout_is_persisted_per_account(self):
        data = await self.register(); email = data["profile"]["email"]
        for _ in range(5):
            await self.auth("login", {"email": email, "password": "wrong test password"}, 401)
        await self.auth("login", {"email": email, "password": self.password}, 429)
        account = self.store.get(self.app[STATE]["authenticator"].account_key(email))
        self.assertGreater(account["locked_until_s"], time.time())

    async def test_production_client_refresh_and_authorization_through_real_http(self):
        root = Path(__file__).resolve().parents[2]
        node = os.environ.get("LINGUALIVE_NODE") or shutil.which("node")
        self.assertIsNotNone(node)
        process = await asyncio.create_subprocess_exec(node, str(root / "tools/integration/auth-client-check.mjs"),
                                                       str(self.client.make_url("/")), cwd=root,
                                                       stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        self.assertEqual(process.returncode, 0, stderr.decode())
        result = json.loads(stdout)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["checks"]), 6)

    async def test_cli_provisions_only_an_existing_verified_account(self):
        data = await self.verified()
        root = Path(__file__).resolve().parents[2]
        environment = {**os.environ, "APP_ENV": "test", "DYNAMODB_ENDPOINT": "http://127.0.0.1:8000", "DYNAMODB_TABLE": self.store.table, "APP_DATA_DIR": self.folder.name}
        process = await asyncio.create_subprocess_exec(str(root / "scripts/auth-admin"), "grant-admin", "--email", data["profile"]["email"], "--reason", "Test CLI provisioning", cwd=root, env=environment,
                                                       stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        self.assertEqual(process.returncode, 0, stderr.decode())
        self.assertEqual(json.loads(stdout)["roles"], ["user", "admin"])
        login = await self.auth("login", {"email": data["profile"]["email"], "password": self.password})
        self.assertIn("admin", login["profile"]["roles"])
