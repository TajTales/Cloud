"""from dataclasses import dataclass
from pathlib import Path
import os
import re
from urllib.parse import urlsplit

from ..config import ConfigurationError


@dataclass(frozen=True)
class PersistenceSettings:
    endpoint: str
    table_name: str
    data_dir: Path

    @classmethod
    def from_environment(cls, environment=None):
        values = os.environ if environment is None else environment
        parsed = urlsplit(values.get("DYNAMODB_ENDPOINT", "http://127.0.0.1:8000"))
        try:
            port = parsed.port
        except ValueError:
            raise ConfigurationError("DYNAMODB_ENDPOINT has an invalid port") from None
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or not port or parsed.path not in {"", "/"} or parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise ConfigurationError("This adapter requires an explicit HTTP loopback DynamoDB endpoint")
        # Normalize localhost to a literal address; do not rely on DNS or proxies.
        host = "[::1]" if parsed.hostname == "::1" else "127.0.0.1"
        table = values.get("DYNAMODB_TABLE", "lingualive-local")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,255}", table):
            raise ConfigurationError("DYNAMODB_TABLE is invalid")
        if "APP_DATA_DIR" in values and not values["APP_DATA_DIR"]:
            raise ConfigurationError("APP_DATA_DIR must not be empty")
        directory = Path(values.get("APP_DATA_DIR", Path(__file__).resolve().parents[3] / ".local-data")).expanduser().resolve()
        if directory == Path(directory.anchor):
            raise ConfigurationError("APP_DATA_DIR must be a dedicated data directory")
        return cls(f"http://{host}:{port}", table, directory)"""
from dataclasses import dataclass
from pathlib import Path
import os
import re
from urllib.parse import urlsplit

from ..config import ConfigurationError


@dataclass(frozen=True)
class PersistenceSettings:
    endpoint: str
    table_name: str
    data_dir: Path
    mode: str = "local"
    region: str = ""
    #new
    bucket: str = ""

    @classmethod
    def _cloud(cls, values):
        region = values.get("AWS_REGION", "")
        if not re.fullmatch(r"[a-z]{2}(-[a-z]+)+-\d", region):
            raise ConfigurationError("AWS_REGION is required in cloud mode")
        if values.get("DYNAMODB_ENDPOINT"):
            raise ConfigurationError("DYNAMODB_ENDPOINT must not be set in cloud mode")
        table = values.get("DYNAMODB_TABLE", "")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,255}", table):
            raise ConfigurationError("DYNAMODB_TABLE is required and must be valid in cloud mode")
        if "APP_DATA_DIR" in values and not values["APP_DATA_DIR"]:
            raise ConfigurationError("APP_DATA_DIR must not be empty")
        directory = Path(values.get("APP_DATA_DIR", Path(__file__).resolve().parents[3] / ".local-data")).expanduser().resolve()
        if directory == Path(directory.anchor):
            raise ConfigurationError("APP_DATA_DIR must be a dedicated data directory")
        #new 
        bucket = values.get("S3_BUCKET", "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket):
            raise ConfigurationError("S3_BUCKET is required and must be valid in cloud mode")
        return cls("", table, directory, "cloud", region, bucket)
        #return cls("", table, directory, "cloud", region)

    @classmethod
    def from_environment(cls, environment=None):
        values = os.environ if environment is None else environment
        if values.get("DEPLOYMENT_MODE", "local") == "cloud":
            return cls._cloud(values)
        parsed = urlsplit(values.get("DYNAMODB_ENDPOINT", "http://127.0.0.1:8000"))
        try:
            port = parsed.port
        except ValueError:
            raise ConfigurationError("DYNAMODB_ENDPOINT has an invalid port") from None
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or not port or parsed.path not in {"", "/"} or parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise ConfigurationError("This adapter requires an explicit HTTP loopback DynamoDB endpoint")
        # Normalize localhost to a literal address; do not rely on DNS or proxies.
        host = "[::1]" if parsed.hostname == "::1" else "127.0.0.1"
        table = values.get("DYNAMODB_TABLE", "lingualive-local")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,255}", table):
            raise ConfigurationError("DYNAMODB_TABLE is invalid")
        if "APP_DATA_DIR" in values and not values["APP_DATA_DIR"]:
            raise ConfigurationError("APP_DATA_DIR must not be empty")
        directory = Path(values.get("APP_DATA_DIR", Path(__file__).resolve().parents[3] / ".local-data")).expanduser().resolve()
        if directory == Path(directory.anchor):
            raise ConfigurationError("APP_DATA_DIR must be a dedicated data directory")
        return cls(f"http://{host}:{port}", table, directory)