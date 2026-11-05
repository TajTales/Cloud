"""
Test script and CLI client for the meikipop OCR server.

Usage:
    # 1. Parse an actual image file via HTTP POST:
    python test_server.py /path/to/screenshot.png

    # 2. Parse an image file via WebSocket:
    python test_server.py /path/to/screenshot.png --ws

    # 3. Stream an image file multiple times over WebSocket (e.g., 5 frames):
    python test_server.py /path/to/screenshot.png --stream 5

    # 4. Run the full automated test suite (when no image file is provided):
    python test_server.py
"""
import argparse
import asyncio
import io
import json
import os
import sys
import time

import aiohttp
from PIL import Image, ImageDraw

SERVER_URL = os.environ.get("OCR_SERVER_URL", "http://localhost:8080").rstrip("/")
WS_URL = os.environ.get("OCR_WS_URL", SERVER_URL.replace("http://", "ws://").replace("https://", "wss://") + "/ws")


def configure_urls(host_or_url: str):
    """Configure SERVER_URL and WS_URL from a user-supplied host or URL."""
    global SERVER_URL, WS_URL
    target = host_or_url.strip()
    if not target.startswith(("http://", "https://")):
        # If user passed an IP or hostname with or without port (e.g. 34.12.34.56 or 34.12.34.56:8080)
        target = f"http://{target}"
    SERVER_URL = target.rstrip("/")
    ws_proto = "wss://" if SERVER_URL.startswith("https://") else "ws://"
    WS_URL = SERVER_URL.replace("http://", ws_proto).replace("https://", ws_proto) + "/ws"


def make_test_image(text: str = "テスト", width: int = 400, height: int = 200) -> bytes:
    """Generate a simple test PNG image with text."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((50, 80), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def print_ocr_result(data: dict):
    """Pretty print the OCR response."""
    if "error" in data:
        print(f"❌ OCR Error: {data['error']}")
        return

    paragraphs = data.get("paragraphs", [])
    elapsed = data.get("elapsed_ms", "?")
    print(f"⏱  Processed in {elapsed} ms")
    print(f"📄 Found {len(paragraphs)} paragraph(s):\n")

    for i, p in enumerate(paragraphs):
        full_text = p.get("full_text", "")
        is_vert = p.get("is_vertical", False)
        box = p.get("box", {})
        dir_label = "Vertical" if is_vert else "Horizontal"
        print(f"  [{i + 1}] \"{full_text}\" ({dir_label})")
        if box:
            print(f"      Box: center=({box.get('center_x', 0):.3f}, {box.get('center_y', 0):.3f}) "
                  f"size=({box.get('width', 0):.3f} x {box.get('height', 0):.3f})")

        words = p.get("words", [])
        if words and len(words) > 1:
            word_texts = [w.get("text", "") for w in words[:15]]
            if len(words) > 15:
                word_texts.append("...")
            print(f"      Words/Chars: {' '.join(word_texts)}")
        print()


# ── Parse user image ─────────────────────────────────────────────────────────

async def parse_image_http(image_path: str, raw_json: bool = False):
    """Send an image file via HTTP POST /ocr."""
    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        sys.exit(1)

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    print(f"📤 Sending '{image_path}' ({len(image_bytes):,} bytes) to {SERVER_URL}/ocr ...")

    async with aiohttp.ClientSession() as session:
        start = time.perf_counter()
        async with session.post(
            f"{SERVER_URL}/ocr",
            data=image_bytes,
            headers={"Content-Type": "application/octet-stream"},
        ) as resp:
            total_elapsed = (time.perf_counter() - start) * 1000
            if resp.status != 200:
                text = await resp.text()
                print(f"❌ Server returned status {resp.status}: {text}")
                return

            data = await resp.json()
            if raw_json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print_ocr_result(data)
                print(f"Roundtrip HTTP latency: {total_elapsed:.1f} ms")


async def parse_image_ws(image_path: str, stream_count: int = 1, raw_json: bool = False):
    """Send or stream an image file via WebSocket /ws."""
    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        sys.exit(1)

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    print(f"🔌 Connecting to {WS_URL} ...")
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(WS_URL) as ws:
            print(f" Connected! Streaming '{image_path}' ({len(image_bytes):,} bytes) x {stream_count} frame(s)...\n")

            for frame in range(1, stream_count + 1):
                t0 = time.perf_counter()
                await ws.send_bytes(image_bytes)

                msg = await ws.receive()
                t1 = time.perf_counter()
                data = json.loads(msg.data)

                if stream_count > 1:
                    print(f"--- Frame {frame}/{stream_count} (roundtrip {(t1 - t0) * 1000:.1f} ms) ---")

                if raw_json:
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print_ocr_result(data)

                if frame < stream_count:
                    await asyncio.sleep(0.1)


# ── Automated Test Suite ─────────────────────────────────────────────────────

async def test_health():
    print("=" * 50)
    print("TEST: GET /health")
    print("=" * 50)
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SERVER_URL}/health") as resp:
            data = await resp.json()
            print(f"  Status: {resp.status}")
            print(f"  Response: {json.dumps(data, indent=2)}")
            assert resp.status == 200
            assert data["status"] == "ok"
            print("  ✓ PASSED\n")


async def test_http_ocr():
    print("=" * 50)
    print("TEST: POST /ocr (single image)")
    print("=" * 50)
    image_bytes = make_test_image()
    print(f"  Sending {len(image_bytes)} byte PNG...")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{SERVER_URL}/ocr",
            data=image_bytes,
            headers={"Content-Type": "application/octet-stream"},
        ) as resp:
            data = await resp.json()
            print(f"  Status: {resp.status}")
            print(f"  Elapsed: {data.get('elapsed_ms', '?')}ms")
            print(f"  Paragraphs found: {len(data.get('paragraphs', []))}")
            for i, p in enumerate(data.get("paragraphs", [])):
                print(f"    [{i}] \"{p['full_text']}\"  vertical={p['is_vertical']}")
            assert resp.status == 200
            assert "paragraphs" in data
            print("  ✓ PASSED\n")


async def test_http_no_data():
    print("=" * 50)
    print("TEST: POST /ocr (empty body → 400)")
    print("=" * 50)
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{SERVER_URL}/ocr", data=b"") as resp:
            data = await resp.json()
            print(f"  Status: {resp.status}")
            print(f"  Response: {data}")
            assert resp.status == 400
            print("  ✓ PASSED\n")


async def test_websocket_single():
    print("=" * 50)
    print("TEST: WebSocket /ws (single frame)")
    print("=" * 50)
    image_bytes = make_test_image("WebSocketテスト")

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(WS_URL) as ws:
            print(f"  Connected to {WS_URL}")
            await ws.send_bytes(image_bytes)

            msg = await ws.receive()
            data = json.loads(msg.data)
            print(f"  Elapsed: {data.get('elapsed_ms', '?')}ms")
            print(f"  Paragraphs found: {len(data.get('paragraphs', []))}")
            assert "paragraphs" in data
            print("  ✓ PASSED\n")


async def test_websocket_stream():
    num_frames = 5
    print("=" * 50)
    print(f"TEST: WebSocket /ws (streaming {num_frames} frames)")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(WS_URL) as ws:
            print(f"  Connected to {WS_URL}")
            for i in range(num_frames):
                image_bytes = make_test_image(f"フレーム {i+1}")
                await ws.send_bytes(image_bytes)

                msg = await ws.receive()
                data = json.loads(msg.data)
                n_para = len(data.get("paragraphs", []))
                elapsed = data.get("elapsed_ms", "?")
                print(f"  Frame {i+1}/{num_frames}: {n_para} paragraphs, {elapsed}ms")

            print(f"  All {num_frames} frames processed over single connection")
            print("  ✓ PASSED\n")


async def test_websocket_ping():
    print("=" * 50)
    print("TEST: WebSocket /ws (ping keepalive)")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(WS_URL) as ws:
            await ws.send_str("ping")
            msg = await ws.receive()
            print(f"  Sent 'ping', got: '{msg.data}'")
            assert msg.data == "pong"
            print("  ✓ PASSED\n")


async def run_suite():
    print("\n🔍 meikipop-ocr-server test suite\n")
    print(f"  Server: {SERVER_URL}")
    print(f"  WebSocket: {WS_URL}\n")

    tests = [
        test_health,
        test_http_ocr,
        test_http_no_data,
        test_websocket_single,
        test_websocket_stream,
        test_websocket_ping,
    ]

    passed = 0
    for test in tests:
        try:
            await test()
            passed += 1
        except aiohttp.ClientError as e:
            print(f"  ✗ FAILED: Could not connect — {e}")
            print("    Is the server running? Start it with:")
            print("    PYTHONPATH=src python3 src/meikipop_ocr_server/server.py --provider dummy\n")
            sys.exit(1)
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}\n")
        except Exception as e:
            print(f"  ✗ FAILED: {e}\n")

    print("=" * 50)
    print(f"Results: {passed}/{len(tests)} tests passed")
    print("=" * 50)
    sys.exit(0 if passed == len(tests) else 1)


def main():
    parser = argparse.ArgumentParser(
        description="OCR Server Test Suite & Image Parser CLI"
    )
    parser.add_argument(
        "image",
        nargs="?",
        default=None,
        help="Path to an image file (PNG, JPG, etc.) to parse with OCR. If omitted, runs the test suite."
    )
    parser.add_argument(
        "--ws",
        action="store_true",
        help="Use WebSocket /ws instead of HTTP POST /ocr"
    )
    parser.add_argument(
        "--stream",
        type=int,
        default=1,
        help="Stream the image N times over WebSocket (implies --ws)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON response instead of formatted text"
    )
    parser.add_argument(
        "--host", "--url",
        default=None,
        help="Server host/URL (e.g. 34.12.34.56 or http://34.12.34.56:8080). Defaults to localhost:8080"
    )

    args = parser.parse_args()

    if args.host:
        configure_urls(args.host)

    if args.image:
        if args.stream > 1 or args.ws:
            asyncio.run(parse_image_ws(args.image, stream_count=args.stream, raw_json=args.json))
        else:
            asyncio.run(parse_image_http(args.image, raw_json=args.json))
    else:
        asyncio.run(run_suite())


if __name__ == "__main__":
    main()
