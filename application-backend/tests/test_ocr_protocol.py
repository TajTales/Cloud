"""Exercise the actual internal server with test-only synthetic providers."""
import asyncio
import base64
import io
from pathlib import Path
import sys
import threading
import unittest

from aiohttp.test_utils import TestClient, TestServer
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "meikipop-ocr-server/src"))
from meikipop_ocr_server.server import create_app
from meikipop_ocr_server.ocr.interface import BoundingBox, Paragraph, Word


class SyntheticProvider:
    NAME = "fixture.synthetic.protocol-only"
    def __init__(self):
        self.gate = None
        self.closed = False
        self.mode = "text"
    def scan(self, image):
        if self.gate:
            self.gate.wait(2)
        if self.mode == "error":
            raise RuntimeError("secret internal synthetic error must not escape")
        if self.mode == "empty":
            return []
        box = BoundingBox(.5, .5, .4, .2)
        return [Paragraph("合成", [Word("合成", "", box)], box, False)]
    def close(self):
        self.closed = True


class OcrProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.provider = SyntheticProvider()
        self.client = TestClient(TestServer(create_app(self.provider, timeout_s=.05 if "timeout" in self._testMethodName else 2)))
        await self.client.start_server()
        output = io.BytesIO(); Image.new("RGB", (640, 360), "white").save(output, format="PNG")
        self.image = output.getvalue()
    async def asyncTearDown(self):
        if self.provider.gate:
            self.provider.gate.set()
        await self.client.close()
        self.assertTrue(self.provider.closed)

    async def test_http_raw_json_multipart_and_no_text_preserve_original_schema(self):
        from aiohttp import FormData
        form = FormData(); form.add_field("image", self.image, filename="synthetic.png", content_type="image/png")
        for kwargs in [{"data": self.image}, {"json": {"image": base64.b64encode(self.image).decode()}}, {"data": form}]:
            response = await self.client.post("/ocr", **kwargs)
            self.assertEqual(response.status, 200, await response.text())
            data = await response.json(); self.assertEqual(set(data), {"paragraphs", "elapsed_ms"})
            self.assertEqual(data["paragraphs"][0]["full_text"], "合成")
        self.provider.mode = "empty"
        response = await self.client.post("/ocr", data=self.image)
        self.assertEqual((await response.json())["paragraphs"], [])

    async def test_invalid_image_base64_and_size_errors_are_bounded(self):
        for kwargs, status in [({"data": b"invalid"}, 400), ({"json": {"image": "@@invalid"}}, 400), ({"data": io.BytesIO(b"x" * 1048577)}, 413)]:
            response = await self.client.post("/ocr", **kwargs)
            self.assertEqual(response.status, status)
            self.assertIn("error", await response.json())

    async def test_timeout_keeps_provider_slot_busy_until_native_call_finishes(self):
        self.provider.gate = threading.Event()
        response = await self.client.post("/ocr", data=self.image)
        self.assertEqual(response.status, 504)
        busy = await self.client.post("/ocr", data=self.image)
        self.assertEqual(busy.status, 503)
        self.provider.gate.set()
        await asyncio.sleep(.02)
        restored = await self.client.post("/ocr", data=self.image)
        self.assertEqual(restored.status, 200)

    async def test_internal_errors_are_sanitized_and_foreign_origin_rejected(self):
        self.provider.mode = "error"
        response = await self.client.post("/ocr", data=self.image)
        self.assertEqual(response.status, 500)
        self.assertNotIn("secret internal", await response.text())
        denied = await self.client.post("/ocr", data=self.image, headers={"Origin": "https://evil.invalid"})
        self.assertEqual(denied.status, 403)
        denied_ws = await self.client.get("/ws", headers={"Origin": "https://evil.invalid"})
        self.assertEqual(denied_ws.status, 403)

    async def test_direct_websocket_binary_ping_and_base64_remain_separate_protocol(self):
        async with self.client.ws_connect("/ws") as socket:
            await socket.send_str("ping"); self.assertEqual((await socket.receive()).data, "pong")
            await socket.send_bytes(self.image)
            self.assertEqual((await socket.receive_json())["paragraphs"][0]["full_text"], "合成")
            await socket.send_json({"image": base64.b64encode(self.image).decode()})
            self.assertIn("paragraphs", await socket.receive_json())
