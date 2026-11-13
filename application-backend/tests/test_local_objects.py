from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from pathlib import Path
import tempfile
import unittest

from lingualive_api.config import ConfigurationError
from lingualive_api.persistence.bundle import cursor_secret
from lingualive_api.persistence.cursor import CursorCodec
from lingualive_api.persistence.errors import Conflict, IntegrityFailure, InvalidRecord, NotFound
from lingualive_api.persistence.objects import LocalObjectStore
from lingualive_api.persistence.settings import PersistenceSettings


class LocalObjectTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.store = LocalObjectStore(self.folder.name)

    def test_bytes_and_metadata_survive_new_adapter_instance(self):
        reference = self.store.put("frames/tmp/test/image.png", b"synthetic-image-bytes", "image/png", max_bytes=100)
        other = LocalObjectStore(self.folder.name)
        self.assertEqual(other.read(reference.object_key), b"synthetic-image-bytes")
        self.assertEqual(other.stat(reference.object_key), reference)
        self.assertEqual(reference.sha256, hashlib.sha256(b"synthetic-image-bytes").hexdigest())

    def test_streaming_upload_and_read_budget(self):
        self.store.put("recordings/test/video.webm", iter([b"a" * 4, b"b" * 4]), "video/webm", max_bytes=8)
        self.assertEqual(b"".join(self.store.chunks("recordings/test/video.webm", chunk_size=3)), b"aaaabbbb")
        with self.assertRaises(InvalidRecord):
            self.store.read("recordings/test/video.webm", max_bytes=7)

    def test_invalid_checksum_and_large_stream_leave_no_object(self):
        for key, args in [("checksum/test", {"max_bytes": 5, "expected_sha256": "0" * 64}), ("size/test", {"max_bytes": 2})]:
            with self.assertRaises((InvalidRecord, IntegrityFailure)):
                self.store.put(key, b"data", "application/json", **args)
            with self.assertRaises(NotFound):
                self.store.stat(key)
        self.assertFalse(list(Path(self.folder.name).rglob(".staging-*")))

    def test_traversal_absolute_and_control_keys_are_rejected(self):
        for key in ["../outside", "/absolute", "a//b", "a/./b", "a/../b", "a\\b", "a\x00b", ""]:
            with self.subTest(key=key), self.assertRaises(InvalidRecord):
                self.store.put(key, b"x", "application/json", max_bytes=1)

    def test_immutable_retry_and_conflicting_replacement(self):
        first = self.store.put("ocr/result.json", b"{}", "application/json", max_bytes=100)
        self.assertEqual(self.store.put("ocr/result.json", b"{}", "application/json", max_bytes=100), first)
        with self.assertRaises(Conflict):
            self.store.put("ocr/result.json", b"[]", "application/json", max_bytes=100)
        self.assertEqual(self.store.read("ocr/result.json"), b"{}")

    def test_concurrent_identical_puts_share_one_object(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            values = list(pool.map(lambda _: self.store.put("shared/key", b"same", "application/json", max_bytes=100), range(8)))
        self.assertEqual(len(set(values)), 1)

    def test_concurrent_conflicting_puts_never_overwrite_winner(self):
        def put(data):
            try:
                return self.store.put("conflict/key", data, "application/json", max_bytes=100)
            except Conflict:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            values = list(pool.map(put, [b"first", b"second"]))
        self.assertEqual(sum(value is not None for value in values), 1)
        self.assertIn(self.store.read("conflict/key"), [b"first", b"second"])

    def test_corruption_and_symlinks_are_not_successful_reads(self):
        self.store.put("integrity/key", b"original", "application/json", max_bytes=100)
        (self.store.location("integrity/key") / "body").write_bytes(b"changed")
        with self.assertRaises(IntegrityFailure):
            self.store.read("integrity/key")
        body = self.store.location("integrity/key") / "body"
        body.unlink()
        body.symlink_to(Path(self.folder.name) / "outside")
        with self.assertRaises(IntegrityFailure):
            self.store.stat("integrity/key")

    def test_delete_is_idempotent(self):
        self.store.put("delete/key", b"x", "application/json", max_bytes=1)
        self.assertTrue(self.store.delete("delete/key"))
        self.assertFalse(self.store.delete("delete/key"))

    def test_cursor_key_persists_privately_without_becoming_source_data(self):
        first = cursor_secret(self.folder.name)
        self.assertEqual(cursor_secret(self.folder.name), first)
        self.assertEqual(len(first), 32)
        self.assertEqual((Path(self.folder.name) / "cursor.key").stat().st_mode & 0o077, 0)

    def test_signed_cursor_binding_expiration_and_tampering(self):
        now = [100]
        codec = CursorCodec(b"x" * 32, clock=lambda: now[0])
        binding = {"pk": "USER#alice", "kind": "word", "filters": {}}
        key = {"pk": "USER#alice", "sk": "WORD#one"}
        token = codec.encode(binding, key)
        self.assertEqual(codec.decode(token, binding), key)
        for candidate, scope in [(token + "x", binding), (token, {**binding, "pk": "USER#bob"}), (token, {**binding, "filters": {"language": "zh"}})]:
            with self.assertRaises(InvalidRecord):
                codec.decode(candidate, scope)
        now[0] += 3601
        with self.assertRaises(InvalidRecord):
            codec.decode(token, binding)

    def test_persistence_settings_never_accept_a_cloud_or_proxy_url(self):
        for endpoint in ["https://dynamodb.ap-southeast-1.amazonaws.com", "http://example.test:8000", "http://127.0.0.1:8000/path", "http://user:secret@127.0.0.1:8000", "http://127.0.0.1:8000?x=1"]:
            with self.subTest(endpoint=endpoint), self.assertRaises(ConfigurationError):
                PersistenceSettings.from_environment({"DYNAMODB_ENDPOINT": endpoint})
        self.assertEqual(PersistenceSettings.from_environment({"DYNAMODB_ENDPOINT": "http://localhost:8000"}).endpoint, "http://127.0.0.1:8000")


if __name__ == "__main__":
    unittest.main()
