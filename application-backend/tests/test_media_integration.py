"""Real API/DB/HTTP worker tests with an explicitly synthetic raw OCR producer."""
import asyncio
import io
import json
import time
import os
from pathlib import Path
import shutil
from contextlib import suppress
from unittest.mock import patch
from uuid import uuid4

from aiohttp import web
from aiohttp.test_utils import TestServer
from PIL import Image

from lingualive_api.app import STATE
from lingualive_api.media import SERVICE
from lingualive_api.persistence.catalog import Scope
from test_learning_integration import LocalIntegrationCase


class MediaIntegrationTests(LocalIntegrationCase):
    async def asyncSetUp(self):
        self.provider_calls = 0
        self.mode = "text"
        self.gate = None
        app = web.Application()
        async def health(request):
            return web.json_response({"provider": "fixture.synthetic", "ready": True})
        async def scan(request):
            self.provider_calls += 1
            await request.read()
            if self.gate:
                await self.gate.wait()
            if self.mode == "busy":
                return web.json_response({"error": "synthetic busy"}, status=503)
            if self.mode == "timeout":
                return web.json_response({"error": "synthetic timeout"}, status=504)
            if self.mode == "invalid":
                return web.json_response({"invented": True})
            box = {"center_x": .5, "center_y": .5, "width": .4, "height": .2}
            paragraphs = [] if self.mode == "empty" else [{"full_text": "合成テスト", "is_vertical": False, "box": box, "words": [{"text": "合成テスト", "separator": "", "box": box}]}]
            return web.json_response({"paragraphs": paragraphs, "elapsed_ms": 1.0})
        app.router.add_get("/health", health); app.router.add_post("/ocr", scan)
        self.provider = TestServer(app)
        await self.provider.start_server()
        self.extra_environment = {"OCR_ENABLED": "1", "OCR_SERVICE_URL": str(self.provider.make_url("/")).rstrip("/")}
        try:
            await super().asyncSetUp()
        except BaseException:
            await self.provider.close()
            raise
        self.media = self.app[STATE]["media"]
        self.token = (await self.register())["access_token"]
        self.study = await self.session(self.token)
        self.source = await self.source_for(self.study["session_id"])

    async def asyncTearDown(self):
        if self.gate:
            self.gate.set()
        await super().asyncTearDown()
        await self.provider.close()

    async def source_for(self, session_id, *, token=None):
        token = token or self.token
        current = await self.api("GET", "/sessions/" + session_id, token)
        return await self.api("POST", f"/sessions/{session_id}/sources", token, {"source_id": str(uuid4()), "kind": "local_video", "width_px": 640, "height_px": 360,
                               "duration_ms": 30000, "expected_version": current["version"]}, 201)

    def image(self):
        output = io.BytesIO()
        Image.new("RGB", (640, 360), "white").save(output, format="PNG")
        return output.getvalue()

    async def upload(self, index=0, *, source=None, content=None, do_put=True):
        source = source or self.source
        content = self.image() if content is None else content
        body = {"source_id": source["source_id"], "frame_id": str(uuid4()), "frame_index": index, "media_time_ms": index * 1000,
                "captured_at": "2026-11-13T00:00:00.000Z", "width_px": 640, "height_px": 360, "content_type": "image/png", "size_bytes": len(content)}
        uploaded = await self.api("POST", f"/sessions/{self.study['session_id']}/uploads", self.token, body, 201)
        if do_put:
            response = await self.client.session.put(uploaded["upload"]["url"], headers=uploaded["upload"]["headers"], data=content)
            self.assertEqual(response.status, 204, await response.text())
        return uploaded, body

    async def job(self, upload, *, expected=202, token=None, session_id=None, key=None):
        return await self.api("POST", f"/sessions/{session_id or self.study['session_id']}/ocr-jobs", token or self.token,
                              {"upload_id": upload["upload_id"], "frame_id": upload["frame_id"]}, expected, key)

    async def terminal(self, job):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            current = await self.api("GET", "/ocr-jobs/" + job["job_id"], self.token)
            if current["status"] not in {"queued", "processing"}:
                return current
            await asyncio.sleep(.1)
        self.fail("Durable OCR job did not terminate")

    async def test_frame_job_result_roundtrip_and_private_object_reference(self):
        upload, metadata = await self.upload()
        job = await self.job(upload)
        done = await self.terminal(job)
        self.assertEqual(done["status"], "succeeded", done)
        result = await self.api("GET", "/results/" + done["result_id"], self.token)
        self.assertEqual(result["provider"], "fixture.synthetic")
        self.assertEqual(result["ocr"]["paragraphs"][0]["full_text"], "合成テスト")
        self.assertEqual(result["source_id"], metadata["source_id"])
        self.assertEqual(result["frame_id"], metadata["frame_id"])
        self.assertEqual(result["job_id"], job["job_id"])
        current = await self.api("GET", "/sessions/" + self.study["session_id"], self.token)
        self.assertEqual(current["latest_seq"], result["seq"])
        page = await self.api("GET", f"/sessions/{self.study['session_id']}/results?through_seq={current['latest_seq']}", self.token)
        self.assertEqual(page["items"][0]["result_id"], result["result_id"])
        stored = self.storage.repository.get_by_id(SERVICE, "result", result["result_id"])
        content = self.storage.read_object(SERVICE, stored.scope, stored.data["object_key"])
        self.assertEqual(json.loads(content), result)
        await self.api("POST", f"/sessions/{self.study['session_id']}/end", self.token, {"expected_version": current["version"]})
        self.assertEqual((await self.api("GET", "/results/" + done["result_id"], self.token)), result)

    async def test_empty_ocr_is_success_not_provider_failure(self):
        self.mode = "empty"
        upload, _ = await self.upload()
        done = await self.terminal(await self.job(upload))
        self.assertEqual(done["status"], "succeeded")
        result = await self.api("GET", "/results/" + done["result_id"], self.token)
        self.assertEqual(result["ocr"]["paragraphs"], [])

    async def test_invalid_image_metadata_signature_and_large_body_rejected(self):
        upload, _ = await self.upload(content=b"not an image", do_put=False)
        response = await self.client.session.put(upload["upload"]["url"], headers=upload["upload"]["headers"], data=b"not an image")
        self.assertEqual(response.status, 422)
        response = await self.client.session.put(upload["upload"]["url"], headers={"X-Upload-Token": "forged"}, data=b"not an image")
        self.assertEqual(response.status, 403)
        response = await self.client.session.put(upload["upload"]["url"], headers=upload["upload"]["headers"], data=io.BytesIO(b"x" * 1048577))
        self.assertEqual(response.status, 413)
        await self.job(upload, expected=409)
        self.assertEqual(self.provider_calls, 0)

    async def test_duplicate_job_is_one_provider_call_and_same_result(self):
        upload, _ = await self.upload()
        key = str(uuid4())
        first = await self.job(upload, key=key)
        replay = await self.job(upload, expected=200, key=key)
        other_key = await self.job(upload, expected=200)
        self.assertEqual(first["job_id"], replay["job_id"])
        self.assertEqual(first["job_id"], other_key["job_id"])
        await self.terminal(first)
        self.assertEqual(self.provider_calls, 1)

    async def test_stale_source_results_are_not_committed_or_shown_as_new(self):
        self.gate = asyncio.Event()
        upload, _ = await self.upload()
        job = await self.job(upload)
        for _ in range(60):
            if self.provider_calls:
                break
            await asyncio.sleep(.05)
        self.assertEqual(self.provider_calls, 1)
        next_source = await self.source_for(self.study["session_id"])
        self.gate.set()
        done = await self.terminal(job)
        self.assertEqual(done["status"], "failed")
        self.assertEqual(done["error"]["code"], "STALE_SOURCE")
        self.assertIsNone(done["result_id"])
        current = await self.api("GET", "/sessions/" + self.study["session_id"], self.token)
        self.assertEqual(current["latest_seq"], 0)
        self.assertEqual(current["current_source_id"], next_source["source_id"])
        _, body = await self.upload(source=next_source)
        await self.api("POST", f"/sessions/{self.study['session_id']}/uploads", self.token, {**body, "source_id": self.source["source_id"]}, 409)

    async def test_out_of_order_frame_is_rejected_and_queue_is_bounded(self):
        self.gate = asyncio.Event()
        first, _ = await self.upload(2)
        job = await self.job(first)
        next_upload, _ = await self.upload(3)
        await self.job(next_upload, expected=429)
        self.gate.set(); await self.terminal(job)
        previous, _ = await self.upload(1)
        response = await self.job(previous, expected=409)
        self.assertEqual(response["error"]["details"]["reason"], "out_of_order_frame")

    async def test_permission_rejects_foreign_upload_job_result(self):
        upload, _ = await self.upload()
        done = await self.terminal(await self.job(upload))
        other = (await self.register())["access_token"]
        await self.api("GET", "/ocr-jobs/" + done["job_id"], other, expected=403)
        await self.api("GET", "/results/" + done["result_id"], other, expected=403)
        await self.job(upload, token=other, expected=403)

    async def test_provider_errors_remain_distinct_from_empty_result(self):
        for index, (mode, code) in enumerate([("busy", "OCR_BUSY"), ("timeout", "OCR_TIMEOUT"), ("invalid", "PROVIDER_INVALID_RESPONSE")]):
            self.mode = mode
            upload, _ = await self.upload(index)
            done = await self.terminal(await self.job(upload))
            self.assertEqual(done["status"], "failed")
            self.assertEqual(done["error"]["code"], code)
            self.assertIsNone(done["result_id"])

    async def test_source_idempotency_and_stale_version_can_retry_same_key(self):
        key = str(uuid4())
        body = {"source_id": str(uuid4()), "kind": "local_video", "width_px": 640, "height_px": 360, "duration_ms": 30000, "expected_version": 1}
        path = f"/sessions/{self.study['session_id']}/sources"
        await self.api("POST", path, self.token, body, 409, key)
        body["expected_version"] = self.source["session_version"]
        source = await self.api("POST", path, self.token, body, 201, key)
        replay = await self.api("POST", path, self.token, body, 200, key)
        self.assertEqual(source, replay)

    async def test_snapshot_pagination_and_cursor_filter_binding(self):
        results = []
        for index in range(3):
            upload, _ = await self.upload(index)
            results.append(await self.terminal(await self.job(upload)))
        path = f"/sessions/{self.study['session_id']}/results?through_seq=3&limit=1"
        first = await self.api("GET", path, self.token)
        from urllib.parse import quote
        second = await self.api("GET", path + "&cursor=" + quote(first["next_cursor"], safe=""), self.token)
        self.assertEqual([first["items"][0]["seq"], second["items"][0]["seq"]], [1, 2])
        await self.api("GET", path + "&after_seq=1&cursor=" + quote(first["next_cursor"], safe=""), self.token, expected=400)

    async def test_worker_replacement_recovers_expired_lease_and_fences_old_worker(self):
        task = self.app[STATE]["ocr_task"]
        task.cancel()
        with suppress(asyncio.CancelledError): await task
        upload, _ = await self.upload()
        job = await self.job(upload)
        original = self.app[STATE]["ocr_worker"]
        candidate = self.storage.repository.get_by_id(SERVICE, "job", job["job_id"])
        claimed = original.claim(candidate)
        old = self.storage.repository.raw(claimed.scope, "job", claimed.identifier)
        data = {**claimed.data, "lease_until_s": int(time.time()) - 1}
        self.store.transact(self.media.rows(claimed.scope, "job", data, old["revision"] + 1, old["revision"]))
        from lingualive_api.ocr_worker import OcrWorker
        replacement = OcrWorker(self.media, original.provider)
        await replacement.run_once()
        done = await self.terminal(job)
        self.assertEqual(done["status"], "succeeded")
        result = await self.api("GET", "/results/" + done["result_id"], self.token)
        uploaded = self.storage.repository.get_by_id(SERVICE, "upload", upload["upload_id"])
        self.assertFalse(original.succeed(claimed, uploaded, result["ocr"]))
        self.assertEqual((await self.api("GET", "/sessions/" + self.study["session_id"], self.token))["latest_seq"], 1)
        self.assertEqual(self.provider_calls, 1)

    async def test_upload_expiry_and_ended_session_do_not_reach_provider(self):
        upload, _ = await self.upload(do_put=False)
        with patch.object(self.storage.store, "clock", return_value=time.time() + 121):
            response = await self.client.session.put(upload["upload"]["url"], headers=upload["upload"]["headers"], data=self.image())
        self.assertEqual(response.status, 404)
        current = await self.api("GET", "/sessions/" + self.study["session_id"], self.token)
        await self.api("POST", f"/sessions/{self.study['session_id']}/end", self.token, {"expected_version": current["version"]})
        response = await self.job(upload, expected=409)
        self.assertEqual(response["error"]["code"], "SESSION_ENDED")
        self.assertEqual(self.provider_calls, 0)

    async def test_production_frontend_ocr_client_uses_real_upload_job_and_polling(self):
        image = Path(self.folder.name) / "synthetic.png"; image.write_bytes(self.image())
        root = Path(__file__).resolve().parents[2]
        process = await asyncio.create_subprocess_exec(shutil.which("node"), str(root / "tools/integration/ocr-client-check.mjs"), str(self.client.make_url("/")), str(image), cwd=root,
                                                       stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        self.assertEqual(process.returncode, 0, stderr.decode())
        self.assertEqual(len(json.loads(stdout)["checks"]), 8)

    async def test_browser_admin_permissions_do_not_become_internal_worker_authority(self):
        from lingualive_api.local_admin import LocalAdmin
        account = await self.register("scoped-admin@example.invalid")
        headers = {"X-Local-Client": "browser", "Authorization": "Bearer " + account["access_token"]}
        response = await self.client.post("/local-auth/verification/request", json={}, headers=headers)
        self.assertEqual(response.status, 200)
        messages = [json.loads(path.read_text()) for path in (self.storage.objects.root.parent / "mailbox").glob("*.json")]
        code = next(message["code"] for message in messages if message["to"] == "scoped-admin@example.invalid")
        response = await self.client.post("/local-auth/verification/confirm", json={"code": code}, headers=headers)
        self.assertEqual(response.status, 200)
        LocalAdmin(self.app[STATE]["authenticator"]).provision("scoped-admin@example.invalid", grant=True, reason="Test bounded browser admin")
        admin = await self.auth("login", {"email": "scoped-admin@example.invalid", "password": self.password})
        await self.api("GET", "/sessions/" + self.study["session_id"], admin["access_token"], expected=403)
        response = await self.client.get("/local-auth/admin/users", headers={"X-Local-Client": "browser", "Authorization": "Bearer " + admin["access_token"]})
        self.assertEqual(response.status, 200)
