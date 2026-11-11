#!/usr/bin/env python3
"""One entrypoint for structural review, approved conformance and captured messages."""

from __future__ import annotations

import argparse
import ast
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

try:
    from contracts_core import (
        ContractError, ContractStore, Draft7Validator, REPO, compare_contract_directories,
        load, semantic_issues,
    )
except ModuleNotFoundError as exc:
    print(f"SETUP_REQUIRED: {exc.name}; install isolated tools/contract-testing/requirements.txt", file=sys.stderr)
    raise SystemExit(3)


def example_check(store):
    counts = {"request_examples": 0, "parameter_examples": 0, "success_examples": 0, "error_examples": 0, "ws_examples": 0}
    errors, operation_ids = [], set()
    base = (store.contracts / "openapi.yaml").as_uri()
    for method, path, operation in store.operations():
        identifier = operation["operationId"]
        if identifier in operation_ids:
            errors.append(f"duplicate operationId: {identifier}")
        operation_ids.add(identifier)
        parameters = [store.resolve(p)[0] for p in operation.get("parameters", [])]
        for reference in operation.get("parameters", []):
            parameter, parameter_base = store.resolve(reference, base)
            values = [parameter["example"]] if "example" in parameter else []
            values.extend(store.resolve(item, parameter_base)[0]["value"] for item in parameter.get("examples", {}).values())
            for value in values:
                errors.extend(f"{identifier}/parameter/{parameter['name']}: {issue}" for issue in store.schema_errors(value, parameter["schema"], parameter_base))
                counts["parameter_examples"] += 1
        import re
        if {p["name"] for p in parameters if p["in"] == "path"} != set(re.findall(r"\{([^}]+)\}", path)):
            errors.append(f"path parameter mismatch: {identifier}")
        if not operation.get("security", store.openapi.get("security")):
            errors.append(f"missing auth declaration: {identifier}")
        body = operation.get("requestBody", {})
        for content in body.get("content", {}).values():
            for example in content.get("examples", {}).values():
                issues = store.schema_errors(example["value"], content["schema"], base)
                errors.extend(f"{identifier}/request: {x}" for x in issues)
                counts["request_examples"] += 1
        has_success, has_failure = False, False
        for status, response in operation["responses"].items():
            response, response_base = store.resolve(response, base)
            if status == "204":
                if "content" in response:
                    errors.append(f"{identifier}: 204 declares content")
                has_success = True
                continue
            for header in response.get("headers", {}).values():
                if "example" in header:
                    errors.extend(store.schema_errors(header["example"], header["schema"], response_base))
            for content in response.get("content", {}).values():
                for example in content.get("examples", {}).values():
                    value = example["value"]
                    issues = store.schema_errors(value, content["schema"], response_base)
                    errors.extend(f"{identifier}/{status}: {x}" for x in issues)
                    if int(status) >= 400:
                        envelope = {"$ref": "./schemas/application.schema.json#/definitions/ErrorResponse"}
                        errors.extend(store.schema_errors(value, envelope, base))
                        counts["error_examples"] += 1
                        has_failure = True
                    else:
                        counts["success_examples"] += 1
                        has_success = True
        if not has_success or not has_failure:
            errors.append(f"{identifier}: missing success/failure example")
    for message in store.asyncapi["components"]["messages"].values():
        payload = message["payload"]
        schema = payload.get("schema", payload)
        for example in message.get("examples", []):
            errors.extend(store.schema_errors(example["payload"], schema, (store.contracts / "asyncapi.yaml").as_uri()))
            counts["ws_examples"] += 1
    counts["operations"] = len(operation_ids)
    return counts, errors


def fixture_check(store):
    counts = {"positive": 0, "negative_schema": 0, "negative_semantic": 0}
    errors = []
    for manifest_path, manifest, record, path in store.fixture_sets():
        value = load(path)
        schema = {"$ref": record["schema"]}
        schema_errors = store.schema_errors(value, schema, manifest_path.as_uri(), semantic=False)
        semantic_errors = semantic_issues(value) if not schema_errors else []
        if record["expect_valid"]:
            counts["positive"] += 1
            errors.extend(f"{path.name}: {x}" for x in schema_errors + semantic_errors)
        elif record.get("validation_scope") == "semantic":
            counts["negative_semantic"] += 1
            if schema_errors or not semantic_errors:
                errors.append(f"{path.name}: expected schema-valid input rejected by semantic check")
        else:
            counts["negative_schema"] += 1
            if not schema_errors:
                errors.append(f"{path.name}: expected schema rejection")
        if record.get("operation_id") and record.get("http_status") and record["expect_valid"]:
            errors.extend(store.check_response(record["operation_id"], record["http_status"], value))
    return counts, errors


def correlation_check(store):
    base = store.contracts / "fixtures"
    read = lambda filename: load(base / filename)
    errors = []
    new = read("http/duplicate-job-new.json")["data"]
    retry = read("http/duplicate-job-retry.json")["data"]
    done = read("http/job-succeeded.json")["data"]
    result = read("http/getOcrResult-200.json")["data"]
    event = read("ws/ocr-result_available.json")
    for key in ["job_id", "session_id", "source_id", "frame_id"]:
        if len({new[key], retry[key], done[key], result[key], event["data"][key]}) != 1:
            errors.append(f"poll/WS/result identity mismatch: {key}")
    if done["result_id"] != result["result_id"] or event["data"]["result_id"] != result["result_id"]:
        errors.append("poll/WS result_id mismatch")
    for key in ["frame_index", "media_time_ms", "seq", "created_at"]:
        if event["data"][key] != result[key]:
            errors.append(f"WS/detail result metadata mismatch: {key}")
    if event["seq"] != result["seq"] or event["session_id"] != result["session_id"]:
        errors.append("WS envelope/detail scope mismatch")
    if read("ws/duplicate-result-event.json") != event:
        errors.append("duplicate event fixture differs from original")
    if read("http/current-source-after-switch.json")["data"]["current_source_id"] == result["source_id"]:
        errors.append("old-source fixture is not actually old")
    if read("ocr/success.json") != result["ocr"]:
        errors.append("raw-to-public mapping altered provider content")
    if read("ocr/no-text.json") != read("http/ocr-no-text.json")["data"]["ocr"]:
        errors.append("no-text mapping changed")
    supplement = base / "ct04-draft/manifest.json"
    coverage_count = 0
    if supplement.exists():
        for case in load(supplement).get("coverage", []):
            coverage_count += 1
            for filename in case["fixtures"]:
                path = (store.root / filename).resolve()
                if not path.is_relative_to(base.resolve()) or not path.is_file():
                    errors.append(f"missing coverage fixture: {filename}")
    return {"reference_groups": 7, "scenario_coverage": coverage_count}, errors


def raw_shape_check(store):
    path = store.root / "meikipop-ocr-server/src/meikipop_ocr_server/ocr/interface.py"
    if not path.exists():
        return {"status": "NOT_ACCESSIBLE", "detail": "Provide captured raw response; no cross-repo PASS."}
    tree = ast.parse(path.read_text())
    schema = load(store.contracts / "schemas/ocr-provider.schema.json")
    for name in ["BoundingBox", "Word", "Paragraph"]:
        node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
        fields = {n.target.id for n in node.body if isinstance(n, ast.AnnAssign)}
        if fields != set(schema["definitions"][name]["properties"]):
            raise ContractError(f"Raw dataclass fields changed: {name}")
    return {"status": "EVIDENCED_SHAPE_ONLY", "classes": 3, "real_provider_tested": False}


def run_lint(store):
    report = {"errors": []}
    report["bundle_files"] = store.verify_bundle()
    report["local_references"] = store.all_references()
    schema_paths = sorted((store.contracts / "schemas").glob("*.json"))
    for path in schema_paths:
        Draft7Validator.check_schema(load(path))
    report["json_schemas"] = len(schema_paths)
    result = subprocess.run(
        [sys.executable, "-m", "openapi_spec_validator", str(store.contracts / "openapi.yaml")],
        capture_output=True, text=True,
    )
    if result.returncode:
        raise ContractError("OpenAPI validation failed: " + (result.stderr or result.stdout)[-1500:])
    script = Path(__file__).with_name("validate-asyncapi.cjs")
    parsed = subprocess.run(["node", str(script), str(store.contracts / "asyncapi.yaml")], capture_output=True, text=True)
    if parsed.returncode == 3:
        raise ModuleNotFoundError(parsed.stderr.strip())
    if parsed.returncode:
        raise ContractError("AsyncAPI validation failed: " + (parsed.stderr or parsed.stdout)[-1500:])
    report["asyncapi"] = json.loads(parsed.stdout)
    for name, action in [("fixtures", fixture_check), ("examples", example_check), ("correlations", correlation_check)]:
        report[name], issues = action(store)
        report["errors"].extend(issues)
    report["raw_shape"] = raw_shape_check(store)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Contract checks. DRAFT lint is never approved producer/consumer conformance.")
    parser.add_argument("--lint-draft", action="store_true", help="Structural review only; permits draft lint, not mock startup/conformance.")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--baseline-dir", type=Path, help="Prior contracts/ directory; conservative semantic review detector.")
    parser.add_argument("--message", type=Path, help="Captured JSON message/response to validate, no network calls.")
    parser.add_argument("--schema", help="contracts/-relative JSON schema reference for --message")
    parser.add_argument("--operation", help="Declared operationId for a captured HTTP response")
    parser.add_argument("--http-status", type=int)
    args = parser.parse_args(argv)
    report = {"tool": "CT-04", "conformance": "PENDING", "runtime_integration": "NOT_RUN", "errors": []}
    code = 1
    try:
        store = ContractStore()
        report.update(contract_version=store.version["contract_version"], contract_status=store.version["status"],
                      bundle_sha256=store.version["bundle_sha256"], contract_commit_sha=store.version.get("contract_commit_sha"),
                      approval_pending=store.approval_reasons(), mode="DRAFT_LINT" if args.lint_draft else "APPROVED_CONTRACT_REQUIRED")
        store.verify_bundle()
        if args.message:
            value = load(args.message)
            if args.operation and args.http_status:
                errors = store.check_response(args.operation, args.http_status, value)
            elif args.schema:
                errors = store.schema_errors(value, {"$ref": args.schema}, (store.contracts / "index.json").as_uri())
            else:
                raise ContractError("--message requires --schema or --operation plus --http-status")
            report["errors"].extend(errors)
        else:
            report["lint"] = run_lint(store)
            report["errors"].extend(report["lint"]["errors"])
        if args.baseline_dir:
            changes = compare_contract_directories(args.baseline_dir, store.contracts)
            report["compatibility_review_required"] = changes
            if changes:
                report["errors"].append("Potential semantic/breaking changes need owner/consumer review")
        if report["errors"]:
            code, report["status"] = 1, "FAIL"
        elif report["approval_pending"] and not args.lint_draft:
            code, report["status"] = 2, "PENDING_APPROVAL"
        else:
            code, report["status"] = 0, "STRUCTURE_VALID" if args.lint_draft else "PASS_APPROVED_CONTRACT"
            if not report["approval_pending"] and not args.lint_draft:
                report["conformance"] = "SCHEMA_ONLY; implementation not tested"
        report["tools"] = {name: importlib.metadata.version(name) for name in ["jsonschema", "PyYAML", "openapi-spec-validator", "referencing"]}
    except (ModuleNotFoundError, FileNotFoundError) as exc:
        code, report["status"] = 3, "SETUP_REQUIRED"
        report["errors"].append(str(exc))
    except Exception as exc:
        code, report["status"] = 1, "FAIL"
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    report["exit_code"] = code
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
