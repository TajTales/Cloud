# LinguaLive application backend — nhóm 1, 2 và xác thực local nhóm 3

**Nhóm 4–5, 13/11/2026:** hiện có **26/50 public handlers**, source/upload/job/result, collections và vòng đời phòng metadata. Worker durable đã nối model Nhật/Trung CPU local và FE Solo/history. [API nhóm 4](../docs/GROUP-04-APPLICATION-API.md), [OCR nhóm 5 và cách chạy/thử](../docs/GROUP-05-OCR-PIPELINE.md), [kết quả thực](../docs/group04-05-results.json). Runtime backend thêm Pillow 13.0.0 (25 packages trong lock); hai provider có venv/lock riêng, không đổi dependency frontend. Wrapper dev-local-api hiện bật OCR; có thể tắt bằng OCR_ENABLED=0. Các phần 0/11 handlers và số test bên dưới là mốc lịch sử tương ứng flags/task cũ, không phải tổng hiện tại. Cognito/Chime/recording/lexicon/cloud vẫn pending.

**Nhóm 3, 13/11/2026:** đã bổ sung xác nhận email qua mailbox local, quên/đổi mật khẩu, đổi email, access/refresh rotation và revoke, CLI cấp/thu hồi Admin, quản lý trạng thái tài khoản và audit thật. [Phạm vi và cách thử](../docs/GROUP-03-AUTH-AND-AUTHORIZATION.md). Không tự cấp Admin cho tài khoản thật; Cognito/email internet/WS cloud vẫn pending. Không thêm dependency, đổi runtime hoặc reset dữ liệu. Bản foundation bên dưới là mốc lịch sử khi các feature flags tắt.

**Tích hợp FE local 13/11/2026:** chạy `./scripts/dev-local-api` để bật đăng nhập local thật và 11 operations profile/vocabulary/review/Solo/history/stats. Vite proxy dùng API 8081, FE mặc định `VITE_API_MODE=real`. [Hướng dẫn và ca thử UI](../docs/FE-DB-INTEGRATION-TESTS.md), [local auth DRAFT](../docs/LOCAL-AUTH-DRAFT.md). Đây chưa phải Cognito/cloud/full OCR integration. Các phần nhóm 1–2 bên dưới là mốc trước tích hợp.

**Cập nhật 13/11/2026:** đã có DynamoDB Local 3.3.2, repository và local object storage. Mặc định foundation vẫn không cần DB; bật persistence bằng env. `scripts/test-api` hiện gồm cả storage integration nên cần database local chạy.

```bash
# Terminal A (chỉ chạy khi DB chưa chạy)
./scripts/dev-db
# Terminal B
./scripts/db-admin init
./scripts/db-admin check
PERSISTENCE_ENABLED=1 ./scripts/dev-api
```

Chi tiết setup, cấu hình, schema nội bộ, quyền dữ liệu, backup và kết quả: [nhóm 2](../docs/GROUP-02-DATABASE-AND-STORAGE.md). Runtime lock hiện có 24 packages, gồm Boto3/botocore chỉ kết nối endpoint loopback; không đọc AWS profile/credentials hoặc tạo tài nguyên cloud. Bản hướng dẫn foundation bên dưới vẫn dùng với PERSISTENCE_ENABLED=0.

Backend nền tảng chạy **Python 3.12 + aiohttp**, localhost `8081`. Không cần Docker, Java, database, tài khoản AWS hoặc credentials để khởi động. Frontend vẫn chạy riêng ở `8443`; raw OCR hiện có ở `8080` được giữ nguyên và chưa được gọi trong nhóm 1.

## Chạy ngay trong workspace đã chuẩn bị

Từ root repo:

```bash
./scripts/dev-api --check
./scripts/test-api
./scripts/dev-api
```

`--check` kiểm config và hash contract, không mở socket. `dev-api` giữ terminal chạy; dừng bằng Ctrl+C. Server chỉ bind loopback. Nếu cổng 8081 bận, chọn cổng khác cho chính service này:

```bash
APP_PORT=8082 ./scripts/dev-api
```

Không khởi động lại Vite hoặc kill service khác để lấy cổng.

## Cài trên máy/checkout mới

```bash
python3.12 -m venv application-backend/.venv
application-backend/.venv/bin/python -m pip install -r application-backend/requirements.lock
./scripts/dev-api --check
```

Dependency trực tiếp khai báo trong `pyproject.toml`; `requirements.lock` pin cả 24 dependency runtime trực tiếp/gián tiếp đã chạy trên Python 3.12.16/macOS arm64. Hai validator RFC3339/RFC3986 là dependency bắt buộc để `date-time` và `uri` không bị jsonschema bỏ qua; startup fail nếu thiếu format checker. File lock hiện pin version, chưa có wheel hashes; target OS khác cần kiểm wheel và chạy test trước khi deploy. Không copy/move venv giữa máy. `.venv`, `.local-data`, `.local-tools` và egg-info được ignore trong module, không thay Python toàn máy hoặc dependency OCR/frontend.

Các script dùng venv trên làm mặc định; nếu dùng một venv khác đã cài đúng dependencies:

```bash
LINGUALIVE_PYTHON=/absolute/path/to/venv/bin/python ./scripts/dev-api --check
```

Entrypoint source hoạt động không cần build/install package. Có thể cài package bằng pip trong task packaging sau; build metadata dùng setuptools, tách khỏi dependency runtime.

## HTTP và trạng thái thực tế

```bash
curl -i http://127.0.0.1:8081/health/live
curl -i http://127.0.0.1:8081/health/ready
curl -i http://127.0.0.1:8081/api/v1/me
```

| Request | Kết quả hiện tại |
| --- | --- |
| `GET /health/live` | 200, process đang hoạt động, stage `foundation` |
| `GET /health/ready` | 503 `FEATURE_NOT_CONFIGURED`, nghiệp vụ chưa sẵn sàng |
| API trong OpenAPI thiếu Bearer token | 401 `AUTH_REQUIRED` |
| API có Bearer token nhưng chưa cấu hình verifier | 503 `FEATURE_NOT_CONFIGURED`; không tin token tùy ý |
| Route không tồn tại | 404 JSON error envelope |
| Method không được route hỗ trợ | 405 JSON error envelope, `Allow` header |
| CORS preflight hợp lệ cho public route | 204 không body; không cần đăng nhập |

Hai `/health/*` là endpoints vận hành local mới của application backend, nằm **ngoài** 50 operations public `/api/v1`; không sửa OpenAPI cũ hoặc raw `/health` của OCR. Liveness không có nghĩa đăng nhập/OCR/room đã hoạt động. Readiness cố ý 503 trong release nền tảng này, kể cả khi unit test có dependency injection.

Các path/method public được đọc từ contract để dựng router và áp dụng policy chung. **0 business handlers được cài bởi CLI hiện tại**. Không có dữ liệu fixture được trả như kết quả thật; không phát access token/meeting ticket. Test-only verifier và handlers ở `tests/` không thể bật bằng env hoặc CLI. Header `X-Data-Mode: real` chỉ service thực đang phản hồi, không ngụ ý AWS hay business services đã được tích hợp; `X-Contract-Status: DRAFT` được giữ rõ.

## Config

Mẫu chuẩn: [.env.example](.env.example). Service chỉ đọc biến đã export trong process, không tự load `.env`/dotenv:

| Biến | Mặc định / giới hạn |
| --- | --- |
| `APP_ENV` | `local`; chỉ hỗ trợ `local` hoặc `test`. Production chưa được bật trong nhóm 1 |
| `APP_HOST` | `127.0.0.1`; chỉ loopback (`localhost`, `::1` cũng được) |
| `APP_PORT` | `8081`, số nguyên 1–65535 |
| `ALLOWED_ORIGINS` | `http://localhost:8443,http://127.0.0.1:8443`; exact origins, không wildcard/path/userinfo |
| `APP_MAX_BODY_BYTES` | 1048576 bytes, chỉ được giảm trong release nền tảng |
| `LOG_LEVEL` | `INFO` |
| `DATA_MODE` | Chỉ `real`; CT-04 mock là server riêng, không fallback |
| `CONTRACTS_DIR` | Tự tìm `contracts/` trong checkout; có thể cung cấp absolute path |

Khởi động fail nếu config sai, thiếu bundle hoặc hash bị đổi. Không có AWS SDK, đọc credential store hay network call trong startup. Khi triển khai ngoài checkout, phải cung cấp đầy đủ các file nằm trong bundle theo đường dẫn tương đối của `contract-version.json`, gồm guide CT-02 được hash; không chỉ copy mỗi OpenAPI.

## Cách phát triển nghiệp vụ ở nhóm tiếp theo

- `app.py` khởi tạo app, middleware, liveness/readiness, CORS và dispatch theo operationId. `Result` tự bọc `{data, request_id}`; response phải qua schema. Handler trả 204 phải không có data/body.
- `contracts.py` đọc schema gốc, kiểm request body/path/query/headers và response; local registry không tải schema ngoài. Lỗi validation chỉ chỉ ra field path, không echo giá trị gửi lên. Những invariant nghiệp vụ như source ownership, idempotency storage, bbox edges và Unicode coverage cần được triển khai/kiểm tiếp ở module tương ứng; JSON Schema không thay các kiểm tra đó.
- `auth.py` định nghĩa boundary nhận identity đã xác minh. `UnconfiguredAuthenticator` fail closed. Nhóm auth sẽ bổ sung Cognito verifier thực và kiểm quyền object/membership tại handler; không decode JWT rồi tin claims chưa xác minh.
- Đăng ký handler bằng map `operationId → async handler(request, body) → Result`. Chỉ operationId tồn tại trong bundle được chấp nhận. Test DTO synthetic chỉ nằm trong test.
- Database/repositories, OCR worker/client, lexicon, realtime và media sẽ là module riêng gọi qua interface, không nhét nghiệp vụ vào middleware/provider. Không đổi wire schema hoặc field vì tên model nội bộ.

Middleware gắn `X-Request-Id`, version/status, CORS trên cả success/error, và no-store. Log chỉ method/operationId/status/duration/type lỗi; không log URL query, Bearer token, body hoặc traceback. Lỗi response/exception trở về 500 an toàn; không giả success. Origin được kiểm độc lập với authorization; CORS không thay kiểm quyền.

## Kết quả nghiệm thu

Xem [nhóm 1](../docs/GROUP-01-BACKEND-FOUNDATION.md) và [report thực chạy](../docs/group01-results.json). Bộ test dùng `unittest` + aiohttp TestServer/TestClient trên cổng loopback tạm. Không cần thêm pytest. Config/schema test dùng filesystem thật; identity/DTO trong các test dispatch là synthetic và không chứng minh Cognito thật.

Contract vẫn `0.1.0-draft.1`. [Approval policy](../contracts/approval-policy.json) ghi người chốt hiện tại là Nguyễn Tài Đức, theo yêu cầu một người làm toàn bộ. Policy mới không tự approve package cũ; default contract gate và mock vẫn pending cho đến khi owner xác nhận và pin một release mới đầy đủ.

Nguồn: [aiohttp server](https://docs.aiohttp.org/en/stable/web_advanced.html), [aiohttp testing](https://docs.aiohttp.org/en/stable/testing.html), [Python 3.12 venv](https://docs.python.org/3.12/library/venv.html).
