"""DynamoDB adapter for real AWS. Reuses all logic of DynamoStore; only the connection differs."""
from __future__ import annotations

import logging
from time import time

import boto3
from botocore.config import Config

from .dynamo import DynamoStore
from .errors import StorageUnavailable
from .settings import PersistenceSettings

logger = logging.getLogger("lingualive.dynamo_aws")


class AwsDynamoStore(DynamoStore):
    def __init__(self, settings: PersistenceSettings, *, clock=time):
        if settings.mode != "cloud":
            raise ValueError("AwsDynamoStore requires cloud settings")
        # Deliberately NOT calling super().__init__: it forces loopback + fake credentials.
        self.settings = settings
        self.clock = clock
        # Credentials come from the standard boto3 chain (AWS_PROFILE, env vars, task role).
        session = boto3.session.Session(region_name=settings.region)
        self.client = session.client(
            "dynamodb",
            config=Config(connect_timeout=3, read_timeout=10,
                          retries={"max_attempts": 5, "mode": "standard"}),
        )
        self.table = settings.table_name

    def call(self, method, **kwargs):
        try:
            return super().call(method, **kwargs)
        except StorageUnavailable as exc:
            # The base class hides the AWS error code; log it so AccessDenied etc. are diagnosable.
            cause = exc.__context__
            code = getattr(cause, "response", {}).get("Error", {}).get("Code") if cause else type(cause).__name__
            logger.error("dynamodb_call_failed method=%s code=%s", method, code)
            raise