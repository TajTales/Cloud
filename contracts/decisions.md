# CT-01 — Sổ quyết định kiến trúc D01–D14

**DRAFT — ready_for_review, 11/11/2026.** Snapshot: HEAD `81be4b4a5a7baf24db0c9fdc5bbd2d72fed87340` cộng working tree chưa commit trong [audit](../docs/G0-CURRENT-STATE.md). Chưa đóng băng contract v1; tài liệu này không phải OpenAPI, không cấp quyền triển khai CT-02 và không xác nhận thay cho ba thành viên.

Nguồn đối chiếu: [kế hoạch mục 7](../docs/TIEN-DO-VA-KE-HOACH-HOAN-THANH.md#L275), PDF tr.4–15 và implementation được dẫn ở từng quyết định. Các phương án A/B dưới đây là lựa chọn để review, không phải hai implementation phải xây đồng thời.

## Quy ước trạng thái

| Trạng thái | Nghĩa |
| --- | --- |
| `EVIDENCED` | Sự kiện có bằng chứng trong code/test, chưa nói lựa chọn tương lai được nhóm duyệt |
| `PROPOSED` | Đã có đề xuất kỹ thuật đủ rõ để review, chưa xác nhận |
| `NEEDS_CONFIRMATION` | Cần nhóm quyết định phạm vi/chi phí/hành vi trước khi thiết kế hợp đồng chính thức |
| `BLOCKED` | Một phần quyết định thiếu đầu vào/truy cập để kiểm chứng; ghi rõ cách gỡ |

Không quyết định nào đã được xác nhận bởi cả ba người trong phiên này. D15/D16 đang có trong kế hoạch vẫn giữ trạng thái chưa xác nhận; audit D01–D14 không loại bỏ yêu cầu phân quyền Admin/cấu hình/audit của chúng.

## Bảng lựa chọn để review

| Mã | Đề xuất chính | Trạng thái | Chủ trì xác nhận; người còn lại cùng duyệt |
| --- | --- | --- | --- |
| D01 | Giữ tên/UI LinguaLive; OCR Learning là tên báo cáo; Nhật là mốc tích hợp đầu, Trung vẫn trong scope nếu chưa chốt giảm | `NEEDS_CONFIRMATION` | Đức; cả nhóm |
| D02 | OCR + cách đọc/từ điển + dịch có nguồn; ASR là scope riêng nếu giữ yêu cầu lời thoại | `NEEDS_CONFIRMATION` | Đức; cả nhóm |
| D03 | Một app API `/api/v1`, snake_case; giữ REST Gateway theo PDF, schema máy đọc được làm sau CT-01 | `PROPOSED` | Hoàng Bảo + Đức; cả nhóm |
| D04 | Frontend → app API; worker → provider nội bộ; lexicon là module độc lập trong backend trước | `PROPOSED` | Hoàng Bảo + Bảo Anh; cả nhóm |
| D05 | Ảnh HTTP/S3; durable job; WS chỉ control/result manifest; giữ raw OCR HTTP/WS nội bộ | `NEEDS_CONFIRMATION` | Hoàng Bảo + Bảo Anh + Đức |
| D06 | Chime meeting data messages cho chat trực tiếp; app WS cho OCR/room | `NEEDS_CONFIRMATION` | Hoàng Bảo + Đức; cả nhóm |
| D07 | Giữ React/Vite/Tailwind/lockfile; xác minh backend ngoài; Python 3.12/aiohttp là fallback đề xuất | `NEEDS_CONFIRMATION` | Chủ mỗi phần; cả nhóm |
| D08 | App UUID; Cognito sub/AWS IDs là opaque string; UTC/ms; normalized boxes + source timeline | `PROPOSED` | Cả nhóm |
| D09 | Personal vocabulary mặc định + bộ từ chung theo quyền phòng; không bỏ yêu cầu bộ chung của PDF | `NEEDS_CONFIRMATION` | Đức + Hoàng Bảo + Bảo Anh |
| D10 | Group capture + concatenate; solo file upload tùy chính sách; solo share recording cần luồng riêng | `NEEDS_CONFIRMATION` | Hoàng Bảo + Đức; cả nhóm |
| D11 | Khảo sát Singapore cho region chính; MeikiOCR là ứng viên Nhật cần test, giữ adapter Lens có chủ đích | `BLOCKED` | Hoàng Bảo + Bảo Anh; cả nhóm |
| D12 | Pilot 10 user/2 nguồn OCR; 1 frame/2s; ngưỡng đo và retention là mục tiêu đề xuất | `NEEDS_CONFIRMATION` | Cả nhóm |
| D13 | Backend lexicon adapter; giữ Yomitan renderer; chọn corpus/tokenizer/dịch sau kiểm chứng dữ liệu | `NEEDS_CONFIRMATION` | Bảo Anh; cả nhóm |
| D14 | Giữ form, Cognito public client/SDK SRP; access token xác minh; token memory trước, persistence cần chốt | `NEEDS_CONFIRMATION` | Hoàng Bảo + Đức; cả nhóm |

## D01 — Tên, phạm vi, Nhật/Trung

| Nội dung | Đánh giá |
| --- | --- |
| Hiện trạng `EVIDENCED` | UI dùng LinguaLive [App:346](../src/App.tsx#L346); PDF dùng OCR Learning. Corpus [transcriptVocabulary:15](../src/data/transcriptVocabulary.ts#L15) chỉ phục vụ câu Nhật; ngôn ngữ UI chỉ `vi/en` [App:284](../src/App.tsx#L284). Settings có `ja/zh/en/fr` [AccountPanels:16](../src/components/AccountPanels.tsx#L16) nhưng không chứng minh các pipeline đã hỗ trợ |
| A / B | A: giữ thương hiệu LinguaLive và sản phẩm OCR Learning, triển khai Nhật rồi kiểm chứng Trung. B: đổi thương hiệu/thiết kế hoặc giới hạn bản nộp chỉ Nhật |
| Đề xuất | **A**, giữ giao diện. Phân biệt `ui_locale` với `learning_language`. Ngôn ngữ có trong select/fixture không là ngôn ngữ được nghiệm thu |
| Lý do / ảnh hưởng | Tái sử dụng UI, giảm thay đổi vô ích. PDF tr.4/9 có Nhật/Trung: Nhật trước chỉ là thứ tự; muốn bỏ Trung ở bản cuối phải được cả nhóm xác nhận và sửa báo cáo |
| Module bị ảnh hưởng | Profile/settings, capability languages, OCR provider, lexicon, corpus kiểm thử, README/PDF |
| Xác nhận / trạng thái | Đức tổng hợp; cả ba xác nhận phạm vi và ngôn ngữ bản nộp. **NEEDS_CONFIRMATION** |

## D02 — OCR, cách đọc, dịch và ASR

| Nội dung | Đánh giá |
| --- | --- |
| Hiện trạng `EVIDENCED` | [OCR interface:26](../meikipop-ocr-server/src/meikipop_ocr_server/ocr/interface.py#L26) trả chữ/box; [transcript:243](../src/App.tsx#L243) có thời gian, cách đọc, dịch cố định; [pronounce:269](../src/App.tsx#L269) là TTS. Không thấy ASR client/service trong workspace |
| A / B | A: text lấy từ ảnh, đọc từ lexicon, dịch từ adapter riêng. B: thêm thu âm/ASR/diarization hoặc transcription Chime thành pipeline riêng |
| Đề xuất | **A cho mốc OCR đầu tiên**; xác nhận riêng B nếu vẫn giữ “lời thoại trực tiếp” PDF tr.6. Giữ layout tab nhưng sửa nhãn/mô tả dữ liệu trong task được giao sau; không sửa UI ở CT-01 |
| Lý do / ảnh hưởng | Chữ trên ảnh và tiếng nói là hai nguồn. Có Web Speech TTS không tạo transcript audio; OCR không tự sinh romaji/POS/nghĩa/dịch. Không dùng câu demo làm kết quả fallback |
| Module bị ảnh hưởng | Tab phiên âm, OCRResult/Transcript DTO, lexicon/translations, lịch sử, timeline, báo cáo; nếu B thì audio ingest/ASR/cost/test thêm |
| Xác nhận / trạng thái | Cả ba chốt nguồn của từng dòng transcript và có/không ASR trong bản nộp. **NEEDS_CONFIRMATION** |

## D03 — Public API, naming và app backend

| Nội dung | Đánh giá |
| --- | --- |
| Hiện trạng `EVIDENCED` | [server routes:231](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L231) chỉ có OCR/demo; [Vite:43](../vite.config.ts#L43) chưa proxy app API. `/api/v1` chỉ là [đề xuất kế hoạch:389](../docs/TIEN-DO-VA-KE-HOACH-HOAN-THANH.md#L389). Repo app backend bên ngoài **NOT_ACCESSIBLE** |
| A / B | A: một app backend module hóa, public REST API chung. B: frontend gọi từng OCR/auth/room/storage endpoint tự đặt hoặc chia nhiều service độc lập ngay |
| Đề xuất | **A**: `/api/v1`, JSON snake_case, envelope `data/request_id`, lỗi có code/retryable; UUID app, pagination/cursor và idempotency thống nhất. Ngoại lệ object Chime giữ casing SDK. Giữ Gateway REST như PDF; wiring authorizer/integration xác nhận cùng D11/D14 |
| Lý do / ảnh hưởng | Một nơi kiểm tra identity/ownership/room và lưu dữ liệu; frontend đổi model qua adapter, giữ component. Kiểm repo backend của Hoàng Bảo trước, không dựng backend trùng |
| Module bị ảnh hưởng | `src/api` dự kiến, app auth/profile/room/session/jobs/vocabulary/admin, Gateway; OpenAPI/fixtures chỉ làm sau gate G0 |
| Xác nhận / trạng thái | Hoàng Bảo chủ API, Đức review nhu cầu UI, Bảo Anh review result/lexicon. **PROPOSED** |

## D04 — Ranh giới thành phần

| Nội dung | Đánh giá |
| --- | --- |
| Hiện trạng `EVIDENCED` | React chưa gọi provider; [server:47](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L47) load provider theo interface; [YomitanEntry:18](../src/components/YomitanEntry.tsx#L18) chỉ map dữ liệu demo. Ranh giới OCR adapter đã có, app/lexicon thật chưa có |
| A / B | A: app API sở hữu identity/room/job/storage, worker gọi OCR nội bộ; lexicon là module có interface. B: mở provider thẳng cho browser và thêm user/room vào provider hoặc tạo microservices toàn bộ ngay |
| Đề xuất | **A**. Backend module hóa trước, worker có thể tách process vì model nặng; không bắt lexicon có server/DB riêng khi chưa có tải. OCR raw giữ `full_text/box/is_vertical/words` |
| Lý do / ảnh hưởng | Giữ lại service/provider đang có, tránh trùng auth, giảm số dịch vụ phải vận hành. Public result bọc metadata thay vì phá schema raw. Local standalone OCR test vẫn được dùng để debug, không trở thành đường bypass quyền sản phẩm |
| Module bị ảnh hưởng | App API, job repository/worker, OCR internal client, lexicon adapter; frontend chỉ public contract |
| Xác nhận / trạng thái | Hoàng Bảo + Bảo Anh xác nhận boundary, Đức xác nhận consumer. **PROPOSED** |

## D05 — HTTP/S3 hay WebSocket cho frame

### Bằng chứng giao thức

`aiohttp /ws` tại [server:153](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L153) cho message tối đa **50 × 1024 × 1024 bytes**, xử lý binary ở [162](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L162) và JSON base64 ở [178](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L178). Kết quả trả ngay cùng socket, không có Gateway connection registry hoặc room broadcast. Đây là protocol hiện hữu, **không phải** protocol cloud đã nghiệm thu.

AWS API Gateway WebSocket từ chối binary incoming và đóng kết nối code **1003**; text/base64 là một cách khác cần integration mapping phù hợp. Không thể chuyển nguyên lệnh `send_bytes()` sang Gateway. Nguồn kiểm tra 11/11/2026: [AWS binary media](https://docs.aws.amazon.com/apigateway/latest/developerguide/websocket-api-develop-binary-media-types.html).

Gateway có quota frame **32 KB**, message **128 KB**, integration timeout tối đa **29 giây**, idle **10 phút**, kết nối tối đa **2 giờ**. Browser `WebSocket.send()` không cung cấp quyền chủ động chia WebSocket protocol frame, nên không thiết kế ảnh lớn dựa vào giả định browser sẽ fragment đúng ý; app-level chunks cần protocol riêng. Nguồn quota: [AWS WebSocket limits](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-execution-service-websocket-limits-table.html).

Ảnh 1 MiB đổi base64 dài khoảng 1,398,104 byte, chưa tính JSON, vẫn lớn hơn một message Gateway. Các số 50M ở Nginx/50 MiB aiohttp không nâng quota Gateway. `$connect`/route/connection ID/Management API là lớp adapter riêng, không phải reverse proxy upgrade tới `/ws` hiện tại.

| Nội dung | Đánh giá |
| --- | --- |
| A | HTTP xin upload, PUT ảnh vào S3 theo quyền, tạo durable OCR job; WS gửi control/result manifest nhỏ, GET result/poll khi cần |
| B | Giữ ảnh qua Gateway WS bằng text/base64 chunks có upload/frame/chunk IDs, ghép mảnh, deadline, checksum, dedupe, giới hạn bộ nhớ, quyền và cleanup. Đây là phát triển protocol mới, không chỉ đổi URL |
| C nếu đổi kiến trúc PDF | WS trực tiếp sau reverse proxy tới app có auth có thể nhận binary, nhưng không qua Gateway WS. Phải tự vận hành/reconnect/broadcast và sửa PDF/contract; không tự chọn như đường tắt |
| Đề xuất | **A** cho cloud và cùng upload/job interface ở local. Ảnh không đi qua Gateway WS; raw `/ocr`/`/ws` giữ nội bộ/diagnostics. Upload/job chưa có, cần triển khai ở task sau |
| Lý do / ảnh hưởng | Hợp với tần suất thấp trong PDF, worker model có thể lâu hơn request; hỗ trợ retry/idempotency/poll/khôi phục worker. Đổi mũi tên frame của PDF tr.11–12 và task 5/13, không thay luồng WebRTC video |
| Module bị ảnh hưởng | Capture/source client, upload/job API, S3/CORS, worker, Gateway adapter/connection registry, result routing, retention/test/infra/PDF |
| Xác nhận / trạng thái | Cả ba xác nhận đổi transport ảnh và quyền truy cập S3 tạm. **NEEDS_CONFIRMATION** |

Phần app đề xuất: frame JPEG/PNG tối đa **1 MiB/4 MP**, resize cạnh dài tối đa 1600 px; một job in-flight/source, tần suất khoảng 2 giây; WS event app mục tiêu tối đa 24 KiB. Đây là budget app, không phải provider/AWS mặc định. Worker claim/lease + idempotent completion trong DynamoDB; commit result trước notification. V1 ưu tiên DDB durable job + poll/backoff theo kế hoạch; SQS là lựa chọn bổ sung nếu load/recovery chứng minh cần, không tự thêm hai queue cùng lúc.

Gateway route adapters phải quản lý `$connect/$disconnect`, subscribe theo membership và push bằng connection ID. Lambda authorizer chỉ dùng được ở `$connect`; do đó mỗi business action và broadcast vẫn kiểm tra quyền/expiry. Nguồn: [AWS WS authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api-lambda-auth.html). Worker/job không được dựa vào một socket sống để bảo đảm hoàn thành.

## D06 — Chat phòng học

| Nội dung | Đánh giá |
| --- | --- |
| Hiện trạng `EVIDENCED` | [App:847](../src/App.tsx#L847) chỉ render mảng local; [package.json:13](../package.json#L13) chưa Chime SDK. PDF tr.11 đặt text/voice/video ở Chime, nhưng chưa chốt meeting data messages hay Messaging service |
| A / B | A: Chime meeting data messages cùng meeting media, chat trực tiếp. B: app WS chat có lưu trữ riêng, hoặc Chime Messaging nếu cần lịch sử/channel lâu dài |
| Đề xuất | **A** phù hợp phạm vi hiện tại, topic draft `chat_v1`; app WS chỉ room/OCR. Giữ composer/render text, map sender từ attendee đã được cấp, không tin tên/role client tự khai |
| Lý do / ảnh hưởng | Tận dụng Chime đã yêu cầu trong PDF, tránh dựng transport chat thứ hai. Data messages có giới hạn payload/buffer, không phải kho lịch sử; cần nhóm xác nhận không có persisted chat v1. Ngân sách app <1500 byte UTF-8 toàn envelope và 500 ký tự UI, lấy giới hạn chặt hơn |
| Module bị ảnh hưởng | Chime client/meeting credentials, chat adapter, attendee identity, room lifecycle/tests; không cần thêm chat provider trong OCR |
| Xác nhận / trạng thái | Hoàng Bảo + Đức; cả nhóm xác nhận yêu cầu lịch sử chat. **NEEDS_CONFIRMATION** |

API gửi/nhận meeting data messages có trong [AWS JS AudioVideoFacade](https://aws.github.io/amazon-chime-sdk-js/interfaces/audiovideofacade.html#realtimesenddatamessage). Tài liệu SDK của AWS mô tả payload tối đa 2 KB và buffer có hạn; không suy thành lưu trữ vĩnh viễn: [AWS SDK data message guide](https://github.com/aws/amazon-chime-sdk-cpp/blob/main/guides/api_overview.md#7-send-and-receive-data-message). SDK/version cụ thể phải kiểm tra trước triển khai; chưa thêm package.

## D07 — Stack/runtime/dependency versions

| Nội dung | Đánh giá |
| --- | --- |
| Hiện trạng `EVIDENCED` | [.mise](../.mise.toml#L1), [lock importer](../pnpm-lock.yaml#L9), [pyproject](../meikipop-ocr-server/pyproject.toml#L9), [Docker](../meikipop-ocr-server/Dockerfile#L2). React 19.2.4/Vite 8.0.5/TS 5.9.3/Tailwind 4.2.2; Node máy 22.23.4; pnpm máy 12.18.0 lệch repo 10.34.3; Docker Python 3.12, máy test 3.14.7 |
| A / B | A: giữ frontend + lockfile, dùng backend hiện có nếu cung cấp được; nếu thực sự bắt đầu mới thì Python 3.12/aiohttp module hóa đồng bộ service. B: rewrite frontend/backend bằng framework mới |
| Đề xuất | **A**. Chốt Node patch phù hợp engine Vite và pnpm 10.34.3; xử lý lệch TS config bằng task CT-03 riêng. Python lock/extras và image version cần chủ OCR kiểm chứng, không chỉ dùng ranges hiện tại |
| Lý do / ảnh hưởng | Hạn chế churn và package trùng. Chưa có auth/Chime/AWS/dictionary SDK: CT-01 chỉ ghi nhu cầu, không chọn/cài bản mới hoặc nâng đồng loạt dependencies. Nếu backend ngoài khác stack nhưng phù hợp thì không ép rewrite Python |
| Module bị ảnh hưởng | Runtime manifests, CI/local setup, build/typecheck, backend dev server, OCR container; giữ UI và provider interface |
| Xác nhận / trạng thái | Đức frontend/toolchain, Hoàng Bảo backend, Bảo Anh Python/container; cả ba chốt. **NEEDS_CONFIRMATION** |

## D08 — ID, thời gian, đơn vị và tọa độ

| Nội dung | Đánh giá |
| --- | --- |
| Hiện trạng `EVIDENCED` | [interface:8](../meikipop-ocr-server/src/meikipop_ocr_server/ocr/interface.py#L8) normalized center/size; [server:60](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L60) chỉ scan elapsed_ms; [chat:849](../src/App.tsx#L849) UUID/time local; [adminDemo:6](../src/admin/adminDemo.ts#L6) IDs demo không phải IDs thật |
| A / B | A: quy tắc canonical theo resource/nguồn. B: ID/timestamp/đơn vị tùy module rồi đoán/chuyển ở từng component |
| Đề xuất | **A**: app resource IDs UUID; client tạo UUID đề xuất cho source_id/frame_id, backend đăng ký/xác nhận source, cấp source_index và kiểm quyền/idempotency. `user_id` là Cognito sub opaque string; meeting/attendee/pipeline IDs giữ nguyên AWS. UTC ISO 8601 cho thời điểm, integer `_ms` cho duration/timeline; `_px` cho pixel, bytes cho dung lượng |
| Lý do / ảnh hưởng | Không áp UUID regex chung lên sub/AWS IDs. Mỗi đổi nguồn có source_id mới; frame_index tăng theo source. `media_time_ms` không là wall clock: video dùng currentTime, screen dùng monotonic elapsed; recording có mapping riêng. Box normalized theo frame đã resize, vẽ sau letterbox/object-fit; validate box hữu hạn và nằm trong ảnh |
| Module bị ảnh hưởng | Toàn bộ DTO/IDs, profile/room, capture/overlay, result ordering/dedup, history/playback, Unicode token offsets |
| Xác nhận / trạng thái | Cả ba, Đức kiểm tra hiển thị, Bảo Anh kiểm tọa độ. **PROPOSED** |

AWS lưu ý Cognito sub không nên bị validate theo một chuẩn UUID cụ thể: [Cognito access token/sub](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html). Chi tiết [kế hoạch:333](../docs/TIEN-DO-VA-KE-HOACH-HOAN-THANH.md#L333) đã tách app UUID và sub; giữ ngoại lệ đó khi viết schema. Offset từ điển đề xuất Unicode code points, end-exclusive; tokenizer mẫu dùng UTF-16 index, không bê nguyên sang contract mới.

## D09 — Từ cá nhân và bộ từ chung

| Nội dung | Đánh giá |
| --- | --- |
| Hiện trạng `EVIDENCED` | [savedWords:392](../src/App.tsx#L392), [save:825](../src/App.tsx#L825) theo chữ; không owner/room/entry/sense ID hoặc shared repository. PDF tr.6 nêu xây bộ từ chung |
| A / B | A: personal mặc định, shared room scope riêng khi bật, quyền rõ ràng. B: tất cả từ lưu vào một bộ chung hoặc chỉ personal |
| Đề xuất | **A**. Một saved word identity theo owner/scope + language + entry_id + sense_id, nhiều occurrences; room có shared_vocabulary_enabled. Member thêm/xóa từ mình thêm, host quản lý bộ chung; backend kiểm quyền |
| Lý do / ảnh hưởng | Không làm mất quyền riêng tư dữ liệu cá nhân, tránh trùng chữ khác nghĩa và không bỏ yêu cầu PDF. Nút hiện có mặc định lưu cá nhân; thêm lựa chọn scope trong task tích hợp được xác nhận, không tự sửa thiết kế ở CT-01 |
| Module bị ảnh hưởng | Vocabulary/collection/review API, schema/index, popup save adapter, room shared list/quyền, history |
| Xác nhận / trạng thái | Đức UX, Hoàng Bảo persistence/quyền, Bảo Anh canonical dictionary identity; cả ba. **NEEDS_CONFIRMATION** |

## D10 — Lưu/phát lại video solo và group

| Nội dung | Đánh giá |
| --- | --- |
| Hiện trạng `EVIDENCED` | [useRoomMedia:39](../src/hooks/useRoomMedia.ts#L39) object URL chỉ tồn tại cục bộ. Không thấy upload video, MediaRecorder, Chime capture/concatenation hoặc signed playback API; history [App:278](../src/App.tsx#L278) cố định |
| A / B | A: đáp ứng playback thật theo từng nguồn. B: chỉ OCR text/history và state unavailable, giảm scope video |
| Đề xuất | **A để hoàn thành đúng PDF**, triển khai sau solo OCR/room. Group: Chime capture + concatenate, lưu S3 và metadata/timeline. Solo file: upload video có chủ đích nếu muốn mở lại trên thiết bị khác. Solo screen: recorder/upload pipeline riêng sau kiểm tra browser, không tạo Chime meeting chỉ để gọi solo |
| Lý do / ảnh hưởng | Chime không tự có recording chỉ vì đã tạo meeting. Text OCR/file object URL không thể tạo lại video. `unavailable/processing/ready/failed` cần cho UX nhưng không thay yêu cầu xem lại; nếu chọn B phải được cả ba duyệt và cập nhật PDF |
| Module bị ảnh hưởng | Consent/retention/giới hạn video, recording APIs, worker/media pipeline, S3, playback authorization/URL expiry, source→recording timeline, history/player |
| Xác nhận / trạng thái | Hoàng Bảo pipeline/cost, Đức browser/player; Bảo Anh log timeline; cả ba chốt nguồn và phạm vi video. **NEEDS_CONFIRMATION** |

Media capture tạo artifacts, concatenation mới ghép thành file lớn và bắt đầu ghép khi capture dừng; cần pipeline, S3 permissions và trạng thái xử lý: [AWS media concatenation](https://docs.aws.amazon.com/chime-sdk/latest/dg/create-concat-pipe.html). Không báo playback ready ngay khi người học rời phòng.

## D11 — Region, AWS services và OCR model

| Nội dung | Đánh giá |
| --- | --- |
| Hiện trạng `EVIDENCED` | Không region/bucket/table/user-pool/app-client/meeting deployment manifest trong repo. [DEPLOY:32](../meikipop-ocr-server/DEPLOY.md#L32) là manual EC2 guide; defaults glensv2 [server:248](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L248), Admin [adminDemo:5](../src/admin/adminDemo.ts#L5) MeikiOCR. AWS account và backend ngoài **NOT_ACCESSIBLE** |
| A / B | A: app/data region tập trung gần nhóm, khai báo Chime control/media/pipeline region riêng; benchmark local model cho Nhật. B: tiếp tục vùng/default provider khác nhau hoặc lấy remote OCR làm mặc định không kiểm chứng |
| Đề xuất | **A**; ứng viên `ap-southeast-1` cho app/data và Chime sau IF-01 smoke/quyền/budget. MeikiOCR là ứng viên chính cho Nhật vì adapter có sẵn; Lens giữ như provider được chọn rõ nếu cần. Không auto fallback giữa provider hoặc coi MeikiOCR đã đạt Trung |
| Lý do / ảnh hưởng | Quyết định model cần RAM/CPU/container/accuracy thật, có thể cần tải model lần đầu. ScreenAI cần native assets [provider:50](../meikipop-ocr-server/src/meikipop_ocr_server/ocr/providers/screenai/provider.py#L50); owocr cần service ngoài [provider:17](../meikipop-ocr-server/src/meikipop_ocr_server/ocr/providers/owocr/provider.py#L17). Không chọn t3.small từ ví dụ giá trong DEPLOY làm capacity đã đo |
| Module bị ảnh hưởng | Region/env, IAM/network/Gateway/EC2, Cognito/S3/DDB, Chime meeting/media pipelines, provider/container/model cache, cost/benchmark |
| Xác nhận / trạng thái | Hoàng Bảo cung cấp account/region/service evidence và repo backend; Bảo Anh real model test/asset version. **BLOCKED** ở phần kiểm chứng deployment/model; đề xuất vẫn review được |

AWS tách Chime meeting control/media và media pipeline regions; bảng hiện tại có Singapore cho cả control/media của hai nhóm đó: [AWS Chime regions](https://docs.aws.amazon.com/chime-sdk/latest/dg/sdk-available-regions.html). Đây là bằng chứng dịch vụ công bố, không là bằng chứng account nhóm đã được cấp quyền hoặc đã tạo tài nguyên.

## D12 — Capacity, latency, accuracy và retention

| Nội dung | Đánh giá |
| --- | --- |
| Hiện trạng `EVIDENCED` | [server:63](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L63) không đo upload/queue/broadcast; [test stream:224](../meikipop-ocr-server/test_server.py#L224) không benchmark accuracy. 6/6 dummy checks không cho p95/capacity model thật |
| A / B | A: pilot có budget/ngưỡng đo và dataset cố định, nâng tải sau bằng chứng. B: giữ “realtime/Auto Scaling” nhưng không định lượng |
| Đề xuất | **A**, các số bên dưới là mục tiêu đề xuất để duyệt, chưa đạt. Pilot tối đa 10 user, 2 nguồn OCR đồng thời (hai group hoặc group+solo); host/solo mỗi nguồn khoảng 1 frame/2 giây, một in-flight; không OCR lại theo mỗi member |
| Lý do / ảnh hưởng | Giới hạn tính theo nguồn, không theo viewer; 2 nguồn × 0,5 frame/s là tối đa khoảng 1 job/s trước backpressure, chưa có chứng cứ máy hiện tại xử lý nổi. Bỏ frame trung gian và report busy thay queue vô hạn |
| Module bị ảnh hưởng | Capture/rate limit, worker concurrency/queue/lease, metrics, infra scaling, lifecycle/retention, QA corpus/report |
| Xác nhận / trạng thái | Cả ba chốt ngưỡng và budget, Bảo Anh đo provider, Hoàng Bảo tải/cloud, Đức trải nghiệm. **NEEDS_CONFIRMATION** |

Budget đo đề xuất:

- OCR end-to-end p95 ≤4 giây tại pilot sau warmup; đo capture→render, tách upload/queue/scan/notify. Deadline job ban đầu 30 giây là giới hạn lỗi, không phải mục tiêu UX.
- Dataset ít nhất 100 ảnh Nhật gồm ngang/dọc/no-text/ảnh khó, transcript ground truth; đề xuất CER ≤10% trên subset chất lượng đã thỏa thuận, báo riêng subset khó/box. Trung cần corpus và ngưỡng riêng trước tuyên bố hỗ trợ. Đây là số để nhóm điều chỉnh, không lấy từ dummy.
- Chạy hai phòng tách dữ liệu ít nhất 30 phút, có reconnect/đổi nguồn/worker restart; không rò quyền hoặc mất job âm thầm. Chỉ chọn máy/concurrency/ASG sau số đo, không coi `--workers 2` là capacity cam kết.
- Raw frame đề xuất lên lịch dọn sau 1 ngày; OCR text/metadata 90 ngày, recording 7 ngày nếu người dùng bật lưu. Thời gian/quota/xóa theo yêu cầu phải được nhóm chốt; retention không đồng nghĩa đúng từng giây với cơ chế cleanup bất đồng bộ. Không xóa text đang cần chỉ vì raw frame hết hạn.

## D13 — Từ điển, tách từ, reading và dịch

| Nội dung | Đánh giá |
| --- | --- |
| Hiện trạng `EVIDENCED` | [data:15](../src/data/transcriptVocabulary.ts#L15) 18 mục tự soạn; [tokenizer:39](../src/data/transcriptVocabulary.ts#L39) greedy match, chưa morphology. [Yomitan:54](../src/components/YomitanEntry.tsx#L54) renderer thật; [snapshot README:10](../third_party/yomitan/README.md#L10) không DB/extension background |
| A / B | A: backend lexicon adapter theo schema, trả entry/sense/lemma/reading/POS/provenance; renderer hiện hữu nhận qua mapping. B: đưa toàn bộ Yomitan extension/DB/scanner vào website hoặc dùng LLM thay toàn bộ dictionary |
| Đề xuất | **A**. Bảo Anh khảo sát corpus Nhật (ứng viên JMdict) và tokenizer phù hợp runtime; chọn corpus Trung riêng nếu scope giữ. Chưa pin thư viện/corpus hoặc license chưa kiểm chứng. Không cần rewrite popup hoặc cài extension cho người dùng |
| Lý do / ảnh hưởng | Renderer không tự tạo nghĩa. Reading/POS/lemma phải từ nguồn thật; offset code point, end-exclusive, unknown có schema rõ. Nghĩa không phải tiếng Việt thì ghi ngôn ngữ thực; dịch Việt qua adapter riêng/có nguồn, nội dung sinh máy đánh dấu. Không để AI bịa mục từ khi lookup thất bại |
| Module bị ảnh hưởng | LX-01…05, cache/index/provider dữ liệu, lexicon DTO, YomitanEntry adapter, saved-word identity, translation service, corpus/notice/version |
| Xác nhận / trạng thái | Bảo Anh đưa corpus/sample results/giấy phép/version/runtime; Đức kiểm UI; Hoàng Bảo API/storage; cả ba duyệt. **NEEDS_CONFIRMATION** |

Nguồn JMdict chỉ là ứng viên khảo sát, chưa tải/import hoặc xác minh corpus/license trong workspace. Kiểm tra trang EDRDG ở lượt audit bị timeout, nên không dùng giả định về nội dung/điều khoản của corpus làm quyết định đã chốt. Giấy phép renderer hiện có ghi trong [snapshot:5](../third_party/yomitan/README.md#L5); giấy phép dictionary data là đầu vào riêng.

## D14 — Cognito flow và token policy

| Nội dung | Đánh giá |
| --- | --- |
| Hiện trạng `EVIDENCED` | [App:473](../src/App.tsx#L473) không gọi auth API; [profile:366](../src/App.tsx#L366) local; [AccountPanels:11](../src/components/AccountPanels.tsx#L11) không gửi email. Không Cognito SDK/config/issuer/client trong repo, dependency chưa được chọn |
| A / B | A: giữ form hiện tại, Cognito public app client không secret, SDK user-pool SRP/challenge flow. B: Managed Login Authorization Code + PKCE, form hiện tại chuyển sang nút điều hướng login, cần callback/logout config. Không tự triển khai password/token issuer giả |
| Đề xuất | **A để giữ UI**, phụ thuộc review SDK có hỗ trợ SRP và cấu hình app client. Có signup/confirm/reset/change-email/challenge states; social login chỉ bật khi IdP/flow riêng đã được cấu hình và nghiệm thu. B là phương án thay nếu nhóm ưu tiên managed login và chấp nhận UX điều hướng |
| Lý do / ảnh hưởng | Public client không có secret trong JS. API dùng access token đúng loại; kiểm signature/issuer/client_id/token_use/expiry và quyền tài khoản, không chỉ decode token hoặc tin local flag. Nếu giữ REST Gateway, đề xuất Lambda authorizer dùng cùng quy tắc access-token với backend; không cấu hình nhầm scope/token type khi chọn flow SRP |
| Module bị ảnh hưởng | Client auth adapter/form/challenges/session refresh, Gateway HTTP/WS authorizers, `/me`, Admin role/disable/revoke policy, local setup/tests |
| Xác nhận / trạng thái | Hoàng Bảo chủ Cognito/authorizer/token config; Đức browser/forms; Bảo Anh dùng service identity nội bộ; cả ba chốt. **NEEDS_CONFIRMATION** |

Token policy đề xuất để chốt cùng A:

1. Access token 15 phút, refresh token 1 ngày là budget v1 đề xuất, cấu hình theo khả năng app client và chi phí/UX nhóm chọn. Access/refresh giữ trong memory qua storage adapter, không dùng `lingualive-auth=true` hoặc tự để SDK fallback localStorage. Reload sẽ cần đăng nhập lại theo phương án này.
2. Nếu “Ghi nhớ đăng nhập”/giữ phiên qua reload là yêu cầu bắt buộc, **chưa được coi đã giải quyết**: nhóm phải chọn storage policy khác hoặc BFF HttpOnly-cookie và bổ sung contract/CSRF/logout trước CT-02. Không âm thầm bỏ tính năng PDF hoặc tự lưu refresh token dài hạn vào localStorage.
3. Refresh single-flight, lỗi hết phiên về login; không retry 401 vô hạn. Nếu bật refresh rotation thì phải dùng flow/API tương thích, không mặc định `REFRESH_TOKEN_AUTH` vẫn dùng được. Nguồn: [Cognito refresh/rotation](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-refresh-token.html).
4. Logout xóa state/cache theo user, revoke theo policy đã chọn và dừng media/socket. Admin khóa user cần account/session state được backend kiểm tra và đóng/revoke WS/Chime theo policy; chỉ verify JWT signature/exp không tự phản ánh mọi revocation. Nguồn: [Cognito revocation limitations](https://docs.aws.amazon.com/cognito/latest/developerguide/token-revocation.html).
5. WS browser xin ticket ngắn hạn một lần từ app API có xác thực; không gắn refresh token vào query. Vai trò User/Admin lấy từ danh tính/quyền kiểm chứng, host/member từ membership; dev preview phải tắt trong real mode kể cả DEV=true.

Flow SRP/challenge và phương án managed login được mô tả tại [Cognito authentication flows](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-authentication-flow-methods.html). Audit đã kiểm dependencies hiện tại; chưa chọn thêm SDK cụ thể, chưa tạo Cognito pool/client hoặc endpoint login.

## Ghi nhận xác nhận và gate tiếp theo

| Người | Xác nhận phương án/ngoại lệ | Ngày / bằng chứng |
| --- | --- | --- |
| Nguyễn Tài Đức | Chưa có | Chưa có |
| Nguyễn Hoàng Bảo | Chưa có | Chưa có |
| Trần Nguyên Bảo Anh | Chưa có | Chưa có |

Khi review, ghi lựa chọn từng Dxx, ngoại lệ, người xác nhận và link bằng chứng; nếu đổi phương án thì cập nhật cả [kiến trúc](../docs/G0-INTEGRATION-ARCHITECTURE.md) và [câu hỏi](../docs/G0-OPEN-QUESTIONS.md). Giữ số D01–D14 để không làm mất mapping task cũ. D15/D16 phải được review cùng trước freeze v1 cho User/Admin.

**CT-02 chính thức chưa được bắt đầu.** Chỉ khi cả nhóm chốt scope/transport/auth/stack/IDs/storage/ownership và xử lý input còn thiếu mới giao viết OpenAPI/AsyncAPI/fixtures chuẩn; không gọi tài liệu draft này là hợp đồng đã freeze.
