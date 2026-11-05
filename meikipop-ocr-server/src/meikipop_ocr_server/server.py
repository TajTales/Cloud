"""
Standalone OCR server with HTTP and WebSocket support.

Usage:
    meikipop-ocr-server                          # defaults to glensv2 on port 8080
    meikipop-ocr-server --provider meikiocr      # use meikiocr provider
    meikipop-ocr-server --port 9000              # custom port

HTTP:
    curl -X POST http://localhost:8080/ocr --data-binary @screenshot.png

WebSocket (persistent streaming):
    Connect to ws://localhost:8080/ws
    Send binary PNG frames → receive JSON OCR results
"""
import argparse
import asyncio
import io
import json
import logging
from pathlib import Path
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

from aiohttp import web
from PIL import Image

from meikipop_ocr_server.ocr.interface import OcrProvider

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_FILE = STATIC_DIR / "index.html"

# Registry of available providers (lazy-loaded)
PROVIDER_MAP = {
    "glensv2": ("meikipop_ocr_server.ocr.providers.glensv2", "GoogleLensOcrV2"),
    "meikiocr": ("meikipop_ocr_server.ocr.providers.meikiocr", "MeikiOcrProvider"),
    "owocr": ("meikipop_ocr_server.ocr.providers.owocr", "OwocrWebsocketProvider"),
    "screenai": ("meikipop_ocr_server.ocr.providers.screenai", "ScreenAiOcr"),
    "dummy": ("meikipop_ocr_server.ocr.providers.dummy", "DummyProvider"),
}


def load_provider(name: str, **kwargs) -> OcrProvider:
    """Dynamically load and instantiate an OCR provider by name."""
    if name not in PROVIDER_MAP:
        available = ", ".join(PROVIDER_MAP.keys())
        raise ValueError(f"Unknown provider '{name}'. Available: {available}")

    module_path, class_name = PROVIDER_MAP[name]
    import importlib
    module = importlib.import_module(module_path)
    provider_class = getattr(module, class_name)
    return provider_class(**kwargs)


def _run_ocr(provider: OcrProvider, image_bytes: bytes) -> dict:
    """Run OCR synchronously (called from thread pool). Returns a result dict."""
    image = Image.open(io.BytesIO(image_bytes))
    start = time.perf_counter()
    paragraphs = provider.scan(image)
    elapsed = time.perf_counter() - start

    if paragraphs is None:
        return {"error": "OCR processing failed", "elapsed_ms": round(elapsed * 1000, 1)}

    return {
        "paragraphs": [asdict(p) for p in paragraphs],
        "elapsed_ms": round(elapsed * 1000, 1),
    }


async def _extract_image_bytes(request: web.Request) -> bytes:
    """Extract raw image bytes from raw body, multipart upload, or JSON base64."""
    content_type = request.content_type.lower() if request.content_type else ""

    if "multipart/form-data" in content_type:
        reader = await request.multipart()
        field = await reader.next()
        while field is not None:
            if field.name in ("image", "file", "img") or field.filename:
                return await field.read()
            field = await reader.next()
        raise ValueError("No file found in multipart upload (field name should be 'image' or 'file')")

    elif "application/json" in content_type:
        data = await request.json()
        b64_str = data.get("image") or data.get("image_base64") or data.get("data")
        if not b64_str:
            raise ValueError("No 'image' or 'image_base64' field found in JSON payload")
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]
        import base64
        return base64.b64decode(b64_str)

    else:
        # Default: raw bytes
        return await request.read()


def create_app(provider: OcrProvider, max_workers: int = 2) -> web.Application:
    """Create and configure the aiohttp application."""
    app = web.Application()
    executor = ThreadPoolExecutor(max_workers=max_workers)

    # ── HTTP POST /ocr ───────────────────────────────────────────────
    async def ocr_endpoint(request: web.Request) -> web.Response:
        """
        Accept an image:
        - Raw binary image bytes (e.g. Content-Type: application/octet-stream or image/png)
        - Form file upload (multipart/form-data)
        - JSON payload with base64 string: {"image": "<base64_data>"}

        Returns OCR results as JSON.
        All bounding box coordinates are normalized (0.0-1.0 relative to image dimensions).
        """
        try:
            body = await _extract_image_bytes(request)
        except Exception as e:
            return web.json_response({"error": f"Failed to read image payload: {e}"}, status=400)

        if not body:
            return web.json_response({"error": "No image data provided"}, status=400)

        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(executor, _run_ocr, provider, body)
        except Exception as e:
            logger.exception("OCR endpoint error")
            return web.json_response({"error": f"Could not process image: {e}"}, status=400)

        if "error" in result and "paragraphs" not in result:
            return web.json_response(result, status=500)

        return web.json_response(result)

    # ── WebSocket /ws ────────────────────────────────────────────────
    async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
        """
        Persistent WebSocket connection for streaming OCR.

        Protocol:
          1. Client connects to ws://host:port/ws
          2. Client sends a binary message containing PNG/JPEG image bytes
             (or a JSON text message {"image": "<base64>"})
          3. Server replies with a JSON text message containing the OCR result
          4. Repeat — connection stays open for continuous streaming
          5. Send 'ping' for keepalive → replies with 'pong'
        """
        ws = web.WebSocketResponse(max_msg_size=50 * 1024 * 1024)  # 50 MB max frame
        await ws.prepare(request)

        peer = request.remote
        logger.info(f"WebSocket client connected: {peer}")

        loop = asyncio.get_running_loop()
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.BINARY:
                    # Run OCR in thread pool to avoid blocking the event loop
                    try:
                        result = await loop.run_in_executor(
                            executor, _run_ocr, provider, msg.data
                        )
                        await ws.send_json(result)
                    except Exception as e:
                        logger.exception("WebSocket OCR error")
                        await ws.send_json({"error": str(e)})

                elif msg.type == web.WSMsgType.TEXT:
                    text = msg.data.strip()
                    if text.lower() == "ping":
                        await ws.send_str("pong")
                    else:
                        # Also allow sending base64 JSON over WebSocket
                        try:
                            data = json.loads(text)
                            if isinstance(data, dict) and ("image" in data or "image_base64" in data):
                                b64_str = data.get("image") or data.get("image_base64")
                                if "," in b64_str:
                                    b64_str = b64_str.split(",", 1)[1]
                                import base64
                                img_bytes = base64.b64decode(b64_str)
                                result = await loop.run_in_executor(
                                    executor, _run_ocr, provider, img_bytes
                                )
                                await ws.send_json(result)
                                continue
                        except Exception:
                            pass

                        await ws.send_json({
                            "error": "Send binary image data (or JSON with base64 'image'), or 'ping' for keepalive"
                        })

                elif msg.type in (web.WSMsgType.CLOSE, web.WSMsgType.ERROR):
                    break

        except asyncio.CancelledError:
            pass
        finally:
            logger.info(f"WebSocket client disconnected: {peer}")

        return ws

    # ── GET /health ──────────────────────────────────────────────────
    async def health(request: web.Request) -> web.Response:
        return web.json_response({
            "status": "ok",
            "provider": provider.NAME,
            "endpoints": {
                "web": "GET /",
                "http": "POST /ocr",
                "websocket": "ws://host:port/ws",
                "health": "GET /health",
            },
        })

    # ── GET / (Web UI) ───────────────────────────────────────────────
    async def index(request: web.Request) -> web.Response:
        if INDEX_FILE.is_file():
            return web.FileResponse(INDEX_FILE)
        return web.Response(
            text="Meikipop OCR Server is running. UI not found.",
            content_type="text/plain"
        )

    app.router.add_get("/", index)
    if STATIC_DIR.is_dir():
        app.router.add_static("/static", STATIC_DIR)
    app.router.add_post("/ocr", ocr_endpoint)
    app.router.add_get("/ws", websocket_handler)
    app.router.add_get("/health", health)

    return app


def main():
    parser = argparse.ArgumentParser(
        prog="meikipop-ocr-server",
        description="Standalone OCR HTTP + WebSocket server extracted from meikipop"
    )
    parser.add_argument(
        "--provider", "-p",
        default="glensv2",
        choices=list(PROVIDER_MAP.keys()),
        help="OCR provider to use (default: glensv2)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Max OCR worker threads (default: 2)"
    )
    parser.add_argument(
        "--low-bandwidth",
        action="store_true",
        help="Enable low-bandwidth mode for Google Lens (smaller images)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Build provider kwargs
    provider_kwargs = {}
    if args.provider == "glensv2":
        provider_kwargs["low_bandwidth"] = args.low_bandwidth

    logger.info(f"Loading OCR provider: {args.provider}")
    try:
        provider = load_provider(args.provider, **provider_kwargs)
    except Exception as e:
        logger.critical(f"Failed to load provider '{args.provider}': {e}", exc_info=True)
        sys.exit(1)

    logger.info(
        f"Starting server on {args.host}:{args.port} with provider '{provider.NAME}'\n"
        f"  Web UI:    http://{args.host}:{args.port}/\n"
        f"  HTTP API:  POST http://{args.host}:{args.port}/ocr\n"
        f"  WebSocket: ws://{args.host}:{args.port}/ws\n"
        f"  Health:    GET  http://{args.host}:{args.port}/health"
    )
    app = create_app(provider, max_workers=args.workers)
    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
