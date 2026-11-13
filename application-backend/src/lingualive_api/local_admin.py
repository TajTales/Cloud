"""Local account authority. Public business Admin endpoints remain separate."""
from uuid import uuid4

from .auth import Identity
from .errors import ApiError
from .learning import utc_now
from .persistence.catalog import Scope

PERMISSIONS = ["users.read", "users.status.write", "audit.read"]
REGISTRY = {"pk": "LOCAL_AUTH#ADMIN_REGISTRY", "sk": "active"}


class LocalAdmin:
    def __init__(self, auth):
        self.auth, self.store, self.repo = auth, auth.store, auth.repo

    def require(self, actor, permission):
        profile = self.auth.record(actor.user_id)
        if "admin" not in profile.data["roles"] or permission not in profile.data["permissions"]:
            raise ApiError(403, "FORBIDDEN", "Bạn không có quyền quản trị này.")
        if not profile.data["email_verified"]:
            raise ApiError(403, "USER_NOT_VERIFIED", "Vui lòng xác nhận email trước khi quản trị.")
        return profile

    def audit_actions(self, actor, target, action, reason, request_id):
        event = {"event_id": str(uuid4()), "occurred_at": utc_now(), "level": "success", "outcome": "succeeded",
                 "action": action, "actor": {"user_id": actor.user_id, "display_name": actor.user_id},
                 "target": {"type": "user", "id": target["user_id"], "label": target["display_name"]},
                 "reason": reason, "detail": "Local account authority change", "request_id": request_id, "action_id": None}
        row, ref, _ = self.repo.rows(Scope("system", "local-auth-audit"), "audit", event, 1)
        return [self.store.put_action(row), self.store.put_action(ref)]

    def registry_action(self, user_id, *, active):
        old = self.store.get(REGISTRY)
        members = set(old["user_ids"] if old else [])
        if active:
            members.add(user_id)
        elif user_id in members:
            if len(members) == 1:
                raise ApiError(409, "LAST_ADMIN_PROTECTED", "Không thể vô hiệu hóa Admin hoạt động cuối cùng.")
            members.remove(user_id)
        revision = old["revision"] if old else 0
        return self.store.put_action({**REGISTRY, "revision": revision + 1, "user_ids": sorted(members)}, revision)

    def provision(self, email, *, grant, reason):
        """Only invoked by the OS-owner CLI; never a browser registration field."""
        email = self.auth.email(email)
        self.reason(reason)
        account = self.store.get(self.auth.account_key(email))
        if not account:
            raise ApiError(404, "RESOURCE_NOT_FOUND", "Chưa có tài khoản với email này.")
        profile = self.auth.record(account["user_id"])
        if grant and not profile.data["email_verified"]:
            raise ApiError(403, "USER_NOT_VERIFIED", "Cần xác nhận email trước khi cấp Admin.")
        roles = ["user", "admin"] if grant else ["user"]
        permissions = PERMISSIONS if grant else []
        actor = Identity("local-os-owner", ("admin",))
        actions = [self.auth.profile_action(profile, {"roles": roles, "permissions": permissions}),
                   self.auth.account_action(account, {"auth_epoch": account.get("auth_epoch", 0) + 1}),
                   self.registry_action(account["user_id"], active=grant)]
        actions += self.audit_actions(actor, profile.data, "admin.grant" if grant else "admin.revoke", reason.strip(), "cli-" + str(uuid4()))
        self.store.transact(actions)
        return {"user_id": account["user_id"], "roles": roles, "sign_in_again": True}

    @staticmethod
    def reason(reason):
        if not isinstance(reason, str) or not 3 <= len(reason.strip()) <= 300:
            raise ApiError(400, "VALIDATION_ERROR", "Lý do cần từ 3 đến 300 ký tự.")

    def users(self, actor, query):
        self.require(actor, "users.read")
        if not set(query) <= {"limit", "cursor"}:
            raise ApiError(400, "VALIDATION_ERROR", "Chỉ hỗ trợ limit và cursor.")
        try:
            limit = int(query.get("limit", "20"))
        except ValueError:
            raise ApiError(400, "VALIDATION_ERROR", "Limit không hợp lệ.") from None
        if not 1 <= limit <= 100:
            raise ApiError(400, "VALIDATION_ERROR", "Limit cần từ 1 đến 100.")
        records, cursor = self.repo.operational_page(actor, "profile", limit=limit, cursor=query.get("cursor"))
        return {"items": [record.data for record in records], "next_cursor": cursor}

    def set_status(self, actor, body, request_id):
        caller = self.require(actor, "users.status.write")
        self.auth.fields(body, ["user_id", "status", "expected_version", "reason"])
        self.reason(body["reason"])
        if not isinstance(body["user_id"], str) or not 1 <= len(body["user_id"]) <= 256 or not isinstance(body["status"], str) or body["status"] not in {"active", "suspended"} or type(body["expected_version"]) is not int:
            raise ApiError(400, "VALIDATION_ERROR", "Trạng thái hoặc phiên bản không hợp lệ.")
        if actor.user_id == body["user_id"] and body["status"] == "suspended":
            raise ApiError(409, "SELF_SUSPEND_FORBIDDEN", "Bạn không thể tự khóa tài khoản.")
        target = self.auth.record(body["user_id"], active=False)
        if target.revision != body["expected_version"]:
            raise ApiError(409, "VERSION_CONFLICT", "Tài khoản đã thay đổi. Hãy tải lại danh sách.")
        if target.data["status"] == "pending":
            raise ApiError(409, "USER_NOT_VERIFIED", "Không thể bỏ qua bước xác nhận tài khoản.")
        account = self.store.get(self.auth.account_key(target.data["email"]))
        if not account:
            raise ApiError(404, "RESOURCE_NOT_FOUND", "Không tìm thấy tài khoản local.")
        actions = [self.auth.profile_action(target, {"status": body["status"]}),
                   self.auth.account_action(account, {"auth_epoch": account.get("auth_epoch", 0) + 1})]
        if actor.user_id != target.identifier:
            actions.append(self.store.check_action(self.repo.raw(caller.scope, "profile", actor.user_id)))
        if "admin" in target.data["roles"]:
            actions.append(self.registry_action(target.identifier, active=body["status"] == "active"))
        actions += self.audit_actions(actor, target.data, "user.status." + body["status"], body["reason"].strip(), request_id)
        self.store.transact(actions)
        return self.auth.record(target.identifier, active=False).data

    def audit(self, actor, query):
        self.require(actor, "audit.read")
        if not set(query) <= {"cursor"}:
            raise ApiError(400, "VALIDATION_ERROR", "Chỉ hỗ trợ cursor.")
        rows, cursor = self.repo.list(actor, Scope("system", "local-auth-audit"), "audit", limit=50, cursor=query.get("cursor"), reverse=True)
        return {"items": [row.data for row in rows], "next_cursor": cursor}
