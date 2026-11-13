# Local authentication overlay — DRAFT, nhóm 3, 13/11/2026

Overlay revision: `local-auth-draft.2`; thay bản local 8 giờ/fixed-user trước nhóm 3. Owner: Nguyễn Tài Đức. Chỉ dành cho phát triển loopback, không phải public contract release, Cognito flow hoặc JWT giả. Original bundle `0.1.0-draft.1` và D14 giữ nguyên DRAFT. [Phạm vi, kiểm thử, nghiệm thu và công việc AWS còn lại](GROUP-03-AUTH-AND-AUTHORIZATION.md).

## Bật và xác thực

Chỉ `APP_ENV=local|test`, host loopback, `PERSISTENCE_ENABLED=1`, `LOCAL_AUTH_ENABLED=1`; `scripts/dev-local-api` bật hai flag cuối. FE đi qua Vite proxy cùng origin; mọi route dưới đây cần đúng một `X-Local-Client: browser`. Origin nếu có phải nằm trong allowlist. Không mở CORS preflight cho custom auth header. Authenticated rows cần `Authorization: Bearer <access_token>`, không lấy identity/role từ body hoặc cookie browser tự khai.

Mutation body JSON object, chỉ nhận đúng fields liệt kê; endpoint không cần field nhận `{}` hoặc không body. Body tối đa 4096 bytes. Success `{data,request_id}`; error envelope gốc được validate. Không trả password/hash/mã OTP/refresh token trong API response. Mọi response no-store. Các route là **local overlay mới/hiện có**, không ngầm tuyên bố 50 public operations gốc đã triển khai.

| Method/path dưới `/local-auth/` | Quyền | Body | Data thành công |
| --- | --- | --- | --- |
| POST `register` | Anonymous | email, password, display_name | 201 AuthData |
| POST `login` | Anonymous | email, password | 200 AuthData |
| GET `session` | HttpOnly cookie | Không | 200 AuthData; rotate refresh |
| POST `refresh` | HttpOnly cookie | `{}` | 200 AuthData; rotate refresh |
| POST `logout` | Cookie, idempotent khi không có cookie | `{}` | 200 `{signed_out:true}` |
| POST `logout-all` | Bearer | `{}` | 200 `{signed_out:true}` |
| POST `verification/request` | Bearer | `{}` | 200 Accepted |
| POST `verification/confirm` | Bearer | code | 200 Profile |
| POST `password/forgot` | Anonymous | email | 200 Accepted, kể cả email không tồn tại |
| POST `password/reset` | Anonymous | email, code, password mới | 200 `{signed_out:true}` |
| POST `password/change` | Bearer | current_password, password mới | 200 `{signed_out:true}` |
| POST `email/request` | Bearer + password hiện tại | email mới, password | 200 Accepted |
| POST `email/confirm` | Bearer | code | 200 `{signed_out:true}` |
| GET `admin/users` | Admin + users.read | Query limit 1…100 mặc định 20, cursor optional | 200 Page<Profile> |
| POST `admin/status` | Admin + users.status.write | user_id, status active/suspended, expected_version integer, reason 3…300 | 200 Profile |
| GET `admin/audit` | Admin + audit.read | Query cursor optional; page 50 | 200 Page<AuditEvent> |

Tổng **16 method/path** local. Các Admin route local dùng Profile để không bịa created_at lịch sử cho account cũ; **không đồng nhất** với `/api/v1/admin/users`/AdminUser gốc. Public Admin business operations vẫn chưa có handlers. Search/filter tài khoản được FE áp dụng lên danh sách đã phân trang; local endpoint chỉ limit/cursor. Khi có backend Admin chuẩn cần adapter consumer riêng.

Schema/validation:

- Email normalized trim + lowercase, tối đa 254 ký tự; password 8…128; display_name trim 1…60; code chuỗi đúng 8 chữ số.
- AuthData: access_token nonempty opaque string, expires_at_s integer epoch seconds, auth_provider const `local_password`, profile theo [Profile gốc](../contracts/schemas/application.schema.json). Refresh token chỉ được set-cookie.
- Accepted: `{accepted:true,delivery_mode:"local_mailbox"}`. Nghĩa là tiếp nhận yêu cầu, không khẳng định email tồn tại hoặc thư internet đã gửi.
- Page: `{items:[...],next_cursor:string|null}`. Profile và AuditEvent tái dùng schema gốc qua persistence catalog; local Admin không thêm/sửa field vào DTO gốc.
- 400 VALIDATION_ERROR: field sai, mã sai/hết hạn/đã dùng/quá 5 lần, mật khẩu hiện tại sai. 401 AUTH_REQUIRED/TOKEN_EXPIRED: thiếu/sai/hết hạn/revoked token hoặc cookie. 403 FORBIDDEN: tài khoản không active hoặc thiếu role/permission; details.account_status chỉ có khi tài khoản không active/missing. 403 USER_NOT_VERIFIED: local Admin chưa xác nhận.
- 409 VERSION_CONFLICT: email trùng, CAS race/profile stale. 409 SELF_SUSPEND_FORBIDDEN/LAST_ADMIN_PROTECTED: guard quản trị. 409 USER_NOT_VERIFIED: không activate bypass trạng thái pending. 404 RESOURCE_NOT_FOUND: không có local account theo target. 429 RATE_LIMITED: throttle/cooldown/lockout. 503 PROVIDER_UNAVAILABLE: DB hoặc mailbox lỗi. Unexpected exception dùng 500 INTERNAL_ERROR, không echo secret.
- Khi refresh hoặc challenge CAS tranh chấp, trả 409; không tự phát token/code thành công. `email/confirm` transaction không thành công thì profile/email/code không bị consume một phần.

## Storage nội bộ và tương thích

Không đổi table/GSI, không migration/reset. Tất cả keys bí mật dưới `LOCAL_AUTH#` để `db-admin inspect` tiếp tục ẩn. `db-admin export` là backup private có hashes, không public/commit.

| Namespace | Nội dung |
| --- | --- |
| ACCOUNT / SHA256(email) | user_id, salt, scrypt hash, algorithm, revision; auth_epoch, failed_logins, locked_until_s; account mới có created_at/last_sign_in_at; tài khoản cũ không bịa created_at |
| SESSION / SHA256(access) | user_id, family_id, auth_epoch, expires_at_s, revision; legacy session có thể thiếu family/epoch |
| REFRESH / SHA256(refresh) | user_id, family_id, auth_epoch, expires_at_s, revision; token cũ xóa cùng transaction khi rotate |
| FAMILY / SHA256(family UUID) | user_id, auth_epoch, absolute expires_at_s, revision; delete để revoke family |
| CHALLENGE / SHA256(user_id:purpose) | salt, HMAC code, target email, auth_epoch, attempts, sent/expiry, revision; purpose verify_email/reset_password/change_email |
| ADMIN_REGISTRY / active | Active Admin user_ids, revision; conditional guard giữ lại Admin cuối cùng |

Profile không lưu credential, vẫn original schema; role/permission/status chỉ service quản trị thay đổi. Audit nằm ở system scope `local-auth-audit`, original AuditEvent, transaction cùng thay đổi. Chỉ ghi succeeded của mutation đã commit; denied/auth-attempt audit đầy đủ còn là việc production sau.

Cookie `lingualive_local_session`: HttpOnly, SameSite Strict, path `/local-auth`, max-age 24 giờ; không Secure vì loopback HTTP. Access sống tối đa 15 phút; refresh/family tối đa 24 giờ từ login/register, không kéo dài bằng refresh. Chỉ hashes lưu DB; expiry kiểm mỗi request, không phụ thuộc native TTL cleanup. Mọi session bị vô hiệu khi auth_epoch thay đổi. Token/mật khẩu không lưu localStorage/sessionStorage. Cookie cũ còn hạn được upgrade; các API response AuthData cũ vẫn tương thích field-level nhưng TTL/cookie semantics đã đổi. Không chấp nhận access token mới làm refresh cookie.

Mailbox tại `.local-data/mailbox` và HMAC key `.local-data/auth/cursor.key` trong module backend, ignored/private. File thư 0600 có mã để chủ máy test; không phải email provider, không có public endpoint đọc mã. Đọc bằng `scripts/auth-admin mailbox --email ...`. Mã được consume atomically, nhưng ghi file mailbox không phải distributed transaction với DB; lỗi IO cố gắng xóa challenge rồi trả 503. Chưa có TTL cleanup mailbox/session hoặc retry delivery worker.

## Quan hệ với Cognito

11 learning operations giữ `/api/v1`, snake_case, resource UUID, CAS/version/idempotency, error envelope và schema gốc. Identity local là `local:<UUID>`, không giả làm Cognito sub. Sau này cần auth adapter Cognito, verifier và mapping ownership. D14 vẫn ưu tiên xem xét flow SDK/SRP giữ form; PKCE là lựa chọn khác cần xác nhận, không phải việc đã triển khai ở đây. Không copy password hashes hoặc mặc định local email_verified là chứng cứ xác minh email thật trên cloud.
