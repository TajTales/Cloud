"""Real DynamoDB Local integration. All users/DTOs/bytes below are SYNTHETIC.

Requires scripts/dev-db. Creates/deletes only a fresh lingualive-test-* table;
never seeds the application table or calls an AWS endpoint.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
import os
import secrets
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from lingualive_api.auth import Identity
from lingualive_api.config import Settings
from lingualive_api.contracts import ContractRegistry
from lingualive_api.persistence.bundle import PersistenceBundle
from lingualive_api.persistence.catalog import SPECS, Scope, canonical, digest
from lingualive_api.persistence.dynamo import DynamoStore
from lingualive_api.persistence.errors import Conflict, Forbidden, IntegrityFailure, InvalidRecord, NotFound
from lingualive_api.persistence.idempotency import IdempotencyStore
from lingualive_api.persistence.settings import PersistenceSettings

ROOT = Path(__file__).resolve().parents[2]


def fixture(name):
    return json.loads((ROOT / "contracts/fixtures" / name).read_text())


class PersistenceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.config = PersistenceSettings.from_environment({
            "DYNAMODB_ENDPOINT": os.environ.get("DYNAMODB_ENDPOINT", "http://127.0.0.1:8000"),
            "DYNAMODB_TABLE": "lingualive-test-" + uuid4().hex,
            "APP_DATA_DIR": cls.folder.name,
        })
        cls.contracts = ContractRegistry(Settings.from_environment({}).contracts_dir)
        cls.bundle = PersistenceBundle(cls.config, cls.contracts)
        try:
            cls.bundle.store.ensure_table()
        except Exception:
            cls.bundle.close()
            cls.folder.cleanup()
            raise
        cls.repo, cls.store = cls.bundle.repository, cls.bundle.store

    @classmethod
    def tearDownClass(cls):
        try:
            assert cls.config.table_name.startswith("lingualive-test-")
            cls.store.call("delete_table", TableName=cls.config.table_name)
        finally:
            cls.bundle.close()
            cls.folder.cleanup()

    def setUp(self):
        self.alice = Identity("synthetic-user-" + uuid4().hex, ("user",))
        self.bob = Identity("synthetic-user-" + uuid4().hex, ("user",))
        self.admin = Identity("synthetic-service-worker", ("admin",))
        self.scope = Scope("user", self.alice.user_id)

    def profile(self, actor=None):
        actor = actor or self.alice
        data = fixture("http/getMe-200.json")["data"]
        data["user_id"], data["roles"] = actor.user_id, list(actor.roles)
        return self.repo.save(actor, Scope("user", actor.user_id), "profile", data)

    def session(self):
        data = fixture("http/getSession-200.json")["data"]
        data.update(session_id=str(uuid4()), owner_user_id=self.alice.user_id)
        scope = Scope("session", data["session_id"])
        return self.repo.save(self.alice, scope, "session", self.repo.catalog.project("session", data))

    def source(self, session):
        data = fixture("http/registerSource-200.json")["data"]
        data.update(source_id=str(uuid4()), session_id=session.identifier, source_index=1, session_version=2)
        return self.repo.register_source(self.alice, data, expected_session_version=session.revision)

    def word(self, *, scope=None, creator=None):
        scope, creator = scope or self.scope, creator or self.alice
        shared = scope.kind == "room"
        data = fixture("http/saveSharedVocabulary-201.json" if shared else "http/saveVocabulary-201.json")["data"]
        data.update(word_id=str(uuid4()), entry_id="fixture:entry-" + uuid4().hex, created_by=creator.user_id,
                    owner_user_id=None if shared else scope.identifier, room_id=scope.identifier if shared else None)
        return data

    def room(self):
        data = fixture("http/getRoom-200.json")["data"]
        room_id, session_id = str(uuid4()), str(uuid4())
        data["room"].update(room_id=room_id, shared_session_id=session_id, host_user_id=self.alice.user_id, code="".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(8)))
        data["membership"].update(membership_id=str(uuid4()), room_id=room_id, user_id=self.alice.user_id)
        data["session"].update(session_id=session_id, room_id=room_id, owner_user_id=self.alice.user_id)
        projected = [self.repo.catalog.project(kind, data[key]) for kind, key in [("room", "room"), ("membership", "membership"), ("session", "session")]]
        return self.repo.create_room_bundle(self.alice, *projected)

    def join(self, room, actor):
        membership = fixture("http/getRoom-200.json")["data"]["membership"]
        membership.update(membership_id=str(uuid4()), room_id=room.identifier, user_id=actor.user_id, room_role="member")
        membership["capabilities"] = {key: False for key in membership["capabilities"]}
        return self.repo.save(self.alice, room.scope, "membership", membership)

    def pipeline_metadata(self):
        session = self.session()
        source = self.source(session)
        upload = fixture("http/createFrameUpload-200.json")["data"]
        upload.update(upload_id=str(uuid4()), session_id=session.identifier, source_id=source.identifier, frame_id=str(uuid4()))
        request = fixture("http/createFrameUpload-request.json")
        extras = {key: request[key] for key in ["frame_index", "media_time_ms", "captured_at", "width_px", "height_px", "content_type", "size_bytes"]}
        extras.update(object_key=f"frames/tmp/{session.identifier}/{source.identifier}/{upload['frame_id']}.jpg", state="ready", expires_at_s=4102444800)
        uploaded = self.repo.save(self.alice, session.scope, "upload", self.repo.catalog.project("upload", upload, extras))
        job = fixture("http/duplicate-job-new.json")["data"]
        job.update(job_id=str(uuid4()), session_id=session.identifier, source_id=source.identifier, frame_id=upload["frame_id"], frame_index=extras["frame_index"], media_time_ms=extras["media_time_ms"])
        meta = {"upload_id": uploaded.identifier, "deadline_at_s": 4102444800, "lease_owner": None, "lease_until_s": None, "lease_token": None, "attempt": 0}
        queued = self.repo.save(self.alice, session.scope, "job", self.repo.catalog.project("job", job, meta))
        return session, source, uploaded, queued

    def result(self, session, source, job, seq=1):
        result = {key: fixture("http/getOcrResult-200.json")["data"][key] for key in self.repo.catalog.definitions["ResultManifest"]["properties"]}
        result.update(result_id=str(uuid4()), job_id=job.identifier, session_id=session.identifier, source_id=source.identifier,
                      frame_id=job.data["frame_id"], frame_index=job.data["frame_index"], media_time_ms=job.data["media_time_ms"], seq=seq)
        key = f"ocr/{session.identifier}/{source.identifier}/{result['result_id']}.json"
        reference = self.bundle.put_object(self.alice, session.scope, key, b'{"synthetic":true}', "application/json", max_bytes=100)
        return self.repo.save(self.admin, session.scope, "result", {**result, "object_key": key, "sha256": reference.sha256, "schema_version": "1.0"})

    def test_table_bootstrap_is_repeatable_and_versioned(self):
        self.store.ensure_table()
        self.assertTrue(self.store.health())
        item = self.store.get({"pk": "SYSTEM#MODEL", "sk": "META"})
        self.assertEqual(item["model_version"], 1)

    def test_profile_roundtrip_and_new_client_persistence(self):
        created = self.profile()
        other = PersistenceBundle(self.config, self.contracts)
        try:
            loaded = other.repository.get(self.alice, self.scope, "profile", self.alice.user_id)
            self.assertEqual(loaded, created)
        finally:
            other.close()

    def test_sdk_ignores_aws_profile_files_and_environment(self):
        with patch.dict(os.environ, {"AWS_PROFILE": "must-not-load-a-real-profile", "AWS_CONFIG_FILE": "/missing-real-config", "AWS_SHARED_CREDENTIALS_FILE": "/missing-real-credentials", "HTTPS_PROXY": "http://invalid-proxy:1"}):
            store = DynamoStore(self.config)
            try:
                self.assertTrue(store.health())
                self.assertEqual(store.client.meta.endpoint_url, self.config.endpoint)
            finally:
                store.close()

    def test_private_data_is_not_accessible_across_users(self):
        self.profile()
        with self.assertRaises(Forbidden):
            self.repo.get(self.bob, self.scope, "profile", self.alice.user_id)
        with self.assertRaises(Forbidden):
            self.repo.list(self.bob, self.scope, "word")

    def test_profile_cannot_escalate_roles_or_authority_fields(self):
        record = self.profile()
        changed = {**record.data, "roles": ["admin"], "version": 2}
        with self.assertRaises(Forbidden):
            self.repo.save(self.alice, self.scope, "profile", changed, expected_revision=1)
        self.assertEqual(self.repo.get(self.alice, self.scope, "profile", self.alice.user_id).revision, 1)

    def test_optimistic_concurrency_allows_only_one_writer(self):
        original = self.profile()
        def update(name):
            try:
                return self.repo.save(self.alice, self.scope, "profile", {**original.data, "display_name": name, "version": 2}, expected_revision=1)
            except Conflict:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(update, ["SYNTHETIC first", "SYNTHETIC second"]))
        self.assertEqual(sum(item is not None for item in results), 1)
        self.assertEqual(self.repo.get(self.alice, self.scope, "profile", self.alice.user_id).revision, 2)

    def test_vocabulary_duplicate_is_one_resource_and_senses_are_distinct(self):
        word = self.word()
        first, created = self.repo.save_word(self.alice, self.scope, word)
        self.assertTrue(created)
        again, created = self.repo.save_word(self.alice, self.scope, {**word, "word_id": str(uuid4())})
        self.assertFalse(created)
        self.assertEqual(again.identifier, first.identifier)
        second, created = self.repo.save_word(self.alice, self.scope, {**word, "word_id": str(uuid4()), "sense_id": "fixture:another-sense"})
        self.assertTrue(created)
        self.assertNotEqual(second.identifier, first.identifier)

    def test_concurrent_duplicate_vocabulary_is_atomic(self):
        word = self.word()
        with ThreadPoolExecutor(max_workers=2) as pool:
            values = list(pool.map(lambda _: self.repo.save_word(self.alice, self.scope, {**word, "word_id": str(uuid4())}), range(2)))
        self.assertEqual(sum(created for _, created in values), 1)
        self.assertEqual(values[0][0].identifier, values[1][0].identifier)

    def test_review_state_persists_without_overwriting_identity(self):
        word, _ = self.repo.save_word(self.alice, self.scope, self.word())
        updated = self.repo.save(self.alice, self.scope, "word", {**word.data, "review_state": "known", "version": 2}, expected_revision=1)
        self.assertEqual(updated.data["review_state"], "known")
        with self.assertRaises(InvalidRecord):
            self.repo.save(self.alice, self.scope, "word", {**updated.data, "sense_id": "other", "version": 3}, expected_revision=2)

    def test_collection_reference_is_scoped_to_owner(self):
        data = fixture("http/createCollection-201.json")["data"]
        data["collection_id"] = str(uuid4())
        collection = self.repo.save(self.alice, self.scope, "collection", self.repo.catalog.project("collection", data))
        word = {**self.word(), "collection_id": collection.identifier}
        self.repo.save_word(self.alice, self.scope, word)
        with self.assertRaises(NotFound):
            self.repo.save_word(self.bob, Scope("user", self.bob.user_id), {**word, "word_id": str(uuid4()), "owner_user_id": self.bob.user_id, "created_by": self.bob.user_id})

    def test_cursor_pages_have_no_duplicates_and_are_query_bound(self):
        expected = set()
        for _ in range(5):
            record, _ = self.repo.save_word(self.alice, self.scope, self.word())
            expected.add(record.identifier)
        cursor, found = None, []
        for _ in range(10):
            page, cursor = self.repo.list(self.alice, self.scope, "word", limit=2, cursor=cursor)
            found += [record.identifier for record in page]
            if not cursor:
                break
        self.assertEqual(set(found), expected)
        self.assertEqual(len(found), len(expected))
        _, cursor = self.repo.list(self.alice, self.scope, "word", limit=2)
        with self.assertRaises(InvalidRecord):
            self.repo.list(self.alice, self.scope, "word", limit=2, cursor=cursor, filters={"language": "zh"})

    def test_source_switch_is_atomic_and_version_checked(self):
        session = self.session()
        source = self.source(session)
        changed = self.repo.get(self.alice, session.scope, "session", session.identifier)
        self.assertEqual((changed.data["current_source_id"], changed.revision), (source.identifier, 2))
        with self.assertRaises(Conflict):
            self.repo.register_source(self.alice, {**source.data, "source_id": str(uuid4())}, expected_session_version=1)

    def test_jobs_keep_references_and_reject_inconsistent_frames(self):
        session, source, upload, job = self.pipeline_metadata()
        self.assertEqual(self.repo.get_by_id(self.alice, "job", job.identifier), job)
        with self.assertRaises(Forbidden):
            self.repo.get_by_id(self.bob, "job", job.identifier)
        bad = {**job.data, "job_id": str(uuid4()), "frame_id": str(uuid4())}
        with self.assertRaises(InvalidRecord):
            self.repo.save(self.alice, session.scope, "job", bad)
        self.assertNotIn("poll_after_ms", job.data)
        self.assertNotIn("upload", upload.data)  # no persisted presigned URL

    def test_result_references_watermark_and_immutable_seq(self):
        session, source, upload, job = self.pipeline_metadata()
        first = self.result(session, source, job, seq=1)
        second = self.result(session, source, job, seq=2)
        page, _ = self.repo.list(self.alice, session.scope, "result", through_seq=1)
        self.assertEqual([record.identifier for record in page], [first.identifier])
        with self.assertRaises(Conflict):
            self.result(session, source, job, seq=1)
        with self.assertRaises(InvalidRecord):
            self.repo.save(self.admin, session.scope, "result", second.data, expected_revision=1)

    def test_object_reference_guards_scope_and_integrity(self):
        session = self.session()
        key = f"frames/tmp/{session.identifier}/test/frame.png"
        reference = self.bundle.put_object(self.alice, session.scope, key, b"synthetic-bytes", "image/png", max_bytes=100)
        self.assertEqual(self.bundle.read_object(self.alice, session.scope, key), b"synthetic-bytes")
        with self.assertRaises(Forbidden):
            self.bundle.read_object(self.bob, session.scope, key)
        with self.assertRaises(InvalidRecord):
            self.bundle.put_object(self.alice, session.scope, "ocr/another-session/result.json", b"{}", "application/json", max_bytes=100)
        self.assertEqual(self.bundle.objects.verify(key), reference)

    def test_room_bundle_and_code_uniqueness_are_atomic(self):
        room, membership, session = self.room()
        self.assertEqual(self.repo.lookup_room_code(self.bob, room.data["code"]), room.identifier)
        with self.assertRaises(Forbidden):
            self.repo.get(self.bob, room.scope, "room", room.identifier)
        duplicate_room = {**room.data, "room_id": str(uuid4()), "shared_session_id": str(uuid4())}
        duplicate_member = {**membership.data, "membership_id": str(uuid4()), "room_id": duplicate_room["room_id"]}
        duplicate_session = {**session.data, "session_id": duplicate_room["shared_session_id"], "room_id": duplicate_room["room_id"]}
        with self.assertRaises(Conflict):
            self.repo.create_room_bundle(self.alice, duplicate_room, duplicate_member, duplicate_session)
        self.assertIsNone(self.repo.get_by_id(self.admin, "room", duplicate_room["room_id"]))

    def test_shared_vocabulary_requires_active_membership_and_creator_or_host(self):
        room, _, _ = self.room()
        bob_membership = self.join(room, self.bob)
        shared = self.word(scope=room.scope, creator=self.bob)
        word, _ = self.repo.save_word(self.bob, room.scope, shared)
        self.assertEqual(self.repo.get(self.alice, room.scope, "shared_word", word.identifier), word)
        with self.assertRaises(InvalidRecord):
            self.repo.save(self.bob, room.scope, "shared_word", {**shared, "review_state": "known", "version": 2}, expected_revision=1)
        left = {**bob_membership.data, "left_at": "2026-11-13T12:00:00.000Z"}
        self.repo.save(self.alice, room.scope, "membership", left, expected_revision=1)
        with self.assertRaises(Forbidden):
            self.repo.get(self.bob, room.scope, "shared_word", word.identifier)

    def test_revocation_between_authorize_and_write_aborts_entire_transaction(self):
        room, _, _ = self.room()
        member = self.join(room, self.bob)
        payload = self.word(scope=room.scope, creator=self.bob)
        transact = self.store.transact
        changed = [False]
        def revoke_then_write(actions):
            if not changed[0]:
                changed[0] = True
                row, _, _ = self.repo.rows(room.scope, "membership", {**member.data, "left_at": "2026-11-13T12:00:00.000Z"}, 2)
                transact([self.store.put_action(row, 1)])
            return transact(actions)
        with patch.object(self.store, "transact", side_effect=revoke_then_write):
            with self.assertRaises(Conflict):
                self.repo.save(self.bob, room.scope, "shared_word", payload)
        self.assertIsNone(self.repo.get(self.admin, room.scope, "shared_word", payload["word_id"]))

    def test_expiration_is_checked_even_without_native_ttl_deletion(self):
        payload = {"connection_id": "synthetic-" + uuid4().hex, "user_id": self.alice.user_id, "expires_at_s": 1, "subscriptions": []}
        scope = Scope("system", "connections")
        self.repo.save(self.admin, scope, "connection", payload)
        self.assertIsNone(self.repo.get(self.admin, scope, "connection", payload["connection_id"]))

    def test_idempotency_replay_conflict_and_stale_reservation(self):
        clock = [1000]
        cache = IdempotencyStore(self.store, clock=lambda: clock[0])
        key = "synthetic-key-" + uuid4().hex
        token = cache.reserve(self.alice, "POST", "/api/v1/sessions", key, {"title": "A"}, ttl_s=10)
        with self.assertRaises(Conflict):
            cache.reserve(self.alice, "POST", "/api/v1/sessions", key, {"title": "B"}, ttl_s=10)
        with self.assertRaises(Conflict):
            cache.reserve(self.alice, "POST", "/api/v1/sessions", key, {"title": "A"}, ttl_s=10)
        resource_id = str(uuid4())
        cache.complete(token, resource_type="session", resource_id=resource_id, http_status=201)
        replay = cache.reserve(self.alice, "POST", "/api/v1/sessions", key, {"title": "A"})
        self.assertEqual(replay.resource["id"], resource_id)
        clock[0] += 11
        newer = cache.reserve(self.alice, "POST", "/api/v1/sessions", key, {"title": "B"})
        with self.assertRaises(Conflict):
            cache.complete(token, resource_type="session", resource_id=resource_id, http_status=201)
        self.assertNotEqual(token.token, newer.token)

    def test_domain_mutation_and_idempotency_completion_commit_together(self):
        cache = IdempotencyStore(self.store)
        reservation = cache.reserve(self.alice, "POST", "/api/v1/collections", uuid4().hex, {"title": "synthetic"})
        key = {"pk": "TEST#" + uuid4().hex, "sk": "ONE"}
        existing = {**key, "revision": 1, "value": "existing"}
        self.store.transact([self.store.put_action(existing)])
        with self.assertRaises(Conflict):
            cache.complete(reservation, resource_type="collection", resource_id=str(uuid4()), http_status=201,
                           mutations=[self.store.put_action({**key, "revision": 1, "value": "bad"})])
        state = self.store.get(reservation.key, include_expired=True)
        self.assertEqual(state["state"], "pending")
        self.assertEqual(self.store.get(key)["value"], "existing")

    def test_model_rejects_large_inline_bodies_and_derived_credentials(self):
        data = fixture("http/getSession-200.json")["data"]
        with self.assertRaises(InvalidRecord):
            self.repo.catalog.validate("session", data)
        with self.assertRaises(InvalidRecord):
            self.repo.catalog.validate("ticket", {"ticket_hash": "a" * 64, "user_id": self.alice.user_id, "expires_at_s": 4102444800, "used": False, "token": "never-store-this"})
        with self.assertRaises(InvalidRecord):
            self.store.transact([self.store.put_action({"pk": "TEST", "sk": "LARGE", "payload": "x" * 400000})])

    def test_system_records_require_admin_and_preserve_original_schema_fields(self):
        scope = Scope("system", "audit")
        data = fixture("http/adminGetAudit-200.json")["data"]
        data["event_id"] = str(uuid4())
        with self.assertRaises(Forbidden):
            self.repo.save(self.alice, scope, "audit", data)
        saved = self.repo.save(self.admin, scope, "audit", data)
        self.assertEqual(self.repo.get(self.admin, scope, "audit", saved.identifier), saved)

    def test_delete_removes_uniqueness_and_reference_atomically(self):
        data = self.word()
        word, _ = self.repo.save_word(self.alice, self.scope, data)
        self.repo.delete(self.alice, self.scope, "word", word.identifier, expected_revision=1)
        self.assertIsNone(self.repo.get(self.alice, self.scope, "word", word.identifier))
        again, created = self.repo.save_word(self.alice, self.scope, {**data, "word_id": str(uuid4())})
        self.assertTrue(created)
        self.assertNotEqual(again.identifier, word.identifier)

    def test_history_empty_then_persistent_private_metadata(self):
        page, cursor = self.repo.list(self.alice, self.scope, "history", reverse=True)
        self.assertEqual((page, cursor), ([], None))
        session = self.session()
        data = {key: session.data[key] for key in ["session_id", "title", "mode", "language", "started_at", "ended_at"]}
        history = self.repo.save(self.alice, self.scope, "history", data)
        page, _ = self.repo.list(self.alice, self.scope, "history", reverse=True)
        self.assertEqual([item.identifier for item in page], [history.identifier])
        with self.assertRaises(Forbidden):
            self.repo.get(self.bob, self.scope, "history", history.identifier)

    def test_occurrence_keeps_result_source_and_word_references(self):
        session, source, _, job = self.pipeline_metadata()
        result = self.result(session, source, job)
        word, _ = self.repo.save_word(self.alice, self.scope, self.word())
        occurrence = {"word_id": word.identifier, "session_id": session.identifier, "source_id": source.identifier, "result_id": result.identifier,
                      "media_time_ms": result.data["media_time_ms"], "surface": "SYNTHETIC_SURFACE"}
        occurrence["occurrence_id"] = digest(occurrence)
        record = self.repo.save(self.alice, self.scope, "occurrence", occurrence)
        self.assertEqual(self.repo.get(self.alice, self.scope, "occurrence", record.identifier), record)
        with self.assertRaises(Conflict):
            self.repo.save(self.alice, self.scope, "occurrence", occurrence)

    def test_recording_metadata_requires_object_and_never_stores_playback_url(self):
        session = self.session()
        key = f"recordings/{session.identifier}/synthetic.webm"
        self.bundle.put_object(self.alice, session.scope, key, b"SYNTHETIC_NOT_A_REAL_VIDEO", "video/webm", max_bytes=100)
        data = {"recording_id": str(uuid4()), "session_id": session.identifier, "state": "ready", "duration_ms": 1000, "timeline": [], "error": None, "object_key": key}
        saved = self.repo.save(self.alice, session.scope, "recording", data)
        self.assertEqual(self.repo.get(self.alice, session.scope, "recording", saved.identifier), saved)
        with self.assertRaises(InvalidRecord):
            self.repo.save(self.alice, session.scope, "recording", {**data, "recording_id": str(uuid4()), "playback_url": "https://example.invalid/signed"})

    def test_config_admin_actions_and_hashed_tickets_are_internal_records(self):
        for kind, filename in [("config", "http/adminGetConfig-200.json"), ("admin_action", "http/adminGetAction-200.json")]:
            dto = fixture(filename)["data"]
            if kind == "admin_action":
                dto["action_id"] = str(uuid4())
            scope = Scope("system", kind + "-" + uuid4().hex)
            saved = self.repo.save(self.admin, scope, kind, self.repo.catalog.project(kind, dto))
            self.assertEqual(self.repo.get(self.admin, scope, kind, saved.identifier), saved)
        ticket = {"ticket_hash": hashlib.sha256(uuid4().bytes).hexdigest(), "user_id": self.alice.user_id, "expires_at_s": 4102444800, "used": False}
        scope = Scope("system", "tickets")
        saved = self.repo.save(self.admin, scope, "ticket", ticket)
        self.assertNotIn("ticket", saved.data)
        with self.assertRaises(Forbidden):
            self.repo.get(self.alice, scope, "ticket", saved.identifier)

    def test_processing_job_requires_fencing_fields(self):
        session, _, _, job = self.pipeline_metadata()
        with self.assertRaises(InvalidRecord):
            self.repo.save(self.admin, session.scope, "job", {**job.data, "status": "processing"}, expected_revision=1)
        updated = {**job.data, "status": "processing", "attempt": 1, "lease_owner": "synthetic-worker", "lease_token": str(uuid4()), "lease_until_s": 4102444700}
        saved = self.repo.save(self.admin, session.scope, "job", updated, expected_revision=1)
        self.assertEqual(saved.revision, 2)
        with self.assertRaises(Conflict):
            self.repo.save(self.admin, session.scope, "job", updated, expected_revision=1)

    def test_another_member_cannot_delete_someone_elses_shared_word(self):
        room, _, _ = self.room()
        self.join(room, self.bob)
        carol = Identity("synthetic-carol-" + uuid4().hex, ("user",))
        self.join(room, carol)
        word, _ = self.repo.save_word(self.bob, room.scope, self.word(scope=room.scope, creator=self.bob))
        with self.assertRaises(Forbidden):
            self.repo.delete(carol, room.scope, "shared_word", word.identifier, expected_revision=1)
        self.repo.delete(self.alice, room.scope, "shared_word", word.identifier, expected_revision=1)

    def test_unregistered_file_is_not_readable_through_scope_service(self):
        session = self.session()
        key = f"frames/tmp/{session.identifier}/orphan.png"
        self.bundle.objects.put(key, b"orphan", "image/png", max_bytes=100)
        with self.assertRaises(NotFound):
            self.bundle.read_object(self.alice, session.scope, key)

    def test_storage_does_not_accept_unknown_entity_types(self):
        with self.assertRaises(InvalidRecord):
            self.repo.catalog.validate("arbitrary_table", {"token": "should-never-be-stored"})

    def test_operational_job_index_is_admin_only_and_reads_current_rows(self):
        _, _, _, job = self.pipeline_metadata()
        with self.assertRaises(Forbidden):
            self.repo.operational_page(self.alice, "job", status="queued")
        found, cursor = set(), None
        for _ in range(100):
            rows, cursor = self.repo.operational_page(self.admin, "job", status="queued", limit=2, cursor=cursor)
            found.update(row.identifier for row in rows)
            if not cursor:
                break
        self.assertIn(job.identifier, found)

    def test_different_request_ids_cannot_duplicate_a_job_for_the_same_frame(self):
        session, _, _, job = self.pipeline_metadata()
        with self.assertRaises(Conflict):
            self.repo.save(self.alice, session.scope, "job", {**job.data, "job_id": str(uuid4())})


if __name__ == "__main__":
    unittest.main()
