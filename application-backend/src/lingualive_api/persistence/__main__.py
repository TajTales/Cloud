import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from ..config import ConfigurationError, Settings
from ..contracts import ContractRegistry
from .bundle import PersistenceBundle
from .catalog import canonical
from .errors import PersistenceError
from .settings import PersistenceSettings


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local-only storage administration; no cloud endpoints or credential discovery.")
    parser.add_argument("action", choices=["init", "check", "export", "inspect"])
    parser.add_argument("--output", type=Path, help="New NDJSON file for export; existing files will not be overwritten")
    args = parser.parse_args(argv)
    bundle = None
    try:
        config = PersistenceSettings.from_environment()
        bundle = PersistenceBundle(config, ContractRegistry(Settings.from_environment().contracts_dir))
        if args.action == "init":
            bundle.store.ensure_table()
        if args.action == "inspect":
            items, private_count = [], 0
            for item in bundle.store.export_items():
                if item["pk"].startswith("LOCAL_AUTH#") or item["pk"].startswith("IDEMPOTENCY#"):
                    private_count += 1
                    continue
                if "payload" in item:
                    item["payload"] = json.loads(item["payload"])
                items.append(item)
            print(json.dumps({"table": config.table_name, "items": items, "hidden_auth_and_idempotency_items": private_count}, ensure_ascii=False, indent=2))
            return 0
        if args.action == "export":
            if args.output is None:
                parser.error("export requires --output")
            digest, count = hashlib.sha256(), 0
            descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w") as output:
                for item in bundle.store.export_items():
                    line = canonical(item) + "\n"
                    output.write(line)
                    digest.update(line.encode())
                    count += 1
                output.flush()
                os.fsync(output.fileno())
            print(json.dumps({"status": "EXPORTED", "model_version": 1, "items": count, "sha256": digest.hexdigest(), "note": "Quiesce writes for a consistent multi-page snapshot. Object bodies are backed up separately."}))
            return 0
        health = bundle.health()
        print(json.dumps({"mode": "local", "endpoint": config.endpoint, "table": config.table_name, "model_version": 1, **health}))
        return 0 if all(value == "ready" for value in health.values()) else 1
    except (ConfigurationError, PersistenceError, OSError) as exc:
        print(f"STORAGE_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        if bundle:
            bundle.close()


if __name__ == "__main__":
    raise SystemExit(main())
