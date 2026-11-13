"""Contract-shaped source/upload/job/result services over local adapters."""
from datetime import datetime, timezone
import hashlib
import hmac
import json
from time import time
from uuid import uuid4

from .auth import Identity
from .errors import ApiError
from .images import validate_image
from .learning import utc_now
from .persistence.catalog import Scope, digest
from .persistence.errors import Conflict, NotFound

OPERATIONS = ("registerSource", "createFrameUpload", "createOcrJob", "getOcrJob", "listSessionResults", "getOcrResult")
SERVICE = Identity("local-ocr-worker", ("admin",))


def epoch_iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class MediaService:
    def __init__(self, storage, learning, *, enabled=False, languages=("ja",), clock=time):
        self.storage, self.repo, self.store = storage, storage.repository, storage.store
        self.learning, self.enabled, self.clock = learning, enabled, clock
        self.languages = languages

    def session(self, actor, session_id, *, write=False):
        record = self.repo.get_by_id(actor, "session", session_id)
        if not record:
            raise ApiError(404, "SESSION_NOT_FOUND", "Không tìm thấy phiên học.")
        if write:
            self.repo.authorize(actor, record.scope, "upload", write=True)
            if record.data["status"] != "active":
                raise ApiError(409, "SESSION_ENDED", "Phiên học đã kết thúc.")
            # Source publishing belongs to the owner/host, not system-role bypass.
            if actor.user_id != record.data["owner_user_id"]:
                raise ApiError(403, "FORBIDDEN", "Chỉ chủ nguồn được gửi frame nhận dạng.")
        return record

    def current(self, session, source_id):
        if session.data["current_source_id"] != source_id:
            raise ApiError(409, "STALE_SOURCE", "Nguồn học đã thay đổi. Bỏ frame của nguồn cũ.")

    def rows(self, scope, kind, data, revision=1, expected=0):
        row, ref, unique = self.repo.rows(scope, kind, data, revision)
        actions = [self.store.put_action(row, expected)]
        if not expected:
            actions.append(self.store.put_action(ref))
            if unique:
                actions.append(self.store.put_action(unique))
        return actions

    def guard(self, record):
        return self.store.check_action(self.repo.raw(record.scope, record.kind, record.identifier))

    def reserve(self, actor, method, path, headers, body):
        return self.learning.reserve(actor, method, path, headers, body)

    def finish(self, reservation, kind, identifier, status, actions):
        self.storage.idempotency.complete(reservation, resource_type=kind, resource_id=identifier, http_status=status, mutations=actions)

    def upload_view(self, record, origin):
        data = record.data
        signature = self.upload_signature(data)
        return {key: data[key] for key in ["upload_id", "session_id", "source_id", "frame_id"]} | {
            "upload": {"method": "PUT", "url": origin + "/local-uploads/" + data["upload_id"],
                       "headers": {"Content-Type": data["content_type"], "X-Upload-Token": signature},
                       "expires_at": epoch_iso(data["expires_at_s"])}}

    def upload_signature(self, data):
        message = "local-frame-upload:v1:" + digest({key: data[key] for key in ["upload_id", "session_id", "source_id", "frame_id", "expires_at_s"]})
        return hmac.new(self.storage.cursors.secret, message.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def job_view(record):
        return {key: value for key, value in record.data.items() if key not in {"upload_id", "deadline_at_s", "lease_owner", "lease_until_s", "lease_token", "attempt"}} | {
            "poll_after_ms": 500 if record.data["status"] in {"queued", "processing"} else None}

    def put_upload(self, upload_id, token, content, content_type):
        # A short-lived local upload capability, analogous to a signed PUT URL.
        upload = self.repo.get_by_id(SERVICE, "upload", upload_id)
        if not upload:
            raise ApiError(404, "RESOURCE_NOT_FOUND", "Upload không tồn tại hoặc đã hết hạn.")
        data = upload.data
        if not isinstance(token, str) or not hmac.compare_digest(token, self.upload_signature(data)):
            raise ApiError(403, "FORBIDDEN", "Không có quyền tải frame này.")
        session = self.session(Identity(self.repo.get_by_id(SERVICE, "session", data["session_id"]).data["owner_user_id"], ("user",)), data["session_id"], write=True)
        owner = self.repo.get(SERVICE, Scope("user", session.data["owner_user_id"]), "profile", session.data["owner_user_id"])
        if not owner or owner.data["status"] != "active":
            raise ApiError(403, "FORBIDDEN", "Tài khoản không hoạt động.")
        self.current(session, data["source_id"])
        if len(content) != data["size_bytes"] or content_type != data["content_type"]:
            raise ApiError(422, "INVALID_IMAGE", "Ảnh khác metadata đã đăng ký.")
        validate_image(content, content_type, expected_size=(data["width_px"], data["height_px"]))
        if data["state"] == "consumed":
            raise ApiError(409, "VERSION_CONFLICT", "Frame đã được đưa vào job.")
        reference = self.storage.objects.put(data["object_key"], [content], content_type, max_bytes=1048576)
        if data["state"] == "ready":
            return 204
        actions = self.rows(upload.scope, "object_ref", reference.dictionary())
        actions += self.rows(upload.scope, "upload", {**data, "state": "ready"}, upload.revision + 1, upload.revision)
        actions.append(self.guard(session))
        self.store.transact(actions)
        return 204

    def handle(self, operation, actor, body, params, query, headers, path, method, origin):
        if operation == "getOcrJob":
            record = self.repo.get_by_id(actor, "job", params["job_id"])
            if not record:
                raise ApiError(404, "RESOURCE_NOT_FOUND", "Không tìm thấy job.")
            return self.job_view(record), 200
        if operation == "getOcrResult":
            record = self.repo.get_by_id(actor, "result", params["result_id"])
            if not record:
                raise ApiError(404, "RESOURCE_NOT_FOUND", "Không tìm thấy kết quả.")
            raw = self.storage.read_object(actor, record.scope, record.data["object_key"], max_bytes=1048576)
            return json.loads(raw), 200
        session = self.session(actor, params["session_id"], write=operation != "listSessionResults")
        scope, now = session.scope, utc_now()
        if operation == "listSessionResults":
            through = int(query["through_seq"])
            if through > session.data["latest_seq"]:
                raise ApiError(400, "VALIDATION_ERROR", "Watermark vượt quá phiên hiện tại.")
            after = int(query.get("after_seq", 0))
            filters = {"source_id": query["source_id"]} if "source_id" in query else None
            binding = {"session_id": session.identifier, "after_seq": after, "through_seq": through, "source_id": query.get("source_id")}
            cursor = query.get("cursor")
            # Bind consumer filters as well as the repository's snapshot watermark.
            if cursor:
                decoded = self.storage.cursors.decode(cursor, {"pk": scope.pk, **binding})
                cursor = decoded["sk"]
            records, next_cursor = self.repo.list(actor, scope, "result", limit=int(query.get("limit", 20)), cursor=cursor,
                                                  filters=filters, through_seq=through)
            if next_cursor:
                next_cursor = self.storage.cursors.encode({"pk": scope.pk, **binding}, {"pk": scope.pk, "sk": next_cursor})
            keys = self.repo.catalog.definitions["ResultManifest"]["properties"]
            return {"items": [{key: record.data[key] for key in keys} for record in records if record.data["seq"] > after],
                    "next_cursor": next_cursor, "through_seq": through}, 200
        reservation = self.reserve(actor, method, path, headers, body)
        if reservation.resource:
            kind = reservation.resource["type"]
            record = self.repo.get_by_id(actor, kind, reservation.resource["id"])
            if not record:
                raise ApiError(409, "VERSION_CONFLICT", "Tài nguyên của yêu cầu cũ không còn sẵn sàng.")
            return (record.data if kind == "source" else self.upload_view(record, origin) if kind == "upload" else self.job_view(record)), 200
        try:
            return self.mutate(operation, actor, body, session, reservation, now, origin)
        except BaseException:
            # No durable mutation is made outside the completion transaction.
            self.storage.idempotency.abandon(reservation)
            raise

    def mutate(self, operation, actor, body, session, reservation, now, origin):
        scope = session.scope
        if operation == "registerSource":
            if session.revision != body["expected_version"]:
                raise Conflict("Session version changed")
            previous = self.repo.get(actor, scope, "source", session.data["current_source_id"]) if session.data["current_source_id"] else None
            if body["width_px"] * body["height_px"] > 100000000 or max(body["width_px"], body["height_px"]) > 32768:
                raise ApiError(400, "VALIDATION_ERROR", "Nguồn video có kích thước không hợp lệ.")
            source = {key: body[key] for key in ["source_id", "kind", "width_px", "height_px", "duration_ms"]} | {
                "session_id": session.identifier, "source_index": previous.data["source_index"] + 1 if previous else 1,
                "started_at": now, "timeline_origin_ms": 0, "session_version": session.revision + 1}
            if source["kind"] == "screen_share" and source["duration_ms"] is not None:
                raise ApiError(400, "VALIDATION_ERROR", "Chia sẻ màn hình không có thời lượng video cố định.")
            updated = {**session.data, "current_source_id": source["source_id"], "version": session.revision + 1}
            self.finish(reservation, "source", source["source_id"], 201,
                        self.rows(scope, "source", source) + self.rows(scope, "session", updated, session.revision + 1, session.revision))
            return source, 201
        if operation == "createFrameUpload":
            self.current(session, body["source_id"])
            source = self.repo.get(actor, scope, "source", body["source_id"])
            if body["width_px"] * body["height_px"] > 4000000 or abs(body["width_px"] / body["height_px"] / (source.data["width_px"] / source.data["height_px"]) - 1) > .02:
                raise ApiError(400, "VALIDATION_ERROR", "Frame cần giữ đúng tỷ lệ nguồn video.")
            if source.data["duration_ms"] is not None and body["media_time_ms"] > source.data["duration_ms"] + 1000:
                raise ApiError(400, "VALIDATION_ERROR", "Mốc frame nằm ngoài video.")
            upload_id = str(uuid4())
            data = {**body, "session_id": session.identifier, "upload_id": upload_id,
                    "object_key": f"frames/tmp/{session.identifier}/{upload_id}", "state": "awaiting", "expires_at_s": int(self.clock()) + 120}
            self.finish(reservation, "upload", upload_id, 201, self.rows(scope, "upload", data) + [self.guard(session)])
            return self.upload_view(self.repo.get(actor, scope, "upload", upload_id), origin), 201
        if not self.enabled:
            raise ApiError(503, "FEATURE_NOT_CONFIGURED", "Nhận dạng OCR chưa được bật.")
        if session.data["language"] not in self.languages:
            raise ApiError(422, "UNSUPPORTED_LANGUAGE", "Chưa cấu hình provider cho ngôn ngữ này.")
        upload = self.repo.get_by_id(actor, "upload", body["upload_id"])
        if not upload or upload.scope != scope or upload.data["frame_id"] != body["frame_id"]:
            raise ApiError(404, "RESOURCE_NOT_FOUND", "Không tìm thấy upload phù hợp với frame/phiên này.")
        self.current(session, upload.data["source_id"])
        unique_key = self.repo.uniqueness(scope, "job", upload.data)
        existing = self.store.get(unique_key)
        if existing:
            old = self.repo.get(actor, scope, "job", existing["entity_id"])
            if old.data["upload_id"] != upload.identifier:
                raise ApiError(409, "IDEMPOTENCY_CONFLICT", "Frame này đã được gắn với upload khác.")
            self.finish(reservation, "job", old.identifier, 200, [])
            return self.job_view(old), 200
        if upload.data["state"] != "ready":
            raise ApiError(409, "UPLOAD_NOT_READY", "Frame chưa được tải lên thành công.")
        slot_key = {"pk": "LOCAL_OCR#SLOT", "sk": session.identifier}
        slot = self.store.get(slot_key, include_expired=True)
        if slot and slot["expires_at_s"] > self.clock():
            raise ApiError(429, "RATE_LIMITED", "Phiên học đang xử lý một frame. Vui lòng chờ.", retryable=True)
        order_key = {"pk": "LOCAL_OCR#FRAME_ORDER", "sk": upload.data["source_id"]}
        order = self.store.get(order_key)
        if order and upload.data["frame_index"] <= order["frame_index"]:
            raise ApiError(409, "VERSION_CONFLICT", "Frame đến sai thứ tự.", details={"reason": "out_of_order_frame"})
        job_id = str(uuid4())
        data = {key: upload.data[key] for key in ["session_id", "source_id", "frame_id", "frame_index", "media_time_ms"]} | {
            "job_id": job_id, "status": "queued", "result_id": None, "error": None, "created_at": now, "updated_at": now,
            "upload_id": upload.identifier, "deadline_at_s": int(self.clock()) + 60,
            "lease_owner": None, "lease_until_s": None, "lease_token": None, "attempt": 0}
        actions = self.rows(scope, "job", data)
        actions += self.rows(scope, "upload", {**upload.data, "state": "consumed"}, upload.revision + 1, upload.revision)
        actions += [self.guard(session), self.store.put_action({**slot_key, "job_id": job_id, "expires_at_s": data["deadline_at_s"], "revision": slot["revision"] + 1 if slot else 1}, slot["revision"] if slot else 0),
                    self.store.put_action({**order_key, "frame_index": data["frame_index"], "revision": order["revision"] + 1 if order else 1}, order["revision"] if order else 0)]
        self.finish(reservation, "job", job_id, 202, actions)
        return self.job_view(self.repo.get(actor, scope, "job", job_id)), 202
