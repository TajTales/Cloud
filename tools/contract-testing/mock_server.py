#!/usr/bin/env python3
"""Loopback fixture HTTP mock. No draft override, credentials or production fallback."""

from __future__ import annotations

import argparse
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import time
from urllib.parse import parse_qs, urlsplit

try:
    from contracts_core import ContractError, ContractStore, PendingApproval, decode_json, load
except ModuleNotFoundError as exc:
    print(f"SETUP_REQUIRED: {exc.name}; isolated contract tooling is required", file=sys.stderr)
    raise SystemExit(3)


class FixturePlanner:
    """Select existing declared responses; no business storage or auth implementation."""

    def __init__(self, store):
        self.store = store
        self.scenarios = {}
        supplement = store.contracts / "fixtures/ct04-draft/manifest.json"
        if supplement.exists():
            for scenario in load(supplement).get("mock_scenarios", []):
                self.scenarios[(scenario["operation_id"], scenario["name"])] = scenario

    def common_error(self, status):
        response = self.store.openapi["components"]["responses"][f"Error{status}"]
        example = next(iter(response["content"]["application/json"]["examples"].values()))
        return status, copy.deepcopy(example["value"])

    def check_request(self, operation, parameters, query, headers, body):
        issues = []
        for item in operation.get("parameters", []):
            parameter, base = self.store.resolve(item)
            location, name = parameter["in"], parameter["name"]
            values = {"path": parameters, "query": query, "header": headers}.get(location, {})
            value = values.get(name.lower() if location == "header" else name)
            if value is None:
                if parameter.get("required"):
                    issues.append(f"Missing {location} parameter {name}")
                continue
            schema, _ = self.store.resolve(parameter["schema"], base)
            if schema.get("type") == "integer":
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    issues.append(f"Invalid integer {name}")
                    continue
            issues.extend(self.store.schema_errors(value, parameter["schema"], base))
        request = operation.get("requestBody")
        if request:
            if body is None and request.get("required"):
                issues.append("Missing JSON body")
            elif body is not None:
                issues.extend(self.store.schema_errors(body, request["content"]["application/json"]["schema"]))
        elif body is not None:
            issues.append("Body not declared by this operation")
        return issues

    @staticmethod
    def fixture_scope_matches(parameters, body):
        data = body.get("data", {}) if isinstance(body, dict) else {}
        for name, expected in parameters.items():
            candidates = [data.get(name)]
            for nested in ["room", "session"]:
                if isinstance(data.get(nested), dict):
                    candidates.append(data[nested].get(name))
            actual = [value for value in candidates if value is not None]
            if actual and any(value != expected for value in actual):
                return False
        return True

    def choose(self, operation_id, scenario="success", parameters=None):
        operation = self.store.operation(operation_id)[2]
        parameters = parameters or {}
        if scenario == "token-expired":
            status, body = 401, load(self.store.contracts / "fixtures/http/token-expired.json")
        elif scenario == "forbidden":
            status, body = self.common_error(403)
        elif (operation_id, scenario) in self.scenarios:
            selected = self.scenarios[(operation_id, scenario)]
            path = (self.store.root / selected["fixture"]).resolve()
            if not path.is_relative_to((self.store.contracts / "fixtures").resolve()):
                raise ContractError("Mock scenario must use a registered common fixture")
            status, body = selected["http_status"], load(path)
        elif scenario == "success":
            # These responses require real services. Never issue redacted/fake auth/meeting tickets.
            if operation_id in {"createRealtimeTicket", "getMeetingCredentials"}:
                status, body = self.common_error(503)
            else:
                status = next(int(s) for s in operation["responses"] if s.startswith("2"))
                if status == 204:
                    body = None
                else:
                    response, _ = self.store.response(operation_id, status)
                    examples = response["content"]["application/json"]["examples"]
                    body = copy.deepcopy(next(iter(examples.values()))["value"])
        else:
            status, body = self.common_error(400)
        if status < 400 and not self.fixture_scope_matches(parameters, body):
            status, body = self.common_error(404)
        issues = self.store.check_response(operation_id, status, body)
        if issues:
            raise ContractError("Refusing to serve response that violates schema: " + "; ".join(issues[:3]))
        return status, body


def make_handler(store, planner, allowed_origins, default_delay_ms):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format, *args):
            # Do not log request URLs, headers, bearer/ticket values or bodies.
            return

        def send_fixture(self, status, body):
            data = b"" if body is None else json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()
            self.send_response(status)
            self.send_header("X-Data-Mode", "mock")
            self.send_header("X-Mock-Server", "CT04-fixtures-only")
            self.send_header("X-Contract-Version", store.version["contract_version"])
            self.send_header("X-Contract-Status", store.version["status"])
            if isinstance(body, dict) and body.get("request_id"):
                self.send_header("X-Request-Id", body["request_id"])
            if status == 401:
                self.send_header("WWW-Authenticate", 'Bearer error="invalid_token"')
            if status in {429, 503}:
                self.send_header("Retry-After", "2")
            origin = self.headers.get("Origin")
            if origin in allowed_origins:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
                self.send_header("Access-Control-Expose-Headers", "X-Data-Mode,X-Mock-Server,X-Contract-Version,X-Contract-Status,X-Request-Id,Retry-After")
            if body is not None:
                self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass  # Expected when a mock client tests network timeout/cancellation.

        def do_OPTIONS(self):
            origin = self.headers.get("Origin")
            requested = self.headers.get("Access-Control-Request-Method", "GET")
            known = store.match(requested, urlsplit(self.path).path)
            if origin not in allowed_origins or not known:
                self.send_fixture(*planner.common_error(403))
                return
            self.send_response(204)
            self.send_header("X-Data-Mode", "mock")
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", requested)
            self.send_header("Access-Control-Allow-Headers", "Authorization,Content-Type,Idempotency-Key,X-Request-Id,X-Mock-Scenario,X-Mock-Delay-Ms")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def dispatch(self):
            matched = store.match(self.command, urlsplit(self.path).path)
            if not matched:
                self.send_fixture(*planner.common_error(404))
                return
            operation, path_params = matched
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 0 or length > 65536 or self.headers.get("Transfer-Encoding"):
                    self.send_fixture(*planner.common_error(400))
                    self.close_connection = True
                    return
                content = self.rfile.read(length)
                try:
                    body = decode_json(content) if content else None
                except ContractError as exc:
                    raise ValueError("Invalid JSON") from exc
                query_values = parse_qs(urlsplit(self.path).query, keep_blank_values=True)
                if any(len(values) != 1 for values in query_values.values()):
                    raise ValueError("Repeated query parameter")
                query = {key: values[0] for key, values in query_values.items()}
                headers = {key.lower(): value for key, value in self.headers.items()}
                if content and self.headers.get_content_type() != "application/json":
                    self.send_fixture(*planner.common_error(400))
                    return
                if planner.check_request(operation, path_params, query, headers, body):
                    self.send_fixture(*planner.common_error(400))
                    return
                delay = int(self.headers.get("X-Mock-Delay-Ms", str(default_delay_ms)))
                if not 0 <= delay <= 2000:
                    self.send_fixture(*planner.common_error(400))
                    return
                scenario = self.headers.get("X-Mock-Scenario", "success")
                status, response = planner.choose(operation["operationId"], scenario, path_params)
                if delay:
                    time.sleep(delay / 1000)
                self.send_fixture(status, response)
            except ContractError:
                # Tool failure is explicit; do not replace it with a synthetic 200 success.
                self.send_fixture(*planner.common_error(500))
            except (ValueError, TypeError, KeyError):
                self.send_fixture(*planner.common_error(400))

        do_GET = dispatch
        do_POST = dispatch
        do_PATCH = dispatch
        do_DELETE = dispatch
        do_PUT = dispatch

    return Handler


def serve(store, host, port, allowed_origins, delay_ms):
    store.verify_bundle()
    store.require_approval()  # Must happen BEFORE creating any listening socket.
    supplement = store.contracts / "fixtures/ct04-draft/manifest.json"
    if supplement.exists() and load(supplement).get("status") != "APPROVED":
        raise PendingApproval("CT-04 supplemental scenarios are DRAFT; do not serve unapproved fixtures")
    planner = FixturePlanner(store)
    handler = make_handler(store, planner, set(allowed_origins), delay_ms)
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    print(f"MOCK ONLY — fixture data, no real auth/OCR/storage. {host}:{server.server_port}; {store.version['contract_version']}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Approved-contract fixture mock; NO --allow-draft or real fallback.")
    parser.add_argument("--mode", choices=["mock"], required=True)
    parser.add_argument("--host", choices=["127.0.0.1", "localhost"], default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--allow-origin", action="append", default=["http://localhost:8443"])
    parser.add_argument("--delay-ms", type=int, default=0)
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535 or not 0 <= args.delay_ms <= 2000:
        parser.error("Invalid port or delay; maximum delay is 2000ms")
    try:
        serve(ContractStore(), args.host, args.port, args.allow_origin, args.delay_ms)
        return 0
    except PendingApproval as exc:
        print(f"PENDING_APPROVAL: mock NOT started; {exc}", file=sys.stderr)
        return 2
    except (FileNotFoundError, ModuleNotFoundError) as exc:
        print(f"SETUP_REQUIRED: {exc}", file=sys.stderr)
        return 3
    except (ContractError, OSError) as exc:
        print(f"MOCK_FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
