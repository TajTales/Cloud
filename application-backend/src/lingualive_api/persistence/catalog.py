"""Internal records reuse public field schemas; derived views/URLs are excluded."""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from urllib.parse import urljoin
from uuid import UUID

from .errors import InvalidRecord


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    except (ValueError, TypeError):
        raise InvalidRecord("Record must contain finite JSON values") from None


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class Scope:
    kind: str
    identifier: str

    def __post_init__(self):
        if self.kind not in {"user", "session", "room", "system"} or not isinstance(self.identifier, str) or not self.identifier or len(self.identifier.encode()) > 1024 or any(ord(c) < 32 for c in self.identifier):
            raise InvalidRecord("Invalid storage scope")
        if self.kind in {"session", "room"}:
            try:
                UUID(self.identifier)
            except ValueError:
                raise InvalidRecord("Session/room scope requires a UUID") from None

    @property
    def pk(self):
        return self.kind.upper() + "#" + digest(self.identifier)


@dataclass(frozen=True)
class Spec:
    schema: str | None
    id_field: str
    scopes: tuple[str, ...]
    excluded: tuple[str, ...] = ()


SPECS = {
    "profile": Spec("Profile", "user_id", ("user",)),
    "session": Spec("Session", "session_id", ("session",), ("capabilities", "current_source", "capture_limits")),
    "source": Spec("Source", "source_id", ("session",)),
    "upload": Spec("Upload", "upload_id", ("session",), ("upload",)),
    "job": Spec("Job", "job_id", ("session",), ("poll_after_ms",)),
    "result": Spec("ResultManifest", "result_id", ("session",)),
    "room": Spec("Room", "room_id", ("room",), ("member_count",)),
    "membership": Spec("Membership", "membership_id", ("room",)),
    "word": Spec("SavedWord", "word_id", ("user",)),
    "shared_word": Spec("SharedWord", "word_id", ("room",)),
    "collection": Spec("Collection", "collection_id", ("user",), ("word_count",)),
    "history": Spec("HistoryItem", "session_id", ("user",), ("duration_ms", "saved_words_count", "playback_state")),
    "occurrence": Spec("Occurrence", "occurrence_id", ("user", "room")),
    "recording": Spec(None, "recording_id", ("session",)),
    "object_ref": Spec(None, "object_key", ("session",)),
    "audit": Spec("AuditEvent", "event_id", ("system",)),
    "config": Spec("AdminConfig", "version", ("system",)),
    "admin_action": Spec("AdminAction", "action_id", ("system",)),
    "connection": Spec(None, "connection_id", ("system",)),
    "ticket": Spec(None, "ticket_hash", ("system",)),
}
GLOBAL_IDS = {"session", "source", "upload", "job", "result", "room", "recording"}


class Catalog:
    def __init__(self, contracts):
        self.contracts = contracts
        self.base = (contracts.directory / "schemas/application.schema.json").as_uri()
        self.definitions = contracts.documents[self.base]["definitions"]

    def schema(self, kind):
        if kind not in SPECS:
            raise InvalidRecord("Unknown entity kind")
        spec = SPECS[kind]
        if spec.schema:
            schema = deepcopy(self.definitions[spec.schema])
            for key in spec.excluded:
                schema["properties"].pop(key)
                schema["required"].remove(key)
        else:
            string = {"type": "string", "minLength": 1, "maxLength": 1024}
            if kind == "object_ref":
                properties = {"object_key": string, "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"}, "size_bytes": {"type": "integer", "minimum": 0}, "content_type": string}
            elif kind == "recording":
                playback = self.definitions["Playback"]["properties"]
                properties = {key: deepcopy(playback[key]) for key in ["session_id", "recording_id", "state", "duration_ms", "timeline", "error"]}
                properties["recording_id"] = {"type": "string", "format": "uuid"}
                properties["object_key"] = {"anyOf": [string, {"type": "null"}]}
            elif kind == "connection":
                properties = {"connection_id": string, "user_id": string, "expires_at_s": {"type": "integer", "minimum": 1}, "subscriptions": {"type": "array", "items": {"type": "object", "required": ["kind", "id"], "properties": {"kind": {"enum": ["session", "room"]}, "id": {"type": "string", "format": "uuid"}}, "additionalProperties": False}}}
            else:
                properties = {"ticket_hash": {"type": "string", "pattern": "^[a-f0-9]{64}$"}, "user_id": string, "expires_at_s": {"type": "integer", "minimum": 1}, "used": {"type": "boolean"}}
            schema = {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}
        if kind == "occurrence":
            schema["properties"].update({"occurrence_id": {"type": "string", "pattern": "^[a-f0-9]{64}$"}, "word_id": {"type": "string", "format": "uuid"}})
            schema["required"] += ["occurrence_id", "word_id"]
        string = {"type": "string", "minLength": 1, "maxLength": 1024}
        uuid = {"type": "string", "format": "uuid"}
        checksum = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
        extra = {}
        if kind == "upload":
            fields = self.definitions["UploadCreate"]["properties"]
            extra = {key: deepcopy(fields[key]) for key in ["frame_index", "media_time_ms", "captured_at", "width_px", "height_px", "content_type", "size_bytes"]}
            extra.update(object_key=string, state={"enum": ["awaiting", "ready", "consumed"]}, expires_at_s={"type": "integer", "minimum": 1})
        elif kind == "job":
            extra = {"upload_id": uuid, "deadline_at_s": {"type": "integer", "minimum": 1},
                     "lease_owner": {"anyOf": [string, {"type": "null"}]}, "lease_until_s": {"type": ["integer", "null"]},
                     "lease_token": {"anyOf": [uuid, {"type": "null"}]}, "attempt": {"type": "integer", "minimum": 0}}
        elif kind == "result":
            extra = {"object_key": string, "sha256": checksum, "schema_version": string}
        schema["properties"].update(extra)
        schema["required"] += list(extra)
        def refs(node):
            if isinstance(node, dict):
                return {key: urljoin(self.base, value) if key == "$ref" else refs(value) for key, value in node.items()}
            if isinstance(node, list):
                return [refs(item) for item in node]
            return node
        return refs(schema)

    def validate(self, kind, data):
        canonical(data)
        if self.contracts.issues(data, self.schema(kind), self.base):
            raise InvalidRecord("Entity does not match its internal schema")
        if kind == "job":
            leased = [data[name] is not None for name in ["lease_owner", "lease_until_s", "lease_token"]]
            if (data["status"] == "processing" and (not all(leased) or data["attempt"] < 1)) or (data["status"] != "processing" and any(leased)):
                raise InvalidRecord("Job lease fields do not match its state")
        if kind == "recording" and data["state"] == "ready" and data["object_key"] is None:
            raise InvalidRecord("A ready recording requires an object reference")

    def project(self, kind, public_dto, extra=None):
        spec = SPECS[kind]
        if spec.schema is None or kind == "occurrence":
            raise InvalidRecord("This internal record requires explicit construction")
        if self.contracts.issues(public_dto, {"$ref": self.base + "#/definitions/" + spec.schema}):
            raise InvalidRecord("Source DTO does not match the original public schema")
        output = {key: deepcopy(value) for key, value in public_dto.items() if key not in spec.excluded}
        if extra:
            if output.keys() & extra.keys():
                raise InvalidRecord("Internal fields must not override public DTO fields")
            output.update(deepcopy(extra))
        self.validate(kind, output)
        return output

    def identifier(self, kind, data):
        return str(data[SPECS[kind].id_field])

    def key(self, scope, kind, data):
        if scope.kind not in SPECS[kind].scopes:
            raise InvalidRecord("Entity cannot be stored in this scope")
        identifier = self.identifier(kind, data)
        if kind in {"session", "room"}:
            sk = "META"
        elif kind == "profile":
            sk = "PROFILE"
        elif kind == "membership":
            sk = "MEMBERSHIP#" + digest(data["user_id"])
        elif kind == "result":
            sk = f"RESULT#{data['seq']:020d}#{identifier}"
        elif kind in {"history", "audit"}:
            sk = kind.upper() + "#" + data["started_at" if kind == "history" else "occurred_at"] + "#" + identifier
        elif kind == "occurrence":
            sk = "OCCURRENCE#" + data["word_id"] + "#" + identifier
        else:
            sk = kind.upper() + "#" + digest(identifier)
        return {"pk": scope.pk, "sk": sk}

    def reference_key(self, scope, kind, identifier):
        owner = "GLOBAL" if kind in GLOBAL_IDS else scope.pk
        return {"pk": "REF#" + kind + "#" + digest(owner), "sk": digest(str(identifier))}
