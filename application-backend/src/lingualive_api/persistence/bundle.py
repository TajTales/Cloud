import os
from pathlib import Path
import tempfile

from .cursor import CursorCodec
from .dynamo import DynamoStore
from .errors import Conflict, IntegrityFailure, InvalidRecord, NotFound
from .idempotency import IdempotencyStore
from .objects import LocalObjectStore
from .repository import Repository


def cursor_secret(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = directory / "cursor.key"
    if target.is_symlink():
        raise IntegrityFailure("Cursor key must not be a symlink")
    temporary = None
    try:
        if not target.exists():
            with tempfile.NamedTemporaryFile(dir=directory, delete=False) as output:
                temporary = Path(output.name)
                output.write(os.urandom(32))
                output.flush()
                os.fsync(output.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                pass
        key = target.read_bytes()
        if len(key) != 32:
            raise IntegrityFailure("Cursor signing key is invalid")
        return key
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


class PersistenceBundle:
    def __init__(self, settings, contracts):
        self.store = DynamoStore(settings)
        try:
            self.objects = LocalObjectStore(settings.data_dir / "objects")
            self.cursors = CursorCodec(cursor_secret(settings.data_dir))
            self.repository = Repository(self.store, contracts, self.cursors)
            self.idempotency = IdempotencyStore(self.store)
        except Exception:
            self.store.close()
            raise

    def health(self):
        return {"database": "ready" if self.store.health() else "unavailable", "object_storage": "ready" if self.objects.root.is_dir() else "unavailable"}

    def close(self):
        self.store.close()

    def put_object(self, actor, scope, key, chunks, content_type, *, max_bytes, expected_sha256=None):
        self.repository.authorize(actor, scope, "object_ref", write=True)
        if scope.kind != "session" or not any(key.startswith(prefix + scope.identifier + "/") for prefix in ["frames/tmp/", "ocr/", "recordings/"]):
            raise InvalidRecord("Object key must be assigned to its session")
        reference = self.objects.put(key, chunks, content_type, max_bytes=max_bytes, expected_sha256=expected_sha256)
        existing = self.repository.get(actor, scope, "object_ref", key)
        if existing:
            if existing.data != reference.dictionary():
                raise IntegrityFailure("Object bytes differ from the database reference")
            return reference
        try:
            self.repository.save(actor, scope, "object_ref", reference.dictionary())
        except Conflict:
            existing = self.repository.get(actor, scope, "object_ref", key)
            if not existing or existing.data != reference.dictionary():
                raise
        # No filesystem/database distributed transaction: failed DB writes leave
        # an inaccessible orphan, never a fabricated successful upload.
        return reference

    def read_object(self, actor, scope, key, *, max_bytes=1048576):
        record = self.repository.get(actor, scope, "object_ref", key)
        if not record:
            raise NotFound("Object is not registered to this scope")
        if self.objects.stat(key).dictionary() != record.data:
            raise IntegrityFailure("Object metadata does not match its database reference")
        return self.objects.read(key, max_bytes=max_bytes)
