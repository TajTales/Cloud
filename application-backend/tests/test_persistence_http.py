import os
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from aiohttp.test_utils import TestClient, TestServer

from lingualive_api.app import create_app
from lingualive_api.config import Settings
from lingualive_api.persistence.dynamo import DynamoStore
from lingualive_api.persistence.settings import PersistenceSettings


class PersistenceHttpTests(unittest.IsolatedAsyncioTestCase):
    async def test_database_ready_does_not_fabricate_auth_or_full_readiness(self):
        with tempfile.TemporaryDirectory() as folder:
            values = {"APP_ENV": "test", "PERSISTENCE_ENABLED": "1", "APP_DATA_DIR": folder,
                      "DYNAMODB_ENDPOINT": "http://127.0.0.1:8000", "DYNAMODB_TABLE": "lingualive-test-http-" + uuid4().hex}
            store = DynamoStore(PersistenceSettings.from_environment(values))
            store.ensure_table()
            client = None
            try:
                with patch.dict(os.environ, values):
                    client = TestClient(TestServer(create_app(Settings.from_environment(values))))
                    await client.start_server()
                response = await client.get("/health/ready")
                self.assertEqual(response.status, 503)
                body = await response.json()
                self.assertEqual(body["error"]["details"]["dependencies"], {"database": "ready", "object_storage": "ready", "authentication": "not_configured"})
                self.assertFalse(body["error"]["details"]["business_services_ready"])
                response = await client.get("/api/v1/me", headers={"Authorization": "Bearer synthetic-untrusted"})
                self.assertEqual(response.status, 503)
            finally:
                if client:
                    await client.close()
                assert store.table.startswith("lingualive-test-")
                store.call("delete_table", TableName=store.table)
                store.close()
