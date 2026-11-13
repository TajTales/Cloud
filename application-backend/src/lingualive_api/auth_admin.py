"""Explicit OS-owner commands. No HTTP self-promotion or account seeding."""
import argparse
import json

from .config import ConfigurationError, Settings
from .contracts import ContractRegistry
from .errors import ApiError
from .local_admin import LocalAdmin
from .local_auth import LocalAuth
from .persistence.bundle import PersistenceBundle
from .persistence.settings import PersistenceSettings
from .persistence.errors import PersistenceError


def main():
    parser = argparse.ArgumentParser(description="Local account administration; no AWS calls")
    parser.add_argument("action", choices=["grant-admin", "revoke-admin", "mailbox"])
    parser.add_argument("--email", required=True)
    parser.add_argument("--reason")
    args = parser.parse_args()
    settings = Settings.from_environment()
    email = LocalAuth.email(args.email)
    if args.action == "mailbox":
        directory = PersistenceSettings.from_environment().data_dir / "mailbox"
        messages = []
        if directory.exists():
            for path in directory.glob("*.json"):
                if path.is_symlink():
                    continue
                data = json.loads(path.read_text())
                if data["to"] == email:
                    messages.append(data)
        print(json.dumps(sorted(messages, key=lambda item: item["expires_at_s"], reverse=True), ensure_ascii=False, indent=2))
        return
    if not args.reason:
        parser.error("--reason is required for authority changes")
    storage = PersistenceBundle(PersistenceSettings.from_environment(), ContractRegistry(settings.contracts_dir))
    try:
        result = LocalAdmin(LocalAuth(storage)).provision(email, grant=args.action == "grant-admin", reason=args.reason)
        print(json.dumps(result, ensure_ascii=False))
    except ApiError as error:
        parser.exit(1, error.code + ": " + error.message + "\n")
    except (ConfigurationError, PersistenceError, OSError) as error:
        parser.exit(2, "LOCAL_AUTH_ADMIN_UNAVAILABLE: " + type(error).__name__ + "\n")
    finally:
        storage.close()


if __name__ == "__main__":
    main()
