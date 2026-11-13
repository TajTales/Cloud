"""Loopback-only authentication; no cloud issuer or external email is simulated."""
import asyncio
import hashlib
import hmac
import re
import secrets
from time import time
from uuid import uuid4

from .auth import Identity
from .errors import ApiError
from .learning import utc_now
from .local_mail import LocalMailbox
from .persistence.bundle import cursor_secret
from .persistence.catalog import Scope
from .persistence.errors import Conflict, StorageUnavailable

COOKIE = "lingualive_local_session"
SESSION_SECONDS = 15 * 60
REFRESH_SECONDS = 24 * 60 * 60
CODE_SECONDS = 10 * 60


class LocalAuth:
    ready = True

    def __init__(self, storage, *, clock=time, mailbox=None):
        self.storage, self.clock = storage, clock
        self.store, self.repo = storage.store, storage.repository
        directory = storage.objects.root.parent
        self.mailbox = mailbox or LocalMailbox(directory / "mailbox")
        self.code_key = cursor_secret(directory / "auth")

    @staticmethod
    def key(kind, value):
        return {"pk": "LOCAL_AUTH#" + kind, "sk": hashlib.sha256(value.encode()).hexdigest()}

    @classmethod
    def account_key(cls, email):
        return cls.key("ACCOUNT", email)

    @classmethod
    def session_key(cls, token):
        return cls.key("SESSION", token)

    @staticmethod
    def fields(body, fields):
        if not isinstance(body, dict) or set(body) != set(fields):
            raise ApiError(400, "VALIDATION_ERROR", "Biểu mẫu có trường thiếu hoặc không hợp lệ.")

    @staticmethod
    def email(value):
        if not isinstance(value, str):
            raise ApiError(400, "VALIDATION_ERROR", "Email không hợp lệ.")
        value = value.strip().lower()
        if len(value) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ApiError(400, "VALIDATION_ERROR", "Email không hợp lệ.")
        return value

    @staticmethod
    def password(value):
        if not isinstance(value, str) or not 8 <= len(value) <= 128:
            raise ApiError(400, "VALIDATION_ERROR", "Mật khẩu cần từ 8 đến 128 ký tự.")
        return value

    @classmethod
    def credentials(cls, body):
        if not isinstance(body, dict):
            raise ApiError(400, "VALIDATION_ERROR", "Vui lòng nhập email và mật khẩu.")
        return cls.email(body.get("email")), cls.password(body.get("password"))

    @staticmethod
    def password_hash(password, salt):
        return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1, dklen=32).hex()

    def password_matches(self, account, password):
        candidate = self.password_hash(password, account["salt"] if account else "0" * 32)
        return account is not None and hmac.compare_digest(candidate, account["password_hash"])

    def record(self, user_id, *, active=True):
        identity = Identity(user_id, ("user",))
        record = self.repo.get(identity, Scope("user", user_id), "profile", user_id)
        if not record or (active and record.data["status"] != "active"):
            raise ApiError(403, "FORBIDDEN", "Tài khoản không hoạt động.", details={"account_status": record.data["status"] if record else "missing"})
        return record

    def profile(self, identity):
        return self.record(identity.user_id).data

    def account(self, user_id):
        profile = self.record(user_id)
        account = self.store.get(self.account_key(profile.data["email"]))
        if not account or account["user_id"] != user_id:
            raise ApiError(401, "AUTH_REQUIRED", "Vui lòng đăng nhập lại.")
        return profile, account

    def profile_action(self, record, changes):
        version = record.revision + 1
        row, _, _ = self.repo.rows(record.scope, "profile", {**record.data, **changes, "version": version}, version)
        return self.store.put_action(row, record.revision)

    def account_action(self, account, changes):
        return self.store.put_action({**account, **changes, "revision": account["revision"] + 1}, account["revision"])

    def register(self, body):
        self.fields(body, ["email", "password", "display_name"])
        email, password = self.credentials(body)
        name = body["display_name"]
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 60:
            raise ApiError(400, "VALIDATION_ERROR", "Tên hiển thị cần từ 1 đến 60 ký tự.")
        identity = Identity("local:" + str(uuid4()), ("user",))
        profile = {"user_id": identity.user_id, "display_name": name.strip(), "email": email,
                   "email_verified": False, "roles": ["user"], "permissions": [], "status": "active",
                   "locale": "vi", "timezone": "Asia/Ho_Chi_Minh", "learning_language": "ja", "version": 1}
        salt = secrets.token_hex(16)
        account = {**self.account_key(email), "revision": 1, "user_id": identity.user_id, "auth_epoch": 0,
                   "salt": salt, "password_hash": self.password_hash(password, salt), "algorithm": "scrypt-n16384-r8-p1",
                   "created_at": utc_now(), "last_sign_in_at": None}
        row, reference, _ = self.repo.rows(Scope("user", identity.user_id), "profile", profile, 1)
        try:
            self.store.transact([self.store.put_action(item) for item in [account, row, reference]])
        except Conflict:
            raise ApiError(409, "VERSION_CONFLICT", "Email này đã được đăng ký trên máy này.") from None
        # Compatibility: existing learners can study before local email confirmation.
        # Administrative authority always requires confirmation.
        return self.issue(identity)

    def login(self, body):
        self.fields(body, ["email", "password"])
        email, password = self.credentials(body)
        account = self.store.get(self.account_key(email))
        matches = self.password_matches(account, password)
        if account and account.get("locked_until_s", 0) > self.clock():
            raise ApiError(429, "RATE_LIMITED", "Vui lòng chờ một phút trước khi đăng nhập lại.", retryable=True)
        if not matches:
            if account:
                failures = account.get("failed_logins", 0) + 1
                self.store.transact([self.account_action(account, {"failed_logins": failures % 5,
                                     "locked_until_s": int(self.clock()) + 60 if failures >= 5 else 0})])
            raise ApiError(401, "AUTH_REQUIRED", "Email hoặc mật khẩu không đúng.")
        self.record(account["user_id"])
        self.store.transact([self.account_action(account, {"last_sign_in_at": utc_now(), "failed_logins": 0, "locked_until_s": 0})])
        return self.issue(Identity(account["user_id"], ("user",)))

    def issue(self, identity):
        profile, account = self.account(identity.user_id)
        now = int(self.clock())
        token, refresh, family_id = secrets.token_urlsafe(32), secrets.token_urlsafe(32), str(uuid4())
        common = {"user_id": identity.user_id, "auth_epoch": account.get("auth_epoch", 0), "revision": 1}
        family = {**self.key("FAMILY", family_id), **common, "expires_at_s": now + REFRESH_SECONDS}
        access = {**self.session_key(token), **common, "family_id": family_id, "expires_at_s": now + SESSION_SECONDS}
        renewal = {**self.key("REFRESH", refresh), **common, "family_id": family_id, "expires_at_s": now + REFRESH_SECONDS}
        self.store.transact([self.store.put_action(item) for item in [family, access, renewal]] +
                            [self.store.check_action(account), self.store.check_action(self.repo.raw(profile.scope, "profile", identity.user_id))])
        return {"access_token": token, "expires_at_s": access["expires_at_s"], "auth_provider": "local_password",
                "profile": profile.data, "_refresh_token": refresh}

    def verify(self, token):
        if not isinstance(token, str) or not 32 <= len(token) <= 128:
            raise ApiError(401, "AUTH_REQUIRED", "Vui lòng đăng nhập.")
        row = self.store.get(self.session_key(token))
        if not row or row["expires_at_s"] <= self.clock():
            raise ApiError(401, "TOKEN_EXPIRED", "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.")
        profile, account = self.account(row["user_id"])
        if row.get("auth_epoch", 0) != account.get("auth_epoch", 0):
            raise ApiError(401, "TOKEN_EXPIRED", "Phiên đăng nhập đã bị thu hồi.")
        if "family_id" in row:
            family = self.store.get(self.key("FAMILY", row["family_id"]))
            if not family or family["expires_at_s"] <= self.clock():
                raise ApiError(401, "TOKEN_EXPIRED", "Phiên đăng nhập đã bị thu hồi.")
        return Identity(row["user_id"], tuple(profile.data["roles"])), row

    async def verify_access_token(self, token):
        try:
            identity, _ = await asyncio.to_thread(self.verify, token)
            return identity
        except StorageUnavailable:
            raise ApiError(503, "PROVIDER_UNAVAILABLE", "Chưa kết nối được dịch vụ dữ liệu.", retryable=True) from None

    def restore(self, token):
        """Rotate an HttpOnly refresh token; upgrade old 8h cookies without reset."""
        if not isinstance(token, str) or not 32 <= len(token) <= 128:
            raise ApiError(401, "AUTH_REQUIRED", "Vui lòng đăng nhập.")
        row = self.store.get(self.key("REFRESH", token))
        if not row:
            identity, legacy = self.verify(token)
            if "family_id" in legacy:
                # Internal legacy helper compatibility; HTTP rejects access tokens as cookies.
                return {"access_token": token, "expires_at_s": legacy["expires_at_s"], "auth_provider": "local_password", "profile": self.profile(identity)}
            data = self.issue(identity)
            self.logout(token)
            return data
        profile, account = self.account(row["user_id"])
        family = self.store.get(self.key("FAMILY", row["family_id"]))
        if not family or row["expires_at_s"] <= self.clock() or row["auth_epoch"] != account.get("auth_epoch", 0):
            raise ApiError(401, "TOKEN_EXPIRED", "Phiên đăng nhập đã hết hạn.")
        access, refresh = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        expires = min(int(self.clock()) + SESSION_SECONDS, family["expires_at_s"])
        renewal = {**row, **self.key("REFRESH", refresh), "revision": 1}
        self.store.transact([self.store.delete_action(self.key("REFRESH", token), row["revision"]),
                            self.store.put_action(renewal), self.store.check_action(family), self.store.check_action(account),
                            self.store.put_action({**row, **self.session_key(access), "expires_at_s": expires, "revision": 1})])
        return {"access_token": access, "expires_at_s": expires, "auth_provider": "local_password", "profile": profile.data, "_refresh_token": refresh}

    def logout(self, token):
        if not token:
            return
        refresh = self.store.get(self.key("REFRESH", token))
        access = self.store.get(self.session_key(token))
        row = refresh or access
        if not row:
            return
        family = self.store.get(self.key("FAMILY", row["family_id"])) if "family_id" in row else None
        actions = [self.store.delete_action({"pk": row["pk"], "sk": row["sk"]}, row["revision"])]
        if family:
            actions.append(self.store.delete_action({"pk": family["pk"], "sk": family["sk"]}, family["revision"]))
        try:
            self.store.transact(actions)
        except Conflict:
            # Concurrent logout is already complete; no fabricated DB success on outage.
            if family and self.store.get({"pk": family["pk"], "sk": family["sk"]}):
                raise

    def logout_all(self, identity, body):
        self.fields(body, [])
        _, account = self.account(identity.user_id)
        self.store.transact([self.account_action(account, {"auth_epoch": account.get("auth_epoch", 0) + 1})])
        return {"signed_out": True}

    def send_code(self, account, purpose, email):
        key = self.key("CHALLENGE", account["user_id"] + ":" + purpose)
        previous = self.store.get(key)
        now = int(self.clock())
        if previous and now - previous["sent_at_s"] < 60:
            raise ApiError(429, "RATE_LIMITED", "Vui lòng chờ một phút trước khi yêu cầu mã mới.", retryable=True)
        code, salt = f"{secrets.randbelow(100000000):08d}", secrets.token_hex(16)
        digest = hmac.new(self.code_key, (salt + code).encode(), hashlib.sha256).hexdigest()
        row = {**key, "revision": previous["revision"] + 1 if previous else 1, "user_id": account["user_id"],
               "code_hash": digest, "salt": salt, "email": email, "attempts": 0,
               "auth_epoch": account.get("auth_epoch", 0), "sent_at_s": now, "expires_at_s": now + CODE_SECONDS}
        self.store.transact([self.store.put_action(row, previous["revision"] if previous else 0), self.store.check_action(account)])
        try:
            self.mailbox.deliver(email=email, purpose=purpose, code=code, expires_at_s=row["expires_at_s"])
        except OSError:
            self.store.transact([self.store.delete_action(key, row["revision"])])
            raise ApiError(503, "PROVIDER_UNAVAILABLE", "Chưa tạo được thư xác nhận. Vui lòng thử lại.", retryable=True) from None

    def check_code(self, account, purpose, value):
        if not isinstance(value, str) or not re.fullmatch(r"\d{8}", value):
            raise ApiError(400, "VALIDATION_ERROR", "Mã xác nhận gồm 8 chữ số.")
        key = self.key("CHALLENGE", account["user_id"] + ":" + purpose)
        row = self.store.get(key)
        valid = row and row["expires_at_s"] > self.clock() and row["attempts"] < 5 and row["auth_epoch"] == account.get("auth_epoch", 0)
        if valid:
            candidate = hmac.new(self.code_key, (row["salt"] + value).encode(), hashlib.sha256).hexdigest()
            valid = hmac.compare_digest(candidate, row["code_hash"])
        if not valid:
            if row and row["attempts"] < 5:
                self.store.transact([self.store.put_action({**row, "attempts": row["attempts"] + 1, "revision": row["revision"] + 1}, row["revision"])])
            raise ApiError(400, "VALIDATION_ERROR", "Mã không đúng, đã hết hạn hoặc đã được sử dụng.")
        return row, self.store.delete_action(key, row["revision"])

    def verification_request(self, identity, body):
        self.fields(body, [])
        profile, account = self.account(identity.user_id)
        if not profile.data["email_verified"]:
            self.send_code(account, "verify_email", profile.data["email"])
        return {"accepted": True, "delivery_mode": self.mailbox.mode}

    def verification_confirm(self, identity, body):
        self.fields(body, ["code"])
        profile, account = self.account(identity.user_id)
        _, consume = self.check_code(account, "verify_email", body["code"])
        self.store.transact([consume, self.profile_action(profile, {"email_verified": True}), self.store.check_action(account)])
        return self.profile(identity)

    def password_forgot(self, body):
        self.fields(body, ["email"])
        email = self.email(body["email"])
        account = self.store.get(self.account_key(email))
        if account:
            # Do not expose existence or per-account cooldown through this endpoint.
            try:
                self.send_code(account, "reset_password", email)
            except ApiError as error:
                if error.status != 429:
                    raise
        return {"accepted": True, "delivery_mode": self.mailbox.mode}

    def password_reset(self, body):
        self.fields(body, ["email", "code", "password"])
        email, password = self.credentials(body)
        account = self.store.get(self.account_key(email))
        if not account:
            raise ApiError(400, "VALIDATION_ERROR", "Mã không đúng, đã hết hạn hoặc đã được sử dụng.")
        _, consume = self.check_code(account, "reset_password", body["code"])
        salt = secrets.token_hex(16)
        self.store.transact([consume, self.account_action(account, {"salt": salt, "password_hash": self.password_hash(password, salt),
                                                                 "auth_epoch": account.get("auth_epoch", 0) + 1, "failed_logins": 0, "locked_until_s": 0})])
        return {"signed_out": True}

    def password_change(self, identity, body):
        self.fields(body, ["current_password", "password"])
        current, password = self.password(body["current_password"]), self.password(body["password"])
        _, account = self.account(identity.user_id)
        if not self.password_matches(account, current):
            raise ApiError(400, "VALIDATION_ERROR", "Mật khẩu hiện tại không đúng.")
        salt = secrets.token_hex(16)
        self.store.transact([self.account_action(account, {"salt": salt, "password_hash": self.password_hash(password, salt),
                                                         "auth_epoch": account.get("auth_epoch", 0) + 1, "failed_logins": 0, "locked_until_s": 0})])
        return {"signed_out": True}

    def email_request(self, identity, body):
        self.fields(body, ["email", "password"])
        email, password = self.credentials(body)
        profile, account = self.account(identity.user_id)
        if email == profile.data["email"] or self.store.get(self.account_key(email)):
            raise ApiError(409, "VERSION_CONFLICT", "Không thể sử dụng địa chỉ email này.")
        if not self.password_matches(account, password):
            raise ApiError(400, "VALIDATION_ERROR", "Mật khẩu hiện tại không đúng.")
        self.send_code(account, "change_email", email)
        return {"accepted": True, "delivery_mode": self.mailbox.mode}

    def email_confirm(self, identity, body):
        self.fields(body, ["code"])
        profile, account = self.account(identity.user_id)
        challenge, consume = self.check_code(account, "change_email", body["code"])
        moved = {**account, **self.account_key(challenge["email"]), "revision": 1, "auth_epoch": account.get("auth_epoch", 0) + 1}
        self.store.transact([consume, self.store.delete_action(self.account_key(profile.data["email"]), account["revision"]),
                            self.store.put_action(moved), self.profile_action(profile, {"email": challenge["email"], "email_verified": True})])
        return {"signed_out": True}
