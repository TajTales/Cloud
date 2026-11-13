"""Durable local polling worker. HTTP raw OCR only; no Gateway binary WS."""
import asyncio
import json
import logging
from time import time
from uuid import uuid4

import aiohttp

from .contracts import strict_json
from .errors import ApiError
from .learning import utc_now
from .media import SERVICE
from .persistence.catalog import Scope
from .persistence.errors import Conflict, StorageUnavailable

LOGGER = logging.getLogger("lingualive.ocr")


class HttpOcrProvider:
    def __init__(self, url, *, allow_test_provider=False):
        self.url, self.allow_test_provider = url, allow_test_provider
        self.http = None
        self.name = None

    async def __aenter__(self):
        self.http = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20), trust_env=False)
        return self

    async def __aexit__(self, *_):
        await self.http.close()

    async def read_json(self, response):
        chunks, length = [], 0
        async for chunk in response.content.iter_chunked(65536):
            length += len(chunk)
            if length > 1048576:
                raise ApiError(502, "PROVIDER_INVALID_RESPONSE", "Kết quả OCR vượt giới hạn.")
            chunks.append(chunk)
        content = b"".join(chunks)
        try:
            return strict_json(content)
        except (ValueError, UnicodeDecodeError):
            raise ApiError(502, "PROVIDER_INVALID_RESPONSE", "Provider OCR trả dữ liệu không hợp lệ.") from None

    async def scan(self, content, content_type, language="ja"):
        try:
            async with self.http.get(self.url + "/health") as response:
                health = await self.read_json(response)
                name = health.get("provider", "") if isinstance(health, dict) else ""
                if response.status != 200 or not isinstance(name, str) or not name or health.get("ready") is False:
                    raise ApiError(503, "PROVIDER_UNAVAILABLE", "Provider OCR chưa sẵn sàng.", retryable=True)
                if not self.allow_test_provider and any(part in name.lower() for part in ["dummy", "fixture", "synthetic"]):
                    raise ApiError(503, "PROVIDER_UNAVAILABLE", "Chế độ thực không dùng provider minh họa.")
                if (isinstance(health.get("languages"), list) and language not in health["languages"]) or (language != "ja" and "languages" not in health and not self.allow_test_provider):
                    raise ApiError(422, "UNSUPPORTED_LANGUAGE", "Provider không hỗ trợ ngôn ngữ của phiên học.")
                self.name = name
            async with self.http.post(self.url + "/ocr", data=content, headers={"Content-Type": content_type}) as response:
                result = await self.read_json(response)
                if response.status in {429, 503}:
                    raise ApiError(503, "OCR_BUSY", "Provider OCR đang bận.", retryable=True)
                if response.status == 504:
                    raise ApiError(504, "OCR_TIMEOUT", "Nhận dạng ảnh quá thời gian.", retryable=True)
                if response.status != 200 or not isinstance(result, dict) or "error" in result:
                    raise ApiError(502, "PROVIDER_UNAVAILABLE", "Không nhận dạng được frame này.", retryable=True)
                return result
        except asyncio.TimeoutError:
            raise ApiError(504, "OCR_TIMEOUT", "Nhận dạng ảnh quá thời gian.", retryable=True) from None
        except aiohttp.ClientError:
            raise ApiError(503, "PROVIDER_UNAVAILABLE", "Chưa kết nối được dịch vụ OCR.", retryable=True) from None


class RoutedOcrProvider:
    def __init__(self, japanese_url, chinese_url=None, *, allow_test_provider=False):
        self.providers = {"ja": HttpOcrProvider(japanese_url, allow_test_provider=allow_test_provider)}
        if chinese_url:
            self.providers["zh"] = HttpOcrProvider(chinese_url, allow_test_provider=allow_test_provider)
        self.name = None

    async def __aenter__(self):
        for provider in self.providers.values():
            await provider.__aenter__()
        return self

    async def __aexit__(self, *args):
        for provider in self.providers.values():
            await provider.__aexit__(*args)

    async def scan(self, content, content_type, language="ja"):
        provider = self.providers.get(language)
        if not provider:
            raise ApiError(422, "UNSUPPORTED_LANGUAGE", "Chưa có provider cho ngôn ngữ này.")
        result = await provider.scan(content, content_type, language)
        self.name = provider.name
        return result


class OcrWorker:
    def __init__(self, media, provider, *, clock=time):
        self.media, self.provider, self.clock = media, provider, clock
        self.repo, self.store = media.repo, media.store
        self.owner = "local-worker-" + str(uuid4())

    def candidates(self):
        output = []
        for status in ["queued", "processing"]:
            rows, _ = self.repo.operational_page(SERVICE, "job", status=status, limit=100)
            output.extend(row for row in rows if status == "queued" or row.data["lease_until_s"] <= self.clock())
        return output

    def release_slot(self, job):
        key = {"pk": "LOCAL_OCR#SLOT", "sk": job.data["session_id"]}
        slot = self.store.get(key, include_expired=True)
        return [self.store.delete_action(key, slot["revision"])] if slot and slot["job_id"] == job.identifier else []

    def failure(self, job, code, message, *, retryable=False, expired=False):
        data = {**job.data, "status": "expired" if expired else "failed", "updated_at": utc_now(),
                "error": {"code": code, "message": message, "details": {}, "retryable": retryable},
                "result_id": None, "lease_owner": None, "lease_until_s": None, "lease_token": None}
        self.store.transact(self.media.rows(job.scope, "job", data, job.revision + 1, job.revision) + self.release_slot(job))

    def claim(self, candidate):
        job = self.repo.get_by_id(SERVICE, "job", candidate.identifier)
        if not job or job.revision != candidate.revision or job.data["status"] not in {"queued", "processing"}:
            return None
        if job.data["status"] == "processing" and job.data["lease_until_s"] > self.clock():
            return None
        if job.data["deadline_at_s"] <= self.clock() or job.data["attempt"] >= 3:
            self.failure(job, "JOB_EXPIRED", "Job OCR đã hết hạn.", expired=True)
            return None
        session = self.repo.get_by_id(SERVICE, "session", job.data["session_id"])
        if session.data["status"] != "active" or session.data["current_source_id"] != job.data["source_id"]:
            self.failure(job, "STALE_SOURCE", "Nguồn hoặc phiên học đã thay đổi.")
            return None
        try:
            self.media.session(type(SERVICE)(session.data["owner_user_id"], ("user",)), session.identifier, write=True)
        except ApiError:
            self.failure(job, "FORBIDDEN", "Không còn quyền gửi frame trong phiên này.")
            return None
        profile = self.repo.get(SERVICE, Scope("user", session.data["owner_user_id"]), "profile", session.data["owner_user_id"])
        if not profile or profile.data["status"] != "active":
            self.failure(job, "FORBIDDEN", "Tài khoản không còn hoạt động.")
            return None
        data = {**job.data, "status": "processing", "updated_at": utc_now(), "attempt": job.data["attempt"] + 1,
                "lease_owner": self.owner, "lease_until_s": int(self.clock()) + 30, "lease_token": str(uuid4())}
        self.store.transact(self.media.rows(job.scope, "job", data, job.revision + 1, job.revision) + [self.media.guard(session)])
        return self.repo.get_by_id(SERVICE, "job", job.identifier)

    def content(self, job):
        upload = self.repo.get_by_id(SERVICE, "upload", job.data["upload_id"])
        if not upload:
            raise ApiError(410, "UPLOAD_EXPIRED", "Frame đã hết hạn.")
        return upload, self.media.storage.read_object(SERVICE, upload.scope, upload.data["object_key"])

    def succeed(self, claimed, upload, raw):
        contracts = self.repo.catalog.contracts
        if contracts.issues(raw, {"$ref": "./schemas/ocr-provider.schema.json#/definitions/Success"}):
            raise ApiError(502, "PROVIDER_INVALID_RESPONSE", "Kết quả OCR sai raw schema.")
        for _ in range(4):
            job = self.repo.get_by_id(SERVICE, "job", claimed.identifier)
            if job.data["status"] != "processing" or job.data["lease_token"] != claimed.data["lease_token"] or job.data["lease_until_s"] <= self.clock():
                return False
            session = self.repo.get_by_id(SERVICE, "session", job.data["session_id"])
            if session.data["status"] != "active" or session.data["current_source_id"] != job.data["source_id"]:
                self.failure(job, "STALE_SOURCE", "Đã bỏ kết quả của nguồn cũ.")
                return False
            result_id = str(uuid4())
            manifest = {key: job.data[key] for key in ["job_id", "session_id", "source_id", "frame_id", "frame_index", "media_time_ms"]} | {
                "result_id": result_id, "seq": session.data["latest_seq"] + 1, "created_at": utc_now()}
            public = {**manifest, "language": session.data["language"], "provider": self.provider.name,
                      "image": {key: upload.data[key] for key in ["width_px", "height_px"]}, "ocr": raw}
            if contracts.issues(public, {"$ref": "./schemas/application.schema.json#/definitions/PublicResult"}):
                raise ApiError(502, "PROVIDER_INVALID_RESPONSE", "Kết quả OCR hoặc tọa độ không hợp lệ.")
            for paragraph in raw["paragraphs"]:
                for box in [paragraph["box"], *[word["box"] for word in paragraph["words"]]]:
                    if any(box[axis] - box[size] / 2 < -.000001 or box[axis] + box[size] / 2 > 1.000001 for axis, size in [("center_x", "width"), ("center_y", "height")]):
                        raise ApiError(502, "PROVIDER_INVALID_RESPONSE", "Tọa độ OCR nằm ngoài ảnh.")
            content = json.dumps(public, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()
            if len(content) > 1048576:
                raise ApiError(502, "PROVIDER_INVALID_RESPONSE", "Kết quả OCR vượt giới hạn lưu trữ.")
            reference = self.media.storage.objects.put(f"ocr/{session.identifier}/{result_id}.json", [content], "application/json", max_bytes=1048576)
            result = {**manifest, "object_key": reference.object_key, "sha256": reference.sha256, "schema_version": "0.1.0-draft.1"}
            updated = {**job.data, "status": "succeeded", "result_id": result_id, "error": None, "updated_at": utc_now(),
                       "lease_owner": None, "lease_until_s": None, "lease_token": None}
            session_data = {**session.data, "latest_seq": manifest["seq"], "version": session.revision + 1}
            actions = self.media.rows(job.scope, "object_ref", reference.dictionary()) + self.media.rows(job.scope, "result", result)
            actions += self.media.rows(job.scope, "job", updated, job.revision + 1, job.revision)
            actions += self.media.rows(session.scope, "session", session_data, session.revision + 1, session.revision) + self.release_slot(job)
            try:
                self.store.transact(actions)
                return True
            except Conflict:
                continue
        raise Conflict("Session changed repeatedly during result commit")

    async def run_once(self):
        candidates = await asyncio.to_thread(self.candidates)
        for candidate in candidates:
            try:
                claimed = await asyncio.to_thread(self.claim, candidate)
                if not claimed:
                    continue
                try:
                    upload, content = await asyncio.to_thread(self.content, claimed)
                    session = await asyncio.to_thread(self.repo.get_by_id, SERVICE, "session", claimed.data["session_id"])
                    raw = await self.provider.scan(content, upload.data["content_type"], session.data["language"])
                    await asyncio.to_thread(self.succeed, claimed, upload, raw)
                except ApiError as error:
                    current = await asyncio.to_thread(self.repo.get_by_id, SERVICE, "job", claimed.identifier)
                    if current and current.data["lease_token"] == claimed.data["lease_token"]:
                        await asyncio.to_thread(self.failure, current, error.code, error.message, retryable=error.retryable)
            except Conflict:
                continue
        return len(candidates)

    async def run(self):
        while True:
            try:
                await self.run_once()
            except Exception as error:
                # Preserve durable leases for recovery. Never log image/token/body.
                LOGGER.error(json.dumps({"event": "ocr_worker_iteration_failed", "exception_type": type(error).__name__}))
            await asyncio.sleep(.25)
