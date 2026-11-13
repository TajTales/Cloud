import hashlib
from importlib.metadata import version
import json
from pathlib import Path

import rapidocr_onnxruntime

root = Path(__file__).resolve().parents[2]
lock = json.loads((root / "meikipop-ocr-server/models-zh.lock.json").read_text())
if version("rapidocr-onnxruntime") != lock["package_version"]:
    raise RuntimeError("Chinese OCR package version does not match its lock")
directory = Path(rapidocr_onnxruntime.__file__).parent / "models"
for item in lock["models"]:
    content = (directory / item["filename"]).read_bytes()
    if len(content) != item["size_bytes"] or hashlib.sha256(content).hexdigest() != item["sha256"]:
        raise RuntimeError("Chinese OCR model checksum mismatch")
print(json.dumps({"status": "PINNED_CHINESE_MODELS_VERIFIED", "models": len(lock["models"]), "offline": True}))
