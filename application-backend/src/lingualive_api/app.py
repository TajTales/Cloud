from __future__ import annotations

from dataclasses import dataclass
import asyncio
import json
import logging
from time import perf_counter
from uuid import uuid4

from aiohttp import web

from .auth import Identity, UnconfiguredAuthenticator
from .config import Settings
from .contracts import ContractFailure, ContractRegistry, strict_json
from .errors import ApiError, unavailable

LOGGER = logging.getLogger("lingualive.api")
STATE = web.AppKey("foundation_state", dict)
REQUEST_ID = web.RequestKey("request_id", str)
IDENTITY = web.RequestKey("identity", Identity)
ALLOWED_HEADERS = {"authorization", "content-type", "idempotency-key", "x-request-id"}


@dataclass(frozen=True)
class Result:
    data: object = None
    status: int = 200


def json_response(body, status=200):
    if status == 204:
        if body is not None:
            raise ContractFailure("204 response must not have a body")
        return web.Response(status=204)
    return web.Response(status=status, text=json.dumps(body, ensure_ascii=False, allow_nan=False, separators=(",", ":")), content_type="application/json")


@web.middleware
async def foundation_middleware(request, handler):
    start = perf_counter()
    state = request.app[STATE]
    supplied = request.headers.getall("X-Request-Id", [])
    valid_id = len(supplied) == 1 and 1 <= len(supplied[0]) <= 128 and not any(ord(c) < 32 or ord(c) == 127 for c in supplied[0])
    request[REQUEST_ID] = supplied[0] if valid_id else str(uuid4())
    origin = request.headers.get("Origin")
    try:
        if supplied and not valid_id:
            raise ApiError(400, "VALIDATION_ERROR", "Invalid X-Request-Id header.")
        if origin is not None and origin not in state["settings"].allowed_origins:
            raise ApiError(403, "FORBIDDEN", "Origin is not allowed.")
        response = await handler(request)
    except ApiError as exc:
        try:
            body = exc.body(request[REQUEST_ID])
            if state["contracts"].error_issues(body):
                raise ContractFailure("Invalid application error envelope")
            operation = state["contracts"].operations.get(request.match_info.route.name)
            if operation and state["contracts"].response_issues(operation, exc.status, body):
                raise ContractFailure("Error response violates operation schema")
            response = json_response(body, exc.status)
            if exc.status == 401:
                response.headers["WWW-Authenticate"] = "Bearer"
            if exc.retryable and exc.status in {429, 503}:
                response.headers["Retry-After"] = "2"
        except Exception as internal:
            LOGGER.error(json.dumps({"event": "invalid_error_response", "request_id": request[REQUEST_ID], "exception_type": type(internal).__name__}))
            response = json_response(ApiError(500, "INTERNAL_ERROR", "An internal error occurred.").body(request[REQUEST_ID]), 500)
    except web.HTTPException as exc:
        status = exc.status
        operation = state["contracts"].operations.get(request.match_info.route.name)
        if operation and str(status) not in operation.definition["responses"]:
            status = 400
        code = "RESOURCE_NOT_FOUND" if status == 404 else "VALIDATION_ERROR"
        body = ApiError(status, code, "Route not found." if status == 404 else "Request could not be accepted.").body(request[REQUEST_ID])
        response = json_response(body, status)
        if exc.status == 405:
            response.headers["Allow"] = exc.headers["Allow"]
    except Exception as exc:
        # Log only exception type, never submitted data, tokens, URLs or traceback.
        LOGGER.error(json.dumps({"event": "request_error", "request_id": request[REQUEST_ID], "exception_type": type(exc).__name__}))
        response = json_response(ApiError(500, "INTERNAL_ERROR", "An internal error occurred.").body(request[REQUEST_ID]), 500)
    response.headers.update({
        "X-Request-Id": request[REQUEST_ID], "X-Data-Mode": "real",
        "X-Contract-Version": state["contracts"].version["contract_version"],
        "X-Contract-Status": state["contracts"].version["status"], "Cache-Control": "no-store",
    })
    if origin in state["settings"].allowed_origins:
        response.headers.update({"Access-Control-Allow-Origin": origin, "Vary": "Origin",
                                 "Access-Control-Expose-Headers": "X-Request-Id,X-Data-Mode,X-Contract-Version,X-Contract-Status,Retry-After"})
    LOGGER.info(json.dumps({"event": "http_request", "request_id": request[REQUEST_ID],
                            "method": request.method, "operation_id": request.match_info.route.name,
                            "status": response.status, "duration_ms": round((perf_counter() - start) * 1000, 3)}))
    return response


async def liveness(request):
    settings = request.app[STATE]["settings"]
    return json_response({"data": {"status": "alive", "stage": "persistence" if settings.persistence_enabled else "foundation", "environment": settings.environment}, "request_id": request[REQUEST_ID]})


async def readiness(request):
    # Health is not business readiness. No cloud integrations are claimed by this release.
    storage = request.app[STATE].get("persistence")
    dependencies = await asyncio.to_thread(storage.health) if storage else {"database": "not_configured", "object_storage": "not_configured"}
    state = request.app[STATE]
    auth = "local_password_ready" if state["settings"].local_auth_enabled and state["authenticator"].ready else "not_configured"
    dependencies = {**dependencies, "authentication": auth}
    if state["settings"].local_auth_enabled:
        dependencies.update(ocr="worker_enabled" if state["settings"].ocr_enabled else "not_connected", cognito="not_configured")
    raise ApiError(503, "FEATURE_NOT_CONFIGURED", "Full application services are not ready.", details={"stage": "local_integration" if state["settings"].local_auth_enabled else "persistence" if storage else "foundation", "business_services_ready": False, "implemented_business_operations": len(state["handlers"]), "dependencies": dependencies})


async def preflight(request):
    state = request.app[STATE]
    if request.headers.get("Origin") not in state["settings"].allowed_origins:
        raise ApiError(403, "FORBIDDEN", "Origin is not allowed.")
    method = request.headers.get("Access-Control-Request-Method", "")
    found = [op for op in state["contracts"].operations.values() if op.method == method]
    # Resolve the actual method against the router to avoid accepting unknown paths.
    resolved = await request.app.router.resolve(request.clone(method=method)) if found else None
    if resolved is None or resolved.http_exception is not None or resolved.route.name not in state["contracts"].operations:
        raise ApiError(404, "RESOURCE_NOT_FOUND", "Route not found.")
    headers = {item.strip().lower() for item in request.headers.get("Access-Control-Request-Headers", "").split(",") if item.strip()}
    if not headers <= ALLOWED_HEADERS:
        raise ApiError(403, "FORBIDDEN", "Requested headers are not allowed.")
    response = web.Response(status=204)
    response.headers.update({"Access-Control-Allow-Methods": method,
                             "Access-Control-Allow-Headers": ",".join(sorted(ALLOWED_HEADERS))})
    return response


async def dispatch(request):
    state = request.app[STATE]
    operation = state["contracts"].operations[request.match_info.route.name]
    auth_headers = request.headers.getall("Authorization", [])
    if not auth_headers:
        raise ApiError(401, "AUTH_REQUIRED", "An access token is required.")
    pieces = auth_headers[0].split()
    if len(auth_headers) != 1 or len(pieces) != 2 or pieces[0].lower() != "bearer":
        raise ApiError(401, "AUTH_REQUIRED", "A Bearer access token is required.")
    identity = await state["authenticator"].verify_access_token(pieces[1])
    if not identity.user_id:
        raise ContractFailure("Authenticator returned an invalid identity")
    if "Admin" in operation.definition.get("tags", []) and "admin" not in identity.roles:
        raise ApiError(403, "FORBIDDEN", "Administrator access is required.")
    if "Admin" not in operation.definition.get("tags", []):
        # Repository admin authority is also used by internal workers. A browser
        # admin using learner APIs must still satisfy ownership/membership.
        identity = Identity(identity.user_id, ("user",))
    request[IDENTITY] = identity
    content = await request.read()
    body = None
    if content:
        if request.content_type != "application/json" or request.charset not in {None, "utf-8", "UTF-8"}:
            raise ApiError(400, "VALIDATION_ERROR", "A UTF-8 JSON body is required.")
        try:
            body = strict_json(content)
        except (ValueError, UnicodeDecodeError):
            raise ApiError(400, "VALIDATION_ERROR", "Invalid JSON body.") from None
    if any(len(request.query.getall(key)) != 1 for key in request.query):
        raise ApiError(400, "VALIDATION_ERROR", "Repeated query parameters are not supported.")
    headers = {key.lower(): value for key, value in request.headers.items()}
    for reference in operation.definition.get("parameters", []):
        parameter, _ = state["contracts"].resolve(reference)
        if parameter["in"] == "header" and len(request.headers.getall(parameter["name"], [])) > 1:
            raise ApiError(400, "VALIDATION_ERROR", "Repeated contract headers are not supported.")
    issues = state["contracts"].request_issues(operation, request.match_info, request.query, headers, body)
    if issues:
        raise ApiError(400, "VALIDATION_ERROR", "Request does not match the contract.", details={"fields": issues[:10]})
    business_handler = state["handlers"].get(operation.identifier)
    if business_handler is None:
        raise unavailable()
    result = await business_handler(request, body)
    if not isinstance(result, Result):
        raise ContractFailure("Handler must return a Result")
    if result.status == 204:
        if result.data is not None:
            raise ContractFailure("204 handler must not return data")
        output = None
    else:
        output = {"data": result.data, "request_id": request[REQUEST_ID]}
    if state["contracts"].response_issues(operation, result.status, output):
        raise ContractFailure("Handler response does not match the contract")
    return json_response(output, result.status)


def create_app(settings=None, *, authenticator=None, handlers=None):
    settings = settings or Settings.from_environment()
    contracts = ContractRegistry(settings.contracts_dir)
    handlers = dict(handlers or {})
    if not handlers.keys() <= contracts.operations.keys():
        raise ContractFailure("Handler registration contains unknown operationIds")
    app = web.Application(middlewares=[foundation_middleware], client_max_size=settings.max_body_bytes)
    app[STATE] = {"settings": settings, "contracts": contracts,
                  "authenticator": authenticator or UnconfiguredAuthenticator(), "handlers": handlers, "persistence": None}
    storage_settings = None
    if settings.persistence_enabled:
        from .persistence.settings import PersistenceSettings
        storage_settings = PersistenceSettings.from_environment()
    async def storage_context(application):
        if settings.persistence_enabled:
            from .persistence.bundle import PersistenceBundle
            storage = await asyncio.to_thread(PersistenceBundle, storage_settings, contracts)
            application[STATE]["persistence"] = storage
            try:
                yield
            finally:
                await asyncio.to_thread(storage.close)
        else:
            yield
    app.cleanup_ctx.append(storage_context)
    if settings.local_auth_enabled:
        from .local_integration import configure_local_integration
        configure_local_integration(app)
    # Operational localhost-only routes, outside the existing public business contract.
    app.router.add_get("/health/live", liveness, name="liveness")
    app.router.add_get("/health/ready", readiness, name="readiness")
    for operation in contracts.operations.values():
        app.router.add_route(operation.method, operation.path, dispatch, name=operation.identifier)
    for path in sorted({op.path for op in contracts.operations.values()}):
        app.router.add_route("OPTIONS", path, preflight)
    return app
