# meikipop-ocr-server

Standalone OCR HTTP + WebSocket server extracted from [meikipop](https://github.com/rtr46/meikipop). Provides Japanese OCR capabilities via an interactive Web UI, REST API, and persistent WebSocket streaming.

## Features

- 🌐 **Interactive Web UI**: Drag-and-drop, file upload, or `Ctrl+V` paste from clipboard with interactive bounding box overlays.
- ⚡ **HTTP REST API**: `POST /ocr` accepts raw image bytes, multipart file uploads, or JSON base64.
- 🔄 **WebSocket Streaming**: `GET /ws` for continuous real-time image processing.
- 📦 **Docker & AWS Ready**: Ready-to-deploy Dockerfile, Docker Compose, and Nginx configurations.

## Quick Start

```bash
# 1. Start server with Google Lens OCR
PYTHONPATH=src python3 src/meikipop_ocr_server/server.py --provider glensv2 --port 8080

# 2. Open the Web UI in your browser:
#    http://localhost:8080
```

## Docker Quick Start

```bash
# Build and run with Docker Compose
docker compose up -d

# Visit http://localhost in your browser
```

## Parsing Images with the Test CLI

You can parse any image file directly using `test_server.py`:

```bash
# 1. Parse an image file via HTTP POST:
python3 test_server.py /path/to/screenshot.png

# 2. Parse an image file via WebSocket:
python3 test_server.py /path/to/screenshot.png --ws

# 3. Stream an image file N times over WebSocket (continuous streaming):
python3 test_server.py /path/to/screenshot.png --stream 10

# 4. Print raw JSON response:
python3 test_server.py /path/to/screenshot.png --json

# 5. Test a remote server (e.g. Google Cloud / EC2 instance):
python3 test_server.py /path/to/screenshot.png --host 34.12.34.56

# 6. Run the automated 6-step test suite (against local or remote):
python3 test_server.py
python3 test_server.py --host 34.12.34.56
```

## API

### `POST /ocr` (one-shot HTTP)

Send raw image bytes as the request body. Returns OCR results as JSON.

```bash
curl -X POST http://localhost:8080/ocr \
  --data-binary @screenshot.png \
  -H "Content-Type: application/octet-stream"
```

### `ws://host:port/ws` (streaming WebSocket)

Connect once, then keep sending PNG/JPEG frames as binary WebSocket messages. Each frame gets a JSON response back. The connection stays open — ideal for continuous screen capture.

**Protocol:**
1. Connect to `ws://localhost:8080/ws`
2. Send a binary message containing image bytes (PNG, JPEG, BMP, etc.)
3. Receive a JSON text message with the OCR result
4. Repeat for each frame
5. Send text `ping` for keepalive → receives `pong`

**Python client example:**

```python
import asyncio
import aiohttp

async def stream_ocr():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect("ws://localhost:8080/ws") as ws:
            while True:
                # Capture or load your image
                with open("frame.png", "rb") as f:
                    image_bytes = f.read()

                await ws.send_bytes(image_bytes)
                response = await ws.receive_json()
                print(response)

                await asyncio.sleep(0.5)  # adjust your frame rate

asyncio.run(stream_ocr())
```

### Response Format

```json
{
  "paragraphs": [
    {
      "full_text": "日本語のテキスト",
      "is_vertical": false,
      "box": {
        "center_x": 0.5,
        "center_y": 0.3,
        "width": 0.8,
        "height": 0.05
      },
      "words": [
        {
          "text": "日本語の",
          "separator": "",
          "box": {
            "center_x": 0.3,
            "center_y": 0.3,
            "width": 0.2,
            "height": 0.05
          }
        }
      ]
    }
  ],
  "elapsed_ms": 234.5
}
```

All bounding box coordinates are **normalized** (0.0–1.0 relative to image dimensions).

### `GET /health`

Health check endpoint.

```bash
curl http://localhost:8080/health
```

## Available Providers

| Name | Description | Requires Network |
|------|-------------|-----------------|
| `glensv2` | Google Lens v2 (default) | Yes |
| `meikiocr` | MeikiOCR local model | No |
| `screenai` | Chrome Screen AI local | No |
| `owocr` | owocr via WebSocket | Local WebSocket |
| `dummy` | Test/template provider | No |
