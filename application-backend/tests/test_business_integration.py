"""Application metadata APIs; these do not test Chime or group video calls."""
from uuid import uuid4

from test_learning_integration import LocalIntegrationCase


class BusinessIntegrationTests(LocalIntegrationCase):
    async def test_room_create_join_leave_rejoin_close_and_permissions(self):
        host = (await self.register())["access_token"]
        member = (await self.register())["access_token"]
        key = str(uuid4())
        body = {"title": "Nhóm thử thật", "language": "ja", "shared_vocabulary_enabled": True}
        created = await self.api("POST", "/rooms", host, body, 201, key)
        room_id, code = created["room"]["room_id"], created["room"]["code"]
        self.assertEqual(len(code), 8)
        self.assertEqual(created["room"]["member_count"], 1)
        replay = await self.api("POST", "/rooms", host, body, 200, key)
        self.assertEqual(replay["room"]["room_id"], room_id)
        await self.api("GET", "/rooms/" + room_id, member, expected=403)
        joined = await self.api("POST", "/rooms/join", member, {"code": code})
        self.assertEqual(joined["room"]["member_count"], 2)
        self.assertFalse(joined["membership"]["capabilities"]["can_share_source"])
        again = await self.api("POST", "/rooms/join", member, {"code": code})
        self.assertEqual(again["room"]["member_count"], 2)
        members = await self.api("GET", f"/rooms/{room_id}/members", host)
        self.assertEqual(len(members["items"]), 2)
        await self.api("POST", f"/rooms/{room_id}/close", member, {"expected_version": 1}, 403)
        await self.api("POST", f"/rooms/{room_id}/meeting-credentials", member, expected=503)
        left = await self.api("POST", f"/rooms/{room_id}/leave", member)
        self.assertIsNotNone(left["left_at"])
        await self.api("GET", "/rooms/" + room_id, member, expected=403)
        self.assertEqual(len((await self.api("GET", "/history", member))["items"]), 1)
        await self.api("POST", "/rooms/join", member, {"code": code})
        closed = await self.api("POST", f"/rooms/{room_id}/close", host, {"expected_version": 1})
        self.assertEqual(closed["room"]["status"], "closed")
        self.assertEqual(closed["room"]["member_count"], 0)
        self.assertEqual(closed["session"]["status"], "ended")
        self.assertFalse(closed["membership"]["capabilities"]["can_send_ocr"])
        await self.api("POST", "/rooms/join", member, {"code": code}, 409)

    async def test_host_leave_closes_room_and_is_idempotent(self):
        token = (await self.register())["access_token"]
        created = await self.api("POST", "/rooms", token, {"title": "Phòng chủ rời", "language": "ja", "shared_vocabulary_enabled": False}, 201)
        key = str(uuid4()); path = f"/rooms/{created['room']['room_id']}/leave"
        first = await self.api("POST", path, token, key=key)
        replay = await self.api("POST", path, token, key=key)
        self.assertEqual(first, replay)
        self.assertIsNotNone(first["left_at"])
        self.assertEqual((await self.api("GET", "/rooms/" + created["room"]["room_id"], token))["room"]["status"], "closed")

    async def test_collections_versions_private_scope_and_actual_word_count(self):
        token = (await self.register())["access_token"]
        key = str(uuid4()); body = {"title": "Từ trong chuyến đi", "language": "ja"}
        collection = await self.api("POST", "/collections", token, body, 201, key)
        self.assertEqual(collection["word_count"], 0)
        self.assertEqual((await self.api("POST", "/collections", token, body, 200, key))["collection_id"], collection["collection_id"])
        word = await self.api("POST", "/vocabulary", token, {**self.word_request(), "collection_id": collection["collection_id"]}, 201)
        self.assertEqual((await self.api("GET", "/collections", token))["items"][0]["word_count"], 1)
        path = "/collections/" + collection["collection_id"]
        updated = await self.api("PATCH", path, token, {"title": "Tên mới", "expected_version": 1})
        self.assertEqual(updated["version"], 2)
        await self.api("PATCH", path, token, {"title": "Stale", "expected_version": 1}, 409)
        other = (await self.register())["access_token"]
        self.assertEqual((await self.api("GET", "/collections", other))["items"], [])
        await self.api("PATCH", path, other, {"title": "Forbidden", "expected_version": 2}, 404)
        await self.api("DELETE", "/vocabulary/" + word["word_id"], token, expected=204)
        self.assertEqual((await self.api("GET", "/collections", token))["items"][0]["word_count"], 0)
