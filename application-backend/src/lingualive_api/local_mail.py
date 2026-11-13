"""Private development mailbox. Deliberately does not send external email."""
import json
import os
from pathlib import Path
from uuid import uuid4


class LocalMailbox:
    mode = "local_mailbox"

    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.directory.is_symlink():
            raise ValueError("Mailbox must not be a symlink")
        self.directory.chmod(0o700)

    def deliver(self, *, email, purpose, code, expires_at_s):
        path = self.directory / (str(uuid4()) + ".json")
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump({"delivery_mode": self.mode, "to": email, "purpose": purpose,
                       "code": code, "expires_at_s": expires_at_s}, output, ensure_ascii=False)
            output.flush()
            os.fsync(output.fileno())
