# CT-04 — Chạy validation, fixtures và mock

**DRAFT — ready_for_review, 11/11/2026.** Package đầu vào `0.1.0-draft.1` chưa có xác nhận của ba thành viên, `contract_commit_sha: null`. CT-04 cung cấp công cụ và kiểm tra cấu trúc để review. Chưa có kết quả tương thích contract chính thức hoặc tích hợp producer/consumer thật. Xem [ACCEPTANCE](ACCEPTANCE.md) và [kết quả thực chạy](ct04-results.json).

## 1. Phạm vi và lựa chọn công cụ

Đã đối chiếu [decisions](../contracts/decisions.md), [OpenAPI](../contracts/openapi.yaml), [AsyncAPI](../contracts/asyncapi.yaml), năm JSON schemas, manifest/fixtures gốc, CT-01 audit/architecture/open questions, CT-02 guide và CT-03 ownership/local setup/Git workflow. Không có quyết định nào được tự nâng thành APPROVED.

| Hiện trạng | Lựa chọn CT-04 | Lý do |
| --- | --- | --- |
| Frontend dùng pnpm, Node 22, không có script test/framework test trong package.json | Node `node:test` cho kiểm tra fixtures phía JavaScript | Có sẵn trong Node, không thêm Vitest/Jest hoặc đổi dependency UI |
| OCR có Python CLI test_server.py; chưa có framework test chung/CI trong workspace | Python `unittest` cho công cụ QA | Có sẵn trong Python; không import/start provider hoặc cài model |
| CT-02 đã có venv kiểm schema và Node AsyncAPI parser tách biệt | Dùng lại đúng các bản đã kiểm; khai báo trong [requirements](../tools/contract-testing/requirements.txt) và [tool versions](../tools/contract-testing/tool-versions.json) | Validator chuẩn xử lý cấu trúc, JSON Schema và references tốt hơn việc tự viết trình phân tích |
| Chưa có mock/framework HTTP ứng dụng | Mock HTTP dùng Python stdlib, đọc OpenAPI và fixtures chung | Không thêm Prism/Express/FastAPI hoặc tạo backend thay thế |
| Chưa có workflow CI được tìm thấy | Ghi lệnh có thể đưa vào CI sau review | Chưa tạo workflow hoặc required status check trên GitHub |

QA-only: `openapi-spec-validator==0.7.2`, `jsonschema==4.26.0`, `referencing==0.36.2`, `PyYAML==6.0.3`, `@asyncapi/parser@3.6.6`. CT-04 **không cài thêm package**, không sửa package.json, pnpm-lock.yaml, pyproject.toml hoặc runtime sản phẩm. File requirements là công thức cài tools cho máy khác; chưa là lock toàn bộ dependency gián tiếp.

Nguồn công cụ: [OpenAPI Spec Validator](https://openapi-spec-validator.readthedocs.io/en/latest/), [AsyncAPI parser chính thức](https://github.com/asyncapi/parser-js), [Python unittest](https://docs.python.org/3/library/unittest.html), [Python HTTP server](https://docs.python.org/3/library/http.server.html). Mock này chỉ dành cho local.

## 2. Chuẩn bị môi trường QA độc lập

Trong máy được audit, dùng lại các công cụ CT-02 còn trong `/private/tmp`:

```bash
export CT04_PYTHON=/private/tmp/ct02-validator-venv/bin/python
export CT04_ASYNCAPI_PARSER=/private/tmp/ct02-asyncapi-validation/node_modules/@asyncapi/parser
./scripts/validate-contracts --lint-draft
./scripts/test-contract-tools
```

Thư mục tạm có thể bị dọn. Trên máy mới, sau khi có Python >=3.10 và Node 22 phù hợp toolchain nhóm, có thể tạo môi trường riêng bằng các lệnh sau. **Các lệnh cài này chưa chạy trong CT-04**, không cài lại dependency frontend/OCR:

```bash
ct04_tools_dir="$(mktemp -d "${TMPDIR:-/tmp}/lingualive-ct04.XXXXXX")"
python3 -m venv "$ct04_tools_dir/python"
"$ct04_tools_dir/python/bin/python" -m pip install -r tools/contract-testing/requirements.txt
npm install --prefix "$ct04_tools_dir/node" --ignore-scripts --no-audit --no-fund @asyncapi/parser@3.6.6
export CT04_PYTHON="$ct04_tools_dir/python/bin/python"
export CT04_ASYNCAPI_PARSER="$ct04_tools_dir/node/node_modules/@asyncapi/parser"
```

`npm` ở đây chỉ cài validator vào thư mục QA ngoài repo, không thay pnpm của frontend. Không có auto-install trong các entrypoint. Thiếu công cụ trả exit 3. Không dùng Python venv dummy OCR làm bằng chứng provider/model đã hoạt động.

## 3. Entrypoint và exit codes

```bash
# Kiểm cấu trúc DRAFT; kết quả không phải nghiệm thu contract.
./scripts/validate-contracts --lint-draft --report /private/tmp/ct04-lint.json

# Gate mặc định: hiện trả 2 / PENDING_APPROVAL.
./scripts/validate-contracts --report /private/tmp/ct04-gate.json

# Test chính công cụ và kiểm tra quan hệ giữa synthetic fixtures.
./scripts/test-contract-tools
```

| Exit | Ý nghĩa |
| --- | --- |
| `0` | `--lint-draft`: STRUCTURE_VALID; hoặc contract đã duyệt vượt qua schema checks; unit test tool chạy đạt. Không tự là integrated |
| `1` | Schema/fixture/reference/envelope/semantic check không hợp lệ; hash lệch; hoặc thay đổi cần review compatibility |
| `2` | Thiếu approval/SHA; mock chưa được phép listen. Cũng là mã argparse khi tham số CLI sai: đọc thông báo để phân biệt |
| `3` | Thiếu dependency, executable hoặc file cần thiết để chạy kiểm tra |

Đầu ra JSON của validator luôn có `conformance`, `runtime_integration`, `contract_status`, lý do pending và `exit_code`. Kể cả lint draft trả 0, conformance vẫn PENDING và runtime integration NOT_RUN. Không dùng `|| true` hoặc đổi schema để làm một CI gate xanh. Chỉ job review cấu trúc được dùng `--lint-draft`; job chứng nhận compatibility phải dùng gate mặc định và giữ trạng thái pending/fail khi exit 2.

Validator thực hiện: strict JSON/YAML (không key trùng/NaN), xác minh 159 hash của package CT-02, resolve local refs (không tải schema ngoài), OpenAPI 3.1 validator, AsyncAPI 3.0 parser, năm JSON Schema Draft-07, positive/negative fixtures, HTTP request/response/header examples, error envelopes, WS payload examples và các invariant bổ sung: code point offset, normalized box edges, image/UTF-8 budget, IDs/seq/scope, raw/public mapping và polling/WS references. Raw schema provider vẫn giữ nguyên; không áp constraint public vào raw response.

AsyncAPI parser hiện có **1 informational diagnostic** khuyên dùng 3.1.0, 0 errors/0 warnings. Thông tin đó được giữ trong report; CT-04 không tự đổi phiên bản tài liệu.

### Compatibility trước khi đổi package

```bash
./scripts/validate-contracts --lint-draft --baseline-dir /path/to/prior-checkout/contracts
```

So sánh OpenAPI/AsyncAPI và union các file schemas cũ/mới: phát hiện removal/addition, required/enum/security/type/constraint và các thay đổi khác có thể ảnh hưởng consumer; bỏ qua annotation mô tả/examples. Có thay đổi cần review thì trả 1. Đây là guard thận trọng, có thể báo cả thay đổi additive; **không chứng minh semantic backward compatibility**. Owner phải review direction request/response, corpus, auth/state machine và approvals. So sánh với chính thư mục hiện tại chỉ là sanity không-diff; không thay baseline release đã duyệt.

## 4. Fixtures và trạng thái coverage

Giữ nguyên [manifest CT-02](../contracts/fixtures/manifest.json): 144 JSON (128 positive, 11 negative-schema, 5 negative-semantic). Thêm [manifest CT-04](../contracts/fixtures/ct04-draft/manifest.json): **13 positive JSON mới**, tách biệt và gắn hash nguồn. Tổng lint: 157 JSON = 141 positive + 16 mẫu cố ý sai. Negative test đạt nghĩa là validator đã từ chối đúng mẫu sai, không có nghĩa mẫu đó hợp lệ.

| Nhóm | Case có fixtures để review | Chưa chứng minh |
| --- | --- | --- |
| OCR | Horizontal, vertical, empty, invalid, too-large, timeout, busy | Accuracy/model, readiness, queue saturation, ảnh thật, actual upload limit |
| Session/job | Normal, old-source, out-of-order, duplicate, retry/idempotency conflict | Durable state/idempotency/concurrency thực của backend/worker |
| Auth/room | Token expired, forbidden session/room, closed room, member left | Cognito JWT/revocation/membership thật; giả lập lỗi không thực hiện authorization |
| Lexicon | Inflected, unknown, Unicode supplementary/combining marks, hai selected senses | Corpus/tokenizer/meaning đúng, đồng thời nhiều nghĩa trong một token (`PENDING_D13`) |
| Storage | Duplicate personal vocabulary, forbidden shared vocabulary, empty history | Database ownership/uniqueness/retention thật |

Có 24 mục trong `coverage`; tất cả vẫn DRAFT. `partial`/`not_found` là response tra từ hợp lệ; timeout là error envelope riêng. OCR không có chữ là `paragraphs: []`; provider error không được đổi thành empty success. Chi tiết 13 file mới ở [fixture README](../contracts/fixtures/ct04-draft/README.md).

## 5. Mock HTTP — có gate approval

```bash
./scripts/mock-contracts --mode mock --host 127.0.0.1 --port 8091
```

**Hiện lệnh này trả exit 2 trước khi tạo socket**, vì package và cả hai fixture manifests đều DRAFT. Không có flag `--allow-draft`, không đổi trạng thái phê duyệt chỉ để demo. Không mở cổng mock trong CT-04. Port đề xuất 8091 tách khỏi preview 8443, app API đề xuất 8081 và raw OCR 8080; không kill hoặc restart dịch vụ khác.

Sau khi cả nhóm chốt và phát hành package phù hợp, công cụ yêu cầu approval metadata/SHA và fixture set đã duyệt nằm trong bundle được pin. **Quy tắc đọc metadata của tool là đề xuất CT-04 cần review**: `status: APPROVED`; `approved_by` gồm bản ghi `{name, evidence}` cho đủ ba tên tại decisions; `contract_commit_sha` 40 hex; mọi HTTP operation/tài liệu có `x-contract-status` và fixture manifests phải approved. Manifest CT-04 + các JSON của nó cần được đưa vào `files`/hash của **release mới**, không sửa hash của release cũ để che thay đổi. Tool không xác thực danh tính người duyệt hoặc tính thật của review link; nhóm vẫn chịu trách nhiệm ký nhận. Nếu chỉ duyệt một phần Solo, cần một package/mock scope đã pin riêng và review tooling theo scope đó; hiện chưa hỗ trợ partial approval.

Handler/fixture planner hiện được kiểm bằng unit test trong bộ nhớ, không bind mạng. Thiết kế sau gate:

- Chỉ match method/path thuộc `/api/v1` trong OpenAPI; validate path/query/header/body và response; chưa có business state. Resource ID khác ID fixture trả 404 khi fixture có định danh đối chiếu, không đổi ID trong response để giả vờ đã lưu.
- Default success lấy ví dụ OpenAPI chung; `X-Mock-Scenario: token-expired` trả 401 với `TOKEN_EXPIRED`; `forbidden` trả 403. Có thêm 15 scenario gắn operation trong manifest. Tên scenario không hợp lệ trả 400.
- Named scenarios: upload `too-large` 413; job `busy` 429 / `invalid-image` 422 / `duplicate` 200; poll `processing` 200 / `job-timeout` 200 với failed job; result `no-text` / `out-of-order` 200; lexicon `provider-timeout` 504; history `empty` 200; session `forbidden-session` 403; room `forbidden-room` 403 / join `room-closed` 409; vocabulary `duplicate` 200 / shared `forbidden-shared` 403.
- `X-Mock-Delay-Ms: 0..2000` hoặc `--delay-ms` mô phỏng chậm; client timeout nhỏ hơn delay kiểm cancellation. Handler có lỗi tool/schema trả lỗi, không thay bằng success. Job timeout là HTTP 200 mang job failed, không nhầm với transport timeout hay HTTP 504 của lexicon.
- Header nhận diện: `X-Data-Mode: mock`, `X-Mock-Server`, contract version/status, no-store; 204 không body; 401 có WWW-Authenticate; 429/503 có Retry-After. CORS mặc định chỉ `http://localhost:8443`, thêm origin bằng `--allow-origin`; expose các header nhận diện cho browser.
- Không kiểm JWT thật, không cấp token/ticket/meeting credentials. Hai operations xin ticket/meeting trả 503; fixture credential redacted không được phát ra làm credential chạy được. Presigned URL `.invalid` vẫn chỉ là placeholder: mock không cung cấp S3 PUT hoặc video/ảnh thật.
- Không có WS broker/reconnect/replay, Chime chat, provider thật, database, mutation persistence hoặc session orchestration. Không thể chạy hoàn chỉnh Solo qua S3/job thật chỉ bằng mock HTTP này.

Ví dụ HTTP **chưa chạy qua mạng**, chỉ dùng sau approval và khi mock đã listen:

```bash
curl -i http://127.0.0.1:8091/api/v1/me
curl -i -H 'X-Mock-Scenario: token-expired' http://127.0.0.1:8091/api/v1/me
curl -i -H 'X-Mock-Scenario: empty' http://127.0.0.1:8091/api/v1/history
curl -i --max-time 0.1 -H 'X-Mock-Delay-Ms: 500' http://127.0.0.1:8091/api/v1/me
```

## 6. Harness producer/consumer và adapter

### Frontend — Đức

`consumer-fixtures.test.cjs` dùng JavaScript `Array.from` cho code point, kiểm raw/public, poll/WS reference, duplicate event/job, stale-source, out-of-order frame, inflection/sense identity và empty/unknown/error. **Không import API client hoặc React UI**, vì client thật chưa có; đây là kiểm fixture phía consumer, không phải frontend integration pass.

Khi được giao task tích hợp: đặt API DTO→UI adapter ở module API client/adapter do Đức quản lý theo CT-02 guide; không sửa component để đọc raw provider trực tiếp. `VITE_DATA_MODE`, `VITE_API_BASE_URL`, realtime URL trong [.env.example](../.env.example) hiện chỉ là đề xuất, chưa có consumer. Chọn mock **tường minh**, base mock `http://127.0.0.1:8091/api/v1`; real dùng app API đã xác minh. Lỗi kết nối real phải hiển thị lỗi/cho retry theo policy, không tự bật mock, demo auth hoặc lưu fake login. CT-04 không bật các env hay sửa UI.

### Backend — Hoàng Bảo

Trong repo backend thật, chạy unit/response tests của repo đó rồi xuất JSON từ HTTP response (ghi status, environment, SHA, mode vào biên bản; không ghi bearer/credentials). Từ workspace có contract này:

```bash
# Dùng fixture chỉ để thử harness; không phải response backend thật.
./scripts/validate-contracts --lint-draft --message contracts/fixtures/http/getOcrResult-200.json --operation getOcrResult --http-status 200

# Mẫu lệnh cho response đã capture; sau approval bỏ --lint-draft.
./scripts/validate-contracts --message /path/to/captured-result.json --operation getOcrResult --http-status 200
```

Lặp cho create upload/job, poll, result, permission errors, room, vocabulary/history. Harness đọc JSON không gọi backend và không kiểm HTTP header trên một capture chỉ chứa body; test HTTP của backend phải kiểm cả status/header/auth. Dùng schema checker cho response writer trong test adapter, không gắn dependencies QA vào runtime backend ngoài task được giao. HTTP status phải là status khai báo của operation, error phải dùng envelope chung.

### OCR/worker/lexicon — Bảo Anh, phối hợp Hoàng Bảo

```bash
./scripts/validate-contracts --lint-draft --message contracts/fixtures/ocr/success.json --schema schemas/ocr-provider.schema.json
./scripts/validate-contracts --lint-draft --message contracts/fixtures/lexicon/unicode-code-points.json --schema schemas/lexicon.schema.json
```

Đổi đường dẫn fixture thành capture thật khi có provider/corpus và approval, bỏ `--lint-draft` ở gate chính thức. Raw schema giữ `paragraphs`, `elapsed_ms`, box center/width/height; raw error là `error`, không ép raw thành public envelope. Worker/application adapter bổ sung IDs/timeline/image dimensions và kiểm normalized geometry **trước** public result write; raw metadata/error phải được xử lý riêng. Hiện chỉ so sánh ba dataclass với schema bằng AST và kiểm mapping synthetic raw→public, chưa thực thi mapper/worker thật.

Lexicon kiểm original text/code point/không normalize ngầm; unknown và service failure tách biệt; giữ stable entry/sense IDs/source attribution, không dùng synthetic gloss trong real mode. Mapping tới popup Yomitan nằm ở consumer adapter, corpus/tokenizer ở service; không clone renderer làm dictionary backend.

### Realtime và polling

Unit checks yêu cầu job/result/WS có cùng session/source/frame/job/result IDs và frame_index/media_time_ms/seq/created_at phù hợp. Duplicate `event_id` chỉ apply một lần; source cũ không cập nhật source đang xem; seq là thứ tự sự kiện, frame_index/media time quyết định frame cũ/mới trong cùng source. Đọc lại snapshot/watermark và polling khi reconnect theo AsyncAPI; không truyền binary lên Gateway WS, không dùng raw `/ws` thay protocol app, không thêm chat WS khi nhánh D06 là Chime.

Các rule trên mới được kiểm trên fixtures. Cần test thực backend/worker/consumer cho reconnect, authorization, replay/gap, hết ticket, at-least-once delivery, polling fallback và result visibility trước event. Harness hiện không có network producer/consumer runner xuyên repo.

## 7. Tiếp tục nghiệm thu

Theo [ownership](OWNERSHIP.md) và [Git workflow](GIT-WORKFLOW.md): PR contract/fixtures trước, pin version/bundle/contract SHA, mỗi repo chạy unit/contract test riêng, rồi smoke trên bộ SHA tích hợp đã ghi nhận. CI tương lai có thể chạy `test-contract-tools`, lint review và gate approved thành các job riêng; không coi lint draft là gate approved đã đạt.

Ghi thực tế `mock / dummy / real`, model/corpus/runtime versions, environment, status/exit và ca chưa chạy trong mỗi lần nghiệm thu. Chỉ đưa CT-04 lên `ready_for_integration` khi contract và fixtures approved, gate đạt, mock khởi động và qua HTTP smoke thực. Chỉ gọi `integrated` sau khi các producer/consumer thực sự nối được với nhau. Danh sách owner và ca còn blocked ở [ACCEPTANCE](ACCEPTANCE.md).
