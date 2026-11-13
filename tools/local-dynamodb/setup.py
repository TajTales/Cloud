"""Download only the checksum-pinned vendor distribution; never start a service."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]


def main():
    lock = json.loads((ROOT / "application-backend/local-tools.lock.json").read_text())
    destination = ROOT / "application-backend/.local-tools/dynamodb"
    if destination.exists():
        jar = destination / "DynamoDBLocal.jar"
        if not jar.is_file() or hashlib.sha256(jar.read_bytes()).hexdigest() != lock["jar_sha256"]:
            raise RuntimeError("Existing installation does not match the pin; inspect it before replacing")
        print("DynamoDB Local is already installed and matches the pinned JAR.")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".download-", dir=destination.parent))
    try:
        archive = staging / "vendor.tar.gz"
        digest, size = hashlib.sha256(), 0
        with urlopen(lock["archive_url"], timeout=120) as response, archive.open("wb") as output:
            while block := response.read(1024 * 1024):
                size += len(block)
                if size > lock["archive_bytes"]:
                    raise RuntimeError("Vendor archive changed; review the pin instead of using latest silently")
                digest.update(block)
                output.write(block)
        if size != lock["archive_bytes"] or digest.hexdigest() != lock["archive_sha256"]:
            raise RuntimeError("Vendor archive checksum mismatch; no installation performed")
        payload = staging / "payload"
        payload.mkdir()
        with tarfile.open(archive) as package:
            if sum(item.size for item in package.getmembers()) > 250 * 1024 * 1024:
                raise RuntimeError("Unexpected extracted archive size")
            package.extractall(payload, filter="data")
        jar = payload / "DynamoDBLocal.jar"
        if hashlib.sha256(jar.read_bytes()).hexdigest() != lock["jar_sha256"]:
            raise RuntimeError("Pinned JAR checksum mismatch")
        version = subprocess.check_output(["java", "-jar", str(jar), "-version"], text=True).strip()
        if version != lock["dynamodb_local_version"]:
            raise RuntimeError("Unexpected DynamoDB Local version")
        payload.rename(destination)
        print(f"Installed DynamoDB Local {version}; no AWS account or Docker used.")
    finally:
        shutil.rmtree(staging)


if __name__ == "__main__":
    main()
