"""Tooling/structural tests only. DRAFT fixtures are NOT accepted API behavior."""

import copy
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contracts_core import (
    ContractError, ContractStore, PendingApproval, REPO, compatibility_review, compare_contract_directories,
    decode_json, load, semantic_issues,
)
from mock_server import FixturePlanner, make_handler, serve
import validate


class MemorySocket:
    """Exercise HTTP framing without binding a port or pretending approval."""
    def __init__(self, request):
        self.input = BytesIO(request)
        self.output = BytesIO()

    def makefile(self, *args):
        return self.input

    def sendall(self, data):
        self.output.write(data)


class ContractToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = ContractStore()
        cls.planner = FixturePlanner(cls.store)
        cls.fixtures = REPO / "contracts/fixtures"

    def fixture(self, path):
        return load(self.fixtures / path)

    def http(self, method, path, body=None, headers=None, planner=None):
        payload = b"" if body is None else json.dumps(body).encode()
        fields = {"Host": "localhost", "Connection": "close", **(headers or {})}
        if payload:
            fields.update({"Content-Type": "application/json", "Content-Length": str(len(payload))})
        raw = (f"{method} {path} HTTP/1.1\r\n" + "".join(f"{k}: {v}\r\n" for k, v in fields.items()) + "\r\n").encode() + payload
        transport = MemorySocket(raw)
        handler = make_handler(self.store, planner or self.planner, {"http://localhost:8443"}, 0)
        with patch("mock_server.time.sleep") as sleep:
            handler(transport, ("127.0.0.1", 12345), object())
        head, content = transport.output.getvalue().split(b"\r\n\r\n", 1)
        lines = head.decode().split("\r\n")
        output_headers = {k.lower(): v.strip() for k, v in (line.split(":", 1) for line in lines[1:])}
        self.assertEqual(int(output_headers["content-length"]), len(content))
        return int(lines[0].split()[1]), output_headers, json.loads(content) if content else None, sleep

    def test_strict_json_rejects_duplicate_keys_and_non_finite(self):
        for value in ['{"a":1,"a":2}', '{"v":NaN}', '{"v":Infinity}']:
            with self.subTest(value=value), self.assertRaises(ContractError):
                decode_json(value)

    def test_strict_yaml_rejects_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.yaml"
            path.write_text("a: 1\na: 2\n")
            with self.assertRaises(ContractError):
                load(path)

    def test_parent_bundle_is_unchanged_and_draft_is_blocked(self):
        self.assertEqual(self.store.verify_bundle(), 159)
        self.assertEqual(self.store.version["status"], "DRAFT")
        self.assertTrue(self.store.approval_reasons())
        with self.assertRaises(PendingApproval):
            self.store.require_approval()

    def test_mock_refuses_before_socket_creation(self):
        with patch("mock_server.ThreadingHTTPServer") as server:
            with self.assertRaises(PendingApproval):
                serve(self.store, "127.0.0.1", 0, [], 0)
            server.assert_not_called()

    def test_fixture_positive_and_intentional_negative_counts(self):
        counts, errors = validate.fixture_check(self.store)
        self.assertEqual(errors, [])
        self.assertEqual(counts, {"positive": 141, "negative_schema": 11, "negative_semantic": 5})

    def test_poll_ws_and_raw_mapping_references(self):
        counts, errors = validate.correlation_check(self.store)
        self.assertEqual(errors, [])
        self.assertEqual(counts["scenario_coverage"], 24)
        self.assertEqual(self.fixture("ocr/success.json"), self.fixture("http/getOcrResult-200.json")["data"]["ocr"])

    def test_raw_error_is_not_empty_success(self):
        error = self.fixture("ocr/invalid-image-raw.json")
        base = (self.store.contracts / "index.json").as_uri()
        self.assertFalse(self.store.schema_errors(error, {"$ref": "schemas/ocr-provider.schema.json#/definitions/Error"}, base))
        self.assertTrue(self.store.schema_errors(error, {"$ref": "schemas/ocr-provider.schema.json#/definitions/Success"}, base))
        self.assertEqual(self.fixture("ocr/no-text.json")["paragraphs"], [])

    def test_unicode_code_points_preserve_combining_characters(self):
        value = self.fixture("lexicon/unicode-code-points.json")
        self.assertEqual(semantic_issues(value), [])
        self.assertEqual(value["text"], "😀喫茶店é")
        for token in value["tokens"]:
            self.assertEqual(value["text"][token["start"]:token["end"]], token["surface"])
        value["tokens"][0]["end"] = 2  # UTF-16 surrogate length is wrong for this contract.
        self.assertIn("unicode-code-point-offset-or-coverage", semantic_issues(value))

    def test_normalized_public_boxes_reject_crossing_edge(self):
        value = self.fixture("http/getOcrResult-200.json")
        value["data"]["ocr"]["paragraphs"][0]["box"]["center_x"] = 0.99
        self.assertIn("public-box-crosses-image", self.store.check_response("getOcrResult", 200, value))

    def test_raw_shape_matches_dataclasses_without_importing_provider(self):
        report = validate.raw_shape_check(self.store)
        self.assertEqual(report["status"], "EVIDENCED_SHAPE_ONLY")
        self.assertFalse(report["real_provider_tested"])

    def test_all_planned_fixture_responses_match_declared_status_and_schema(self):
        for _, _, operation in self.store.operations():
            with self.subTest(operation=operation["operationId"]):
                self.planner.choose(operation["operationId"])
                self.planner.choose(operation["operationId"], "token-expired")
                self.planner.choose(operation["operationId"], "forbidden")
        for operation_id, scenario in self.planner.scenarios:
            with self.subTest(operation=operation_id, scenario=scenario):
                status, body = self.planner.choose(operation_id, scenario)
                self.assertEqual(self.store.check_response(operation_id, status, body), [])

    def test_mock_never_issues_realtime_or_meeting_credentials(self):
        for operation_id in ["createRealtimeTicket", "getMeetingCredentials"]:
            status, body = self.planner.choose(operation_id)
            self.assertEqual(status, 503)
            self.assertIn("error", body)
            self.assertNotIn("data", body)

    def test_routing_unknown_resource_does_not_rewrite_fixture_ids(self):
        uid = "00000000-0000-4000-8000-999999999999"
        status, _, body, _ = self.http("GET", f"/api/v1/results/{uid}")
        self.assertEqual(status, 404)
        self.assertIn("error", body)
        self.assertIsNone(self.store.match("GET", "/invented-api"))

    def test_mock_http_success_headers_and_explicit_permission_errors(self):
        uid = self.fixture("http/getOcrResult-200.json")["data"]["result_id"]
        for scenario, expected in [("success", 200), ("token-expired", 401), ("forbidden", 403)]:
            status, headers, body, _ = self.http("GET", f"/api/v1/results/{uid}", headers={
                "Origin": "http://localhost:8443", "X-Mock-Scenario": scenario,
            })
            self.assertEqual(status, expected)
            self.assertEqual(headers["x-data-mode"], "mock")
            self.assertEqual(headers["access-control-allow-origin"], "http://localhost:8443")
            self.assertEqual(self.store.check_response("getOcrResult", status, body), [])
            if expected == 401:
                self.assertEqual(body["error"]["code"], "TOKEN_EXPIRED")
                self.assertIn("www-authenticate", headers)

    def test_mock_delay_and_invalid_delay_without_real_wait(self):
        _, _, _, sleep = self.http("GET", "/api/v1/me", headers={"X-Mock-Delay-Ms": "500"})
        sleep.assert_called_once_with(0.5)
        status, _, _, sleep = self.http("GET", "/api/v1/me", headers={"X-Mock-Delay-Ms": "2001"})
        self.assertEqual(status, 400)
        sleep.assert_not_called()

    def test_mock_rejects_invalid_request_and_requires_idempotency_key(self):
        operation = self.store.operation("createOcrJob")[2]
        session = self.fixture("http/getOcrResult-200.json")["data"]["session_id"]
        body = self.fixture("http/createOcrJob-request.json")
        self.assertTrue(self.planner.check_request(operation, {"session_id": session}, {}, {}, body))
        headers = {"idempotency-key": "ct04-tool-test-1234567890"}
        self.assertEqual(self.planner.check_request(operation, {"session_id": session}, {}, headers, body), [])
        self.assertTrue(self.planner.check_request(operation, {"session_id": session}, {}, headers, {"invented": True}))

    def test_mock_tool_failure_cannot_become_success(self):
        with patch.object(self.planner, "choose", side_effect=ContractError("invalid response")):
            status, _, body, _ = self.http("GET", "/api/v1/me")
        self.assertEqual(status, 500)
        self.assertIn("error", body)

    def test_mock_cors_preflight_has_no_body(self):
        status, _, body, _ = self.http("OPTIONS", "/api/v1/me", headers={
            "Origin": "http://localhost:8443", "Access-Control-Request-Method": "GET",
        })
        self.assertEqual(status, 204)
        self.assertIsNone(body)

    def test_compatibility_guard_detects_behavioral_changes(self):
        before = {"required": ["a"], "enum": ["a", "b"], "security": [{"bearer": []}], "properties": {"a": {"type": "string"}}}
        for change in [
            {**before, "required": ["a", "b"]}, {**before, "enum": ["a"]},
            {**before, "security": []}, {**before, "properties": {}},
        ]:
            self.assertTrue(compatibility_review(before, change))
        self.assertEqual(compatibility_review(before, {**before, "description": "docs only"}), [])

    def test_compatibility_guard_detects_removed_schema_file(self):
        with tempfile.TemporaryDirectory() as directory:
            before, after = Path(directory) / "before", Path(directory) / "after"
            for folder in [before, after]:
                (folder / "schemas").mkdir(parents=True)
                for name in ["openapi.yaml", "asyncapi.yaml"]:
                    (folder / name).write_text("test: true\n")
            (before / "schemas/removed.json").write_text('{}')
            self.assertTrue(any("removed.json: schema/document removed" in x for x in compare_contract_directories(before, after)))

    def test_mock_returns_declared_204_without_a_body(self):
        operation = next(op for _, _, op in self.store.operations() if next(iter(op["responses"])) == "204")
        status, body = self.planner.choose(operation["operationId"])
        self.assertEqual(status, 204)
        self.assertIsNone(body)

    def test_captured_invalid_message_fails_without_editing_schema(self):
        args = ["--lint-draft", "--message", str(self.fixtures / "negative/lexicon-utf16-offset.json"),
                "--schema", "schemas/lexicon.schema.json"]
        with patch("builtins.print"):
            self.assertEqual(validate.main(args), 1)

    def test_captured_draft_default_is_pending_and_explicit_lint_is_structural(self):
        args = ["--message", str(self.fixtures / "http/getOcrResult-200.json"), "--operation", "getOcrResult", "--http-status", "200"]
        with patch("builtins.print"):
            self.assertEqual(validate.main(args), 2)
            self.assertEqual(validate.main(["--lint-draft", *args]), 0)


if __name__ == "__main__":
    unittest.main()
