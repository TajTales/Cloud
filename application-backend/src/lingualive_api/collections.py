from uuid import uuid4

from .errors import ApiError
from .learning import utc_now
from .persistence.catalog import Scope
from .persistence.errors import Conflict

OPERATIONS = ("listCollections", "createCollection", "patchCollection")


class CollectionService:
    def __init__(self, storage, learning, media):
        self.repo, self.learning, self.media = storage.repository, learning, media

    def view(self, actor, record):
        words = self.learning.all_records(actor, Scope("user", actor.user_id), "word")
        return {**record.data, "word_count": sum(word.data["collection_id"] == record.identifier for word in words)}

    def handle(self, operation, actor, body, params, query, headers, path, method):
        scope = Scope("user", actor.user_id)
        if operation == "listCollections":
            rows, cursor = self.repo.list(actor, scope, "collection", limit=int(query.get("limit", 20)), cursor=query.get("cursor"))
            return {"items": [self.view(actor, record) for record in rows], "next_cursor": cursor}, 200
        title = body["title"].strip()
        if not title:
            raise ApiError(400, "VALIDATION_ERROR", "Tên bộ từ không được để trống.")
        if operation == "patchCollection":
            old = self.repo.get(actor, scope, "collection", params["collection_id"])
            if not old:
                raise ApiError(404, "RESOURCE_NOT_FOUND", "Không tìm thấy bộ từ.")
            if old.revision != body["expected_version"]:
                raise Conflict("Collection version changed")
            updated = {**old.data, "title": title, "version": old.revision + 1}
            record = self.repo.save(actor, scope, "collection", updated, expected_revision=old.revision)
            return self.view(actor, record), 200
        if body["language"] not in {"ja", "zh"}:
            raise ApiError(400, "UNSUPPORTED_LANGUAGE", "Chỉ hỗ trợ tiếng Nhật/Trung.")
        reservation = self.learning.reserve(actor, method, path, headers, body)
        if reservation.resource:
            return self.view(actor, self.repo.get(actor, scope, "collection", reservation.resource["id"])), 200
        try:
            data = {"collection_id": str(uuid4()), "title": title, "language": body["language"], "version": 1, "created_at": utc_now()}
            self.media.finish(reservation, "collection", data["collection_id"], 201, self.media.rows(scope, "collection", data))
            return self.view(actor, self.repo.get(actor, scope, "collection", data["collection_id"])), 201
        except BaseException:
            self.media.storage.idempotency.abandon(reservation)
            raise
