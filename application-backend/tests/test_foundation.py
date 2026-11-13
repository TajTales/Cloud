"""Foundation behavior over real loopback HTTP. Test identities/DTOs are synthetic."""
from dataclasses import replace
import json
import socket
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from aiohttp.test_utils import TestClient, TestServer

from lingualive_api.app import create_app, Result, STATE
from lingualive_api.auth import Identity
from lingualive_api.config import ConfigurationError, Settings
from lingualive_api.contracts import ContractFailure, ContractRegistry, strict_json
from lingualive_api.errors import ApiError

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = Settings.from_environment({"APP_ENV": "test"})


def fixture(name):
    return json.loads((ROOT / "contracts/fixtures" / name).read_text())


class TestOnlyVerifier:
    """Dependency injection for transport tests, unavailable from CLI/environment."""
    ready = True

    async def verify_access_token(self, token):
        if token == "synthetic-expired":
            raise ApiError(401, "TOKEN_EXPIRED", "Access token expired.")
        return Identity("synthetic-test-user", ("admin",) if token == "synthetic-admin" else ("user",))


class ConfigurationAndContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts = ContractRegistry(SETTINGS.contracts_dir)

    def test_local_defaults_do_not_need_cloud_configuration(self):
        settings = Settings.from_environment({})
        self.assertEqual((settings.host, settings.port, settings.data_mode), ("127.0.0.1", 8081, "real"))
        self.assertEqual(len(self.contracts.operations), 50)
        self.assertEqual(self.contracts.version["status"], "DRAFT")

    def test_invalid_configuration_fails_before_binding(self):
        for values in [{"APP_ENV": "production"}, {"APP_HOST": "0.0.0.0"}, {"APP_PORT": "0"},
                       {"APP_PORT": "invalid"}, {"APP_MAX_BODY_BYTES": "1048577"}, {"DATA_MODE": "mock"},
                       {"CONTRACTS_DIR": "/missing"}, {"LOG_LEVEL": "unknown"},
                       *[{"ALLOWED_ORIGINS": value} for value in ["*", "https://user:pass@example.test", "https://example.test/path", "http://localhost:invalid"]]]:
            with self.subTest(values=values), self.assertRaises(ConfigurationError):
                Settings.from_environment(values)

    def test_startup_does_not_open_outbound_connections(self):
        with patch("socket.socket.connect", side_effect=AssertionError("No outbound network permitted")):
            app = create_app(SETTINGS)
        self.assertEqual(app[STATE]["handlers"], {})

    def test_bundle_changes_and_outside_paths_are_rejected(self):
        for filename in ["missing.json", "../outside.json"]:
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                contracts = Path(directory) / "contracts"
                contracts.mkdir()
                (contracts / "contract-version.json").write_text(json.dumps({"files": {filename: "0" * 64}, "bundle_sha256": "0" * 64}))
                with self.assertRaises(ContractFailure):
                    ContractRegistry(contracts)

    def test_no_schema_resolution_outside_registry(self):
        with self.assertRaises(ContractFailure):
            self.contracts.resolve({"$ref": "https://example.invalid/remote.json"})

    def test_runtime_adapter_accepts_original_positive_http_fixtures(self):
        manifest = fixture("manifest.json")
        count = 0
        for item in manifest["files"]:
            if item.get("operation_id") and item.get("http_status") and item["expect_valid"]:
                operation = self.contracts.operations[item["operation_id"]]
                self.assertEqual(self.contracts.response_issues(operation, item["http_status"], fixture(item["file"])), [])
                count += 1
        self.assertGreater(count, 50)

    def test_request_adapter_enforces_body_and_idempotency(self):
        op = self.contracts.operations["createOcrJob"]
        path = {"session_id": "00000000-0000-4000-8000-000000000001"}
        body = fixture("http/createOcrJob-request.json")
        self.assertTrue(self.contracts.request_issues(op, path, {}, {}, body))
        self.assertEqual(self.contracts.request_issues(op, path, {}, {"idempotency-key": "synthetic-idempotency-1234"}, body), [])

    def test_strict_json_rejects_ambiguous_or_non_finite_values(self):
        for text in ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '{"a":1e999}']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                strict_json(text)

    def test_204_body_and_undeclared_status_are_rejected(self):
        op = next(op for op in self.contracts.operations.values() if "204" in op.definition["responses"])
        self.assertEqual(self.contracts.response_issues(op, 204, None), [])
        self.assertTrue(self.contracts.response_issues(op, 204, {}))
        with self.assertRaises(ContractFailure):
            self.contracts.response_issues(self.contracts.operations["getMe"], 299, {})

    def test_unknown_handler_registration_is_rejected(self):
        with self.assertRaises(ContractFailure):
            create_app(SETTINGS, handlers={"inventedOperation": None})

    def test_invalid_datetime_and_uri_in_real_dto_shapes_are_rejected(self):
        result = fixture("http/getOcrResult-200.json")
        result["data"]["created_at"] = "2026-99-99T14:30:01.000Z"
        self.assertTrue(self.contracts.response_issues(self.contracts.operations["getOcrResult"], 200, result))
        upload = fixture("http/createFrameUpload-200.json")
        upload["data"]["upload"]["url"] = "not a valid absolute uri"
        self.assertTrue(self.contracts.response_issues(self.contracts.operations["createFrameUpload"], 200, upload))

    def test_missing_format_dependencies_cannot_silently_disable_validation(self):
        with patch("lingualive_api.contracts.FormatChecker", return_value=SimpleNamespace(checkers={"uuid": None, "email": None})):
            with self.assertRaises(ContractFailure):
                ContractRegistry(SETTINGS.contracts_dir)


class FoundationHttpTests(unittest.IsolatedAsyncioTestCase):
    async def open(self, **kwargs):
        app = create_app(kwargs.pop("settings", SETTINGS), **kwargs)
        def loopback_socket(host, port, family):
            listener = socket.socket(family, socket.SOCK_STREAM)
            try:
                listener.bind((host, port))
            except BaseException:
                listener.close()
                raise
            return listener
        client = TestClient(TestServer(app, socket_factory=loopback_socket))
        self.addAsyncCleanup(client.close)
        await client.start_server()
        return client

    async def assert_error(self, response, status, code=None):
        self.assertEqual(response.status, status)
        body = await response.json()
        self.assertEqual(response.headers["X-Request-Id"], body["request_id"])
        self.assertEqual(response.headers["X-Data-Mode"], "real")
        self.assertEqual(response.headers["X-Contract-Status"], "DRAFT")
        self.assertEqual(ContractRegistry(SETTINGS.contracts_dir).error_issues(body), [])
        if code:
            self.assertEqual(body["error"]["code"], code)
        return body

    async def test_liveness_and_readiness_are_different(self):
        client = await self.open()
        response = await client.get("/health/live", headers={"X-Request-Id": "foundation-smoke-1"})
        self.assertEqual(response.status, 200)
        body = await response.json()
        self.assertEqual(body["data"]["status"], "alive")
        self.assertEqual(body["request_id"], "foundation-smoke-1")
        await self.assert_error(await client.get("/health/ready"), 503, "FEATURE_NOT_CONFIGURED")

    async def test_protected_route_requires_token_and_never_issues_one(self):
        client = await self.open()
        response = await client.get("/api/v1/me")
        body = await self.assert_error(response, 401, "AUTH_REQUIRED")
        self.assertNotIn("data", body)
        self.assertIn("WWW-Authenticate", response.headers)

    async def test_cognito_unconfigured_does_not_accept_arbitrary_bearer(self):
        client = await self.open()
        body = await self.assert_error(await client.get("/api/v1/me", headers={"Authorization": "Bearer not-a-real-token"}), 503, "FEATURE_NOT_CONFIGURED")
        self.assertNotIn("not-a-real-token", json.dumps(body))

    async def test_bearer_syntax_and_duplicate_authorization(self):
        client = await self.open()
        for headers in [{"Authorization": "Basic synthetic"}, {"Authorization": "Bearer"},
                        [("Authorization", "Bearer one"), ("Authorization", "Bearer two")]]:
            await self.assert_error(await client.get("/api/v1/me", headers=headers), 401)

    async def test_verified_test_identity_does_not_make_business_services_ready(self):
        client = await self.open(authenticator=TestOnlyVerifier())
        await self.assert_error(await client.get("/api/v1/me", headers={"Authorization": "Bearer synthetic-test-only"}), 503, "FEATURE_NOT_CONFIGURED")

    async def test_admin_scope_is_checked_before_business_dispatch(self):
        client = await self.open(authenticator=TestOnlyVerifier())
        await self.assert_error(await client.get("/api/v1/admin/overview", headers={"Authorization": "Bearer synthetic-user"}), 403, "FORBIDDEN")

    async def test_expired_token_from_verifier_is_preserved(self):
        client = await self.open(authenticator=TestOnlyVerifier())
        await self.assert_error(await client.get("/api/v1/me", headers={"Authorization": "Bearer synthetic-expired"}), 401, "TOKEN_EXPIRED")

    async def test_unknown_route_and_method_have_json_envelopes(self):
        client = await self.open()
        await self.assert_error(await client.get("/api/v1/missing"), 404, "RESOURCE_NOT_FOUND")
        response = await client.put("/api/v1/me")
        await self.assert_error(response, 405, "VALIDATION_ERROR")
        self.assertIn("Allow", response.headers)

    async def test_cors_allowed_origin_also_applies_to_error_responses(self):
        client = await self.open()
        response = await client.get("/api/v1/me", headers={"Origin": "http://localhost:8443"})
        await self.assert_error(response, 401)
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://localhost:8443")
        self.assertIn("X-Data-Mode", response.headers["Access-Control-Expose-Headers"])

    async def test_disallowed_origin_does_not_get_cors_grant(self):
        client = await self.open()
        response = await client.get("/api/v1/me", headers={"Origin": "https://untrusted.example"})
        await self.assert_error(response, 403)
        self.assertNotIn("Access-Control-Allow-Origin", response.headers)

    async def test_preflight_only_allows_declared_methods_and_headers(self):
        client = await self.open()
        headers = {"Origin": "http://localhost:8443", "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "authorization,x-request-id"}
        response = await client.options("/api/v1/me", headers=headers)
        self.assertEqual(response.status, 204)
        self.assertEqual(await response.read(), b"")
        await self.assert_error(await client.options("/api/v1/missing", headers=headers), 404)
        headers["Access-Control-Request-Headers"] = "x-mock-scenario"
        await self.assert_error(await client.options("/api/v1/me", headers=headers), 403)

    async def test_invalid_or_duplicate_request_id_is_replaced_safely(self):
        client = await self.open()
        for headers in [{"X-Request-Id": "x" * 129}, [("X-Request-Id", "one"), ("X-Request-Id", "two")]]:
            body = await self.assert_error(await client.get("/api/v1/me", headers=headers), 400)
            self.assertEqual(len(body["request_id"]), 36)

    async def test_request_validation_does_not_echo_submitted_secrets(self):
        client = await self.open(authenticator=TestOnlyVerifier())
        response = await client.patch("/api/v1/me", json={"roles": ["admin"], "password": "do-not-echo-this"}, headers={"Authorization": "Bearer synthetic-test-only"})
        body = await self.assert_error(response, 400, "VALIDATION_ERROR")
        self.assertNotIn("do-not-echo-this", json.dumps(body))

    async def test_strict_json_and_content_type_over_http(self):
        client = await self.open(authenticator=TestOnlyVerifier())
        for data, content_type in [('{"a":1,"a":2}', "application/json"), ('{"a":NaN}', "application/json"), ('{"a":1e999}', "application/json"), ('{}', "text/plain")]:
            await self.assert_error(await client.patch("/api/v1/me", data=data, headers={"Authorization": "Bearer synthetic-test-only", "Content-Type": content_type}), 400)

    async def test_request_limit_is_enforced(self):
        client = await self.open(settings=replace(SETTINGS, max_body_bytes=64), authenticator=TestOnlyVerifier())
        path = "/api/v1/sessions/00000000-0000-4000-8000-000000000001/uploads"
        await self.assert_error(await client.post(path, data='{"payload":"' + "x" * 100 + '"}', headers={"Authorization": "Bearer synthetic-test-only", "Content-Type": "application/json"}), 413)

    async def test_query_and_idempotency_header_duplicates_are_rejected(self):
        client = await self.open(authenticator=TestOnlyVerifier())
        await self.assert_error(await client.get("/api/v1/vocabulary?limit=1&limit=2", headers={"Authorization": "Bearer synthetic-test-only"}), 400)
        path = "/api/v1/sessions/00000000-0000-4000-8000-000000000001/ocr-jobs"
        headers = [("Authorization", "Bearer synthetic-test-only"), ("Idempotency-Key", "one-key"), ("Idempotency-Key", "another-key")]
        await self.assert_error(await client.post(path, json=fixture("http/createOcrJob-request.json"), headers=headers), 400)

    async def test_schema_guard_rejects_invalid_handler_response(self):
        async def invalid(request, body):
            return Result({"unexpected_secret": "must-not-leak"})
        client = await self.open(authenticator=TestOnlyVerifier(), handlers={"getMe": invalid})
        body = await self.assert_error(await client.get("/api/v1/me", headers={"Authorization": "Bearer synthetic-test-only"}), 500, "INTERNAL_ERROR")
        self.assertNotIn("must-not-leak", json.dumps(body))

    async def test_response_writer_preserves_valid_contract_dto_in_test_only_handler(self):
        async def test_handler(request, body):
            return Result(fixture("http/getMe-200.json")["data"])
        client = await self.open(authenticator=TestOnlyVerifier(), handlers={"getMe": test_handler})
        response = await client.get("/api/v1/me", headers={"Authorization": "Bearer synthetic-test-only"})
        self.assertEqual(response.status, 200)
        output = await response.json()
        contracts = client.server.app[STATE]["contracts"]
        self.assertEqual(contracts.response_issues(contracts.operations["getMe"], 200, output), [])

    async def test_internal_exception_and_query_secrets_are_not_logged(self):
        async def crash(request, body):
            raise RuntimeError("do-not-log-password")
        client = await self.open(authenticator=TestOnlyVerifier(), handlers={"getMe": crash})
        with self.assertLogs("lingualive.api", level="INFO") as logs:
            response = await client.get("/api/v1/me?access_token=do-not-log-token", headers={"Authorization": "Bearer synthetic-secret-header"})
        await self.assert_error(response, 500)
        text = "\n".join(logs.output)
        for secret in ["do-not-log-password", "do-not-log-token", "synthetic-secret-header"]:
            self.assertNotIn(secret, text)

    async def test_malformed_error_from_handler_is_safe_json_500(self):
        async def invalid_error(request, body):
            raise ApiError(503, "NOT_IN_CONTRACT", "must-not-leak")
        client = await self.open(authenticator=TestOnlyVerifier(), handlers={"getMe": invalid_error})
        body = await self.assert_error(await client.get("/api/v1/me", headers={"Authorization": "Bearer synthetic-test-only"}), 500)
        self.assertNotIn("must-not-leak", json.dumps(body))


if __name__ == "__main__":
    unittest.main()
