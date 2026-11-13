import base64
import hashlib
import hmac
import json
from time import time

from .errors import InvalidRecord


class CursorCodec:
    def __init__(self, secret, *, clock=time):
        if len(secret) < 32:
            raise InvalidRecord("Cursor signing key must contain at least 32 bytes")
        self.secret, self.clock = secret, clock

    def encode(self, binding, key):
        body = json.dumps({"v": 1, "binding": binding, "key": key, "expires": int(self.clock()) + 3600}, sort_keys=True, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(body + hmac.digest(self.secret, body, "sha256")).decode().rstrip("=")

    def decode(self, token, binding):
        try:
            if not isinstance(token, str) or len(token) > 8192:
                raise ValueError()
            data = base64.b64decode(token + "=" * (-len(token) % 4), altchars=b"-_", validate=True)
            body, signature = data[:-32], data[-32:]
            if not hmac.compare_digest(signature, hmac.digest(self.secret, body, "sha256")):
                raise ValueError()
            value = json.loads(body)
            indexed = binding.get("index") == "gsi1"
            expected_keys = {"pk", "sk", "gsi_pk", "gsi_sk"} if indexed else {"pk", "sk"}
            partition = "gsi_pk" if indexed else "pk"
            if value["v"] != 1 or value["binding"] != binding or value["expires"] <= self.clock() or set(value["key"]) != expected_keys or value["key"][partition] != binding["pk"]:
                raise ValueError()
            return value["key"]
        except (ValueError, KeyError, TypeError):
            raise InvalidRecord("Invalid, expired or mismatched cursor") from None
