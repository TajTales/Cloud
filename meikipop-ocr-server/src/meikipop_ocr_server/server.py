"""Bounded internal OCR HTTP/WS service. Existing raw success shape is preserved."""
import argparse
import asyncio
import base64
import binascii
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import io
import json
import logging
from pathlib import Path
import time
import warnings

from aiohttp import web
from PIL import Image, UnidentifiedImageError

from meikipop_ocr_server.ocr.interface import OcrProvider

logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_FILE = STATIC_DIR / "index.html"
MAX_IMAGE_BYTES = 1048576
MAX_ENVELOPE_BYTES = MAX_IMAGE_BYTES * 4 // 3 + 65536
STATE = web.AppKey("ocr_runtime", dict)
PROVIDER_MAP = {
    "glensv2": ("meikipop_ocr_server.ocr.providers.glensv2", "GoogleLensOcrV2"),
    "meikiocr": ("meikipop_ocr_server.ocr.providers.meikiocr", "MeikiOcrProvider"),
    "owocr": ("meikipop_ocr_server.ocr.providers.owocr", "OwocrWebsocketProvider"),
    "screenai": ("meikipop_ocr_server.ocr.providers.screenai", "ScreenAiOcr"),
    "dummy": ("meikipop_ocr_server.ocr.providers.dummy", "DummyProvider"),
    "rapidocr": ("meikipop_ocr_server.ocr.providers.rapidocr", "RapidChineseProvider"),
}


def load_provider(name, **kwargs) -> OcrProvider:
    if name not in PROVIDER_MAP:
        raise ValueError("Unknown OCR provider")
    import importlib
    module, cls = PROVIDER_MAP[name]
    return getattr(importlib.import_module(module), cls)(**kwargs)


def _run_ocr(provider, image_bytes):
    if not image_bytes:
        raise ValueError("Empty image")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise OverflowError("Image byte limit")
    started = time.perf_counter()
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(image_bytes)) as image:
            if image.format not in {"PNG", "JPEG"} or getattr(image, "n_frames", 1) != 1:
                raise ValueError("Unsupported image")
            if max(image.size) > 1600 or image.width * image.height > 4000000:
                raise OverflowError("Image pixel limit")
            image.load()
            paragraphs = provider.scan(image)
    elapsed = round((time.perf_counter() - started) * 1000, 1)
    if paragraphs is None:
        return {"error": "OCR processing failed", "elapsed_ms": elapsed}
    return {"paragraphs": [asdict(paragraph) for paragraph in paragraphs], "elapsed_ms": elapsed}


def decode_base64(data):
    if not isinstance(data, dict):
        raise ValueError()
    value = data.get("image") or data.get("image_base64") or data.get("data")
    if not isinstance(value, str) or len(value) > MAX_ENVELOPE_BYTES:
        raise ValueError()
    if value.startswith("data:"):
        value = value.split(",", 1)[1]
    return base64.b64decode(value, validate=True)


async def _extract_image_bytes(request):
    if request.content_length and request.content_length > MAX_ENVELOPE_BYTES:
        raise web.HTTPRequestEntityTooLarge(max_size=MAX_ENVELOPE_BYTES, actual_size=request.content_length)
    if request.content_type == "multipart/form-data":
        reader = await request.multipart()
        for _ in range(8):
            field = await reader.next()
            if field is None:
                break
            selected = field.name in {"image", "file", "img"} or field.filename
            chunks, length = [], 0
            while chunk := await field.read_chunk(8192):
                length += len(chunk)
                if length > (MAX_IMAGE_BYTES if selected else 4096):
                    raise web.HTTPRequestEntityTooLarge(max_size=MAX_IMAGE_BYTES, actual_size=length)
                if selected:
                    chunks.append(chunk)
            if selected:
                return b"".join(chunks)
        raise ValueError("No image field")
    if request.content_type == "application/json":
        return decode_base64(await request.json())
    return await request.read()


def create_app(provider, max_workers=1, *, timeout_s=20, allowed_origins=()):
    if max_workers < 1 or timeout_s <= 0:
        raise ValueError("Invalid OCR runtime limit")
    app = web.Application(client_max_size=MAX_ENVELOPE_BYTES)
    # The provider instance is shared, so admit exactly one inference globally.
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="local-ocr")
    state = {"busy": False, "closing": False}
    app[STATE] = state

    async def process(content):
        if not content:
            return {"error": "No image data provided"}, 400
        if len(content) > MAX_IMAGE_BYTES:
            return {"error": "Image exceeds 1 MiB limit"}, 413
        if state["busy"] or state["closing"]:
            return {"error": "OCR provider is busy"}, 503
        state["busy"] = True
        future = asyncio.get_running_loop().run_in_executor(executor, _run_ocr, provider, content)
        def completed(done):
            state["busy"] = False
            if not done.cancelled():
                done.exception()  # Retrieve late exceptions after an HTTP timeout.
        future.add_done_callback(completed)
        try:
            result = await asyncio.wait_for(asyncio.shield(future), timeout_s)
            return result, 500 if "error" in result else 200
        except asyncio.TimeoutError:
            # A timed-out native inference still owns the slot until it finishes.
            return {"error": "OCR processing timed out"}, 504
        except (OverflowError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            return {"error": "Image exceeds pixel/byte limits"}, 413
        except (UnidentifiedImageError, OSError, ValueError):
            return {"error": "Invalid or unsupported image"}, 400
        except Exception as error:
            logger.error("OCR provider failed: %s", type(error).__name__)
            return {"error": "OCR provider failed"}, 500

    async def ocr_endpoint(request):
        if request.headers.get("Origin") and request.headers["Origin"] not in allowed_origins:
            return web.json_response({"error": "Origin is not allowed"}, status=403)
        try:
            content = await _extract_image_bytes(request)
        except web.HTTPRequestEntityTooLarge:
            return web.json_response({"error": "Image payload is too large"}, status=413)
        except (ValueError, KeyError, IndexError, binascii.Error, json.JSONDecodeError):
            return web.json_response({"error": "Invalid image payload"}, status=400)
        result, status = await process(content)
        return web.json_response(result, status=status)

    async def websocket_handler(request):
        if request.headers.get("Origin") and request.headers["Origin"] not in allowed_origins:
            return web.json_response({"error": "Origin is not allowed"}, status=403)
        socket = web.WebSocketResponse(max_msg_size=MAX_ENVELOPE_BYTES)
        await socket.prepare(request)
        async for message in socket:
            if message.type == web.WSMsgType.TEXT and message.data.strip().lower() == "ping":
                await socket.send_str("pong")
                continue
            try:
                if message.type == web.WSMsgType.BINARY:
                    content = message.data
                elif message.type == web.WSMsgType.TEXT:
                    content = decode_base64(json.loads(message.data))
                else:
                    continue
            except (ValueError, KeyError, IndexError, binascii.Error):
                await socket.send_json({"error": "Send binary PNG/JPEG or JSON base64 image"})
                continue
            result, _ = await process(content)
            await socket.send_json(result)
        return socket

    async def health(request):
        ready = not state["closing"] and (not hasattr(provider, "ocr_client") or provider.ocr_client is not None)
        return web.json_response({"status": "ok" if ready else "unavailable", "ready": ready, "provider": provider.NAME,
                                  "busy": state["busy"], "languages": list(getattr(provider, "SUPPORTED_LANGUAGES", ("ja",))), "max_image_bytes": MAX_IMAGE_BYTES,
                                  "endpoints": {"web": "GET /", "http": "POST /ocr", "websocket": "ws://host:port/ws", "health": "GET /health"}}, status=200 if ready else 503)

    async def index(request):
        return web.FileResponse(INDEX_FILE) if INDEX_FILE.is_file() else web.Response(text="OCR provider is running")

    async def cleanup(application):
        state["closing"] = True
        await asyncio.to_thread(executor.shutdown, wait=True, cancel_futures=True)
        close = getattr(provider, "close", None)
        if close:
            await asyncio.to_thread(close)

    app.on_cleanup.append(cleanup)
    app.router.add_get("/", index)
    app.router.add_static("/static", STATIC_DIR)
    app.router.add_post("/ocr", ocr_endpoint)
    app.router.add_get("/ws", websocket_handler)
    app.router.add_get("/health", health)
    return app


def main():
    parser = argparse.ArgumentParser(description="Internal OCR provider; use loopback behind the application API")
    parser.add_argument("--provider", "-p", default="meikiocr", choices=list(PROVIDER_MAP))
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--low-bandwidth", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    provider = load_provider(args.provider, **({"low_bandwidth": args.low_bandwidth} if args.provider == "glensv2" else {}))
    origins = (f"http://127.0.0.1:{args.port}", f"http://localhost:{args.port}")
    web.run_app(create_app(provider, args.workers, allowed_origins=origins), host=args.host, port=args.port, access_log=None, print=None)


if __name__ == "__main__":
    main()
