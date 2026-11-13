"""Real local HTTP + DynamoDB tests. All accounts/data are disposable synthetic inputs."""
import asyncio
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from aiohttp import CookieJar
from aiohttp.test_utils import TestClient, TestServer

from lingualive_api.app import STATE, create_app
from lingualive_api.config import Settings
from lingualive_api.local_auth import LocalAuth
from lingualive_api.persistence.catalog import Scope
from lingualive_api.persistence.dynamo import DynamoStore
from lingualive_api.persistence.errors import StorageUnavailable
from lingualive_api.persistence.settings import PersistenceSettings


class LocalIntegrationCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.folder = tempfile.TemporaryDirectory()
        values = {"APP_ENV": "test", "PERSISTENCE_ENABLED": "1", "LOCAL_AUTH_ENABLED": "1", "APP_DATA_DIR": self.folder.name,
                  "DYNAMODB_ENDPOINT": "http://127.0.0.1:8000", "DYNAMODB_TABLE": "lingualive-test-learning-" + uuid4().hex}
        values.update(getattr(self, "extra_environment", {}))
        self.store = DynamoStore(PersistenceSettings.from_environment(values))
        self.store.ensure_table()
        try:
            with patch.dict(os.environ, values):
                self.app = create_app(Settings.from_environment(values))
                self.client = TestClient(TestServer(self.app), cookie_jar=CookieJar(unsafe=True))
                await self.client.start_server()
        except BaseException:
            self.store.call("delete_table", TableName=self.store.table)
            self.store.close(); self.folder.cleanup()
            raise
        self.storage = self.app[STATE]["persistence"]
        self.password = "Local test password 2026!"

    async def asyncTearDown(self):
        await self.client.close()
        assert self.store.table.startswith("lingualive-test-")
        self.store.call("delete_table", TableName=self.store.table)
        self.store.close(); self.folder.cleanup()

    async def auth(self, action, body=None, expected=200):
        response = await self.client.request("GET" if action == "session" else "POST", "/local-auth/" + action,
                                             json=body, headers={"X-Local-Client": "browser"})
        result = await response.json()
        self.assertEqual(response.status, expected, result)
        return result.get("data", result)

    async def register(self, email=None):
        return await self.auth("register", {"email": email or uuid4().hex + "@example.invalid", "password": self.password, "display_name": "Người thử nghiệm"}, 201)

    async def api(self, method, path, token, body=None, expected=200, key=None):
        headers = {"Authorization": "Bearer " + token}
        if method == "POST": headers["Idempotency-Key"] = key or str(uuid4())
        response = await self.client.request(method, "/api/v1" + path, json=body, headers=headers)
        result = None if response.status == 204 else await response.json()
        self.assertEqual(response.status, expected, result)
        return result.get("data", result) if result else None

    def word_request(self, word="カフェ"):
        from urllib.parse import quote
        return {"language": "ja", "entry_id": "sample:v1:" + quote(word, safe="~()*!.'-"),
                "sense_id": "sample:v1:meaning", "collection_id": None, "occurrence": None}

    async def word(self, token, word="カフェ"):
        return await self.api("POST", "/vocabulary", token, self.word_request(word), expected=201)

    async def session(self, token):
        return await self.api("POST", "/sessions", token, {"mode": "solo", "title": "Phiên thử DB", "language": "ja"}, expected=201)


class LearningIntegrationTests(LocalIntegrationCase):
    async def test_real_registration_hashes_password_and_token_and_restores(self):
        data = await self.register("learner@example.invalid")
        self.assertFalse(data["profile"]["email_verified"])
        self.assertEqual(data["profile"]["roles"], ["user"])
        rows = list(self.store.export_items())
        serialized = json.dumps(rows)
        self.assertNotIn(self.password, serialized)
        self.assertNotIn(data["access_token"], serialized)
        account = next(row for row in rows if row["pk"] == "LOCAL_AUTH#ACCOUNT")
        self.assertEqual(account["algorithm"], "scrypt-n16384-r8-p1")
        self.assertEqual(len(account["password_hash"]), 64)
        restored = await self.auth("session")
        self.assertEqual(restored["profile"]["user_id"], data["profile"]["user_id"])
        self.assertEqual(LocalAuth(self.storage).restore(data["access_token"])["profile"], data["profile"])

    async def test_wrong_password_duplicate_email_and_logout_revocation(self):
        data = await self.register("learner@example.invalid")
        await self.auth("login", {"email": "learner@example.invalid", "password": "incorrect password"}, 401)
        await self.auth("register", {"email": "LEARNER@example.invalid", "password": self.password, "display_name": "Another"}, 409)
        await self.auth("logout")
        await self.api("GET", "/me", data["access_token"], expected=401)
        login = await self.auth("login", {"email": "LEARNER@example.invalid", "password": self.password})
        self.assertEqual(login["profile"]["user_id"], data["profile"]["user_id"])

    async def test_expired_session_is_not_accepted(self):
        data = await self.register()
        auth = LocalAuth(self.storage)
        row = self.store.get(auth.session_key(data["access_token"]))
        self.store.transact([self.store.put_action({**row, "expires_at_s": 1, "revision": 2}, 1)])
        error = await self.api("GET", "/me", data["access_token"], expected=401)
        self.assertEqual(error["error"]["code"], "TOKEN_EXPIRED")

    async def test_cross_origin_and_missing_local_header_are_rejected(self):
        response = await self.client.post("/local-auth/register", json={})
        self.assertEqual(response.status, 403)
        response = await self.client.post("/local-auth/register", json={}, headers={"Origin": "https://evil.invalid", "X-Local-Client": "browser"})
        self.assertEqual(response.status, 403)

    async def test_profile_version_timezone_and_authority_validation(self):
        data = await self.register(); token = data["access_token"]
        updated = await self.api("PATCH", "/me", token, {"display_name": "Đức đã lưu DB", "timezone": "Asia/Tokyo", "expected_version": 1})
        self.assertEqual(updated["version"], 2)
        self.assertEqual((await self.api("GET", "/me", token))["display_name"], "Đức đã lưu DB")
        await self.api("PATCH", "/me", token, {"display_name": "Stale", "expected_version": 1}, 409)
        await self.api("PATCH", "/me", token, {"timezone": "Unknown/Timezone", "expected_version": 2}, 400)
        await self.api("PATCH", "/me", token, {"email": "other@example.invalid", "expected_version": 2}, 400)
        await self.api("PATCH", "/me", token, {"roles": ["admin"], "expected_version": 2}, 400)

    async def test_vocabulary_duplicate_review_delete_persist(self):
        token = (await self.register())["access_token"]
        word = await self.word(token)
        duplicate = await self.api("POST", "/vocabulary", token, self.word_request())
        self.assertEqual(word["word_id"], duplicate["word_id"])
        self.assertEqual(word["meanings"][0]["origin"], "fixture")
        known = await self.api("PATCH", f"/vocabulary/{word['word_id']}/review", token, {"review_state": "known", "expected_version": 1})
        self.assertEqual(known["version"], 2)
        await self.api("PATCH", f"/vocabulary/{word['word_id']}/review", token, {"review_state": "learning", "expected_version": 1}, 409)
        loaded = await self.api("GET", "/vocabulary", token)
        self.assertEqual(len(loaded["items"]), 1)
        self.assertEqual(loaded["items"][0]["review_state"], "known")
        await self.api("DELETE", f"/vocabulary/{word['word_id']}", token, expected=204)
        await self.api("DELETE", f"/vocabulary/{word['word_id']}", token, expected=204)
        self.assertEqual((await self.api("GET", "/vocabulary", token))["items"], [])

    async def test_idempotency_replay_and_conflict(self):
        token = (await self.register())["access_token"]
        key = str(uuid4())
        word = await self.api("POST", "/vocabulary", token, self.word_request(), 201, key)
        replay = await self.api("POST", "/vocabulary", token, self.word_request(), 200, key)
        self.assertEqual(word["word_id"], replay["word_id"])
        error = await self.api("POST", "/vocabulary", token, self.word_request("近く"), 409, key)
        self.assertEqual(error["error"]["code"], "IDEMPOTENCY_CONFLICT")

    async def test_concurrent_duplicate_saves_are_one_word(self):
        token = (await self.register())["access_token"]
        async def save():
            response = await self.client.post("/api/v1/vocabulary", json=self.word_request(), headers={"Authorization": "Bearer " + token, "Idempotency-Key": str(uuid4())})
            result = await response.json()
            self.assertIn(response.status, {200, 201}, result)
            return result["data"]["word_id"]
        identifiers = await asyncio.gather(*(save() for _ in range(4)))
        self.assertEqual(len(set(identifiers)), 1)
        self.assertEqual(len((await self.api("GET", "/vocabulary", token))["items"]), 1)

    async def test_accounts_cannot_read_or_modify_each_others_data(self):
        first, second = await self.register(), await self.register()
        word = await self.word(first["access_token"])
        session = await self.session(first["access_token"])
        self.assertEqual((await self.api("GET", "/vocabulary", second["access_token"]))["items"], [])
        self.assertEqual((await self.api("GET", "/history", second["access_token"]))["items"], [])
        await self.api("GET", "/sessions/" + session["session_id"], second["access_token"], expected=403)
        await self.api("PATCH", f"/vocabulary/{word['word_id']}/review", second["access_token"], {"review_state": "known", "expected_version": 1}, 404)

    async def test_solo_session_history_and_end_are_real(self):
        token = (await self.register())["access_token"]
        key = str(uuid4()); body = {"mode": "solo", "title": "Test lưu lịch sử", "language": "ja"}
        session = await self.api("POST", "/sessions", token, body, 201, key)
        replay = await self.api("POST", "/sessions", token, body, 200, key)
        self.assertEqual(session["session_id"], replay["session_id"])
        self.assertFalse(session["capabilities"]["can_send_ocr"])
        self.assertIsNone((await self.api("GET", "/history", token))["items"][0]["ended_at"])
        ended = await self.api("POST", f"/sessions/{session['session_id']}/end", token, {"expected_version": 1})
        self.assertEqual(ended["status"], "ended")
        again = await self.api("POST", f"/sessions/{session['session_id']}/end", token, {"expected_version": 1})
        self.assertEqual(again, ended)
        self.assertIsNotNone((await self.api("GET", "/history", token))["items"][0]["duration_ms"])
        raw = self.storage.repository.raw(Scope("session", session["session_id"]), "session", session["session_id"])
        self.assertEqual(json.loads(raw["payload"])["status"], "ended")

    async def test_cursor_pages_preserve_words(self):
        token = (await self.register())["access_token"]
        await self.word(token, "カフェ"); await self.word(token, "近く")
        page = await self.api("GET", "/vocabulary?limit=1", token)
        self.assertIsNotNone(page["next_cursor"])
        from urllib.parse import quote
        second = await self.api("GET", "/vocabulary?limit=1&cursor=" + quote(page["next_cursor"], safe=""), token)
        self.assertNotEqual(page["items"][0]["word_id"], second["items"][0]["word_id"])

    async def test_database_outage_is_error_not_fake_success(self):
        token = (await self.register())["access_token"]
        with patch.object(self.storage.store, "call", side_effect=StorageUnavailable("injected outage")):
            error = await self.api("POST", "/vocabulary", token, self.word_request(), 503)
        self.assertEqual(error["error"]["code"], "PROVIDER_UNAVAILABLE")
        self.assertEqual((await self.api("GET", "/vocabulary", token))["items"], [])

    async def test_unknown_lexicon_does_not_invent_dictionary_data(self):
        token = (await self.register())["access_token"]
        body = {**self.word_request(), "entry_id": "unknown:entry"}
        await self.api("POST", "/vocabulary", token, body, 404)
        self.assertEqual((await self.api("GET", "/vocabulary", token))["items"], [])

    async def test_inflected_sample_saves_lemma_without_invented_reading(self):
        token = (await self.register())["access_token"]
        word = await self.word(token, "曲がる")
        self.assertEqual(word["lemma"], "曲がる")
        self.assertEqual(word["reading"]["kana"], "まがる")
        self.assertIsNone(word["reading"]["romaji"])
        self.assertEqual(word["meanings"][0]["origin"], "fixture")

    async def test_production_frontend_client_persists_through_actual_http(self):
        root = Path(__file__).resolve().parents[2]
        node = os.environ.get("LINGUALIVE_NODE") or shutil.which("node")
        self.assertIsNotNone(node, "Node 22 is required for the FE consumer test")
        process = await asyncio.create_subprocess_exec(node, str(root / "tools/integration/learning-client-check.mjs"),
                                                       str(self.client.make_url("/")), cwd=root,
                                                       stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        self.assertEqual(process.returncode, 0, stderr.decode())
        result = json.loads(stdout)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["checks"]), 13)
        rows = list(self.store.export_items())
        profiles = [json.loads(item["payload"]) for item in rows if item.get("entity_kind") == "profile"]
        self.assertEqual(profiles[0]["display_name"], "FE name persisted")
        words = [json.loads(item["payload"]) for item in rows if item.get("entity_kind") == "word"]
        self.assertEqual([word["lemma"] for word in words], ["近く"])
