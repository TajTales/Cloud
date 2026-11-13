"""Runtime schema adapter. Reads the original bundle; never generates DTO schemas."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin

from jsonschema import Draft7Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7
import yaml


class ContractFailure(ValueError):
    pass


def strict_json(data):
    def unique(pairs):
        output = {}
        for key, value in pairs:
            if key in output:
                raise ValueError("Duplicate JSON key")
            output[key] = value
        return output

    def constant(_):
        raise ValueError("Non-finite JSON number")

    def number(text):
        result = float(text)
        if not math.isfinite(result):
            raise ValueError("Non-finite JSON number")
        return result

    return json.loads(data, object_pairs_hook=unique, parse_constant=constant, parse_float=number)


@dataclass(frozen=True)
class Operation:
    method: str
    path: str
    identifier: str
    definition: dict


class ContractRegistry:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.base = (self.directory / "openapi.yaml").as_uri()
        self.version = strict_json((self.directory / "contract-version.json").read_text())
        lines = []
        for name, digest in sorted(self.version["files"].items()):
            path = (self.directory.parent / name).resolve()
            if not path.is_relative_to(self.directory.parent) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ContractFailure("Contract bundle is missing or changed; review/version the package before startup")
            lines.append(f"{name} {digest}\n")
        if hashlib.sha256("".join(lines).encode()).hexdigest() != self.version["bundle_sha256"]:
            raise ContractFailure("Contract bundle digest is invalid")
        paths = sorted((self.directory / "schemas").glob("*.json")) + [self.directory / "openapi.yaml"]
        self.documents = {path.as_uri(): yaml.safe_load(path.read_text()) if path.suffix == ".yaml" else strict_json(path.read_text()) for path in paths}
        self.registry = Registry().with_resources(
            (uri, Resource.from_contents(document, default_specification=DRAFT7)) for uri, document in self.documents.items()
        )
        self.format_checker = FormatChecker()
        if not {"date-time", "uri", "email", "uuid"} <= self.format_checker.checkers.keys():
            raise ContractFailure("Required format validators are missing; install the complete requirements.lock")
        self.openapi = self.documents[self.base]
        self.operations = {}
        for path, item in self.openapi["paths"].items():
            for method, definition in item.items():
                if method in {"get", "post", "patch", "put", "delete", "head", "options"}:
                    operation = Operation(method.upper(), "/api/v1" + path, definition["operationId"], definition)
                    if operation.identifier in self.operations:
                        raise ContractFailure("Duplicate operationId")
                    self.operations[operation.identifier] = operation

    def resolve(self, value, base=None):
        base, seen = base or self.base, set()
        while isinstance(value, dict) and "$ref" in value:
            uri, fragment = urldefrag(urljoin(base, value["$ref"]))
            if (uri, fragment) in seen or uri not in self.documents:
                raise ContractFailure("Only local, non-cyclic contract references are supported")
            seen.add((uri, fragment))
            value = self.documents[uri]
            for part in fragment.strip("/").split("/") if fragment else []:
                value = value[unquote(part).replace("~1", "/").replace("~0", "~")]
            base = uri
        return value, base

    def issues(self, value, schema, base=None):
        schema = dict(schema)
        if "$ref" in schema:
            schema["$ref"] = urljoin(base or self.base, schema["$ref"])
        validator = Draft7Validator(schema, registry=self.registry, format_checker=self.format_checker)
        # Do not return validator messages: they can echo submitted passwords/PII.
        return [list(error.absolute_path) for error in validator.iter_errors(value)]

    def response_issues(self, operation, status, body):
        declared = operation.definition["responses"].get(str(status))
        if declared is None:
            raise ContractFailure("Response status is not declared by this operation")
        if status == 204:
            return [] if body is None else [["body"]]
        response, base = self.resolve(declared)
        schema = response["content"]["application/json"]["schema"]
        return self.issues(body, schema, base)

    def error_issues(self, body):
        return self.issues(body, {"$ref": "./schemas/application.schema.json#/definitions/ErrorResponse"})

    def request_issues(self, operation, path_values, query, headers, body):
        issues = []
        for reference in operation.definition.get("parameters", []):
            parameter, base = self.resolve(reference)
            location, name = parameter["in"], parameter["name"]
            value = {"path": path_values, "query": query, "header": headers}.get(location, {}).get(name.lower() if location == "header" else name)
            if value is None:
                if parameter.get("required"):
                    issues.append([location, name])
                continue
            schema, _ = self.resolve(parameter["schema"], base)
            if schema.get("type") == "integer":
                try:
                    if str(int(value)) != value:
                        raise ValueError()
                    value = int(value)
                except (ValueError, TypeError):
                    issues.append([location, name])
                    continue
            issues.extend([location, name, *path] for path in self.issues(value, parameter["schema"], base))
        request = operation.definition.get("requestBody")
        if request and body is not None:
            issues.extend(["body", *path] for path in self.issues(body, request["content"]["application/json"]["schema"]))
        elif (request and request.get("required")) or body is not None:
            issues.append(["body"])
        return issues
