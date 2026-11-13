"""Real model → real application HTTP → real isolated DB → immutable result."""
import asyncio
import io
import json
import os
from pathlib import Path
import tempfile
from time import monotonic
from unittest.mock import patch
from uuid import uuid4

from aiohttp import CookieJar
from aiohttp.test_utils import TestClient, TestServer
from PIL import Image

from lingualive_api.app import create_app
from lingualive_api.config import Settings
from lingualive_api.persistence.dynamo import DynamoStore
from lingualive_api.persistence.settings import PersistenceSettings

ROOT = Path(__file__).resolve().parents[2]
INPUTS = ROOT / "application-backend/.local-data/ocr-acceptance"


async def run():
    cases = json.loads((INPUTS / "cases.json").read_text())
    results = []
    with tempfile.TemporaryDirectory() as directory:
        values = {"APP_ENV": "test", "PERSISTENCE_ENABLED": "1", "LOCAL_AUTH_ENABLED": "1", "OCR_ENABLED": "1",
                  "OCR_SERVICE_URL": "http://127.0.0.1:8080", "OCR_CHINESE_SERVICE_URL": "http://127.0.0.1:8083", "DYNAMODB_ENDPOINT": "http://127.0.0.1:8000",
                  "DYNAMODB_TABLE": "lingualive-test-real-ocr-" + uuid4().hex, "APP_DATA_DIR": directory}
        store = DynamoStore(PersistenceSettings.from_environment(values)); store.ensure_table()
        client = None
        try:
            with patch.dict(os.environ, values):
                client = TestClient(TestServer(create_app(Settings.from_environment(values))), cookie_jar=CookieJar(unsafe=True))
                await client.start_server()
            response = await client.post("/local-auth/register", headers={"X-Local-Client": "browser"}, json={"email": uuid4().hex + "@example.invalid", "password": "Real model integration test!", "display_name": "Real OCR acceptance"})
            assert response.status == 201, await response.text()
            auth = (await response.json())["data"]
            async def api(method, path, body=None, status=200):
                headers = {"Authorization": "Bearer " + auth["access_token"]}
                if method == "POST": headers["Idempotency-Key"] = str(uuid4())
                response = await client.request(method, "/api/v1" + path, headers=headers, json=body)
                result = await response.json()
                assert response.status == status, result
                return result["data"]
            sessions = {}
            for case in cases:
                language = case.get("language", "ja")
                if language not in sessions:
                    sessions[language] = await api("POST", "/sessions", {"mode": "solo", "title": "Real model acceptance", "language": language}, 201)
                session = sessions[language]
                started = monotonic()
                content = (INPUTS / case["image"]).read_bytes()
                with Image.open(io.BytesIO(content)) as image:
                    width, height = image.size
                current = await api("GET", "/sessions/" + session["session_id"])
                source = await api("POST", f"/sessions/{session['session_id']}/sources", {"source_id": str(uuid4()), "kind": "local_video", "width_px": width, "height_px": height, "duration_ms": 10000, "expected_version": current["version"]}, 201)
                frame = {"source_id": source["source_id"], "frame_id": str(uuid4()), "frame_index": 0, "media_time_ms": 1000,
                         "captured_at": "2026-11-13T00:00:00.000Z", "width_px": width, "height_px": height, "content_type": "image/png", "size_bytes": len(content)}
                upload = await api("POST", f"/sessions/{session['session_id']}/uploads", frame, 201)
                response = await client.session.put(upload["upload"]["url"], data=content, headers=upload["upload"]["headers"])
                assert response.status == 204, await response.text()
                job = await api("POST", f"/sessions/{session['session_id']}/ocr-jobs", {"upload_id": upload["upload_id"], "frame_id": frame["frame_id"]}, 202)
                deadline = monotonic() + 70
                while job["status"] in {"queued", "processing"}:
                    assert monotonic() < deadline, "OCR job timed out"
                    await asyncio.sleep(.25)
                    job = await api("GET", "/ocr-jobs/" + job["job_id"])
                assert job["status"] == "succeeded", job
                result = await api("GET", "/results/" + job["result_id"])
                assert ("meikiocr" if language == "ja" else "rapidocr") in result["provider"].lower(), result["provider"]
                actual = "".join(paragraph["full_text"] for paragraph in result["ocr"]["paragraphs"])
                expected = case["expected_text"]
                passed = actual.replace(" ", "").replace("\n", "") == expected
                if case["name"] == "empty": passed = result["ocr"]["paragraphs"] == []
                results.append({"case": case["name"], "pass": passed, "expected": expected, "actual": actual,
                                "provider": result["provider"], "ocr_elapsed_ms": result["ocr"]["elapsed_ms"],
                                "total_ms": round((monotonic() - started) * 1000), "vertical_detected": any(p["is_vertical"] for p in result["ocr"]["paragraphs"]),
                                "public_schema_validated_by_api": True})
            for language, session in sessions.items():
                current = await api("GET", "/sessions/" + session["session_id"])
                page = await api("GET", f"/sessions/{session['session_id']}/results?through_seq={current['latest_seq']}")
                assert len(page["items"]) == sum(case.get("language", "ja") == language for case in cases)
                await api("POST", f"/sessions/{session['session_id']}/end", {"expected_version": current["version"]})
            report = {"status": "PASS" if all(item["pass"] for item in results) else "FAIL", "cases": results,
                      "real_model": True, "input_is_rendered_test_fixture": True, "browser_dom_tested": False,
                      "isolated_table_deleted_after_run": True, "application_user_data_seeded": False}
            (INPUTS / "real-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["status"] == "PASS" else 1
        finally:
            if client: await client.close()
            assert store.table.startswith("lingualive-test-real-ocr-")
            store.call("delete_table", TableName=store.table); store.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
