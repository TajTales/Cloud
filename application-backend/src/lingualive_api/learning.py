"""Application handlers for the first real FE → API → local database flow."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .errors import ApiError
from .auth import Identity
from .persistence.catalog import Scope, digest
from .persistence.errors import Conflict, NotFound

OPERATIONS = ("getMe", "patchMe", "listVocabulary", "saveVocabulary", "deleteVocabulary", "reviewVocabulary",
              "createSession", "getSession", "endSession", "listHistory", "getStats")
CAPTURE_LIMITS = {"version": 1, "max_image_bytes": 1048576, "max_image_pixels": 4000000,
                  "max_long_edge_px": 1600, "frame_interval_ms": 2000, "max_in_flight": 1,
                  "content_types": ["image/jpeg", "image/png"]}


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class LearningService:
    def __init__(self, storage):
        self.storage, self.repo, self.store = storage, storage.repository, storage.store
        self.ocr_enabled = False
        self.ocr_languages = ("ja",)
        path = Path(__file__).resolve().parents[3] / "shared/demo-vocabulary.json"
        self.samples = {item["entry_id"]: item for item in json.loads(path.read_text())["entries"]}

    def profile(self, actor):
        record = self.repo.get(actor, Scope("user", actor.user_id), "profile", actor.user_id)
        if not record:
            raise NotFound("Profile not found")
        return record

    def all_records(self, actor, scope, kind):
        output, cursor = [], None
        for _ in range(200):
            page, cursor = self.repo.list(actor, scope, kind, limit=100, cursor=cursor)
            output.extend(page)
            if not cursor:
                return output
        raise ApiError(503, "FEATURE_NOT_CONFIGURED", "Dữ liệu vượt giới hạn tổng hợp local.")

    def session_view(self, record, actor=None):
        host = actor is None or actor.user_id == record.data["owner_user_id"]
        active = record.data["status"] == "active"
        source = self.repo.raw(record.scope, "source", record.data["current_source_id"]) if record.data["current_source_id"] else None
        return {**record.data, "capabilities": {"can_share_source": active and host, "can_send_ocr": active and host and self.ocr_enabled and record.data["language"] in self.ocr_languages,
                                               "can_close_room": active and host and record.data["mode"] == "group", "can_record": False},
                "capture_limits": CAPTURE_LIMITS, "current_source": self.repo.unpack(source).data if source else None}

    def history_view(self, actor, record):
        # Private history was written by create/join; leaving a room must not
        # make a user's entire history fail. This returns metadata, not content.
        session = self.repo.get_by_id(Identity("history-metadata-reader", ("admin",)), "session", record.data["session_id"])
        data = session.data
        ended = data["ended_at"]
        if data["room_id"]:
            member = self.store.get({"pk": Scope("room", data["room_id"]).pk, "sk": "MEMBERSHIP#" + digest(actor.user_id)})
            if member:
                left = self.repo.unpack(member).data["left_at"]
                ended = min(value for value in [ended, left] if value) if ended or left else None
        duration = None if not ended else max(0, int((datetime.fromisoformat(ended) - datetime.fromisoformat(record.data["started_at"])).total_seconds() * 1000))
        return {**record.data, "ended_at": ended, "duration_ms": duration,
                "saved_words_count": None, "playback_state": "unavailable"}

    def reserve(self, actor, method, path, headers, body):
        try:
            return self.storage.idempotency.reserve(actor, method, path, headers["Idempotency-Key"], body)
        except Conflict:
            raise ApiError(409, "IDEMPOTENCY_CONFLICT", "Khóa yêu cầu đang xử lý hoặc đã dùng cho nội dung khác.") from None

    def handle(self, operation, actor, body, params, query, headers, path, method):
        scope = Scope("user", actor.user_id)
        if operation == "getMe":
            return self.profile(actor).data, 200
        if operation == "patchMe":
            old = self.profile(actor)
            if old.revision != body["expected_version"]:
                raise Conflict("Profile version changed")
            changes = {key: value for key, value in body.items() if key != "expected_version"}
            if "display_name" in changes and not changes["display_name"].strip():
                raise ApiError(400, "VALIDATION_ERROR", "Tên hiển thị không được để trống.")
            if "timezone" in changes:
                try:
                    ZoneInfo(changes["timezone"])
                except (ZoneInfoNotFoundError, ValueError):
                    raise ApiError(400, "VALIDATION_ERROR", "Múi giờ không hợp lệ.") from None
            if changes.get("learning_language", "ja") not in {"ja", "zh"}:
                raise ApiError(400, "UNSUPPORTED_LANGUAGE", "Hiện hỗ trợ tiếng Nhật và tiếng Trung.")
            data = {**old.data, **changes, "version": old.revision + 1}
            return self.repo.save(actor, scope, "profile", data, expected_revision=old.revision).data, 200
        if operation == "listVocabulary":
            filters = {key: value for key, value in query.items() if key in {"language", "collection_id", "review_state"}}
            records, cursor = self.repo.list(actor, scope, "word", limit=int(query.get("limit", 20)), cursor=query.get("cursor"), filters=filters)
            return {"items": [record.data for record in records], "next_cursor": cursor}, 200
        if operation in {"deleteVocabulary", "reviewVocabulary"}:
            old = self.repo.get(actor, scope, "word", params["word_id"])
            if operation == "deleteVocabulary":
                if old:
                    self.repo.delete(actor, scope, "word", old.identifier, expected_revision=old.revision)
                return None, 204
            if not old:
                raise ApiError(404, "WORD_NOT_FOUND", "Không tìm thấy từ trong tài khoản này.")
            if old.revision != body["expected_version"]:
                raise Conflict("Vocabulary version changed")
            return self.repo.save(actor, scope, "word", {**old.data, "review_state": body["review_state"], "version": old.revision + 1}, expected_revision=old.revision).data, 200
        if operation == "saveVocabulary":
            sample = self.samples.get(body["entry_id"])
            if not sample or body["sense_id"] != "sample:v1:meaning" or body["language"] != "ja":
                raise ApiError(404, "WORD_NOT_FOUND", "Nguồn từ này chưa được kết nối. Hiện chỉ lưu được từ trong nội dung mẫu có ghi nguồn.")
            if body["occurrence"] is not None:
                raise ApiError(503, "FEATURE_NOT_CONFIGURED", "Từ từ nguồn OCR cần được tra qua lexicon thật trước khi lưu.")
            collection = self.repo.get(actor, scope, "collection", body["collection_id"]) if body["collection_id"] else None
            if body["collection_id"] and (not collection or collection.data["language"] != body["language"]):
                raise ApiError(404, "RESOURCE_NOT_FOUND", "Không tìm thấy bộ từ phù hợp.")
            reservation = self.reserve(actor, method, path, headers, body)
            if reservation.resource:
                old = self.repo.get(actor, scope, "word", reservation.resource["id"])
                if not old:
                    raise ApiError(409, "IDEMPOTENCY_CONFLICT", "Từ của yêu cầu cũ đã bị xóa. Hãy dùng yêu cầu mới.")
                return old.data, 200
            data = {"word_id": str(uuid4()), "scope": "personal", "owner_user_id": actor.user_id, "room_id": None,
                    "created_by": actor.user_id, "language": "ja", "entry_id": body["entry_id"], "sense_id": body["sense_id"],
                    "lemma": sample["word"], "reading": {"kana": sample["reading"], "romaji": sample.get("romaji"), "pinyin": None},
                    "meanings": [{"language": "vi", "text": sample["meaning"], "origin": "fixture"}],
                    "collection_id": body["collection_id"], "review_state": "new", "version": 1, "created_at": utc_now()}
            row, ref, unique = self.repo.rows(scope, "word", data, 1)
            unique_key = {"pk": unique["pk"], "sk": unique["sk"]}
            existing = self.store.get(unique_key)
            if existing:
                old = self.repo.get(actor, scope, "word", existing["entity_id"])
                self.storage.idempotency.complete(reservation, resource_type="word", resource_id=old.identifier, http_status=200)
                return old.data, 200
            try:
                self.storage.idempotency.complete(reservation, resource_type="word", resource_id=data["word_id"], http_status=201,
                                                  mutations=[self.store.put_action(item) for item in [row, ref, unique]] + ([self.store.check_action(self.repo.raw(scope, "collection", collection.identifier))] if collection else []))
            except Conflict:
                existing = self.store.get(unique_key)
                if not existing:
                    raise
                old = self.repo.get(actor, scope, "word", existing["entity_id"])
                self.storage.idempotency.complete(reservation, resource_type="word", resource_id=old.identifier, http_status=200)
                return old.data, 200
            return data, 201
        if operation == "createSession":
            if body["language"] not in {"ja", "zh"} or not body["title"].strip():
                raise ApiError(400, "VALIDATION_ERROR", "Chọn tiếng Nhật/Trung và nhập tên phiên học.")
            reservation = self.reserve(actor, method, path, headers, body)
            if reservation.resource:
                return self.session_view(self.repo.get_by_id(actor, "session", reservation.resource["id"])), 200
            data = {"session_id": str(uuid4()), "mode": "solo", "owner_user_id": actor.user_id, "room_id": None, "status": "active",
                    "title": body["title"].strip(), "language": body["language"], "current_source_id": None, "started_at": utc_now(),
                    "ended_at": None, "version": 1, "latest_seq": 0}
            mutations = []
            for kind, location, value in [("session", Scope("session", data["session_id"]), data),
                                           ("history", scope, {key: data[key] for key in ["session_id", "title", "mode", "language", "started_at", "ended_at"]})]:
                row, ref, _ = self.repo.rows(location, kind, value, 1)
                mutations += [self.store.put_action(row), self.store.put_action(ref)]
            self.storage.idempotency.complete(reservation, resource_type="session", resource_id=data["session_id"], http_status=201, mutations=mutations)
            return self.session_view(self.repo.get_by_id(actor, "session", data["session_id"])), 201
        if operation in {"getSession", "endSession"}:
            record = self.repo.get_by_id(actor, "session", params["session_id"])
            if not record:
                raise ApiError(404, "SESSION_NOT_FOUND", "Không tìm thấy phiên học.")
            if operation == "getSession":
                return self.session_view(record, actor), 200
            if record.data["mode"] != "solo":
                raise ApiError(503, "FEATURE_NOT_CONFIGURED", "Chưa kết nối vòng đời phòng nhóm.")
            if record.data["status"] == "active" and record.revision != body["expected_version"]:
                raise Conflict("Session version changed")
            reservation = self.reserve(actor, method, path, headers, body)
            if reservation.resource:
                return self.session_view(record), 200
            if record.data["status"] == "active":
                updated = {**record.data, "status": "ended", "ended_at": utc_now(), "version": record.revision + 1}
                row, _, _ = self.repo.rows(record.scope, "session", updated, record.revision + 1)
                mutations = [self.store.put_action(row, record.revision)]
            else:
                updated, mutations = record.data, []
            try:
                self.storage.idempotency.complete(reservation, resource_type="session", resource_id=record.identifier, http_status=200, mutations=mutations)
            except Conflict:
                self.storage.idempotency.abandon(reservation)
                raise
            return self.session_view(self.repo.get_by_id(actor, "session", record.identifier)), 200
        if operation == "listHistory":
            filters = {"language": query["language"]} if "language" in query else None
            records, cursor = self.repo.list(actor, scope, "history", limit=int(query.get("limit", 20)), cursor=query.get("cursor"), filters=filters, reverse=True)
            return {"items": [self.history_view(actor, record) for record in records if not query.get("mode") or record.data["mode"] == query["mode"]], "next_cursor": cursor}, 200
        if operation == "getStats":
            profile = self.profile(actor).data
            history = [self.history_view(actor, item) for item in self.all_records(actor, scope, "history")]
            now = datetime.now(timezone.utc)
            return {"timezone": profile["timezone"], "sampled_at": utc_now(), "study_duration_ms": sum(item["duration_ms"] or 0 for item in history),
                    "saved_words_count": len(self.all_records(actor, scope, "word")), "streak_days": None,
                    "weekly_sessions": sum(datetime.fromisoformat(item["started_at"]) >= now - timedelta(days=7) for item in history), "weekly_goal": None}, 200
        raise ApiError(503, "FEATURE_NOT_CONFIGURED", "Chức năng chưa được kết nối.")
