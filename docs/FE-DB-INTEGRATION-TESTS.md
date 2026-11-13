# Nối giao diện với database local — 13/11/2026

**Sau nhóm 4–5:** Solo đã có source/frame/job/result thật, overlay theo kích thước nội dung và đọc lại OCR ở History. [Các ca thử hiện tại](GROUP-05-OCR-PIPELINE.md). Nhận xét “video chỉ preview/OCR chưa lưu” bên dưới là mốc tích hợp trước nhóm OCR; không còn áp dụng cho thao tác Nhận dạng chữ. Video nguyên file chưa upload/record; reading/dictionary/translation vẫn chưa kết nối.

**Sau nhóm 3:** xem [ca thử tài khoản/Admin và kết quả mới](GROUP-03-AUTH-AND-AUTHORIZATION.md). Mailbox/refresh/đổi thông tin bảo mật và quản lý tài khoản Admin local đã triển khai. Các số 94 tests và giới hạn Auth/Admin bên dưới thuộc mốc trước nhóm 3.

**Cập nhật giao diện theo yêu cầu người dùng:** bỏ thông báo kết nối ở trang đăng nhập và sảnh/phòng học; bỏ menu/modal “Xem dữ liệu đã lưu”. Chỉ thay phần trình bày, giữ API client, hook và toàn bộ luồng lưu dữ liệu. Vòng tiến độ tăng từ 60 lên 88 px, bố trí lại chữ bên trong; danh sách từ có layout riêng với chữ từ 25 px, cách đọc 14 px, nghĩa 16 px, trạng thái tiếng Việt, nút nghe/xóa và responsive. Nội dung hồ sơ/ôn tập/lịch sử dùng ngôn ngữ người học, không hiện thuật ngữ database. Các kết quả 94 tests bên dưới là mốc tích hợp trước chỉnh UI; lượt chỉnh UI kiểm tra type/build, không chạy lại backend hoặc ghi thử vào DB.

Trạng thái: triển khai luồng học cá nhân local, chờ người dùng thao tác nghiệm thu UI. Giữ bố cục, ảnh nền và hiệu ứng hiện có. Không deploy, không Docker/AWS, không đổi dependencies/lockfile, không sửa OCR provider hoặc original public contract bundle.

**Kiểm tra lượt chỉnh UI:** TypeScript (`--ignoreDeprecations 5.0`), Vite build và `git diff --check` đạt exit 0. Web cùng các module/CSS mới trả HTTP 200; health xác nhận database/auth local đang sẵn sàng. Không chạy browser DOM/ảnh chụp tự động trong lượt này.

## Đã nối

| Giao diện | API thực | Dữ liệu DB |
| --- | --- | --- |
| Đăng ký/đăng nhập/khôi phục/logout | `/local-auth/*` — [overlay DRAFT](LOCAL-AUTH-DRAFT.md) | Account hash, profile, session hash/expiry |
| Hồ sơ/cài đặt | GET/PATCH `/api/v1/me` | profile có version, timezone, learning_language |
| Lưu từ từ popup/video mẫu | POST/GET/DELETE `/api/v1/vocabulary` | word, reference, canonical uniqueness, idempotency |
| Ôn tập: đã nhớ/cần ôn | PATCH `/api/v1/vocabulary/{id}/review` | review_state + version |
| Học cá nhân/kết thúc/tiếp tục phiên đang học | POST/GET session, POST end | session + history index, cập nhật kết thúc bằng CAS |
| Lịch sử/thống kê | GET `/api/v1/history`, `/api/v1/stats` | query dữ liệu caller, không số giả |
| Thư viện → Từ đã lưu | GET `/api/v1/vocabulary` | Danh sách từ, cách đọc, nghĩa và trạng thái của tài khoản hiện tại |

Mặc định FE dùng `VITE_API_MODE=real`. `VITE_API_MODE=preview` là lựa chọn chủ động cho giao diện cũ, không tự fallback khi API lỗi. Đổi mode cần restart Vite. Preview có login/Admin minh họa riêng; đổi role preview không cấp quyền API. Email hồ sơ ở real mode là chỉ đọc.

Nghĩa từ vẫn từ catalog **mẫu** lấy từ chính `src/data/transcriptVocabulary.ts` và nhãn video hiện có, được lưu ở `shared/demo-vocabulary.json`. Chỉ lưu khi người dùng bấm; không auto seed danh sách từ. Entry prefix `sample:v1:`, meanings `origin=fixture`, occurrence=null. Không bịa OCR result_id/source_id hay gắn câu mẫu vào kết quả OCR thật. Từ ngoài catalog/lexicon chưa kết nối trả lỗi. Tách rõ thao tác ghi DB thật với nội dung từ điển mẫu.

Phiên học lưu metadata/thời điểm, chưa upload/lưu video/frame. Chưa tính saved_words_count theo phiên vì chưa có OCR occurrences; trường này null, UI hiện `—`. Chưa tính streak; không dùng các số 12/124/8.4 của preview. Chưa đồng bộ phòng nhóm/Chime/chat/shared vocabulary/recording/Admin; real mode báo chưa kết nối khi tạo/join phòng, không tạo phòng giả thành công.

## Chạy lại

Từ root repo, các runtime/dependency đã cài:

```bash
# Terminal 1, chỉ chạy nếu DB chưa chạy
./scripts/dev-db

# Terminal 2, init lặp lại an toàn; không reset DB
./scripts/db-admin init
./scripts/dev-local-api

# Terminal 3, chỉ chạy nếu Vite chưa chạy
pnpm dev --host 127.0.0.1 --port 8443
```

Mở `http://127.0.0.1:8443`, dùng cùng hostname để cookie nhất quán. Nếu API foundation cũ đang chiếm 8081, dừng process do bạn quản lý rồi chạy `dev-local-api`; không start bản thứ hai. Vite có proxy `/api` và `/local-auth` tới 8081. Vite preview/production hosting không tự có proxy này; khi deploy phải cấu hình reverse proxy và auth phù hợp, chưa làm trong task này.

`/health/live` 200 cho process; `/health/ready` vẫn 503 trung thực vì Cognito/OCR/realtime/cloud chưa đủ. Khi local integration bật, details báo 11 operations và authentication=local_password_ready; không dùng full readiness để kết luận luồng local hỏng.

## Các ca bạn thao tác trên giao diện

Các ca dưới đây là **MANUAL_PENDING**, chưa báo browser DOM automation pass. Nên dùng hai profile/cửa sổ riêng cho hai tài khoản và mở DevTools → Network để thấy request/status. Không gửi password/token trong ảnh hoặc log bàn giao.

| Mã | Thao tác | Kỳ vọng trên UI / dữ liệu |
| --- | --- | --- |
| UI-01 | Đăng ký miễn phí → điền tên, email của bạn, mật khẩu >=8 ký tự, xác nhận | Vào sảnh sau API xác nhận. Không có sẵn 3 từ; DB tạo account/profile/session. Email chưa xác minh. |
| UI-02 | Avatar → Hồ sơ → đổi tên thành `Đức test DB` → Lưu → Hoàn tất → reload | Tên còn nguyên; GET me đọc DB; version tăng. |
| UI-03 | Avatar → Cài đặt → đổi timezone/tiếng Nhật hoặc Trung → Lưu → reload | Thiết lập còn nguyên. Email/role không sửa được từ form. |
| UI-04 | Học một mình → phiên âm mẫu → rê chuột/chạm `カフェ` hoặc `喫茶店` → Lưu từ | Sidebar xuất hiện sau POST thành công; dữ liệu mẫu được ghi thành word thật của tài khoản. |
| UI-05 | Lưu lại cùng từ; reload rồi vào Thư viện | Vẫn một word_id, không nhân đôi. Lưu bằng API trùng có thể trả 200 thay vì 201. |
| UI-06 | Ôn tập từ đã lưu → Đã nhớ hoặc Cần ôn lại | Sau mỗi thẻ API PATCH thành công mới chuyển thẻ; reload/data viewer thấy `known`/`learning`, version tăng. |
| UI-07 | Kết thúc buổi học, hoặc chuyển từ phòng sang Lịch sử | Session status=ended, ended_at và duration có giá trị; không tuyên bố có recording. |
| UI-08 | Reload khi còn ở phòng → Lịch sử → phiên đang học → Tiếp tục | Tái dùng session_id đang active; không tự tạo lịch sử mới. Không có source video/stream tự khôi phục. |
| UI-09 | Thư viện → Xóa một từ → reload | Từ biến mất cả UI và DB. Word reference/unique guard được xóa; có thể lưu lại sau đó. |
| UI-10 | Thư viện → Từ đã lưu → tải lại trang; có thể đối chiếu bằng `./scripts/db-admin inspect` | Từ, cách đọc, nghĩa và trạng thái còn nguyên; menu avatar không còn mục xem dữ liệu. |
| UI-11 | Logout → thử sai mật khẩu → đăng nhập đúng | Sai trả 401; phiên cũ bị revoke; đúng giữ nguyên tên/từ/lịch sử. |
| UI-12 | Tài khoản B bằng browser profile riêng, mở thư viện/lịch sử | Không thấy dữ liệu A. Đổi UUID URL API không được truy cập dữ liệu A. |
| UI-13 | Dừng **API bạn đang quản lý**, thử lưu/xóa/sửa, rồi bật lại và tải lại trang | Hiện lỗi, không hiện thành công hoặc tự chuyển mock; dữ liệu chỉ thay đổi nếu server thực sự đã commit. |
| UI-14 | Hai tab A mở hồ sơ cùng version; tab 1 lưu, tab 2 lưu bản cũ | 409 VERSION_CONFLICT; tab 2 không ghi đè im lặng. Tải lại rồi sửa. |
| UI-15 | Tạo/join phòng, Google/Facebook | Hiển thị chưa kết nối/disabled; không báo có phòng thành công. Quên mật khẩu theo ca AUTH-UI-05 của nhóm 3, dùng mailbox local. |

Chuyển sang Thư viện/Lịch sử từ phòng kết thúc phiên hiện tại để có duration thật. Đóng tab/reload không bảo đảm gọi end; lịch sử giữ phiên active để tiếp tục/kết thúc chủ động. Session timeout/abandoned cleanup thuộc lifecycle tiếp theo.

## Xem DB trực tiếp

```bash
./scripts/db-admin check
./scripts/db-admin inspect
```

`inspect` query/scan maintenance local, decode payload JSON và ẩn auth/idempotency rows. Đọc raw DB chỉ dành cho owner máy; không phải API admin. File `application-backend/.local-data/db-view.ndjson` cũ là snapshot, không tự đổi khi bạn thao tác. Không dùng file đó làm bằng chứng live nếu chưa xuất bản mới. Các file `.local-data` vẫn bị ignore. `export` chỉ tạo file mới, không ghi đè; giữ backup chứa hashes ở chế độ private.

## Kiểm thử tự động và phạm vi bằng chứng

```bash
./scripts/test-api
node node_modules/typescript/bin/tsc --noEmit --ignoreDeprecations 5.0
node node_modules/vite/bin/vite.js build
```

Đã chạy 94 tests backend đạt exit 0: 79 tests nền tảng/persistence có sẵn + 15 tests tích hợp mới. Test mới dùng HTTP loopback và DynamoDB Local thật trong bảng `lingualive-test-learning-*`, đóng/xóa sau test. Auth/account/DTO là input synthetic cho test, không được seed vào bảng ứng dụng.

Trong đó một test chạy **chính** `src/api/learning.ts` bằng Node/TypeScript đã có, gọi HTTP server thật, kiểm 13 bước đăng ký/hồ sơ/lưu trùng/đọc/ôn/xóa/session/history/stats/restore/logout/login; kiểm trực tiếp DB còn hồ sơ và từ tương ứng. Cookie/timers là adapter Node, không phải mock API; **không phải browser DOM/UI click test**. Các test còn lại kiểm expiry/revocation, CSRF boundary, profile authority, CAS, hai user, pagination, concurrent duplicate, idempotency conflict và injected storage outage.

TypeScript config cũ đặt `ignoreDeprecations=6.0` trong khi compiler cài tại workspace cần `5.0`; lệnh đầu không override trả TS5103. Đã giữ config/dependency cũ và dùng override khi kiểm; type check và Vite build đạt exit 0. Không đổi schema/fixture để làm xanh test. Original contract vẫn DRAFT; startup xác minh bundle cũ nguyên vẹn, không tự phát hành v1.

## File thay đổi trong lượt tích hợp

Lượt chỉnh giao diện tiếp theo cập nhật `src/App.tsx`, `src/cinematic.css`, nội dung AccountPanels/ReviewCards và tài liệu này; thêm `src/components/SavedVocabulary.tsx` cùng CSS riêng. Component tiếp tục dùng `api.words`, callback xóa cũ và luồng ôn tập cũ; không sửa backend, DB, API client, media hooks, contract hoặc dữ liệu backup.

- Backend mới: `local_auth.py`, `learning.py`, `local_integration.py`, test `test_learning_integration.py`.
- Backend cập nhật: config flag, app registration/readiness, CLI operation counts, `db-admin inspect`, `.env.example`, README.
- FE mới: `src/api/learning.ts`, `src/hooks/useLearningApi.ts`.
- FE cập nhật: `App.tsx`, AccountPanels, ReviewCards, Vite proxy, root env example. Không sửa CSS/assets/hiệu ứng.
- Công cụ/dữ liệu mới: `scripts/dev-local-api`, `shared/demo-vocabulary.json`, `tools/integration/learning-client-check.mjs`.
- Tài liệu: file này, `LOCAL-AUTH-DRAFT.md`, bản cập nhật LOCAL-SETUP/ACCEPTANCE và báo cáo kiểm tra `fe-db-integration-results.json`.
