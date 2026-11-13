import argparse
import json
import logging
import sys

from aiohttp import web

from .app import create_app, STATE
from .config import ConfigurationError, Settings
from .contracts import ContractFailure


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local API; optional real local password auth/persistence. No Docker or AWS cloud.")
    parser.add_argument("--check", action="store_true", help="Validate config and contract package without opening a socket")
    args = parser.parse_args(argv)
    try:
        settings = Settings.from_environment()
        app = create_app(settings)
        logging.basicConfig(level=settings.log_level, format="%(message)s")
        contracts = app[STATE]["contracts"]
        if args.check:
            print(json.dumps({"status": "FOUNDATION_CONFIG_VALID", "environment": settings.environment,
                              "host": settings.host, "port": settings.port, "contract_version": contracts.version["contract_version"],
                              "contract_status": contracts.version["status"], "bundle_sha256": contracts.version["bundle_sha256"],
                              "declared_operations": len(contracts.operations), "implemented_business_operations": len(app[STATE]["handlers"]),
                              "persistence_enabled": settings.persistence_enabled,
                              "auth_provider": "local_password" if settings.local_auth_enabled else "not_configured",
                              "business_services_ready": False}, indent=2))
            return 0
        display_host = f"[{settings.host}]" if ":" in settings.host else settings.host
        print(f"Local API: http://{display_host}:{settings.port}; {len(app[STATE]['handlers'])} local business operations; full system integration pending.", flush=True)
        web.run_app(app, host=settings.host, port=settings.port, access_log=None, print=None)
        return 0
    except (ConfigurationError, ContractFailure) as exc:
        print(f"STARTUP_FAILED: {exc}", file=sys.stderr)
        return 2
    except OSError:
        print("STARTUP_FAILED: could not bind local address/port", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
