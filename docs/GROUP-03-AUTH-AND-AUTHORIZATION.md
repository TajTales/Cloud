# Nhóm 3 — Tài khoản, phiên đăng nhập và phân quyền

Ngày triển khai: 13/11/2026. Owner hiện tại: Nguyễn Tài Đức. Đây là **nhóm công việc thứ 3 trong lộ trình backend đang thực hiện**, tương ứng AU-01…AU-04/G1 của [kế hoạch gốc](TIEN-DO-VA-KE-HOACH-HOAN-THANH.md); không phải G3 từ điển của kế hoạch gốc.

Trạng thái: **LOCAL_IMPLEMENTED / MANUAL_ACCEPTANCE_PENDING**. Xác thực local có password/session/database thật, dùng hộp thư phát triển trên máy. **Cognito, gửi email ra ngoài, HTTP/WS auth trên AWS chưa triển khai/nghiệm thu**. Không đổi G1/AU-01 thành cloud-complete. Không gọi AWS, Docker, deploy, reset dữ liệu, cấp quyền cho tài khoản thật hoặc sửa OCR provider.

Public contract vẫn `0.1.0-draft.1`, DRAFT; bundle SHA-256 `bcfd39b6a2fd85d74cd5efd53e7a6bff753f60bf7e286246c27ef696c1c6bfd2`. Base HEAD khi làm: `84606206d7c32b1c110065fdcc915a3d8b2ad8c6`, cộng working tree chưa commit từ các nhóm trước và nhóm này. Không commit/push. Quyết định D14 không tự chuyển APPROVED hoặc tự đổi SRP thành PKCE. Giao thức local là [overlay DRAFT](LOCAL-AUTH-DRAFT.md), không phải Cognito JWT giả.

## Phạm vi đã triển khai

| Việc | Bằng chứng | Giới hạn |
| --- | --- | --- |
| Đăng ký, đăng nhập, scrypt, phục hồi dữ liệu | [LocalAuth](../application-backend/src/lingualive_api/local_auth.py), [HTTP integration](../application-backend/src/lingualive_api/local_integration.py) | `local:<UUID>`, không phải Cognito sub. Basic study vẫn cho tài khoản chưa xác nhận để giữ hành vi cũ; quyền Admin bắt buộc xác nhận |
| Xác nhận email, gửi lại mã, quên/đặt lại mật khẩu | [LocalAuth](../application-backend/src/lingualive_api/local_auth.py), [mailbox](../application-backend/src/lingualive_api/local_mail.py), [form](../src/components/AccountPanels.tsx) | Mailbox local không chứng minh sở hữu hộp thư email ngoài máy |
| Đổi mật khẩu, đổi email | Cùng service/form; yêu cầu mật khẩu hiện tại; email mới cần mã; đổi key account + profile trong transaction | Email chỉ đổi khi confirm thành công; uniqueness tranh chấp trả 409; không cho PATCH /me đổi email |
| Refresh/expiry/logout | [API client](../src/api/learning.ts), [hook](../src/hooks/useLearningApi.ts) | Access 15 phút, refresh tối đa 24 giờ tuyệt đối; token memory/cookie, không localStorage |
| Phân quyền tài khoản | Đọc roles/status từ profile DB mỗi lần verify; cấp quyền bằng [CLI](../application-backend/src/lingualive_api/auth_admin.py) | Không nhận roles/permissions từ signup/profile/browser preview |
| Quản lý tài khoản Admin | [service](../application-backend/src/lingualive_api/local_admin.py), [UI](../src/admin/LocalAdminWorkspace.tsx) | Local overlay chỉ danh sách tài khoản, khóa/mở khóa, audit. Các Admin API nghiệp vụ, phòng, system/OCR config chưa triển khai |
| Scope dữ liệu cá nhân/room | Repository và tests nhóm 2 tiếp tục chạy | Membership/host đã có ở tầng repository; chưa có room/meeting/WS chạy thật, không báo AU-03 realtime pass |
| Đồng bộ profile/settings | GET/PATCH /me, version/CAS, timezone/ngôn ngữ | Giữ UI hiện có. Tài khoản khác có dữ liệu khác |

## Kiểm soát phiên và mã xác nhận

- Password scrypt giữ nguyên tham số và hash tài khoản cũ. Không reset/migrate DB. Account thiếu `auth_epoch` được hiểu là 0; cookie phiên 8 giờ cũ còn hợp lệ được đổi sang phiên mới khi restore, không đổi user_id hoặc từ đã lưu. Cookie đã hết hạn cần đăng nhập lại.
- Bearer opaque 256 bit, chỉ lưu hash. Access 15 phút; refresh riêng trong HttpOnly/SameSite Strict cookie path `/local-auth`, không trả refresh token trong JSON. Refresh dùng CAS để token cũ không được dùng lại; session family hết hạn tuyệt đối sau 24 giờ, không kéo dài vô hạn bằng reload.
- Logout thu hồi family của phiên hiện tại. Đổi mật khẩu/reset/đổi email/logout-all/tăng giảm quyền/khóa hoặc mở khóa tăng `auth_epoch`, làm mọi access/refresh cũ mất hiệu lực. Mở khóa không hồi sinh token cũ.
- FE refresh single-flight, retry request tối đa một lần cho TOKEN_EXPIRED, giữ nguyên idempotency key/body. Không refresh cho lỗi mạng, không fallback sang mock. Web Locks tuần tự hóa cookie refresh giữa các tab trên browser hỗ trợ; browser thiếu Web Locks vẫn có CAS backend, có thể cần reload khi hai tab cùng refresh. Client từ chối đổi subject âm thầm khi tài khoản tab khác thay đổi.
- Khi phiên bị thu hồi/khóa được phát hiện qua request, hook xóa state/token và media hook dừng stream. Không có WS thật để đóng trong nhóm này. Logout vẫn thử thu hồi token khi end-session lỗi; lịch sử có thể còn active để xử lý sau. Nếu DB/API lỗi, UI báo chưa logout được, không hứa đã revoke.
- Mã 8 chữ số, hạn 10 phút, tối đa 5 lần nhập sai, resend cách ít nhất 60 giây. Lưu HMAC với secret riêng tại thư mục dữ liệu; mã không nằm trong DB/API/log request. Mã bị consume cùng transaction với thay đổi; sai purpose/hết hạn/đã dùng/auth_epoch cũ đều bị từ chối.
- Throttle process/IP 10 lần/phút cho register/login/forgot/reset, 60 cho mutation local khác; 5 sai mật khẩu khóa đăng nhập tài khoản 60 giây lưu DB. Reset mật khẩu đúng mã gỡ khóa đăng nhập. Đây là local controls, chưa phải WAF/distributed production rate limiting. Forgot trả cùng envelope khi email không tồn tại; không cam kết chống mọi timing side channel.
- Admin yêu cầu role + permission DB + active + email_verified. Khóa bản thân bị chặn. Active-admin registry cập nhật có CAS trong cùng transaction; không thể thu hồi Admin hoạt động cuối cùng. Ghi audit thành công cùng transaction trạng thái/quyền; lỗi lưu audit không được đổi tài khoản. Chưa có audit riêng cho mọi request bị từ chối hoặc auth attempts.

## Chạy và thao tác nghiệm thu

Từ root repo, chỉ chạy một instance mỗi port:

```bash
# Terminal 1: nếu DB chưa chạy
./scripts/dev-db
# Terminal 2
./scripts/dev-local-api
# Terminal 3: nếu Vite chưa chạy
pnpm dev --host 127.0.0.1 --port 8443
```

Mở `http://127.0.0.1:8443`. Dùng cùng hostname. Không cần Docker, AWS, SMTP, thư viện mới hay cài lại môi trường. `db-admin init` chỉ cần cho checkout/bảng mới, không reset bảng hiện tại. Readiness tổng thể vẫn 503 vì OCR/Cognito/realtime chưa kết nối; liveness phải 200.

| Ca | Thao tác | Kỳ vọng |
| --- | --- | --- |
| AUTH-UI-01 | Tài khoản cũ đăng nhập, reload, kiểm tra thư viện | Giữ user_id/từ/lịch sử, không tạo account demo |
| AUTH-UI-02 | Avatar → Hồ sơ → Xác nhận email → Yêu cầu mã | Chỉ thông báo mailbox thử; không nói đã gửi email ngoài máy |
| AUTH-UI-03 | Chạy lệnh mailbox bên dưới, nhập mã mới nhất `verify_email` | Profile email_verified=true; mã dùng lần hai bị từ chối |
| AUTH-UI-04 | Sai mã 5 lần; resend quá sớm; mã >10 phút | Bị chặn đúng; chờ resend rồi lấy thư mới, không đổi schema để bỏ lỗi |
| AUTH-UI-05 | Đăng xuất → Quên mật khẩu → email → mã `reset_password` → mật khẩu mới | Mật khẩu cũ bị từ chối; token/cookie cũ mất hiệu lực; từ/lịch sử vẫn còn |
| AUTH-UI-06 | Avatar → Cài đặt → Đổi mật khẩu | Kiểm mật khẩu cũ, sau thành công yêu cầu đăng nhập lại |
| AUTH-UI-07 | Cài đặt → Đổi email; thử sai mật khẩu/mã rồi nhập đúng mã `change_email` | Trước confirm email cũ còn nguyên; sau confirm email mới đăng nhập được cùng user_id; phiên cũ bị thu hồi |
| AUTH-UI-08 | Hai profile browser đăng nhập cùng tài khoản; chọn Đăng xuất mọi phiên | Request tiếp theo ở cả hai bị 401, về login. Không tuyên bố push logout tức thời khi tab không gửi request |
| AUTH-UI-09 | Để access gần hết 15 phút, thao tác thư viện/hồ sơ | Một refresh đồng thời trong mỗi client, tiếp tục thao tác; hết refresh tối đa 24 giờ cần login lại |
| AUTH-UI-10 | Cấp quyền bằng CLI cho tài khoản đã xác nhận, đăng nhập lại → avatar → Quản trị tài khoản | Có danh sách tài khoản DB thật; User thông thường không có menu/quyền API |
| AUTH-UI-11 | Admin khóa tài khoản B kèm lý do; B thao tác; mở lại B | B bị 403; mở lại phải đăng nhập mới; audit có lý do; bản thân/last Admin không thể bị khóa/thu hồi |
| AUTH-UI-12 | Dừng API do bạn quản lý rồi thử form; bật lại/tải lại | Lỗi rõ ràng, không mock success hoặc tạo token giả |

Đọc mã theo email của tài khoản bạn đang thử (thay địa chỉ ví dụ):

```bash
./scripts/auth-admin mailbox --email 'ban@example.com'
```

Mailbox được ghi tại `application-backend/.local-data/mailbox/`, file JSON 0600, thư mục 0700, chỉ CLI/file local đọc được, không có HTTP endpoint công khai mã. Các thư thử cũ chưa tự dọn; chỉ dùng mã thư đúng purpose mới nhất. Không commit/chia sẻ thư mục dữ liệu hoặc secret HMAC `application-backend/.local-data/auth/cursor.key`. Local OS owner có quyền đọc mã; vì vậy đây không phải chứng minh sở hữu email qua internet.

Cấp Admin **sau khi tài khoản đã tồn tại và đã xác nhận**:

```bash
./scripts/auth-admin grant-admin --email 'ban@example.com' --reason 'Chủ dự án cấp quyền quản trị local'
./scripts/auth-admin revoke-admin --email 'admin-khac@example.com' --reason 'Thu hồi quyền theo phân công mới'
```

Không tự chọn tài khoản thật để cấp Admin, không có mật khẩu Admin mặc định. CLI có quyền của chủ máy, không phải public API. Cấp/thu hồi quyền buộc đăng nhập lại. `revoke-admin` cuối cùng sẽ bị từ chối; tạo/xác nhận/cấp Admin thứ hai nếu cần chuyển quyền.

## Kiểm thử tự động và bằng chứng

Lệnh chính: `./scripts/test-api` (DB local phải chạy). Tạo/xóa riêng `lingualive-test-*`; tài khoản, OTP, dữ liệu trong tests là synthetic và mailbox tạm. Không seed bảng ứng dụng. Các test API/client thực sự chạy HTTP + DynamoDB; không dùng fake token issuer trong integration.

- [Auth integration tests](../application-backend/tests/test_auth_integration.py): confirmation một lần, expiry/cooldown/attempts, reset/change password, email change, logout/family/all, legacy upgrade, role escalation, Admin lock/unlock/version/audit/last-admin/concurrency, mailbox failure, account lockout, CLI và FE consumer.
- [FE auth harness](../tools/integration/auth-client-check.mjs): client TypeScript production, 6 kiểm tra qua HTTP thật, gồm single-flight refresh/restore và không loop khi revoke. Điều chỉnh đồng hồ client để kích hoạt refresh, không giả lập response/token.
- 94 test cũ về foundation/persistence/learning tiếp tục chạy. Browser DOM, bố cục và thao tác trực tiếp trong bảng trên vẫn **MANUAL_PENDING**; Node client harness không phải browser UI test.
- Kết quả lệnh/exit/count tại [bản ghi nhóm 3](group03-results.json). Lượt phát triển đầu có lỗi test đọc cookie bằng path `/` thay vì `/local-auth/session`, đã sửa đúng path; TypeScript bắt nhánh so sánh `session` không còn khả thi, đã bỏ nhánh thừa. Không nới assertions/schema hoặc giấu failure.
- Lượt cuối: **114/114 tests, exit 0** (94 regression + 20 nhóm 3); TypeScript, Vite build và diff-check exit 0. Smoke web 8443 HTTP 200; API liveness alive; `/local-auth/session` và `/api/v1/me` qua Vite trả đúng 401 khi chưa có cookie/token. Smoke không tạo tài khoản/từ thử trong DB ứng dụng. Đã chạy DB/API/Vite local cho người dùng thử; chưa điều khiển browser DOM.

## Còn lại trước nghiệm thu AWS/production

1. Xác nhận D14: flow/SDK Cognito giữ form (SRP/challenges theo draft A) hoặc chọn rõ Managed Login/PKCE; user pool, region, public client, callback/logout nếu cần, chính sách token/refresh/BFF cookie. Không lấy cookie policy local làm quyết định cloud APPROVED.
2. Implement Cognito adapter + JWT verifier bằng thư viện kiểm chứng, signature/JWKS/issuer/client_id/token_use/expiry, account-state/revocation; kiểm thử với pool thật. Adapter hiện tại chỉ LocalAuth/Unconfigured, **chưa có Cognito verifier dùng được**.
3. Thay mailbox bằng cơ chế xác nhận/reset của Cognito theo flow đã chọn; kiểm tra email thật, resend/throttle, bounced mail, đổi email. Không dựng hệ gửi mail thứ hai song song Cognito khi chưa thống nhất.
4. Lập mapping `local:<UUID>` → Cognito sub và chuyển ownership có kiểm tra. Không copy scrypt hash sang Cognito, không tự đổi user_id làm mất liên kết dữ liệu.
5. Khi room/realtime triển khai: HTTP/WS ticket auth, host/member/closed room/reconnect/revocation; các tests repository hiện tại chưa chứng minh WS hoặc Chime thật.
6. HTTPS/Secure cookie và domain/CORS/CSRF production, secret management, distributed throttle, cleanup/retention sessions/mailbox/audit, monitoring; public business Admin DTO/API hoàn chỉnh. Legacy account không có created_at lịch sử không được bịa ngày để khớp AdminUser DTO.

Đủ để tiếp tục phát triển nghiệp vụ/OCR trên môi trường local và nghiệm thu thủ công tài khoản. Chưa đủ để công bố hoàn thành phần Cognito/WS/cloud của nhóm xác thực theo toàn bộ kế hoạch ban đầu.
