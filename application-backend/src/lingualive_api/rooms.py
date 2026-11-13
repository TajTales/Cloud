"""Room metadata lifecycle. Meeting/chat/media credentials are not fabricated."""
import secrets
from uuid import uuid4

from .auth import Identity
from .errors import ApiError
from .learning import utc_now
from .persistence.catalog import Scope, digest
from .persistence.errors import Conflict

OPERATIONS = ("createRoom", "joinRoom", "getRoom", "leaveRoom", "closeRoom", "listRoomMembers")
SERVICE = Identity("local-room-service", ("admin",))
CAPACITY = 8  # Explicit local implementation limit; cloud D12 remains unapproved.


class RoomService:
    def __init__(self, storage, learning, media):
        self.storage, self.repo, self.store = storage, storage.repository, storage.store
        self.learning, self.media = learning, media

    def counter_key(self, room_id):
        return {"pk": "LOCAL_ROOM#MEMBER_COUNT", "sk": room_id}

    def membership(self, actor, room_id):
        row = self.store.get({"pk": Scope("room", room_id).pk, "sk": "MEMBERSHIP#" + digest(actor.user_id)})
        return self.repo.unpack(row) if row else None

    def snapshot(self, actor, room):
        member = self.membership(actor, room.identifier)
        if not member or member.data["left_at"] is not None:
            raise ApiError(403, "FORBIDDEN", "Bạn không còn là thành viên phòng này.")
        count = self.store.get(self.counter_key(room.identifier))
        session = self.repo.get_by_id(actor, "session", room.data["shared_session_id"])
        return {"room": {**room.data, "member_count": count["count"] if count else 0},
                "membership": self.member_view(member, room), "session": self.learning.session_view(session, actor)}

    def member_view(self, member, room):
        host = member.data["room_role"] == "host" and member.data["user_id"] == room.data["host_user_id"]
        active = room.data["status"] == "open" and member.data["left_at"] is None
        return {**member.data, "left_at": member.data["left_at"] or room.data["closed_at"], "capabilities": {"can_share_source": active and host, "can_send_ocr": active and host and self.media.enabled,
                                               "can_close_room": active and host, "can_record": False}}

    def handle(self, operation, actor, body, params, query, headers, path, method):
        if operation == "createRoom":
            if body["language"] not in {"ja", "zh"} or not body["title"].strip():
                raise ApiError(400, "VALIDATION_ERROR", "Nhập tên phòng và chọn tiếng Nhật/Trung.")
            room = None
        elif operation == "joinRoom":
            room_id = self.repo.lookup_room_code(actor, body["code"])
            if not room_id:
                raise ApiError(404, "ROOM_NOT_FOUND", "Mã phòng không tồn tại.")
            room = self.repo.get_by_id(SERVICE, "room", room_id)
        else:
            room = self.repo.get_by_id(SERVICE if operation == "leaveRoom" else actor, "room", params["room_id"])
            if not room:
                raise ApiError(404, "ROOM_NOT_FOUND", "Không tìm thấy phòng.")
        if operation == "getRoom":
            return self.snapshot(actor, room), 200
        if operation == "listRoomMembers":
            rows, cursor = self.repo.list(actor, room.scope, "membership", limit=int(query.get("limit", 20)), cursor=query.get("cursor"))
            items = []
            for row in rows:
                if row.data["left_at"] is not None or room.data["status"] == "closed":
                    continue
                profile = self.repo.get(SERVICE, Scope("user", row.data["user_id"]), "profile", row.data["user_id"])
                items.append({key: row.data[key] for key in ["membership_id", "user_id", "room_role", "joined_at"]} | {"display_name": profile.data["display_name"]})
            return {"items": items, "next_cursor": cursor}, 200
        reservation = self.learning.reserve(actor, method, path, headers, body)
        if reservation.resource:
            current = self.repo.get_by_id(SERVICE, "room", reservation.resource["id"])
            if operation == "leaveRoom":
                member = self.membership(actor, current.identifier)
                return {**{key: member.data[key] for key in ["room_id", "membership_id"]}, "left_at": member.data["left_at"] or current.data["closed_at"]}, 200
            return self.snapshot(actor, current), 200
        try:
            if operation == "createRoom":
                return self.create(actor, body, reservation)
            if room.data["status"] != "open":
                if operation == "closeRoom":
                    self.media.finish(reservation, "room", room.identifier, 200, [])
                    return self.snapshot(actor, room), 200
                raise ApiError(409, "ROOM_CLOSED", "Phòng đã đóng.")
            count = self.store.get(self.counter_key(room.identifier))
            member = self.membership(actor, room.identifier)
            if operation == "joinRoom":
                if member and member.data["left_at"] is None:
                    self.media.finish(reservation, "room", room.identifier, 200, [])
                    return self.snapshot(actor, room), 200
                if count["count"] >= CAPACITY:
                    raise ApiError(409, "ROOM_FULL", "Phòng đã đủ thành viên.")
                now = utc_now()
                membership = {"membership_id": member.identifier if member else str(uuid4()), "room_id": room.identifier,
                              "user_id": actor.user_id, "room_role": "member", "capabilities": {"can_share_source": False, "can_send_ocr": False, "can_close_room": False, "can_record": False},
                              "joined_at": now, "left_at": None}
                actions = self.media.rows(room.scope, "membership", membership, member.revision + 1 if member else 1, member.revision if member else 0)
                if not self.repo.raw(Scope("user", actor.user_id), "history", room.data["shared_session_id"]):
                    session = self.repo.get_by_id(SERVICE, "session", room.data["shared_session_id"])
                    history = {key: session.data[key] for key in ["session_id", "title", "mode", "language", "started_at", "ended_at"]} | {"started_at": now}
                    actions += self.media.rows(Scope("user", actor.user_id), "history", history)
                actions.append(self.store.put_action({**count, "count": count["count"] + 1, "revision": count["revision"] + 1}, count["revision"]))
                actions.append(self.media.guard(room))
            else:
                if not member:
                    raise ApiError(403, "FORBIDDEN", "Bạn không phải thành viên phòng.")
                host = room.data["host_user_id"] == actor.user_id
                if operation == "closeRoom" and not host:
                    raise ApiError(403, "FORBIDDEN", "Chỉ chủ phòng được đóng phòng.")
                if operation == "closeRoom" and room.revision != body["expected_version"]:
                    raise Conflict("Room version changed")
                if host:
                    actions = self.close(room, count)
                elif member.data["left_at"] is None:
                    actions = self.media.rows(room.scope, "membership", {**member.data, "left_at": utc_now()}, member.revision + 1, member.revision)
                    actions += [self.store.put_action({**count, "count": count["count"] - 1, "revision": count["revision"] + 1}, count["revision"]), self.media.guard(room)]
                else:
                    actions = []
            self.media.finish(reservation, "room", room.identifier, 200, actions)
            if operation == "leaveRoom":
                updated = self.membership(actor, room.identifier)
                current = self.repo.get_by_id(SERVICE, "room", room.identifier)
                return {**{key: updated.data[key] for key in ["room_id", "membership_id"]}, "left_at": updated.data["left_at"] or current.data["closed_at"]}, 200
            return self.snapshot(actor, self.repo.get_by_id(SERVICE, "room", room.identifier)), 200
        except BaseException:
            self.storage.idempotency.abandon(reservation)
            raise

    def create(self, actor, body, reservation):
        now, room_id, session_id = utc_now(), str(uuid4()), str(uuid4())
        code = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(8))
        room = {"room_id": room_id, "code": code, "title": body["title"].strip(), "language": body["language"],
                "host_user_id": actor.user_id, "shared_session_id": session_id, "shared_vocabulary_enabled": body["shared_vocabulary_enabled"],
                "status": "open", "version": 1, "created_at": now, "closed_at": None}
        session = {"session_id": session_id, "mode": "group", "owner_user_id": actor.user_id, "room_id": room_id,
                   "status": "active", "title": room["title"], "language": room["language"], "current_source_id": None,
                   "started_at": now, "ended_at": None, "version": 1, "latest_seq": 0}
        membership = {"membership_id": str(uuid4()), "room_id": room_id, "user_id": actor.user_id, "room_role": "host",
                      "capabilities": {"can_share_source": True, "can_send_ocr": self.media.enabled, "can_close_room": True, "can_record": False}, "joined_at": now, "left_at": None}
        history = {key: session[key] for key in ["session_id", "title", "mode", "language", "started_at", "ended_at"]}
        actions = self.media.rows(Scope("room", room_id), "room", room) + self.media.rows(Scope("room", room_id), "membership", membership)
        actions += self.media.rows(Scope("session", session_id), "session", session) + self.media.rows(Scope("user", actor.user_id), "history", history)
        actions.append(self.store.put_action({**self.counter_key(room_id), "count": 1, "revision": 1}))
        self.media.finish(reservation, "room", room_id, 201, actions)
        return self.snapshot(actor, self.repo.get_by_id(SERVICE, "room", room_id)), 201

    def close(self, room, count):
        now = utc_now()
        session = self.repo.get_by_id(SERVICE, "session", room.data["shared_session_id"])
        data = {**room.data, "status": "closed", "closed_at": now, "version": room.revision + 1}
        actions = self.media.rows(room.scope, "room", data, room.revision + 1, room.revision)
        actions += self.media.rows(session.scope, "session", {**session.data, "status": "ended", "ended_at": now, "version": session.revision + 1}, session.revision + 1, session.revision)
        # Closing the room ends presence for all memberships at closed_at.
        # Retain membership records so existing participants can read history.
        actions.append(self.store.put_action({**count, "count": 0, "revision": count["revision"] + 1}, count["revision"]))
        return actions
