"""Opt-in loopback auth overlay. Original public contract bundle stays pinned."""
import asyncio
from contextlib import suppress
from collections import defaultdict, deque
from time import monotonic

from .contracts import strict_json
from .errors import ApiError
from .learning import LearningService, OPERATIONS
from .local_admin import LocalAdmin
from .local_auth import COOKIE, REFRESH_SECONDS, LocalAuth
from .persistence.errors import Conflict, Forbidden, InvalidRecord, NotFound, StorageUnavailable
from .media import MediaService, OPERATIONS as MEDIA_OPERATIONS
from .rooms import RoomService, OPERATIONS as ROOM_OPERATIONS
from .collections import CollectionService, OPERATIONS as COLLECTION_OPERATIONS


async def database_call(function, *args):
    try:
        return await asyncio.to_thread(function, *args)
    except Conflict:
        raise ApiError(409, "VERSION_CONFLICT", "Dữ liệu đã thay đổi. Hãy tải lại rồi thử lại.") from None
    except Forbidden:
        raise ApiError(403, "FORBIDDEN", "Bạn không có quyền truy cập dữ liệu này.") from None
    except NotFound:
        raise ApiError(404, "RESOURCE_NOT_FOUND", "Không tìm thấy dữ liệu.") from None
    except InvalidRecord:
        raise ApiError(400, "VALIDATION_ERROR", "Dữ liệu không hợp lệ.") from None
    except StorageUnavailable:
        raise ApiError(503, "PROVIDER_UNAVAILABLE", "Chưa kết nối được dịch vụ dữ liệu.", retryable=True) from None


def configure_local_integration(app):
    from .app import STATE, IDENTITY, REQUEST_ID, Result, json_response
    state = app[STATE]
    attempts = defaultdict(deque)
    anonymous = {"register", "login", "password/forgot", "password/reset"}
    authenticated = {"verification/request": "verification_request", "verification/confirm": "verification_confirm",
                     "password/change": "password_change", "email/request": "email_request", "email/confirm": "email_confirm",
                     "logout-all": "logout_all"}
    routes = [(name, "POST") for name in anonymous | authenticated.keys() | {"refresh", "logout", "admin/status"}]
    routes += [("session", "GET"), ("admin/users", "GET"), ("admin/audit", "GET")]

    async def auth_route(request):
        if request.headers.getall("X-Local-Client", []) != ["browser"]:
            raise ApiError(403, "FORBIDDEN", "Yêu cầu phải đến từ ứng dụng local.")
        auth, action = state["authenticator"], request.match_info["action"]
        body = {}
        if request.method == "POST":
            if len(attempts) > 1024:
                attempts.clear()
            queue, now = attempts[(request.remote, "anonymous" if action in anonymous else "account")], monotonic()
            while queue and now - queue[0] > 60:
                queue.popleft()
            if len(queue) >= (10 if action in anonymous else 60):
                raise ApiError(429, "RATE_LIMITED", "Bạn thử quá nhiều lần. Vui lòng chờ một phút.", retryable=True)
            queue.append(now)
            content = await request.read()
            if len(content) > 4096:
                raise ApiError(400, "VALIDATION_ERROR", "Biểu mẫu quá lớn.")
            if content:
                if request.content_type != "application/json":
                    raise ApiError(400, "VALIDATION_ERROR", "Cần JSON POST.")
                try:
                    body = strict_json(content)
                except (ValueError, UnicodeDecodeError):
                    raise ApiError(400, "VALIDATION_ERROR", "JSON không hợp lệ.") from None
        if action in anonymous:
            data = await database_call(getattr(auth, action.replace("/", "_")), body)
        elif action in {"session", "refresh"}:
            if action == "refresh":
                auth.fields(body, [])
            cookie = request.cookies.get(COOKIE)
            # A current access token must never act as a renewable cookie.
            def restore():
                if cookie:
                    row = auth.store.get(auth.session_key(cookie))
                    if row and "family_id" in row:
                        raise ApiError(401, "AUTH_REQUIRED", "Vui lòng đăng nhập lại.")
                return auth.restore(cookie)
            data = await database_call(restore)
        elif action == "logout":
            auth.fields(body, [])
            await database_call(auth.logout, request.cookies.get(COOKIE))
            data = {"signed_out": True}
        else:
            values = request.headers.getall("Authorization", [])
            if len(values) != 1 or not values[0].startswith("Bearer "):
                raise ApiError(401, "AUTH_REQUIRED", "Vui lòng đăng nhập.")
            actor = await auth.verify_access_token(values[0][7:])
            if action in authenticated:
                data = await database_call(getattr(auth, authenticated[action]), actor, body)
            elif action == "admin/users":
                data = await database_call(state["local_admin"].users, actor, dict(request.query))
            elif action == "admin/status":
                data = await database_call(state["local_admin"].set_status, actor, body, request[REQUEST_ID])
            else:
                data = await database_call(state["local_admin"].audit, actor, dict(request.query))
        refresh_token = data.pop("_refresh_token", None)
        response = json_response({"data": data, "request_id": request[REQUEST_ID]}, 201 if action == "register" else 200)
        if refresh_token:
            response.set_cookie(COOKIE, refresh_token, httponly=True, samesite="Strict", path="/local-auth", max_age=REFRESH_SECONDS)
        elif data.get("signed_out"):
            response.del_cookie(COOKIE, path="/local-auth")
        return response

    for action, method in routes:
        app.router.add_route(method, "/local-auth/{action:" + action + "}", auth_route)

    async def business(request, body):
        operation = request.match_info.route.name
        data, status = await database_call(state["learning"].handle, operation, request[IDENTITY], body,
                                           dict(request.match_info), dict(request.query), request.headers,
                                           request.path, request.method)
        return Result(data, status)

    state["handlers"].update({name: business for name in OPERATIONS})

    async def extended_business(request, body):
        operation = request.match_info.route.name
        service = "media" if operation in MEDIA_OPERATIONS else "rooms" if operation in ROOM_OPERATIONS else "collections"
        args = [operation, request[IDENTITY], body, dict(request.match_info), dict(request.query), request.headers, request.path, request.method]
        if service == "media":
            args.append(request.headers.get("Origin") or str(request.url.origin()))
        data, status = await database_call(state[service].handle, *args)
        return Result(data, status)

    state["handlers"].update({name: extended_business for name in (*MEDIA_OPERATIONS, *ROOM_OPERATIONS, *COLLECTION_OPERATIONS)})

    async def upload_frame(request):
        if set(request.query):
            raise ApiError(400, "VALIDATION_ERROR", "Upload không nhận query parameters.")
        tokens = request.headers.getall("X-Upload-Token", [])
        if len(tokens) != 1:
            raise ApiError(403, "FORBIDDEN", "Thiếu quyền upload frame.")
        chunks, length = [], 0
        async for chunk in request.content.iter_chunked(65536):
            length += len(chunk)
            if length > 1048576:
                raise ApiError(413, "IMAGE_TOO_LARGE", "Frame vượt giới hạn 1 MiB.")
            chunks.append(chunk)
        content = b"".join(chunks)
        status = await database_call(state["media"].put_upload, request.match_info["upload_id"], tokens[0], content, request.content_type)
        return json_response(None, status)

    app.router.add_put("/local-uploads/{upload_id:[0-9a-fA-F-]{36}}", upload_frame)

    async def integration_context(application):
        state["authenticator"] = LocalAuth(state["persistence"])
        state["local_admin"] = LocalAdmin(state["authenticator"])
        state["learning"] = LearningService(state["persistence"])
        settings = state["settings"]
        state["learning"].ocr_enabled = settings.ocr_enabled
        languages = ("ja", "zh") if settings.ocr_chinese_service_url else ("ja",)
        state["learning"].ocr_languages = languages
        state["media"] = MediaService(state["persistence"], state["learning"], enabled=settings.ocr_enabled, languages=languages)
        state["rooms"] = RoomService(state["persistence"], state["learning"], state["media"])
        state["collections"] = CollectionService(state["persistence"], state["learning"], state["media"])
        yield

    app.cleanup_ctx.append(integration_context)

    if state["settings"].ocr_enabled:
        async def worker_context(application):
            from .ocr_worker import RoutedOcrProvider, OcrWorker
            async with RoutedOcrProvider(state["settings"].ocr_service_url, state["settings"].ocr_chinese_service_url, allow_test_provider=state["settings"].environment == "test") as provider:
                state["ocr_worker"] = OcrWorker(state["media"], provider)
                worker = asyncio.create_task(state["ocr_worker"].run(), name="local-durable-ocr-worker")
                state["ocr_task"] = worker
                try:
                    yield
                finally:
                    worker.cancel()
                    with suppress(asyncio.CancelledError):
                        await worker
        app.cleanup_ctx.append(worker_context)
