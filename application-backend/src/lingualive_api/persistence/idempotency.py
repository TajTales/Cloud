from dataclasses import dataclass
from time import time
from uuid import UUID, uuid4

from .catalog import canonical, digest
from .errors import Conflict, InvalidRecord


@dataclass(frozen=True)
class Reservation:
    key: dict
    request_hash: str
    token: str
    revision: int
    expires_at_s: int
    resource: dict | None = None


class IdempotencyStore:
    """Cache resource references, never HTTP bodies, JWTs or signed upload URLs."""
    def __init__(self, store, *, clock=time):
        self.store, self.clock = store, clock

    def reserve(self, actor, method, path, key, request, *, ttl_s=86400):
        if not actor.user_id or method not in {"POST", "PUT", "PATCH", "DELETE"} or not path.startswith("/api/v1/") or not isinstance(key, str) or not 1 <= len(key) <= 128 or not 1 <= ttl_s <= 86400:
            raise InvalidRecord("Invalid idempotency scope/key/TTL")
        location = {"pk": "IDEMPOTENCY#" + digest([actor.user_id, method, path]), "sk": digest(key)}
        request_hash = digest(request)
        old = self.store.get(location, include_expired=True)
        now = int(self.clock())
        if old and old["expires_at_s"] > now:
            if old["request_hash"] != request_hash:
                raise Conflict("Idempotency key is already bound to another request")
            if old["state"] == "completed":
                return Reservation(location, request_hash, old["token"], old["revision"], old["expires_at_s"], old["resource"])
            raise Conflict("The matching request is still pending")
        revision = old["revision"] + 1 if old else 1
        token = str(uuid4())
        item = {**location, "revision": revision, "state": "pending", "request_hash": request_hash,
                "token": token, "expires_at_s": now + ttl_s, "resource": None}
        self.store.transact([self.store.put_action(item, revision - 1)])
        return Reservation(location, request_hash, token, revision, now + ttl_s)

    def complete(self, reservation, *, resource_type, resource_id, http_status, mutations=()):
        if resource_type not in {"session", "source", "upload", "job", "room", "word", "collection", "admin_action"} or not isinstance(resource_id, str) or not 1 <= len(resource_id) <= 256 or http_status not in {200, 201, 202, 204}:
            raise InvalidRecord("Idempotency completion must reference an application resource")
        try:
            UUID(resource_id)
        except ValueError:
            raise InvalidRecord("Idempotency must reference a resource UUID, never a credential or URL") from None
        resource = {"type": resource_type, "id": resource_id, "http_status": http_status}
        old = self.store.get(reservation.key, include_expired=True)
        if not old or old["token"] != reservation.token or old["request_hash"] != reservation.request_hash or old["expires_at_s"] <= self.clock():
            raise Conflict("Idempotency reservation expired or was replaced")
        if old["state"] == "completed":
            if old["resource"] != resource:
                raise Conflict("Completion refers to a different resource")
            return old["resource"]
        if old["revision"] != reservation.revision:
            raise Conflict("Idempotency revision changed")
        item = {**old, "revision": old["revision"] + 1, "state": "completed", "resource": resource}
        self.store.transact([*mutations, self.store.put_action(item, old["revision"])])
        return resource

    def abandon(self, reservation):
        """Release only our pending reservation after an atomic mutation fails."""
        old = self.store.get(reservation.key, include_expired=True)
        if old and old["state"] == "pending" and old["token"] == reservation.token and old["revision"] == reservation.revision:
            try:
                self.store.transact([self.store.delete_action(reservation.key, old["revision"])])
            except Conflict:
                pass
