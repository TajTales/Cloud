"""Read-only contract inspection. No app routes, credentials or provider imports."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin, urlparse

import yaml
from jsonschema import Draft7Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

REPO = Path(__file__).resolve().parents[2]
LEGACY_MEMBERS = {"Nguyễn Tài Đức", "Nguyễn Hoàng Bảo", "Trần Nguyên Bảo Anh"}
ANNOTATIONS = {"description", "title", "examples", "example", "$comment", "x-owner"}


class ContractError(ValueError):
    pass


class PendingApproval(ContractError):
    pass


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"Duplicate key: {key}")
        result[key] = value
    return result


class UniqueLoader(yaml.SafeLoader):
    pass


def yaml_mapping(loader, node):
    loader.flatten_mapping(node)
    return unique_pairs((loader.construct_object(k), loader.construct_object(v)) for k, v in node.value)


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, yaml_mapping)


def decode_json(value):
    return json.loads(
        value, object_pairs_hook=unique_pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ContractError(f"Non-finite JSON: {value}")),
    )


def load(path):
    path = Path(path)
    if path.suffix in {".yaml", ".yml"}:
        return yaml.load(path.read_text(), Loader=UniqueLoader)
    return decode_json(path.read_text())


def approval_policy(root):
    path = Path(root) / "contracts/approval-policy.json"
    if not path.exists():
        return {"policy_id": "legacy-three-members", "required_approvers": sorted(LEGACY_MEMBERS),
                "sha256": None, "path": None}
    value = load(path)
    schema = {"type": "object", "required": ["policy_version", "policy_id", "required_approvers", "require_evidence", "authorization", "contract_wire_changes"],
              "properties": {"policy_version": {"const": 1}, "policy_id": {"type": "string", "minLength": 1},
                             "required_approvers": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
                             "require_evidence": {"const": True}, "authorization": {"type": "string", "minLength": 1},
                             "contract_wire_changes": {"const": False}}, "additionalProperties": False}
    if list(Draft7Validator(schema).iter_errors(value)):
        raise ContractError("Invalid approval policy; evidence and an explicit approver set are required")
    return {"policy_id": value["policy_id"], "required_approvers": value["required_approvers"],
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "path": "contracts/approval-policy.json"}


def missing_approvals(records, policy):
    names = {item.get("name") for item in records if isinstance(item, dict)
             and isinstance(item.get("name"), str) and isinstance(item.get("evidence"), str) and item["evidence"].strip()}
    return sorted(set(policy["required_approvers"]) - names)


def semantic_issues(value):
    """Arithmetic/code point/wire-budget checks; not server authorization tests."""
    issues = []

    def visit(item):
        if isinstance(item, float) and not math.isfinite(item):
            issues.append("non-finite-number")
        if isinstance(item, dict):
            if "offset_unit" in item and "tokens" in item:
                text, cursor = item["text"], 0
                for token in item["tokens"]:
                    start, end = token["start"], token["end"]
                    if not (0 <= start < end <= len(text)) or start != cursor or text[start:end] != token["surface"]:
                        issues.append("unicode-code-point-offset-or-coverage")
                    cursor = end
                if cursor != len(text):
                    issues.append("incomplete-token-coverage")
            if "ocr" in item and "image" in item:
                if item["image"]["width_px"] * item["image"]["height_px"] > 4000000:
                    issues.append("public-image-pixel-budget")
                for paragraph in item["ocr"].get("paragraphs", []):
                    for word in [paragraph] + paragraph.get("words", []):
                        box = word["box"]
                        cx, cy, width, height = (box[k] for k in ["center_x", "center_y", "width", "height"])
                        if not (0 <= cx - width / 2 <= cx + width / 2 <= 1 and 0 <= cy - height / 2 <= cy + height / 2 <= 1):
                            issues.append("public-box-crosses-image")
            if "schema_version" in item:
                size = len(json.dumps(item, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode())
                if "client_message_id" in item and size >= 1500:
                    issues.append("chime-utf8-byte-budget")
                elif "client_message_id" not in item and size > 24576:
                    issues.append("ws-utf8-byte-budget")
                if item.get("type") == "ocr.result_available":
                    if item["seq"] != item["data"]["seq"] or item["session_id"] != item["data"]["session_id"]:
                        issues.append("event-result-reference")
                if item.get("type") == "session.source_changed" and item["session_id"] != item["data"]["source"]["session_id"]:
                    issues.append("event-source-scope")
                if item.get("type") == "session.subscribed":
                    snapshot = item["data"]["session"]
                    if snapshot["session_id"] != item["session_id"] or snapshot["latest_seq"] != item["data"]["latest_seq"]:
                        issues.append("snapshot-watermark")
            if "capture_limits" in item and "current_source_id" in item:
                source = item["current_source"]
                if (source is None) != (item["current_source_id"] is None):
                    issues.append("session-source-nullability")
                elif source and (source["source_id"] != item["current_source_id"] or source["session_id"] != item["session_id"]):
                    issues.append("session-source-identity")
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    try:
        visit(value)
    except (KeyError, TypeError, ValueError) as exc:
        issues.append(f"malformed-semantic-input:{type(exc).__name__}")
    return issues


class ContractStore:
    def __init__(self, root=REPO):
        self.root = Path(root).resolve()
        if not {"date-time", "uri", "email", "uuid"} <= FormatChecker().checkers.keys():
            raise ModuleNotFoundError("required JSON Schema format validators; install tools/contract-testing/requirements.txt")
        self.contracts = self.root / "contracts"
        self.version = load(self.contracts / "contract-version.json")
        self.approval_policy = approval_policy(self.root)
        self.openapi = load(self.contracts / "openapi.yaml")
        self.asyncapi = load(self.contracts / "asyncapi.yaml")
        paths = sorted((self.contracts / "schemas").glob("*.json")) + [
            self.contracts / "openapi.yaml", self.contracts / "asyncapi.yaml",
        ]
        self.documents = {path.resolve().as_uri(): load(path) for path in paths}
        self.registry = Registry().with_resources(
            (uri, Resource.from_contents(document, default_specification=DRAFT7))
            for uri, document in self.documents.items()
        )

    def verify_bundle(self):
        lines = []
        for filename, digest in sorted(self.version["files"].items()):
            path = (self.root / filename).resolve()
            if not path.is_relative_to(self.root) or not path.is_file():
                raise ContractError(f"Missing/outside bundle file: {filename}")
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ContractError(f"Bundle file changed: {filename}; do not edit schema to make tests pass")
            lines.append(f"{filename} {digest}\n")
        if hashlib.sha256("".join(lines).encode()).hexdigest() != self.version["bundle_sha256"]:
            raise ContractError("Bundle hash mismatch")
        return len(lines)

    def resolve(self, node, base=None):
        base = base or (self.contracts / "openapi.yaml").as_uri()
        seen = set()
        while isinstance(node, dict) and "$ref" in node:
            uri = urljoin(base, node["$ref"])
            if uri in seen:
                raise ContractError(f"Reference cycle: {uri}")
            seen.add(uri)
            document_uri, fragment = urldefrag(uri)
            if document_uri not in self.documents:
                raise ContractError(f"Reference not in local schema registry: {uri}")
            node = self.documents[document_uri]
            for part in fragment.strip("/").split("/") if fragment else []:
                node = node[unquote(part).replace("~1", "/").replace("~0", "~")]
            base = document_uri
        return node, base

    def schema_errors(self, value, schema, base=None, semantic=True):
        base = base or (self.contracts / "openapi.yaml").as_uri()
        if "$ref" in schema:
            schema = {"$ref": urljoin(base, schema["$ref"])}
        errors = [error.message for error in Draft7Validator(
            schema, registry=self.registry, format_checker=FormatChecker(),
        ).iter_errors(value)]
        if semantic and not errors:
            errors.extend(semantic_issues(value))
        return errors

    def all_references(self):
        count = 0

        def visit(node, base):
            nonlocal count
            if isinstance(node, dict):
                if "$ref" in node:
                    self.resolve(node, base)
                    count += 1
                for child in node.values():
                    visit(child, base)
            elif isinstance(node, list):
                for child in node:
                    visit(child, base)

        for uri, document in self.documents.items():
            visit(document, uri)
        return count

    def operations(self):
        for path, item in self.openapi["paths"].items():
            for method, operation in item.items():
                if method in {"get", "post", "put", "patch", "delete", "head", "options"}:
                    yield method.upper(), path, operation

    def operation(self, operation_id):
        for method, path, operation in self.operations():
            if operation["operationId"] == operation_id:
                return method, path, operation
        raise ContractError(f"Unknown operationId: {operation_id}")

    def match(self, method, url_path):
        for current_method, path, operation in self.operations():
            pattern = re.escape("/api/v1" + path)
            names = re.findall(r"\{([^}]+)\}", path)
            for name in names:
                pattern = pattern.replace(re.escape("{" + name + "}"), f"(?P<{name}>[^/]+)")
            matched = re.fullmatch(pattern, url_path)
            if matched and current_method == method:
                return operation, {k: unquote(v) for k, v in matched.groupdict().items()}
        return None

    def response(self, operation_id, status):
        operation = self.operation(operation_id)[2]
        status = str(status)
        if status not in operation["responses"]:
            raise ContractError(f"Status {status} is not declared by {operation_id}")
        return self.resolve(operation["responses"][status])

    def check_response(self, operation_id, status, body):
        response, base = self.response(operation_id, status)
        if int(status) == 204:
            return [] if body is None else ["204 must not have a body"]
        content = response.get("content", {}).get("application/json")
        if not content:
            return ["No declared JSON response schema"]
        return self.schema_errors(body, content["schema"], base)

    def approval_reasons(self):
        reasons = []
        if self.version.get("status") != "APPROVED":
            reasons.append(f"contract_status={self.version.get('status')}; approved contract required")
        missing = missing_approvals(self.version.get("approved_by", []), self.approval_policy)
        if missing:
            reasons.append("required approvals with evidence are missing: " + ", ".join(missing))
        policy_path = self.approval_policy["path"]
        if policy_path and policy_path not in self.version["files"]:
            reasons.append("current approval policy must be pinned in a new contract release before approval")
        if not re.fullmatch(r"[0-9a-f]{40}", self.version.get("contract_commit_sha") or ""):
            reasons.append("contract_commit_sha is not pinned")
        if self.openapi.get("x-contract-status") != "APPROVED" or self.asyncapi.get("x-contract-status") != "APPROVED":
            reasons.append("HTTP/WS document status is not approved")
        if any(op.get("x-contract-status") != "APPROVED" for _, _, op in self.operations()):
            reasons.append("one or more application operations remain draft")
        for uri, document in self.documents.items():
            if "x-contract-status" in document and document["x-contract-status"] != "APPROVED":
                reasons.append(f"document remains draft: {Path(urlparse(uri).path).name}")
        for path in [self.contracts / "fixtures/manifest.json", self.contracts / "fixtures/ct04-draft/manifest.json"]:
            if not path.exists():
                continue
            manifest = load(path)
            if manifest.get("status") != "APPROVED":
                reasons.append(f"fixture manifest remains draft: {path.relative_to(self.contracts)}")
            files = [path] + [(path.parent / item["file"]).resolve() for item in manifest.get("files", [])]
            if any(str(item.relative_to(self.root)) not in self.version["files"] for item in files):
                reasons.append(f"fixture set is not included in pinned bundle: {path.relative_to(self.contracts)}")
        return reasons

    def require_approval(self):
        reasons = self.approval_reasons()
        if reasons:
            raise PendingApproval("; ".join(reasons))

    def fixture_sets(self):
        paths = [self.contracts / "fixtures/manifest.json"]
        supplement = self.contracts / "fixtures/ct04-draft/manifest.json"
        if supplement.exists():
            paths.append(supplement)
        for path in paths:
            manifest = load(path)
            if manifest.get("source_bundle_sha256", self.version["bundle_sha256"]) != self.version["bundle_sha256"]:
                raise ContractError(f"Supplemental fixture source mismatch: {path}")
            for record in manifest["files"]:
                fixture_path = (path.parent / record["file"]).resolve()
                if not fixture_path.is_relative_to(path.parent.resolve()):
                    raise ContractError("Fixture path escapes its manifest directory")
                yield path, manifest, record, fixture_path


def compatibility_review(before, after, path="root"):
    """Conservative review detector, NOT a proof of semantic compatibility."""
    changes = []
    if type(before) is not type(after):
        return [f"{path}: type/shape changed"]
    if isinstance(before, dict):
        for key in sorted(before.keys() | after.keys()):
            if key in ANNOTATIONS:
                continue
            child = f"{path}/{key}"
            if key not in after:
                changes.append(f"{child}: removed; consumer review required")
            elif key not in before:
                changes.append(f"{child}: added constraint/field; direction-specific review required")
            else:
                changes.extend(compatibility_review(before[key], after[key], child))
    elif isinstance(before, list):
        if before != after:
            changes.append(f"{path}: enum/required/order/security array changed; review required")
    elif before != after:
        changes.append(f"{path}: value/constraint changed; review required")
    return changes


def compare_contract_directories(previous, current):
    previous, current = Path(previous), Path(current)
    names = {"openapi.yaml", "asyncapi.yaml"}
    for directory in [previous, current]:
        names.update(str(path.relative_to(directory)) for path in (directory / "schemas").glob("*.json"))
    changes = []
    for name in sorted(names):
        old, new = previous / name, current / name
        if not new.exists():
            changes.append(f"{name}: schema/document removed; consumer review required")
        elif not old.exists():
            changes.append(f"{name}: prior file unavailable; manual review required")
        else:
            changes.extend(compatibility_review(load(old), load(new), name))
    return changes
