# CT-02 — Hợp đồng tích hợp OCR Learning / LinguaLive

**DRAFT — 0.1.0-draft.1, 11/11/2026. Chưa phát hành v1 chính thức.** CT-01 chưa có quyết định nào được cả ba thành viên xác nhận. Yêu cầu CT-02 lần này cho phép soạn draft; không biến điều kiện G0 trong CT-01 thành đã đạt. Không thay đổi `decisions.md` hoặc tự nâng trạng thái các quyết định.

Bộ này mô tả **nhánh đề xuất D05 HTTP/S3 + job + WS manifest**, D06 Chime meeting data messages. Nếu nhóm chọn phương án khác phải sửa đồng bộ schema/examples/consumers trước khi triển khai; không duy trì hai giao thức ngầm. Không có API/backend/resource mới được triển khai bởi tài liệu này.

## Đọc và dùng bản chuẩn

1. Đọc [CT-01 decisions](decisions.md), [audit](../docs/G0-CURRENT-STATE.md) và [các câu hỏi mở](../docs/G0-OPEN-QUESTIONS.md).
2. Dùng cùng `contract_version: 0.1.0-draft.1` và `bundle_sha256` trong [contract-version.json](contract-version.json). `schema_version: 1.0` của WS/chat và `/api/v1` chỉ là tên wire/base path của phương án draft, không có nghĩa contract đã được duyệt/phát hành.
3. Đọc [hướng dẫn tích hợp](../docs/CT-02-INTEGRATION-GUIDE.md) và inventory đầy đủ [catalog.json](catalog.json); chọn operation/schema theo task, không tự đặt field riêng.
4. Chạy [validation có thể lặp lại](VALIDATION.md). Schema pass không thay test backend thật, Cognito, OCR model, browser hay AWS.
5. Trước khi triển khai chính thức, owner ghi xác nhận D01–D16, version/commit cho cả ba bên và cập nhật CHANGELOG. Hiện các file mới chưa commit: HEAD repo không phải commit chứa package CT-02 này. Dùng bundle hash để review chính xác; contract commit SHA chỉ ghi sau khi nhóm thực sự commit.

## File và owner

| File | Vai trò | Owner đề xuất |
| --- | --- | --- |
| [openapi.yaml](openapi.yaml) | OpenAPI **3.1.0**, 50 operations/45 paths, đủ 10 nhóm; mỗi operation có auth/quyền, schema, status, success/error examples và decision dependencies | Hoàng Bảo; Đức review consumer |
| [asyncapi.yaml](asyncapi.yaml) | AsyncAPI **3.0.0**, viewpoint server: receive 5 commands/send 13 events; không có ảnh hoặc chat trên app WS | Hoàng Bảo; Đức/Bảo Anh review |
| [ocr-provider.schema.json](schemas/ocr-provider.schema.json) | Raw shape hiện hữu Success/Error, không đổi field hay siết bounds của provider cũ | Bảo Anh |
| [lexicon.schema.json](schemas/lexicon.schema.json) | Lookup data found/partial/not_found, code point offsets, lemma/POS/reading/nghĩa/nguồn; corpus chưa chọn | Bảo Anh; Hoàng Bảo route; Đức consumer |
| [application.schema.json](schemas/application.schema.json) | DTO chung/envelope, public result, upload/job, profile/session/room, vocabulary/review, history/playback/Admin | Hoàng Bảo; cả hai consumer review |
| [realtime.schema.json](schemas/realtime.schema.json) | Envelope và từng message; dùng lại application DTO, không tự định nghĩa Job/Session lần hai | Hoàng Bảo |
| [chime-chat.schema.json](schemas/chime-chat.schema.json) | Giao thức `chat_v1` riêng, phụ thuộc D06; sender do attendee metadata xác minh | Đức + Hoàng Bảo |
| [fixtures/manifest.json](fixtures/manifest.json) | 144 fixtures + schema pointer, expected validity, metadata synthetic và 3 kịch bản nhất quán | Cả ba |
| [catalog.json](catalog.json) | Inventory máy đọc được của endpoint/event/schema và dependencies | Hoàng Bảo, Đức giữ đồng bộ |
| [contract-version.json](contract-version.json) | Version/status/hashes, liên kết snapshot CT-01; không có approval giả | Đức điều phối |
| [CHANGELOG.md](CHANGELOG.md), [VALIDATION.md](VALIDATION.md) | Ghi thay đổi, kết quả/giới hạn và lệnh kiểm tra | Người sửa contract |

Các JSON Schema dùng Draft-07 để tái sử dụng cho payload AsyncAPI; OpenAPI 3.1 tham chiếu schema ngoài có dialect khai báo. AsyncAPI 3 đặt `schemaFormat` trong **payload Multi Format Schema Object**, không đặt ở cấp message như v2. Nguồn chuẩn: [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0.html), [AsyncAPI 3.0](https://www.asyncapi.com/docs/reference/specification/v3.0.0#multi-format-schema-object).

## Mức hoàn thiện và phần chờ

| Phạm vi | Mức của draft | Còn phụ thuộc |
| --- | --- | --- |
| Raw OCR | Field shape có bằng chứng, không phải nghiệm thu model | Chất lượng/normalization/concurrency/readiness provider thật |
| Solo upload/job/result/resync | `x-completeness: solo-first`; mô tả chi tiết để review và tạo fixtures | D03/04/05/08/11/12/14 chưa được xác nhận; chưa phải đường API chạy được |
| Profile/lexicon/vocabulary | Schema rõ, ví dụ tổng hợp; policy còn đề xuất | Auth/email/token storage, corpus/dịch, lưu từ unknown, ownership/collections |
| Room/meeting/chat | Provisional | D06/D09/D11/D14/D15; object AWS hiện là passthrough hẹp, **chưa đủ để sinh SDK integration cuối** |
| Recording/playback | Provisional | D10/D11/D12; chưa chốt consent, codec, upload video solo, cách ghi solo-share và policy member xem lại |
| Stats/Admin/config/audit | Provisional | Công thức stats, role/revocation, D15/D16, dynamic config/worker ack và budget |

Chỉ `/ocr`, `/ws`, `/health`, `/` và `/static/*` OCR service hiện có implementation; chúng **không** nằm dưới `/api/v1`. Không có `/login` giả hoặc endpoint tự phát access token trong package này.

## Quy tắc chung

- App JSON snake_case, UTC ISO 8601 với `Z`; duration/timeline `_ms`. `Retry-After` là ngoại lệ header HTTP chuẩn tính bằng giây.
- App resource ID UUID; Cognito `sub` và AWS meeting/attendee IDs là opaque string. UUID do client tạo không cấp quyền truy cập; server kiểm đăng ký nguồn/ownership/membership.
- Success JSON `{data, request_id}`; error `{error: {code, message, details, retryable}, request_id}`. 204 **không body**. Unknown là null theo schema, không điền số mẫu hoặc chuỗi `"null"`.
- HTTP auth Bearer access token kiểm chứng. Profile PATCH không nhận email/role/status. Không tự chọn SDK, issuer, client ID, database keys hoặc region từ examples.
- Header `X-Data-Mode: mock|real` là **đề xuất bổ sung của draft này**, do cấu hình server quyết định. Examples là mock/synthetic; client không dùng header request để tự bật quyền hoặc chế độ mock trên real API. Gateway errors cần mapping về cùng envelope khi triển khai.
- Idempotency-Key ổn định theo caller/method/path/body. Key/body giống nhau trả cùng resource/action, khác body là 409. TTL key 24h là đề xuất D12; frame identity vẫn chống trùng trong vòng đời dữ liệu phiên. Khi expiry/quyền/nguồn đổi phải trả trạng thái rõ, không tạo job mới âm thầm.
- 144 fixtures là **dữ liệu tổng hợp**, không là kết quả thật. Placeholder credential đã che không thể dùng đăng nhập/Chime/WS. `origin: fixture`/`provider: fixture.synthetic` chỉ dùng mock được gắn nhãn; real mode không fallback sang chúng.

## Việc vẫn chưa chốt

Giữ toàn bộ câu hỏi CT-01. Review thêm những chi tiết draft mới: `current_source`/capture_limits trong session, source optimistic version, result `seq`, `through_seq` để resync có watermark, header X-Data-Mode, known-only vocabulary save, shared vocabulary không có review_state chung, reason/version/action của Admin. Đây là đề xuất contract cần duyệt, không thay đổi ngầm quyết định cũ.

Không tạo DB table/index, AWS resource, backend route hoặc sửa UI/provider trong CT-02. Xem bảng compatibility và thứ tự bàn giao trong hướng dẫn tích hợp.
