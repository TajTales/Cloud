"""Verified-identity boundary; no token issuer, JWT bypass or local demo login."""
from dataclasses import dataclass
from typing import Protocol

from .errors import unavailable


@dataclass(frozen=True)
class Identity:
    user_id: str
    roles: tuple[str, ...]


class Authenticator(Protocol):
    ready: bool

    async def verify_access_token(self, token: str) -> Identity: ...


class UnconfiguredAuthenticator:
    ready = False

    async def verify_access_token(self, token):
        raise unavailable()
