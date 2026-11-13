"""Immutable local object adapter. It never serves public files or signed URLs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from .errors import Conflict, IntegrityFailure, InvalidRecord, NotFound


@dataclass(frozen=True)
class ObjectRef:
    object_key: str
    sha256: str
    size_bytes: int
    content_type: str

    def dictionary(self):
        return asdict(self)


class LocalObjectStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    @staticmethod
    def check_key(key):
        if not isinstance(key, str) or not key or len(key.encode()) > 1024 or key.startswith("/") or "\\" in key or any(part in {"", ".", ".."} for part in key.split("/")) or any(ord(c) < 32 or ord(c) == 127 for c in key):
            raise InvalidRecord("Object key must be a safe relative server-generated key")

    def location(self, key):
        self.check_key(key)
        digest = hashlib.sha256(key.encode()).hexdigest()
        shard, destination = self.root / digest[:2], self.root / digest[:2] / digest
        if shard.is_symlink() or destination.is_symlink():
            raise IntegrityFailure("Object store path is a symlink")
        return destination

    def put(self, key, data, content_type, *, max_bytes, expected_sha256=None):
        chunks = [data] if isinstance(data, bytes) else data
        if not re.fullmatch(r"[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+", content_type) or max_bytes < 0:
            raise InvalidRecord("Invalid object content type or byte limit")
        destination = self.location(key)
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=destination.parent))
        digest, length = hashlib.sha256(), 0
        try:
            with (staging / "body").open("xb") as output:
                for chunk in chunks:
                    if not isinstance(chunk, bytes):
                        raise InvalidRecord("Object stream must yield bytes")
                    length += len(chunk)
                    if length > max_bytes:
                        raise InvalidRecord("Object exceeds the byte limit")
                    output.write(chunk)
                    digest.update(chunk)
                output.flush()
                os.fsync(output.fileno())
            reference = ObjectRef(key, digest.hexdigest(), length, content_type)
            if expected_sha256 is not None and reference.sha256 != expected_sha256:
                raise IntegrityFailure("Object checksum does not match")
            with (staging / "metadata.json").open("x") as output:
                json.dump(reference.dictionary(), output, sort_keys=True)
                output.flush()
                os.fsync(output.fileno())
            try:
                os.rename(staging, destination)
            except OSError:
                if not destination.is_dir():
                    raise
                existing = self.stat(key)
                if existing != reference:
                    raise Conflict("Object key already contains different bytes or metadata") from None
                # Verify data before treating an immutable retry as success.
                self.verify(key)
            return reference
        finally:
            if staging.exists():
                shutil.rmtree(staging)

    def stat(self, key):
        location = self.location(key)
        if not location.exists():
            raise NotFound("Object not found")
        try:
            if (location / "body").is_symlink() or (location / "metadata.json").is_symlink():
                raise ValueError()
            reference = ObjectRef(**json.loads((location / "metadata.json").read_text()))
            if reference.object_key != key or not re.fullmatch(r"[0-9a-f]{64}", reference.sha256) or reference.size_bytes < 0:
                raise ValueError()
            return reference
        except (ValueError, TypeError, OSError):
            raise IntegrityFailure("Object metadata is missing or invalid") from None

    def chunks(self, key, *, chunk_size=65536):
        reference = self.stat(key)
        digest, length = hashlib.sha256(), 0
        with (self.location(key) / "body").open("rb") as source:
            while chunk := source.read(chunk_size):
                digest.update(chunk)
                length += len(chunk)
                yield chunk
        if digest.hexdigest() != reference.sha256 or length != reference.size_bytes:
            raise IntegrityFailure("Stored object checksum/size mismatch")

    def verify(self, key):
        for _ in self.chunks(key):
            pass
        return self.stat(key)

    def read(self, key, *, max_bytes=1048576):
        if self.stat(key).size_bytes > max_bytes:
            raise InvalidRecord("Use streamed reads for a large object")
        return b"".join(self.chunks(key))

    def delete(self, key):
        location = self.location(key)
        if not location.exists():
            return False
        trash = Path(tempfile.mkdtemp(prefix=".deleting-", dir=location.parent))
        trash.rmdir()
        try:
            os.rename(location, trash)
        except FileNotFoundError:
            return False
        shutil.rmtree(trash)
        return True
