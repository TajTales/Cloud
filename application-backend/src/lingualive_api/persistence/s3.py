"""S3 object adapter with the same interface as LocalObjectStore."""
from __future__ import annotations

import hashlib
import re

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from .errors import IntegrityFailure, InvalidRecord, NotFound, StorageUnavailable
from .objects import LocalObjectStore, ObjectRef


class S3ObjectStore:
    def __init__(self, bucket, region):
        self.bucket = bucket
        self.client = boto3.session.Session(region_name=region).client(
            "s3", config=Config(signature_version="s3v4", connect_timeout=3, read_timeout=10,
                                retries={"max_attempts": 5, "mode": "standard"}))

    check_key = staticmethod(LocalObjectStore.check_key)

    def _head(self, key):
        self.check_key(key)
        try:
            return self.client.head_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            if exc.response["Error"]["Code"] in {"404", "NoSuchKey", "NotFound"}:
                raise NotFound("Object not found") from None
            raise StorageUnavailable("Object storage operation failed") from None
        except BotoCoreError:
            raise StorageUnavailable("Object storage is unavailable") from None

    def presign_put(self, key, content_type, expires=120):
        self.check_key(key)
        return self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires)

    def stat(self, key):
        head = self._head(key)
        sha = head.get("Metadata", {}).get("sha256", "")
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise IntegrityFailure("Object has no verified checksum")
        return ObjectRef(key, sha, head["ContentLength"], head["ContentType"])

    #def adopt_uploaded(self, key, content_type, *, max_bytes):
        """Called after the browser PUT: validate, hash, and stamp the checksum."""
        """head = self._head(key)
        if head["ContentLength"] > max_bytes:
            self.delete(key)
            raise InvalidRecord("Object exceeds the byte limit")
        if head["ContentType"] != content_type:
            self.delete(key)
            raise InvalidRecord("Object content type does not match the upload")
        body = self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        digest = hashlib.sha256(body).hexdigest()
        self.client.copy_object(
            Bucket=self.bucket, Key=key, CopySource={"Bucket": self.bucket, "Key": key},
            Metadata={"sha256": digest}, MetadataDirective="REPLACE", ContentType=content_type)
        return ObjectRef(key, digest, len(body), content_type)"""


    def read_unverified(self, key, *, max_bytes):
        """Read what the browser uploaded; reject oversize before downloading."""
        head = self._head(key)
        if head["ContentLength"] > max_bytes:
            self.delete(key)
            raise InvalidRecord("Object exceeds the byte limit")
        body = self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        return body, head["ContentType"]

    def put(self, key, data, content_type, *, max_bytes, expected_sha256=None):
        body = data if isinstance(data, bytes) else b"".join(data)
        if len(body) > max_bytes:
            raise InvalidRecord("Object exceeds the byte limit")
        digest = hashlib.sha256(body).hexdigest()
        if expected_sha256 is not None and digest != expected_sha256:
            raise IntegrityFailure("Object checksum does not match")
        self.check_key(key)
        try:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=body,
                                   ContentType=content_type, Metadata={"sha256": digest})
        except (ClientError, BotoCoreError):
            raise StorageUnavailable("Object storage operation failed") from None
        return ObjectRef(key, digest, len(body), content_type)

    def chunks(self, key, *, chunk_size=65536):
        ref = self.stat(key)
        digest, length = hashlib.sha256(), 0
        body = self.client.get_object(Bucket=self.bucket, Key=key)["Body"]
        for chunk in body.iter_chunks(chunk_size):
            digest.update(chunk); length += len(chunk)
            yield chunk
        if digest.hexdigest() != ref.sha256 or length != ref.size_bytes:
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
        self.check_key(key)
        self.client.delete_object(Bucket=self.bucket, Key=key)
        return True