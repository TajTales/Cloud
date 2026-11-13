# Nhóm 1 — Nền tảng backend local

**Ghi chú 13/11/2026:** nhóm 2 đã bổ sung [database/object storage local](GROUP-02-DATABASE-AND-STORAGE.md). Báo cáo nhóm 1 và số test 32/34 dưới đây là snapshot lúc kết thúc nhóm 1; lock/runtime/test hiện tại theo báo cáo nhóm 2. `scripts/test-api` hiện bao gồm storage tests nên cần DynamoDB Local chạy.

**12/11/2026 — hoàn thành phạm vi nền tảng local, sẵn sàng làm nhóm 2.** Backend chạy trực tiếp bằng Python 3.12/aiohttp, không cần cài/chạy Docker hoặc thao tác AWS. Không phải nghiệm thu toàn bộ backend nghiệp vụ hay cloud. Chủ dự án hiện là người thực hiện/xác nhận toàn bộ theo chỉ đạo mới; giao diện và các quy ước API/schema từ giai đoạn ba người được giữ.

## 1. Đã thực hiện

| Việc nhóm 1 | Kết quả |
| --- | --- |
| Chọn runtime và tạo module | `application-backend/`, Python 3.12.16/aiohttp 3.14.5, separate venv, 18 runtime dependency versions được pin |
| App startup/config | Env có kiểm tra, bind loopback mặc định 8081, `--check` không mở socket; không cần credentials/cloud/model |
| Xử lý HTTP chung | Request ID, JSON strict, body limit, lỗi có envelope đúng schema, CORS allowlist, log không chứa body/token/query/traceback |
| Adapter theo contract | Đọc original OpenAPI/JSON Schema, kiểm bundle SHA, params/body/response, register handler theo operationId; response sai bị chặn |
| Boundary xác thực | Chỉ nhận identity từ verifier; thiếu token 401, verifier chưa cấu hình 503, có kiểm role Admin. Chưa có Cognito verifier/token issuer |
| Governance một người | Thêm `contracts/approval-policy.json`; CT-04 đọc required approvers/evidence từ policy, không còn bắt buộc ba người trong checkout hiện tại |
| Test và chạy trực tiếp | 32 test backend đạt, 26 Python + 8 Node test QA đạt; standalone process HTTP smoke đạt đúng trạng thái |
| Hướng dẫn | Backend README, env example, `scripts/dev-api`, `scripts/test-api`, cập nhật docs local/ownership/workflow/testing |

Quy ước được tiếp tục dùng: `/api/v1`, JSON snake_case, `{data, request_id}` / error envelope, UTC/ms, UUID tài nguyên và opaque Cognito/AWS identities, raw OCR không đổi, Unicode code point offsets, HTTP/S3 + jobs và WS manifest theo nhánh draft hiện hữu. Python 3.12/aiohttp là phương án D07 được chọn cho implementation local trong task này. Không tự bỏ User/Admin, Nhật/Trung, Group, recording hoặc đổi luồng thành Supabase/Jitsi.

## 2. Cách chạy hiện tại

Từ root repo, venv đã được chuẩn bị ở `application-backend/.venv`:

```bash
./scripts/dev-api --check
./scripts/test-api
./scripts/dev-api
```

Nếu API đã chạy tại 8081 thì không chạy thêm bản thứ hai. Dùng Ctrl+C ở terminal quản lý service để dừng, hoặc chọn `APP_PORT=8082 ./scripts/dev-api` cho một lần thử riêng. Không động Vite preview đang chạy ở 8443.

```bash
curl -i http://127.0.0.1:8081/health/live
curl -i http://127.0.0.1:8081/health/ready
curl -i http://127.0.0.1:8081/api/v1/me
```

Kỳ vọng: health/live 200, health/ready 503, API thiếu token 401. Một chuỗi Bearer bất kỳ trả 503 vì verifier chưa cấu hình, không làm đăng nhập thành công. Default CLI không có business handler hoặc fixture fallback. Hai health routes là endpoints vận hành local ngoài `/api/v1`, không phải thay đổi raw OCR/public business schema.

Config, tạo venv trên máy khác, giới hạn runtime và cách đăng ký handler: [backend README](../application-backend/README.md). `.env.example` chỉ là mẫu, không tự load dotenv. Không cần Postman/Java/Docker/AWS để chạy nhóm 1.

## 3. Contract và phê duyệt

- Original package vẫn **`0.1.0-draft.1`, DRAFT**, cùng bundle SHA `bcfd39b6a2fd85d74cd5efd53e7a6bff753f60bf7e286246c27ef696c1c6bfd2`; **159 file có hash được giữ nguyên**.
- Không sửa `contracts/decisions.md`, OpenAPI, AsyncAPI, schemas, fixtures cũ, catalog/version/report CT-02 hoặc guide thuộc bundle. Đây là snapshot của giai đoạn ba người; các câu nói chưa có app backend trong snapshot mô tả thời điểm đó.
- Policy mới chỉ thay cơ chế xác nhận sang **Nguyễn Tài Đức** có evidence, không ký thay hai người còn lại và không tự phát hành v1. Gate report ghi thêm policy ID/hash để thấy chính sách đang dùng.
- Policy hiện chưa thuộc bundle cũ. Release approved tiếp theo phải version/hash/pin policy và fixtures supplement đầy đủ, kèm contract commit SHA thật. Không tái tính hash release cũ để che thay đổi. `approved_by` cũ vẫn rỗng, `contract_commit_sha` vẫn null.
- Vì vậy default contract validation và mock CT-04 vẫn trả **2 / PENDING_APPROVAL**. Local foundation được xây theo task đã giao trên draft; đây không phải approved conformance hoặc integrated cloud.

## 4. Các file tạo/sửa

Tạo:

- `application-backend/pyproject.toml`, `requirements.lock`, `.gitignore`, `.env.example`, `README.md`.
- `application-backend/src/lingualive_api/{__init__,__main__,app,auth,config,contracts,errors}.py`.
- `application-backend/tests/test_foundation.py`.
- `scripts/dev-api`, `scripts/test-api`.
- `contracts/approval-policy.json`.
- `docs/GROUP-01-BACKEND-FOUNDATION.md`, `docs/group01-results.json`.

Sửa có kiểm soát:

- `tools/contract-testing/contracts_core.py`, `validate.py`, `tests/test_contract_tools.py`, `requirements.txt`: đọc/test policy, đưa hash policy vào report và yêu cầu format validators; giữ mọi schema/fixture gate khác.
- `docs/OWNERSHIP.md`, `GIT-WORKFLOW.md`, `LOCAL-SETUP.md`: thêm quy định hiện hành một người/backend local; phần CT-03 cũ giữ làm lịch sử.
- `docs/CONTRACT-TESTING.md`, `ACCEPTANCE.md`: chỉ rõ policy hiện tại và phân biệt kết quả lịch sử CT-04 với nhóm 1.
- `docs/env/application.env.example`: trỏ tới mẫu backend thật, đánh dấu proposal AWS cũ là lịch sử.

Venv là dependency cục bộ bị ignore, không phải source bàn giao. Không sửa UI/frontend tooling/lockfile, raw OCR/provider, Yomitan, ảnh review-assets, Docker files hoặc hạ tầng AWS. Không commit/push/PR/merge/migration.

## 5. Kiểm chứng thực tế

[Report máy đọc được](group01-results.json) lưu source SHA, commands/exit, runtime/dependency inventory, policy/version/bundle, số test, smoke responses và scope audit.

| Lệnh/kiểm tra | Kết quả |
| --- | --- |
| Tạo venv + pip install requirements.lock | Đạt trên Python 3.12.16; chỉ trong môi trường riêng |
| `./scripts/dev-api --check` | Exit 0; 50 declared operations, **0 implemented business operations** |
| `./scripts/test-api` | Exit 0; **32/32**, có HTTP thật trên loopback tạm |
| `application-backend/.venv/bin/python -m pip check` | Exit 0, dependencies không xung đột |
| `./scripts/validate-contracts --lint-draft` với CT-02 QA env | Exit 0; 157 fixtures, 908 refs; informational AsyncAPI 3.1.0 recommendation vẫn được ghi |
| `./scripts/test-contract-tools` với CT-02 QA env | Exit 0; **26 Python + 8 Node**, gồm hai test policy và một test format mới |
| Default contract gate / mock startup gate | Exit 2 đúng kỳ vọng; chưa approved, mock không listen |
| Standalone API ở 127.0.0.1:8081 | `/health/live` 200; `/health/ready` 503; `/api/v1/me` không token 401; Bearer tùy ý 503 |

Các test auth/response writer có dependency injection sử dụng identity/DTO synthetic **chỉ trong test**. Không báo Cognito/provider/backend nghiệp vụ thật pass. Không gọi AWS, chạy Docker, tải model hoặc thực hiện OCR trong test nhóm 1. Lượt sandbox đầu chặn bind localhost; các test HTTP được chạy lại có quyền loopback và đạt. Hai lỗi phát hiện ở lần HTTP đầu (request context theo aiohttp mới và unknown-route routing) đã sửa trong code, không nới test/schema.

## 6. Phần tiếp theo

Nhóm 2 sẽ thiết kế access patterns và persistence: users/profile metadata, sessions/sources/jobs/results, rooms/members, vocabulary/collections/review, history và object references. Khi vẫn chưa dùng Docker/AWS, DynamoDB Local qua Java là một lựa chọn cần chuẩn bị ở nhóm 2; chưa cài/chạy trong nhóm 1.

Nhóm 3 làm xác thực Cognito thực; sau đó nối Solo OCR/lexicon, Group/realtime, recording/Admin theo kế hoạch. IAM, S3 signed upload/playback, Gateway callbacks, Chime media/recording và cloud performance chỉ được nghiệm thu khi thực sự có AWS/dev environment. Readiness hiện tại không che những phần còn thiếu này.
