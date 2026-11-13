# CT-04 — Biên bản kiểm tra và điều kiện nghiệm thu

**Nhóm 4–5 local, 13/11/2026:** [report mới](group04-05-results.json) ghi **137/137 tests** API/DB/protocol/consumer và **5/5 model smoke cases** Nhật/Trung ngang/dọc/no-text. Tách producer synthetic trong regression khỏi model thực trong acceptance. [Hướng dẫn nghiệm thu UI](GROUP-05-OCR-PIPELINE.md) vẫn MANUAL_PENDING; chưa xác nhận browser DOM, meeting/media/WS cloud/ASR/lexicon hoặc AWS. Không nâng nghiệm thu CT-04/contract DRAFT từ các kết quả này.

**Nhóm 3 local, 13/11/2026:** có [biên bản tài khoản/phân quyền](GROUP-03-AUTH-AND-AUTHORIZATION.md) và [kết quả kiểm tra](group03-results.json) riêng. Xác thực/password/email qua mailbox, token rotation/revoke và Admin account management được kiểm trên HTTP + DynamoDB thật; UI thủ công, Cognito, email internet và WS/AWS vẫn pending. Không thay nghiệm thu CT-04 lịch sử bằng kết quả này.

**Tích hợp FE local 13/11/2026:** 94 tests backend đạt, gồm 15 tests mới và 13 bước của production API client qua HTTP thật/DynamoDB Local. [Các ca thao tác UI](FE-DB-INTEGRATION-TESTS.md) vẫn MANUAL_PENDING; không báo browser click, Cognito, OCR/provider, Group/Chime hoặc AWS pass. [Report hiện tại](fe-db-integration-results.json) ghi riêng, không sửa nghiệm thu CT-04 cũ hoặc approve contract.

**Ghi chú 13/11/2026:** persistence local nhóm 2 có biên bản riêng tại [GROUP-02-DATABASE-AND-STORAGE.md](GROUP-02-DATABASE-AND-STORAGE.md) và [group02-results.json](group02-results.json). Không nâng kết quả CT-04 cũ thành integration/cloud pass.

**Ghi chú 12/11/2026:** biên bản dưới đây giữ nguyên kết quả CT-04 ngày 11/11, khi quy trình còn ba thành viên. Ownership hiện là một người theo [policy mới](../contracts/approval-policy.json). Kết quả backend nền tảng và contract gate hiện tại được ghi riêng ở [nhóm 1](GROUP-01-BACKEND-FOUNDATION.md) và [group01-results.json](group01-results.json); không sửa kết quả lịch sử để giả rằng cloud/business đã chạy.

**DRAFT — ready_for_review, 11/11/2026. Chưa ready_for_integration; chưa integrated.** Công cụ QA đã chạy được. Contract `0.1.0-draft.1` và fixtures vẫn DRAFT, chưa có xác nhận ba thành viên; mock bị chặn trước khi mở cổng. Không có consumer/producer thật được chứng nhận bởi CT-04.

Đọc [hướng dẫn tái chạy](CONTRACT-TESTING.md), [kết quả JSON thực chạy](ct04-results.json), [decisions](../contracts/decisions.md) và [CT-03 local setup](LOCAL-SETUP.md). CT-04 không sửa UI, OCR provider, backend, database hoặc AWS. Không commit/push/deploy/migration.

## 1. Version, source và môi trường

| Mục | Giá trị thực tế |
| --- | --- |
| Branch / source HEAD | `main` / `81be4b4a5a7baf24db0c9fdc5bbd2d72fed87340` |
| Working tree | Có thay đổi/untracked từ trước; HEAD không tái tạo được toàn bộ workspace này |
| Contract version / status | `0.1.0-draft.1` / `DRAFT`, `approved_by: []` |
| Contract commit SHA | `null`; không lấy HEAD cũ thay cho contract commit |
| Bundle SHA-256 | `bcfd39b6a2fd85d74cd5efd53e7a6bff753f60bf7e286246c27ef696c1c6bfd2` |
| Hash package CT-02 | 159 files được xác minh, không đổi |
| Baseline trước CT-04 | 299 file cũ được hash trước khi làm; kết quả so sánh không có file cũ bị đổi |
| Node / pnpm trên máy | `v22.23.4` / `12.18.0`; không đổi về pnpm 10.34.3 trong task QA |
| Python của QA / default | `3.14.7` / `3.14.7`; đây không phải nghiệm thu runtime Docker OCR Python 3.12 |
| Dependencies | Dùng lại môi trường validator CT-02 ngoài repo; 0 package được cài trong CT-04; 0 dependency runtime/lockfile sản phẩm bị đổi |

Hai file docs nghiệm thu và kết quả không thuộc immutable package CT-02. Fixtures mới nằm trong supplement DRAFT gắn hash nguồn; chúng chưa được đưa vào release đã duyệt. Approval gate bao gồm việc pin fixture set trong release mới, không chỉ sửa một chữ DRAFT thành APPROVED.

## 2. Kết quả đã thực chạy

Các lệnh dưới chạy từ root với:

```bash
export CT04_PYTHON=/private/tmp/ct02-validator-venv/bin/python
export CT04_ASYNCAPI_PARSER=/private/tmp/ct02-asyncapi-validation/node_modules/@asyncapi/parser
```

| Lệnh thực chạy | Exit | Kết quả và giới hạn |
| --- | --- | --- |
| `./scripts/validate-contracts --lint-draft` | **0** | STRUCTURE_VALID; OpenAPI/AsyncAPI/JSON Schema/fixtures/examples; conformance PENDING |
| `./scripts/validate-contracts` | **2** | PENDING_APPROVAL đúng thiết kế; không có approved conformance pass |
| `./scripts/test-contract-tools` | **0** | **23 Python unittest + 8 Node tests đạt**, không fail; công cụ và synthetic fixtures |
| `./scripts/validate-contracts --lint-draft --baseline-dir contracts` | **0** | Self-baseline không diff; chưa so với release cũ được duyệt |
| `./scripts/validate-contracts --lint-draft --message contracts/fixtures/negative/lexicon-utf16-offset.json --schema schemas/lexicon.schema.json` | **1** | Từ chối đúng offset UTF-16; negative probe có chủ đích |
| `./scripts/validate-contracts --lint-draft --message contracts/fixtures/ocr/success.json --schema schemas/ocr-provider.schema.json` | **0** | Harness nhận raw synthetic hợp cấu trúc; không phải capture OCR thật |
| `./scripts/validate-contracts --lint-draft --message contracts/fixtures/http/getOcrResult-200.json --operation getOcrResult --http-status 200` | **0** | Harness nhận public response synthetic; không gọi backend |
| Cùng public response ở dòng trên nhưng `--http-status 204` | **1** | Từ chối status không được getOcrResult khai báo |
| `./scripts/mock-contracts --mode mock` | **2** | Mock NOT started, trước socket; thiếu approval và pin fixture supplement |
| `CT04_PYTHON=python3 ./scripts/validate-contracts --lint-draft` | **3** | Default interpreter thiếu dependency QA; báo SETUP_REQUIRED, không auto-install |

Raw stdout/stderr của mỗi lần chạy được ghi tạm khi kiểm tra; file JSON bàn giao giữ actual exit, expected exit, hash output, report validator và tổng số test. 10/10 command expectations khớp. Các exit 1/2/3 nêu trên là kết quả có chủ đích và được ghi tách biệt, không đổi thành API/runtime pass.

Chi tiết lint:

- OpenAPI **3.1.0**, 50 operations; AsyncAPI **3.0.0**, 5 commands/13 events, parser 0 errors/0 warnings/**1 informational** khuyên 3.1.0. Không đổi schema version để bỏ diagnostic.
- **5 JSON Schemas**, **908 local references**, **157 fixtures**: 141 positive hợp cấu trúc; 11 negative-schema + 5 negative-semantic bị từ chối đúng kỳ vọng. Tất cả thuộc contract/fixture DRAFT, không có accepted behavior test.
- **21 HTTP body request examples, 67 parameter example occurrences, 59 success response examples, 396 error example occurrences, 18 WS examples** được kiểm. Các error examples dùng lại qua nhiều operation không phải 396 API riêng.
- Poll/WS/detail/raw mapping tham chiếu nhau qua fixtures; inspect AST ba raw dataclasses, không import/start OCR model. Unit tests kiểm framing/content-length/CORS/204, delay không ngủ thật, HTTP error selection, no fake credentials và approval guard bằng transport trong bộ nhớ.

## 3. Coverage fixtures — vẫn pending nghiệm thu behavior

[Supplement manifest](../contracts/fixtures/ct04-draft/manifest.json) là danh sách máy đọc được cho 24 mục. Các đường dẫn ngắn dưới tính từ `contracts/fixtures/`. **Mọi dòng: STRUCTURE_VALID / DRAFT; real behavior NOT_RUN.**

| Case | Fixture chính | Owner nghiệm thu tiếp |
| --- | --- | --- |
| OCR ngang | `ocr/success.json` | Bảo Anh |
| OCR dọc | `ct04-draft/ocr-vertical.json` | Bảo Anh + Đức overlay |
| Empty OCR | `ocr/no-text.json`, `http/ocr-no-text.json` | Bảo Anh + Hoàng Bảo |
| Invalid image | `ocr/invalid-image-raw.json`, `http/invalid-image.json` | Bảo Anh + Hoàng Bảo |
| Too-large image | `ct04-draft/image-too-large.json` | Hoàng Bảo + Bảo Anh |
| OCR timeout | `http/ocr-timeout-job.json`, `ws/ocr-job_failed.json` | Hoàng Bảo + Bảo Anh |
| OCR busy | `ct04-draft/ocr-busy.json` | Hoàng Bảo + Bảo Anh |
| Normal result | `http/getOcrResult-200.json`, `ws/ocr-result_available.json` | Cả ba |
| Old source | `http/old-source.json`, `http/current-source-after-switch.json`, `http/late-result-old-source.json` | Đức + Hoàng Bảo |
| Out-of-order frame | `ct04-draft/out-of-order-frame.json`, `ct04-draft/out-of-order-event.json` | Cả ba |
| Duplicate job | `http/duplicate-job-new.json`, `http/duplicate-job-retry.json` | Hoàng Bảo + Bảo Anh |
| Retry/idempotency conflict | `ct04-draft/job-processing.json`, `http/idempotency-conflict.json` | Hoàng Bảo + Đức |
| Token expired | `http/token-expired.json` | Hoàng Bảo + Đức |
| Forbidden session | `ct04-draft/forbidden-session.json` | Hoàng Bảo |
| Forbidden room | `ct04-draft/forbidden-room.json` | Hoàng Bảo |
| Room closed | `ct04-draft/room-closed.json`, `ws/room-closed.json` | Hoàng Bảo + Đức |
| Member left | `ws/room-member_left.json` | Hoàng Bảo + Đức |
| Inflected word | `ct04-draft/lexicon-inflected.json` | Bảo Anh + Đức |
| Unknown word | `lexicon/not-found.json` | Bảo Anh + Đức |
| Unicode offsets | `lexicon/unicode-code-points.json`; negative `lexicon-utf16-offset.json`, `lexicon-omits-gap.json` | Bảo Anh + Đức |
| Polysemy identity | `ct04-draft/lexicon-polysemy-a.json`, `lexicon-polysemy-b.json` cùng thư mục | Bảo Anh + Đức |
| Duplicate vocabulary | `http/saveVocabulary-201.json`, `http/saveVocabulary-200.json` | Hoàng Bảo + Đức |
| Forbidden shared vocabulary | `ct04-draft/forbidden-shared-vocabulary.json` | Hoàng Bảo |
| Empty history | `http/listHistory-200.json` | Hoàng Bảo + Đức |

Polysemy mới kiểm hai response chọn nghĩa riêng có sense_id khác nhau; nhiều nghĩa/entry trong cùng popup vẫn **PENDING_D13**. Không sửa schema hoặc giả kết quả từ điển để báo đã giải quyết.

## 4. PASS / FAIL / BLOCKED

| Hạng mục | Trạng thái | Bằng chứng / việc còn lại |
| --- | --- | --- |
| Entry point validation và exit codes | **PASS_TOOLING** | Lint 0; intentional invalid 1; gate 2; missing tools 3 |
| Schema/examples/fixtures cấu trúc | **STRUCTURE_VALID_DRAFT** | Các số lượng ở mục 2; không chứng nhận contract chưa duyệt |
| Unit tests QA/mock planner/handler | **PASS_TOOLING** | 23 + 8; handler dùng in-memory transport, không socket |
| Approval guard | **PASS_TOOLING** | Assert ThreadingHTTPServer không được tạo khi contract pending |
| Regression/scope | **PASS** | 159 package hashes và 299 baseline files không đổi; chỉ file QA/docs/supplement mới |
| Unexpected failures | **NONE_OBSERVED** | Không che fail bằng sửa fixture/schema; negative probes trả lỗi đúng |
| Approved contract conformance | **PENDING_APPROVAL** | decisions, package và fixtures chưa có ba xác nhận; chưa pin contract SHA |
| Mock HTTP listen/curl/real client timeout | **BLOCKED_APPROVAL** | Không khởi động mock trên draft; chưa test socket/network/CORS thực trong browser |
| Frontend consumer thực | **NOT_RUN** | Chưa có API/auth adapter thật; JS fixture tests không import React app |
| App backend producer/API/auth/room/storage | **NOT_ACCESSIBLE** đối với repo ngoài | Chưa tìm thấy app backend trong workspace; cần repo/path/SHA từ Hoàng Bảo, không kết luận repo ngoài chưa phát triển |
| OCR thật/worker public mapping/load | **NOT_RUN**; repo worker ngoài nếu có NOT_ACCESSIBLE | Có raw server source nhưng chưa chạy model/corpus/worker trong CT-04 |
| Lexicon thật/quality/license/polysemy UX | **PENDING_D13 / NOT_RUN** | Chưa xác nhận corpus/tokenizer/translation; gloss fixture không phải tra từ thật |
| Cognito/Chime/Gateway/S3/DynamoDB/dev AWS | **NOT_ACCESSIBLE / NOT_RUN** | Chưa có environment/resources được xác minh cho CT-04, không deploy hoặc cấp credentials |
| Build/typecheck/UI regression | **NOT_RUN_CT04** | Production không đổi. Baseline TypeScript config mismatch đã ghi CT-03, không lấy lint contract thay build |

## 5. Những file CT-04 tạo mới

Không sửa file có sẵn. Không thay đổi contracts/decisions.md, OpenAPI/AsyncAPI, năm schemas, manifest/fixtures CT-02, contract-version hoặc validation-report cũ.

| Nhóm | File |
| --- | --- |
| 3 entrypoints | `scripts/validate-contracts`, `scripts/mock-contracts`, `scripts/test-contract-tools` |
| 8 file công cụ/test | `tools/contract-testing/requirements.txt`, `tool-versions.json`, `contracts_core.py`, `validate.py`, `validate-asyncapi.cjs`, `mock_server.py`, `consumer-fixtures.test.cjs`, `tests/test_contract_tools.py` (cùng root công cụ) |
| 15 file supplement | `contracts/fixtures/ct04-draft/manifest.json`, `README.md` và 13 JSON liệt kê trong manifest/README |
| 3 file tài liệu/kết quả | `docs/CONTRACT-TESTING.md`, `docs/ACCEPTANCE.md`, `docs/ct04-results.json` |

Tổng **29 file mới**. QA dependency manifests không thay dependency sản phẩm. Source files hiện có/dữ liệu UI, OCR server và ảnh review-assets được giữ nguyên.

## 6. Thứ tự và trách nhiệm nghiệm thu tiếp

| Thứ tự | Người | Đầu ra cần có |
| --- | --- | --- |
| 1 | **Cả ba** | Xác nhận decisions nền tảng (ưu tiên D03/D04/D05/D08/D14 cho Solo; D11/D12/D13 cho model/limit/lexicon), phạm vi Group/Admin còn pending; review approval metadata policy CT-04. Không ký thay nhau |
| 2 | **Đức điều phối; cả ba review** | PR package contract mới: approvals/bằng chứng, version/bundle, fixture supplement được pin; contract commit SHA thật và integrated base SHAs từng repo. Không tự lấy HEAD hiện tại làm contract SHA |
| 3 | **Hoàng Bảo** | Cung cấp backend repo/path/SHA/lệnh test/dev; response tests cho upload/job/poll/result/auth/room/vocabulary/history; status/header/permissions và idempotency thật |
| 4 | **Bảo Anh** | Provider raw capture thật, valid image/no-text/error/vertical/timeout/busy; worker map IDs/geometry/timeline/public result; lexicon corpus/offset/inflection/sense/license test có phiên bản model/corpus |
| 5 | **Đức** | API/auth/lexicon adapter, explicit mock/real switch, consumer tests dùng cùng version; test UI không áp stale/duplicate/out-of-order; không fallback real→mock |
| 6 | **Đức + Hoàng Bảo** | Sau approval, khởi động mock và smoke HTTP qua socket/browser, kiểm headers/scenarios/timeout/cancellation; ghi actual exit/log. Đây là bước còn thiếu để xác nhận mock sẵn sàng dùng tích hợp |
| 7 | **Cả ba** | Solo thật: frame upload→job→poll/WS reference→public OCR→lexicon→save vocabulary; permissions/old-source/idempotency/fallback. Sau đó Group/auth/storage/realtime trên dev environment đã xác minh |

Ứng dụng/worker ngoài workspace phải chạy test trong repo thật và trả capture/biên bản, không báo xuyên repo pass chỉ từ file fixture ở đây. Không đưa access token, ticket, presigned URL thật hoặc AWS secrets vào fixture/repo/log chia sẻ.

## 7. Gate kết thúc CT-04

| Điều kiện | Hiện tại |
| --- | --- |
| Validation có thể chạy lại và phát hiện invalid input | Đạt ở mức tooling |
| Fixtures conform schema | Đạt lint cấu trúc; approval của contract/fixtures vẫn pending |
| Mock đúng contract và chạy được HTTP smoke | Handler unit đạt; startup/smoke blocked approval |
| Không che lỗi bằng fake success | Đã kiểm failure path; mode synthetic/mock được ghi rõ |
| Producer/consumer thật đã chạy cùng nhau | Chưa, NOT_RUN |

**Bàn giao: ready_for_review / PENDING_APPROVAL.** Chỉ chuyển `ready_for_integration` sau khi contract được duyệt/pin, default gate đạt và mock qua HTTP smoke thực. `integrated` cần có bằng chứng các module thực sự kết nối; CT-04 hiện chưa có bằng chứng đó.
