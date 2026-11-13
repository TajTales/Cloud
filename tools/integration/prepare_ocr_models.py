"""Download/verify pinned model bytes; never sends source images externally."""
import argparse
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path

from huggingface_hub import hf_hub_download

parser = argparse.ArgumentParser()
parser.add_argument("--offline", action="store_true")
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
lock = json.loads((root / "meikipop-ocr-server/models.lock.json").read_text())
if version("meikiocr") != lock["package_version"]:
    raise RuntimeError("MeikiOCR version does not match the tested model lock")
cache = root / "meikipop-ocr-server/.local-models/hub"
for item in lock["models"]:
    path = Path(hf_hub_download(repo_id=item["repo_id"], filename=item["filename"], revision=item["revision"], cache_dir=str(cache), local_files_only=args.offline))
    if path.stat().st_size != item["size_bytes"] or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
        raise RuntimeError("Model checksum mismatch: " + item["filename"])
    # MeikiOCR 0.3.5 uses the default revision in local_files_only mode. Bind its
    # private cache alias to the verified revision instead of following latest.
    reference = cache / ("models--" + item["repo_id"].replace("/", "--")) / "refs/main"
    reference.parent.mkdir(parents=True, exist_ok=True)
    reference.write_text(item["revision"])
print(json.dumps({"status": "PINNED_MODELS_VERIFIED", "models": len(lock["models"]), "offline": args.offline}))
