# CT-03 — Ownership và ranh giới module

**DRAFT — ready_for_review, 11/11/2026.** Bảng này đề xuất người giao việc/review và ranh giới cho Codex, chưa là xác nhận của cả ba thành viên. Quyền và phạm vi trong nhiệm vụ cụ thể của người dùng vẫn được ưu tiên; ownership không tự tạo thêm thủ tục xin phép cho công việc đã được giao.

Đọc cùng [Git workflow](GIT-WORKFLOW.md), [local setup](LOCAL-SETUP.md), [CT-01](G0-CURRENT-STATE.md) và [CT-02](../contracts/README.md). Không có CODEOWNERS được tạo vì GitHub usernames chưa được xác nhận. Tên owner của remote không đủ để suy ra tài khoản GitHub của từng người.

## 1. Workspace thực tế

Root Git hiện tại chứa frontend React và thư mục OCR đã import; không tìm thấy nested `.git`/submodule riêng trong thư mục con. App backend/worker/lexicon riêng và repo AWS nếu nhóm đã làm ở nơi khác là **NOT_ACCESSIBLE**, không kết luận chưa phát triển.

```text
Cloud.git / main @ 81be4b4
├── src/                         React UI, admin, components, data, media hook
├── public/, third_party/yomitan/ renderer snapshot và assets/notice
├── package.json, pnpm-lock.yaml, .mise.toml, tsconfig.json, vite.config.ts
├── .figma/make/                 công cụ chạy/cài/deploy do scaffold cung cấp
├── meikipop-ocr-server/         Python OCR, providers, static demo, CLI tests,
│                               Dockerfile/Compose/Nginx/systemd
├── contracts/                  CT-01 decisions; CT-02 DRAFT 0.1.0-draft.1
├── docs/                       kế hoạch/audit/integration/ảnh kiểm tra
└── .env.example                template CT-03; không phải config đang hoạt động
```

CT-03 không di chuyển code, tạo repo backend giả hoặc đổi thành monorepo. Nếu backend/OCR được quản lý ở repo riêng, owner cung cấp URL/path/branch/SHA và README trước; giữ từng repo và ghép qua contract/môi trường. Không copy một repo khác vào đây chỉ để khớp sơ đồ tài liệu.

## 2. Ownership matrix

| Người | Module/phạm vi hiện có | Phần tích hợp tương lai được đề xuất | Review phối hợp |
| --- | --- | --- | --- |
| **Nguyễn Tài Đức** | `src/**`, `public/**`, `index.html`, CSS/UI, media hooks, Yomitan web adapter, `docs/review-assets/**` | API/auth/Chime/lexicon clients phía browser, capture/overlay, integration harness, web build; giữ UI đã được chấp nhận | Hoàng Bảo review auth/API/media contract; Bảo Anh review text/box/offset/lexicon |
| **Nguyễn Hoàng Bảo** | Chưa có app backend/IaC được xác minh trong workspace; chủ public API/ownership model của CT-02 | App backend, auth, sessions/rooms/membership/jobs API, storage helpers, AWS/IAM/network/Chime backend/Gateway; path/repo phải được cung cấp | Đức review consumer và integration; Bảo Anh review worker/storage/result interface |
| **Trần Nguyên Bảo Anh** | `meikipop-ocr-server/src/**`, raw provider/interface/postprocessing, static OCR demo, `test_server.py`, `pyproject.toml`, `MANIFEST.in` | OCR worker, readiness/concurrency/benchmark/model packaging, dictionary/tokenizer/translation adapters và OCR text writer theo interface chung | Hoàng Bảo review app/storage/job/infra boundary; Đức review bbox/Unicode/UI mapping |
| **Đức điều phối; Hoàng Bảo + Bảo Anh cùng review** | `contracts/**`, docs kiến trúc/kế hoạch/ownership/local setup | Contract version/bundle, cross-repo integration record, nghiệm thu chéo | Chủ schema và consumer liên quan duyệt nội dung; Đức không duyệt thay owner |

Phân công gốc theo PDF được giữ. Dictionary/lexicon, Admin và review là phần phân công bổ sung dạng đề xuất từ kế hoạch, chưa tự coi là phân công đã được nhóm xác nhận.

## 3. Các file cần một người viết tại một thời điểm

| File/nhóm file | Người điều phối thay đổi | Nguyên tắc |
| --- | --- | --- |
| `src/App.tsx`, entry/global CSS | Đức | Hoàng Bảo/Bảo Anh cung cấp DTO/fixture/interface, không cùng sửa UI trên ba nhánh để “nối hộ” |
| `contracts/openapi.yaml`, application/realtime schema, AsyncAPI | Hoàng Bảo chủ HTTP/WS; Đức điều phối | Một PR contract tại một thời điểm; không mỗi AI tự đặt endpoint/field |
| Raw OCR và lexicon schema | Bảo Anh | Consumer review trước thay required/enum/box/offset; giữ raw shape hiện hữu nếu chưa có migration/adapter |
| `contracts/contract-version.json`, catalog, fixtures manifest, CHANGELOG, docs đã nằm trong bundle | Đức tổng hợp sau review chủ schema | Thay bất kỳ file thuộc bundle phải cập nhật version/hash đồng bộ; không sửa hash chỉ để che lỗi validator |
| `package.json`, `pnpm-lock.yaml`, `.mise.toml`, `tsconfig.json`, `vite.config.ts` | Đức; Hoàng Bảo review môi trường/API | Task runtime/proxy riêng; không nâng dependency hoặc sửa config ngoài task để test pass |
| OCR Docker/Compose/Nginx/systemd và `.env.example` OCR | Bảo Anh container/model; Hoàng Bảo network/deploy | Phân rõ config ứng dụng với infra; không tự deploy hoặc đổi provider khi chỉ sửa docs |
| `.figma/make/**` | Đức, đối chiếu công cụ nền tảng | Không sửa managed scripts để tiện một máy; task cần nêu tác động install/restart/deploy |
| `.gitignore`, env templates | Đức root; Bảo Anh OCR; Hoàng Bảo backend proposal | Chỉ template đã kiểm tra không secret được theo dõi; env local/private vẫn ignored |

Đức ghi nhận một owner đang viết file chung trong mô tả task/PR hoặc tracker nhóm đã chọn. Các AI không tự cùng sửa bảng ownership để “giành chỗ”. Nếu hai task đều cần App.tsx hoặc cùng schema, giao một task tích hợp chung hoặc làm theo thứ tự; mỗi bên bàn giao module/fixture trước.

## 4. Ai duyệt contract?

| Loại thay đổi | Chủ review nội dung | Consumer cần review |
| --- | --- | --- |
| HTTP/auth/room/storage/Admin | Hoàng Bảo | Đức; Bảo Anh khi ảnh hưởng job/result/worker |
| Raw OCR/public result/geometry | Bảo Anh + Hoàng Bảo ở boundary | Đức overlay/client |
| Lexicon/Unicode/POS/dictionary identity | Bảo Anh | Đức renderer/save; Hoàng Bảo route/cache/persistence |
| WS/ticket/reconnect/Chime chat | Hoàng Bảo | Đức client; Bảo Anh notifier/result |
| Quyết định nền tảng, freeze v1, breaking change về auth/transport/ID/unit/offset/state | Cả ba xác nhận; Đức ghi nhận và tích hợp | Cả ba |

Người viết PR không tự làm reviewer duy nhất. Sau khi nhóm chốt workflow, PR thường cần ít nhất một reviewer khác tác giả thuộc các bên trên. Chưa có branch protection/required review rule được cấu hình tự động trong CT-03.

## 5. Ranh giới dữ liệu và thao tác

- Frontend dùng public application contract; không mở đường gọi OCR nội bộ để vượt auth/room/jobs. Role preview/localStorage không cấp quyền thật.
- Worker/provider không tự quản lý user/room hoặc tạo schema DynamoDB/S3 prefix riêng. Hoàng Bảo cung cấp storage/job interface; Bảo Anh dùng và kiểm thử interface đó.
- Không đặt model/dictionary corpus nặng, dependencies hoặc credentials vào Git chỉ để một máy chạy được. Ghi version/checksum/quyền dùng và cách cấp asset trong tài liệu của module khi thực sự triển khai.
- Snapshot Yomitan là mã vendor; giữ manifest/notice/hash và mô tả patch. Không nâng vendor ở PR nối API không liên quan.
- Sửa docs không cấp quyền sửa server/UI; sửa module không cấp quyền đổi contract/lockfile/infra. Ngược lại, nếu task hiện tại đã cho phép thay interface, AI thực hiện trong phạm vi đó và ghi rõ thay đổi cần review, không xin lại quyền chỉ vì bảng này là hướng dẫn.

## 6. Mẫu giao task cho Codex

```text
Task ID: <OC-02 / AU-03 / ...>
Người giao/owner: <tên>
Repo + working directory: <path thực tế>
Branch + integrated base SHA: <full SHA đã được nhóm ghi nhận>
Contract version/status/bundle SHA-256: <đúng contract-version.json>
Contract commit SHA: <full SHA hoặc null nếu draft chưa commit>
Consumer/producer liên quan: <tên, repo, version>
Được sửa: <danh sách module/file cụ thể>
Không nằm trong task: <UI/contract/provider/infra/lockfile khác>
File chung đã giao ai viết: <file, owner, PR/task>
Input/fixtures: <schema pointers và fixture paths>
Commands và acceptance: <check phù hợp, có failure/retry khi cần>
Môi trường: <mock/real/dummy, URLs, runtime; không gửi secret>
Đầu ra: diff, test log/exit code, version/env/migration nếu có, phần còn thiếu.
Nếu contract thiếu: ghi đúng điểm thiếu; tiếp tục phần độc lập,
không tự tạo fake token/API hoặc đổi field để tuyên bố tích hợp xong.
```

GitHub usernames, backend/worker repo paths, integrated base đầu tiên và quyền merge phải được nhóm xác nhận. Khi chưa có usernames, bảng này là nguồn phân công đề xuất; không thêm CODEOWNERS với tên người dùng giả.
