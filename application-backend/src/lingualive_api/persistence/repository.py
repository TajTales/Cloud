"""Scoped, conditional persistence. Caller identity must be verified by the API.

This is a blocking repository, not a public CRUD API or authentication provider.
"""
from dataclasses import dataclass
from time import time

from ..contracts import strict_json
from .catalog import Catalog, GLOBAL_IDS, SPECS, Scope, canonical, digest
from .errors import Conflict, Forbidden, IntegrityFailure, InvalidRecord, NotFound


@dataclass(frozen=True)
class Record:
    kind: str
    identifier: str
    scope: Scope
    data: dict
    revision: int


class Repository:
    def __init__(self, store, contracts, cursors, *, clock=time):
        self.store, self.catalog, self.cursors, self.clock = store, Catalog(contracts), cursors, clock

    def unpack(self, row):
        if not row or row.get("model_version") != 1:
            raise IntegrityFailure("Entity storage version is missing or unsupported")
        data = strict_json(row["payload"])
        self.catalog.validate(row["entity_kind"], data)
        return Record(row["entity_kind"], row["entity_id"], Scope(row["scope_kind"], row["scope_id"]), data, row["revision"])

    def raw(self, scope, kind, identifier):
        reference = self.store.get(self.catalog.reference_key(scope, kind, identifier))
        if not reference:
            return None
        if reference["target_pk"] != scope.pk:
            raise Forbidden("Resource belongs to another scope")
        row = self.store.get({"pk": reference["target_pk"], "sk": reference["target_sk"]})
        if not row:
            raise IntegrityFailure("Resource reference points to a missing row")
        return row

    def authorize(self, actor, scope, kind, *, write=False):
        if not getattr(actor, "user_id", None):
            raise Forbidden("A verified caller identity is required")
        if "admin" in actor.roles:
            return []
        if scope.kind == "system":
            raise Forbidden("System records require administrator/service authority")
        if scope.kind == "user":
            if actor.user_id != scope.identifier:
                raise Forbidden("Private scope belongs to another user")
            return []
        root = self.store.get({"pk": scope.pk, "sk": "META"})
        if not root:
            raise NotFound("Parent scope not found")
        parent = self.unpack(root)
        if scope.kind == "session" and parent.data["room_id"] is None:
            if parent.data["owner_user_id"] != actor.user_id:
                raise Forbidden("Session belongs to another user")
            return [root]
        room_scope = scope if scope.kind == "room" else Scope("room", parent.data["room_id"])
        room = root if scope.kind == "room" else self.store.get({"pk": room_scope.pk, "sk": "META"})
        if not room:
            raise NotFound("Room not found")
        room_data = self.unpack(room).data
        if scope.kind == "room" and kind in {"shared_word", "occurrence"} and not room_data["shared_vocabulary_enabled"]:
            raise Forbidden("Shared vocabulary is disabled for this room")
        member = self.store.get({"pk": room_scope.pk, "sk": "MEMBERSHIP#" + digest(actor.user_id)})
        if not member or self.unpack(member).data["left_at"] is not None:
            raise Forbidden("Active room membership is required")
        membership = self.unpack(member).data
        host = membership["room_role"] == "host" and room_data["host_user_id"] == actor.user_id
        if write:
            if room_data["status"] != "open":
                raise Forbidden("Closed room is read-only")
            allowed = host or kind in {"shared_word", "occurrence"}
            if scope.kind == "session":
                capability = "can_share_source" if kind == "source" else "can_send_ocr"
                allowed = host or (kind in {"source", "upload", "job"} and membership["capabilities"][capability])
            if not allowed:
                raise Forbidden("Room role cannot write this entity")
        return list({(item["pk"], item["sk"]): item for item in [root, room, member]}.values())

    def get(self, actor, scope, kind, identifier):
        self.authorize(actor, scope, kind)
        row = self.raw(scope, kind, identifier)
        return self.unpack(row) if row else None

    def get_by_id(self, actor, kind, identifier):
        if kind not in GLOBAL_IDS:
            raise InvalidRecord("This entity requires an explicit owner/room scope")
        reference = self.store.get(self.catalog.reference_key(Scope("system", "lookup"), kind, identifier))
        if not reference:
            return None
        scope = Scope(reference["scope_kind"], reference["scope_id"])
        return self.get(actor, scope, kind, identifier)

    def uniqueness(self, scope, kind, data):
        if kind in {"word", "shared_word"}:
            return {"pk": "UNIQUE#WORD#" + digest(scope.pk), "sk": digest([data["language"], data["entry_id"], data["sense_id"]])}
        if kind == "room":
            return {"pk": "UNIQUE#ROOM_CODE", "sk": digest(data["code"])}
        if kind == "result":
            return {"pk": "UNIQUE#RESULT_SEQ#" + digest(scope.pk), "sk": str(data["seq"])}
        if kind == "job":
            return {"pk": "UNIQUE#JOB_FRAME#" + digest(scope.pk), "sk": digest([data["source_id"], data["frame_id"]])}
        return None

    def rows(self, scope, kind, data, revision):
        self.catalog.validate(kind, data)
        key = self.catalog.key(scope, kind, data)
        identifier = self.catalog.identifier(kind, data)
        row = {**key, "entity_kind": kind, "entity_id": identifier, "scope_kind": scope.kind, "scope_id": scope.identifier,
               "model_version": 1, "revision": revision, "payload": canonical(data)}
        if kind in {"upload", "connection", "ticket"}:
            row["expires_at_s"] = data["expires_at_s"]
        for name in ["language", "collection_id", "review_state", "status", "source_id"]:
            if name in data:
                row[name] = data[name]
        if kind in {"profile", "room", "job"}:
            row.update(gsi_pk=kind.upper() + "#" + (data["status"] if kind == "job" else "all"),
                       gsi_sk=data.get("created_at", "") + "#" + identifier)
        ref = {**self.catalog.reference_key(scope, kind, identifier), "target_pk": key["pk"], "target_sk": key["sk"],
               "scope_kind": scope.kind, "scope_id": scope.identifier, "revision": 1}
        if "expires_at_s" in row:
            ref["expires_at_s"] = row["expires_at_s"]
        unique_key = self.uniqueness(scope, kind, data)
        unique = {**unique_key, "entity_id": identifier, "revision": 1} if unique_key else None
        return row, ref, unique

    def check_binding(self, actor, scope, kind, data, old=None):
        admin = "admin" in actor.roles
        if scope.kind not in SPECS[kind].scopes:
            raise InvalidRecord("Wrong scope for this entity")
        if scope.kind == "user":
            if kind == "profile" and data["user_id"] != scope.identifier:
                raise InvalidRecord("Profile subject does not match its owner")
            if kind == "word" and (data["owner_user_id"] != scope.identifier or data["scope"] != "personal" or data["room_id"] is not None):
                raise InvalidRecord("Personal vocabulary owner mismatch")
        if scope.kind == "session" and "session_id" in data and data["session_id"] != scope.identifier:
            raise InvalidRecord("Session reference mismatch")
        if scope.kind == "room" and "room_id" in data and data["room_id"] != scope.identifier:
            raise InvalidRecord("Room reference mismatch")
        if kind in {"word", "shared_word"} and not admin:
            if old is None and data["created_by"] != actor.user_id:
                raise Forbidden("Creator must be the authenticated caller")
            if old and old.data["created_by"] != actor.user_id and scope.kind == "room":
                room = self.unpack(self.store.get({"pk": scope.pk, "sk": "META"})).data
                if room["host_user_id"] != actor.user_id:
                    raise Forbidden("Only creator or host may change shared vocabulary")
        if kind == "shared_word" and (data["scope"] != "room" or data["owner_user_id"] is not None):
            raise InvalidRecord("Shared vocabulary must have room scope")
        if kind == "profile" and not admin:
            immutable = ["roles", "permissions", "status", "email", "email_verified"]
            if old and any(data[name] != old.data[name] for name in immutable):
                raise Forbidden("Profile authority fields cannot be changed by a learner")
            if not old and (sorted(data["roles"]) != sorted(actor.roles) or data["permissions"]):
                raise Forbidden("Profile cannot grant unverified roles or permissions")
        if kind in {"object_ref", "result", "recording", "upload"} and data.get("object_key"):
            prefixes = [f"frames/tmp/{scope.identifier}/", f"ocr/{scope.identifier}/", f"recordings/{scope.identifier}/"]
            if not any(data["object_key"].startswith(prefix) for prefix in prefixes):
                raise InvalidRecord("Object key does not belong to this session")
        if old:
            immutable = [key for key in [SPECS[kind].id_field, "user_id", "session_id", "room_id", "owner_user_id", "created_by", "created_at", "started_at", "language", "entry_id", "sense_id", "source_id", "frame_id", "upload_id", "frame_index", "media_time_ms", "seq", "host_user_id", "shared_session_id", "scope"] if key in data]
            if any(data[key] != old.data[key] for key in immutable):
                raise InvalidRecord("Immutable entity identity/ownership cannot be changed")

    def save(self, actor, scope, kind, data, *, expected_revision=0):
        if isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision < 0:
            raise InvalidRecord("Expected revision must be a non-negative integer")
        self.catalog.validate(kind, data)
        identifier = self.catalog.identifier(kind, data)
        root_creation = expected_revision == 0 and kind == "session"
        if root_creation:
            if data["mode"] != "solo" or data["room_id"] is not None or data["owner_user_id"] != actor.user_id:
                raise Forbidden("Group sessions must be created atomically with their room")
            guards = []
        else:
            guards = self.authorize(actor, scope, kind, write=True)
        if kind == "room" and expected_revision == 0:
            raise InvalidRecord("Create rooms with create_room_bundle")
        old_row = self.raw(scope, kind, identifier) if expected_revision else None
        old = self.unpack(old_row) if old_row else None
        if expected_revision and (not old or old.revision != expected_revision):
            raise Conflict("Entity revision changed")
        self.check_binding(actor, scope, kind, data, old)
        if old and kind in {"source", "result", "occurrence", "audit", "history", "object_ref"}:
            raise InvalidRecord("This historical/immutable record cannot be overwritten")
        guards += self.reference_guards(actor, scope, kind, data)
        revision = expected_revision + 1
        if kind in {"profile", "session", "room", "word", "shared_word", "collection"} and data["version"] != revision:
            raise InvalidRecord("Public version must match the new storage revision")
        row, reference, unique = self.rows(scope, kind, data, revision)
        if old and self.catalog.key(scope, kind, old.data) != {"pk": row["pk"], "sk": row["sk"]}:
            raise InvalidRecord("An update cannot change its index key")
        actions = [self.store.put_action(row, expected_revision)]
        if not old:
            actions.append(self.store.put_action(reference))
            if unique:
                actions.append(self.store.put_action(unique))
        for guard in {(item["pk"], item["sk"]): item for item in guards}.values():
            if (guard["pk"], guard["sk"]) != (row["pk"], row["sk"]):
                actions.append(self.store.check_action(guard))
        self.store.transact(actions)
        return self.unpack(row)

    def reference_guards(self, actor, scope, kind, data):
        guards = []
        def require(target_scope, target_kind, identifier):
            row = self.raw(target_scope, target_kind, identifier)
            if not row:
                raise NotFound("Referenced entity not found")
            guards.append(row)
            return self.unpack(row).data
        if scope.kind in {"session", "room"} and kind not in {"session", "room"}:
            parent = self.store.get({"pk": scope.pk, "sk": "META"})
            if not parent:
                raise NotFound("Parent scope not found")
            guards.append(parent)
        if kind in {"upload", "job", "result"}:
            require(scope, "source", data["source_id"])
        if kind == "job":
            upload = require(scope, "upload", data["upload_id"])
            if any(data[name] != upload[name] for name in ["source_id", "frame_id", "frame_index", "media_time_ms"]):
                raise InvalidRecord("Job/upload frame references disagree")
        if kind == "result":
            job = require(scope, "job", data["job_id"])
            if any(data[name] != job[name] for name in ["source_id", "frame_id", "frame_index", "media_time_ms"]):
                raise InvalidRecord("Result/job frame references disagree")
            obj = require(scope, "object_ref", data["object_key"])
            if obj["sha256"] != data["sha256"]:
                raise InvalidRecord("Result/object checksums disagree")
        if kind == "recording" and data["object_key"] is not None:
            require(scope, "object_ref", data["object_key"])
        if kind == "word" and data["collection_id"] is not None:
            require(scope, "collection", data["collection_id"])
        if kind in {"history", "occurrence"}:
            session_scope = Scope("session", data["session_id"])
            self.authorize(actor, session_scope, "session")
            require(session_scope, "session", data["session_id"])
            if kind == "occurrence":
                require(scope, "word" if scope.kind == "user" else "shared_word", data["word_id"])
                result = require(session_scope, "result", data["result_id"])
                if data["source_id"] != result["source_id"]:
                    raise InvalidRecord("Occurrence/result source mismatch")
        return guards

    def register_source(self, actor, source, *, expected_session_version):
        self.catalog.validate("source", source)
        scope = Scope("session", source["session_id"])
        guards = self.authorize(actor, scope, "source", write=True)
        parent = self.store.get({"pk": scope.pk, "sk": "META"})
        old = self.unpack(parent)
        if old.revision != expected_session_version or old.data["status"] != "active":
            raise Conflict("Session version/state changed")
        next_index = 1
        if old.data["current_source_id"]:
            previous = self.unpack(self.raw(scope, "source", old.data["current_source_id"]))
            next_index = previous.data["source_index"] + 1
        if source["source_index"] != next_index or source["session_version"] != expected_session_version + 1:
            raise InvalidRecord("Source index/session version must be assigned by the service")
        updated = {**old.data, "version": old.revision + 1, "current_source_id": source["source_id"]}
        self.catalog.validate("session", updated)
        root, _, _ = self.rows(scope, "session", updated, old.revision + 1)
        row, ref, _ = self.rows(scope, "source", source, 1)
        actions = [self.store.put_action(root, old.revision), self.store.put_action(row), self.store.put_action(ref)]
        actions += [self.store.check_action(item) for item in guards if (item["pk"], item["sk"]) != (root["pk"], root["sk"])]
        self.store.transact(actions)
        return self.unpack(row)

    def save_word(self, actor, scope, data):
        kind = "word" if scope.kind == "user" else "shared_word"
        self.authorize(actor, scope, kind, write=True)
        self.catalog.validate(kind, data)
        self.check_binding(actor, scope, kind, data)
        unique = self.uniqueness(scope, kind, data)
        try:
            return self.save(actor, scope, kind, data), True
        except Conflict:
            record = self.store.get(unique)
            if not record:
                raise
            existing = self.get(actor, scope, kind, record["entity_id"])
            if not existing:
                raise IntegrityFailure("Vocabulary uniqueness record is orphaned") from None
            return existing, False

    def create_room_bundle(self, actor, room, membership, session):
        for kind, data in [("room", room), ("membership", membership), ("session", session)]:
            self.catalog.validate(kind, data)
        if not actor.user_id or room["host_user_id"] != actor.user_id or membership["user_id"] != actor.user_id or membership["room_id"] != room["room_id"] or membership["room_role"] != "host" or membership["left_at"] is not None or session["room_id"] != room["room_id"] or session["session_id"] != room["shared_session_id"] or session["owner_user_id"] != actor.user_id or session["mode"] != "group":
            raise InvalidRecord("Room/session/host membership do not form a consistent bundle")
        actions, output = [], []
        for kind, scope, data in [("room", Scope("room", room["room_id"]), room), ("membership", Scope("room", room["room_id"]), membership), ("session", Scope("session", session["session_id"]), session)]:
            row, ref, unique = self.rows(scope, kind, data, 1)
            actions.extend([self.store.put_action(row), self.store.put_action(ref)])
            if unique:
                actions.append(self.store.put_action(unique))
            output.append(self.unpack(row))
        self.store.transact(actions)
        return output

    def lookup_room_code(self, actor, code):
        if not actor.user_id:
            raise Forbidden("Verified identity required")
        row = self.store.get({"pk": "UNIQUE#ROOM_CODE", "sk": digest(code)})
        return row["entity_id"] if row else None

    def list(self, actor, scope, kind, *, limit=20, cursor=None, filters=None, reverse=False, through_seq=None):
        self.authorize(actor, scope, kind)
        if kind not in SPECS or scope.kind not in SPECS[kind].scopes:
            raise InvalidRecord("Invalid entity scope")
        if not set(filters or {}) <= {"language", "collection_id", "review_state", "status", "source_id"}:
            raise InvalidRecord("Unsupported storage filter")
        prefix = "PROFILE" if kind == "profile" else "META" if kind in {"room", "session"} else kind.upper() + "#"
        if through_seq is not None and (kind != "result" or not isinstance(through_seq, int) or through_seq < 0):
            raise InvalidRecord("through_seq is only supported for result pages")
        binding = {"pk": scope.pk, "kind": kind, "filters": filters or {}, "reverse": reverse, "through_seq": through_seq}
        start = self.cursors.decode(cursor, binding) if cursor else None
        upper = f"RESULT#{through_seq:020d}#\uffff" if through_seq is not None else None
        rows, key = self.store.query(scope.pk, prefix, limit=limit, start=start, reverse=reverse, filters=filters, upper_bound=upper)
        return [self.unpack(row) for row in rows], self.cursors.encode(binding, key) if key else None

    def delete(self, actor, scope, kind, identifier, *, expected_revision):
        if kind in {"profile", "session", "room", "membership"}:
            raise InvalidRecord("Parent/account/membership deletion requires a dedicated lifecycle operation")
        guards = self.authorize(actor, scope, kind, write=True)
        row = self.raw(scope, kind, identifier)
        if not row:
            raise NotFound("Entity not found")
        record = self.unpack(row)
        if record.revision != expected_revision:
            raise Conflict("Entity revision changed")
        self.check_binding(actor, scope, kind, record.data, record)
        actions = [self.store.delete_action({"pk": row["pk"], "sk": row["sk"]}, expected_revision),
                   self.store.delete_action(self.catalog.reference_key(scope, kind, identifier), 1)]
        unique = self.uniqueness(scope, kind, record.data)
        if unique:
            actions.append(self.store.delete_action(unique, 1))
        actions.extend(self.store.check_action(item) for item in guards)
        self.store.transact(actions)

    def operational_page(self, actor, kind, *, status=None, limit=20, cursor=None):
        if not actor.user_id or "admin" not in actor.roles:
            raise Forbidden("Operational index queries require administrator/service authority")
        if kind not in {"profile", "room", "job"} or (kind == "job" and status not in {"queued", "processing", "succeeded", "failed", "expired"}):
            raise InvalidRecord("Unsupported operational index query")
        partition = kind.upper() + "#" + (status if kind == "job" else "all")
        binding = {"pk": partition, "kind": kind, "index": "gsi1"}
        start = self.cursors.decode(cursor, binding) if cursor else None
        rows, key = self.store.query_index(partition, limit=limit, start=start)
        output = []
        for row in rows:
            # GSIs are eventually consistent. Re-read the base item before use;
            # worker state transitions still need a conditional lease write.
            current = self.store.get({"pk": row["pk"], "sk": row["sk"]})
            if current and (kind != "job" or current.get("status") == status):
                output.append(self.unpack(current))
        return output, self.cursors.encode(binding, key) if key else None
