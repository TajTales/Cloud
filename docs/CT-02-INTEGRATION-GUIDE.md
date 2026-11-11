# CT-02 — Hướng dẫn frontend/backend/OCR dùng chung contract

**DRAFT 0.1.0-draft.1. Chưa phải hợp đồng chính thức.** Đọc [contract README](../contracts/README.md), [decisions](../contracts/decisions.md) và [câu hỏi CT-01](G0-OPEN-QUESTIONS.md). Các bảng dưới mô tả interface để review; không báo API đã triển khai.

## 1. Interface hiện tại và mapping cần làm

| Bằng chứng hiện tại | Khác biệt với draft | Adapter/task tiếp theo |
| --- | --- | --- |
| [App.tsx:243](../src/App.tsx#L243): TranscriptLine mẫu có time/japanese/reading/translation | Raw OCR chỉ chữ/box; thời gian public là media_time_ms; reading/nghĩa/dịch thuộc lexicon/translations, không ASR | Đức map text/timeline vào UI; Bảo Anh/Hoàng Bảo cung cấp lexical data; D02 chốt nguồn transcript |
| [transcriptVocabulary.ts:15](../src/data/transcriptVocabulary.ts#L15): 18 mục và greedy tokenizer | Không có morphology/source/sense IDs; index JS hiện UTF-16 | Bảo Anh lexicon thật; Đức dùng Array.from(text) khi map code point, không đem index UTF-16 làm offset chuẩn |
| [YomitanEntry.tsx:18](../src/components/YomitanEntry.tsx#L18): word/kana/romaji/partOfSpeech/meaning | Contract dùng surface, lemma, reading object, POS enum, meanings/examples/source | Giữ renderer; map qua lexiconClient. Không ép null thành nghĩa mẫu, không mất provenance hoặc nhiều sense |
| [App.tsx:392](../src/App.tsx#L392), [ReviewCards:5](../src/components/ReviewCards.tsx#L5): save/review trong state theo chữ | API dùng word_id + entry_id/sense_id + scope/owner/version/review_state | Dùng IDs chống trùng, API error/retry rõ; shared words không có review_state chung |
| [useRoomMedia.ts:9](../src/hooks/useRoomMedia.ts#L9): file/screen preview, cleanup đã có | kind chuẩn local_video/screen_share; chưa capture/upload/source/job IDs | Giữ hook/UI, thêm source registration + frame client; chỉ owner/host được gửi |
| [App:402](../src/App.tsx#L402), [457](../src/App.tsx#L457): roomCode/demo role state | room_id khác invitation code, membership do server cấp; Admin role khác room_role | roomClient + auth adapter lấy verified identity/capabilities, không gửi dev role làm quyền |
| [server.py:60](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L60), [routes:231](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L231) | HTTP /ocr và raw WS /ws tồn tại; không public app API, durable jobs hoặc broadcast | Hoàng Bảo app boundary; Bảo Anh worker/provider; Đức chỉ dùng public API ở real mode |
| [interface.py:26](../meikipop-ocr-server/src/meikipop_ocr_server/ocr/interface.py#L26), [static demo:737](../meikipop-ocr-server/src/meikipop_ocr_server/static/index.html#L737) | Provider full_text/box/is_vertical khác demo text/bounding_box/direction | Không đổi raw để chiều consumer sai; sửa static demo trong task OCR khác, không ở CT-02 |
| [AdminWorkspace:38](../src/admin/AdminWorkspace.tsx#L38) | Fixture IDs/local audit/config không là User/Admin DTO hoặc worker effective config | Đức nối adapter; Hoàng Bảo quyền/audit/action/version; Bảo Anh ack/metrics, theo D15/D16 |

## 2. Luồng Solo chuẩn của nhánh draft D05

1. Cognito auth adapter nhận access token hợp lệ → `GET /me`. Không có endpoint app tự phát token; SDK/flow/token storage chưa chốt D14.
2. `POST /sessions` với mode solo/title/language và Idempotency-Key; owner do server xác định. Giữ session_id/version/latest_seq/capture_limits, không lấy từ profile demo.
3. Tái sử dụng media hook, tạo source_id UUID mới khi đổi nguồn; `POST /sessions/{id}/sources` với expected_version và metadata gốc. Server xác nhận current source, source_index tăng và trả session_version. Retry cùng key/body không ghi đè nguồn mới sau đó.
4. Capture frame_id/frame_index trong nguồn, floor(currentTime*1000) hoặc monotonic elapsed. Resize giữ tỉ lệ, tối đa cạnh 1600 px, 1 MiB/4 MP theo giới hạn hiệu lực; chỉ một in-flight, bỏ frame trung gian khi bận.
5. `POST /sessions/{id}/uploads` với metadata → upload_id và upload.method/url/headers/expires_at. **PUT raw bytes tới đúng URL và headers được cấp, không thêm Bearer token app vào storage URL**, không bọc base64/JSON. S3/dev-storage cần CORS và validation riêng; URL hết hạn không là frame mới.
6. `POST /sessions/{id}/ocr-jobs` với upload_id/frame_id và Idempotency-Key. Server validate binding/object bytes/pixel/format/nguồn/quyền; mới trả 202 queued. Cùng key/body hoặc frame đã đăng ký trả 200 cùng job; khác body/key collision trả 409. Backend conditional writes là việc triển khai, fixtures không chứng minh nó.
7. Worker claim job durable/lease → gọi internal /ocr. Scan trả [] là no-text thành công. Error string/exception phải được map: invalid image, unavailable, timeout, invalid response; không gửi stack trace ra public. Giữ original raw schema, kiểm geometry ở adapter trước publish public result; không silently clamp box hoặc bịa text.
8. Lưu result/index → commit job succeeded/result_id → notify manifest. Crash trước/sau notify có retry/reconciliation; không hứa exactly-once. Kết quả muộn vẫn có thể lưu lịch sử nhưng UI không overlay nguồn khác.
9. Nhận `ocr.result_available` rồi `GET /results/{id}` hoặc poll `GET /ocr-jobs/{id}` theo poll_after_ms. **Job failed/expired vẫn GET 200 với error trong data**; HTTP 401/403/404 là lỗi truy cập request, không job giả. No-text public result vẫn succeeded với paragraphs [].
10. Lookup bằng paragraph original text/context refs all-or-none; text phải khớp paragraph và quyền. Lưu từ known entry/sense qua API, ôn patch review_state/version; reload phải đọc dữ liệu thật. Unknown save policy chưa chốt, không tự cấp entry_id giả.

`POST /uploads` là frame upload, không phải video upload cho D10. Metadata client không thay kiểm tra bytes thực trên server. Header Retry-After dùng giây, các duration JSON dùng _ms. S3 object keys, user_id và actor do server cấp/kiểm, không do frontend dựng tùy ý.

## 3. WebSocket: scope, sequence và phục hồi

- Xin ticket bằng HTTP đã xác thực. Response ws_url **không kèm ticket**; client append query ticket một lần qua URL API/encoding. TTL đề xuất 60s, dùng một lần; không log ticket/access token/JoinToken. Connection không sống quá connection_expires_at, phải xin vé mới khi reconnect.
- Backend kiểm quyền lúc connect, từng action và lúc fanout. Đăng ký session/group không đồng nghĩa người gọi được gửi OCR. Membership/role/account bị thu hồi phải dừng subscription và xử lý WS/media theo policy đã duyệt.
- `room.subscribe` chỉ đăng ký trạng thái phòng, không tự đăng ký OCR. Sau join/snapshot, client dùng shared_session_id để gửi `session.subscribe` riêng nếu cần nhận OCR; unsubscribe không thay REST leave/end.
- Client envelope dùng `action`, `request_id`, `payload`. Server dùng `type`, `event_id`, `request_id` nullable, `seq` nullable, `session_id` nullable, `room_id` nullable, `occurred_at`, `data`. `data` thay vì `payload` ở server là giữ quy ước kế hoạch, không hai payload format tùy consumer.
- seq chỉ cho session domain events. ACK/heartbeat/request.failed dùng seq=null; session ACK vẫn có session_id. Room events có session_id=null/seq=null, room_id và room_version; không so room_version với session seq. Event manifest giữ cùng session_id/seq như top envelope.
- Client lưu event_id/result_id đã apply, bỏ lặp, bỏ nguồn cũ và frame_index nhỏ hơn frame đang xem trong cùng source. Không so frame_index giữa hai nguồn; source order lấy source_index/current_source từ server.
- `after_seq` là gợi ý, **không cam kết replay durable event log**. Đăng ký subscription và lấy snapshot/watermark phải bảo đảm không có khoảng mất event (atomic hoặc buffer tương đương). Nếu không chứng minh bắt kịp, ACK resync_required=true. V1 có thể luôn yêu cầu snapshot/resync khi client khác watermark.
- Khi resync: lấy session snapshot có latest_seq=N; query `/sessions/{id}/results?after_seq=...&through_seq=N&limit=20`, giữ nguyên watermark/filter qua next_cursor. through_seq là đề xuất draft mới; server trả lỗi validation nếu watermark không hợp lệ, không âm thầm dùng một giá trị khác. API này chỉ trả OCR manifests, không toàn bộ room/source events.
- Buffer events mới trong khi tải snapshot/pages; apply snapshot rồi results đến N, sau đó event >N. Nếu có gap/reorder mà không chứng minh an toàn, resnapshot thay vì advance watermark theo max(seq) và bỏ mất event. Room gaps dùng GET room/members, không đọc result list để phục hồi membership.
- App ping/pong khởi điểm 30s, hai lần không đáp thì reconnect; backoff 1/2/4/8... tối đa 30s có jitter. Đây là policy draft, không native WS ping string của aiohttp raw. Poll HTTP job/result khi WS hỏng; 401 refresh single-flight hoặc login lại, không retry vô hạn.
- UTF-8 serialized event tối đa 24 KiB (app budget), không ảnh/binary/base64, không full OCR paragraphs lớn. Chime chat_v1 là file riêng, payload <1500 byte UTF-8 và ≤500 code points; identity sender từ attendee metadata đã xác minh, render text, dedup client_message_id. Không tự thêm chat WS thứ hai.

## 4. Tổ chức adapter và owner — các path sau là ĐỀ XUẤT, chưa được tạo

| Phần dự kiến | Interface phải giữ | Owner |
| --- | --- | --- |
| src/api/appClient.ts + auth adapter | Base URL/env, Bearer access token, envelope/error, 204, correlation, mode header, 401/refresh; không local flag | Đức nối, Hoàng Bảo auth/HTTP |
| src/api/ocrClient.ts + media/capture hook | session/source/upload/job/result IDs, current source, expected_version, metadata/limits, WS+poll một result handler | Đức; Hoàng Bảo endpoints; Bảo Anh result |
| src/api/lexiconClient.ts | Original text/code point offsets, found/partial/unknown/error, provenance/POS/lemma/senses; map sang UI không rewrite renderer | Đức consumer, Bảo Anh processing, Hoàng Bảo routing/cache |
| Vocabulary/room/Admin clients | Stable IDs, personal/shared scope, pagination, permissions, version/conflict, 202/action/error; no fixture fallback | Đức; Hoàng Bảo backend |
| Worker adapter (repo/path do Bảo Anh giao) | Raw request/response, metadata từ job, validate geometry, lease/heartbeat/idempotent completion, writer interface; không tự tạo bảng/GSI/S3 prefix | Bảo Anh; Hoàng Bảo repository/storage helpers |
| Auth/room/storage/WS implementations | Verified subject/roles/membership, current source, durable job/index/connection registry; no provider quản lý user/room | Hoàng Bảo |

Server là nguồn chuẩn của profile/roles/owner/membership/limits. UI localStorage chỉ có thể là cache tách theo user; clear khi logout. Chế độ real không nhận origin fixture/provenance synthetic, không dùng nhãn “đã lưu” khi API lỗi hoặc “applied” khi worker chưa xác nhận.

## 5. Compatibility và điểm draft cần xác nhận

- **Raw OCR không breaking:** giữ đúng field và error string hiện hữu, không thêm public IDs vào provider; raw box ngoài ảnh vẫn shape-valid để không viết lại lịch sử. Public adapter mới phải từ chối geometry sai và tạo job error an toàn; schema semantic checks không sửa code OCR.
- **Consumer demo không tương thích trực tiếp:** full_text/box/is_vertical khác text/bounding_box/direction; display time/romaji/POS không có trong raw. Cần adapter và dữ liệu lexical thật, không đổi raw schema để khớp UI.
- App HTTP API chưa tồn tại trong workspace, nên đây là interface mới, chưa phải breaking release của backend đã chạy. Backend ngoài vẫn NOT_ACCESSIBLE; chủ repo phải kiểm tra tương thích trước khi nhận contract.
- So với ví dụ kế hoạch, draft bổ sung: source expected_version/session_version; Session.current_source/capture_limits/latest_seq; Result seq/created_at; through_seq bounded resync; top-level room_id trên mọi server event; X-Data-Mode; shared vocabulary không chứa personal review_state. Những bổ sung này **cần review**, không gọi là đã chốt.
- D14 auth/token storage/remember-session/email, D13 corpus/translation/unknown save, D10 recording/consent/video upload, D11 account/region/model, D12 limits/retention/stats/capacity và D15/D16 Admin vẫn chưa xác nhận. Admin config max 10 MiB của UI mẫu không nâng trần 1 MiB draft.
- MeetingCredentials cố ý giữ AWS casing với additionalProperties passthrough. Đây là schema hẹp để review shape, **không là schema SDK hoàn chỉnh**; không dùng placeholder để chứng minh gọi Chime được. Recording start/stop là provisional; solo video upload chưa có hợp đồng đầy đủ, không coi nhóm recording đã xong.
- Policy host leave/close/grace/cleanup, quyền history sau leave và thời hạn idempotency/notification recovery cần xác nhận và tests implementation; schema không thể chứng minh các hành vi này.

## 6. Inventory endpoint

Mọi operation là DRAFT; xem openapi.yaml cho request/response/required/nullable/status/examples/permissions cụ thể. Tất cả app endpoints dùng Bearer access token, chưa triển khai trong workspace. `solo-first` chỉ mức mô tả ưu tiên, không là trạng thái accepted.

| Method | Path | operationId | Mức | Phụ thuộc |
| --- | --- | --- | --- | --- |
| GET | `/api/v1/me` | `getMe` | provisional | D03, D04, D08, D14, D15 |
| PATCH | `/api/v1/me` | `patchMe` | provisional | D03, D04, D08, D14, D15 |
| POST | `/api/v1/sessions` | `createSession` | solo-first | D03, D04, D08, D14, D01, D02, D12 |
| GET | `/api/v1/sessions/{session_id}` | `getSession` | solo-first | D03, D04, D08, D14, D05, D12 |
| POST | `/api/v1/sessions/{session_id}/sources` | `registerSource` | solo-first | D03, D04, D08, D14, D05, D12 |
| POST | `/api/v1/sessions/{session_id}/end` | `endSession` | solo-first | D03, D04, D08, D14, D05, D15 |
| POST | `/api/v1/sessions/{session_id}/uploads` | `createFrameUpload` | solo-first | D03, D04, D08, D14, D05, D12 |
| POST | `/api/v1/sessions/{session_id}/ocr-jobs` | `createOcrJob` | solo-first | D03, D04, D08, D14, D05, D11, D12 |
| GET | `/api/v1/ocr-jobs/{job_id}` | `getOcrJob` | solo-first | D03, D04, D08, D14, D05, D12 |
| GET | `/api/v1/sessions/{session_id}/results` | `listSessionResults` | solo-first | D03, D04, D08, D14, D05 |
| GET | `/api/v1/results/{result_id}` | `getOcrResult` | solo-first | D03, D04, D08, D14, D05, D11 |
| POST | `/api/v1/lexicon/lookups` | `lookupLexicon` | provisional | D03, D04, D08, D14, D01, D02, D13 |
| POST | `/api/v1/translations` | `translateText` | provisional | D03, D04, D08, D14, D01, D02, D13 |
| GET | `/api/v1/vocabulary` | `listVocabulary` | provisional | D03, D04, D08, D14, D09, D13 |
| POST | `/api/v1/vocabulary` | `saveVocabulary` | provisional | D03, D04, D08, D14, D09, D13 |
| DELETE | `/api/v1/vocabulary/{word_id}` | `deleteVocabulary` | provisional | D03, D04, D08, D14, D09 |
| PATCH | `/api/v1/vocabulary/{word_id}/review` | `reviewVocabulary` | provisional | D03, D04, D08, D14, D09 |
| GET | `/api/v1/collections` | `listCollections` | provisional | D03, D04, D08, D14, D09 |
| POST | `/api/v1/collections` | `createCollection` | provisional | D03, D04, D08, D14, D09 |
| PATCH | `/api/v1/collections/{collection_id}` | `patchCollection` | provisional | D03, D04, D08, D14, D09 |
| POST | `/api/v1/rooms` | `createRoom` | provisional | D03, D04, D08, D14, D01, D06, D09, D11, D15 |
| GET | `/api/v1/rooms/{room_id}` | `getRoom` | provisional | D03, D04, D08, D14, D06, D15 |
| POST | `/api/v1/rooms/join` | `joinRoom` | provisional | D03, D04, D08, D14, D06, D11, D15 |
| POST | `/api/v1/rooms/{room_id}/leave` | `leaveRoom` | provisional | D03, D04, D08, D14, D06, D15 |
| POST | `/api/v1/rooms/{room_id}/close` | `closeRoom` | provisional | D03, D04, D08, D14, D06, D10, D15 |
| POST | `/api/v1/rooms/{room_id}/meeting-credentials` | `getMeetingCredentials` | provisional | D03, D04, D08, D14, D06, D11, D15 |
| GET | `/api/v1/rooms/{room_id}/members` | `listRoomMembers` | provisional | D03, D04, D08, D14, D06, D15 |
| GET | `/api/v1/rooms/{room_id}/vocabulary` | `listSharedVocabulary` | provisional | D03, D04, D08, D14, D09, D15 |
| POST | `/api/v1/rooms/{room_id}/vocabulary` | `saveSharedVocabulary` | provisional | D03, D04, D08, D14, D09, D13, D15 |
| DELETE | `/api/v1/rooms/{room_id}/vocabulary/{word_id}` | `deleteSharedVocabulary` | provisional | D03, D04, D08, D14, D09, D15 |
| GET | `/api/v1/history` | `listHistory` | provisional | D03, D04, D08, D14, D09, D10, D12 |
| GET | `/api/v1/stats` | `getStats` | provisional | D03, D04, D08, D14, D12 |
| POST | `/api/v1/sessions/{session_id}/recording/start` | `startRecording` | provisional | D03, D04, D08, D14, D10, D11, D12 |
| POST | `/api/v1/sessions/{session_id}/recording/stop` | `stopRecording` | provisional | D03, D04, D08, D14, D10, D11, D12 |
| GET | `/api/v1/sessions/{session_id}/playback` | `getPlayback` | provisional | D03, D04, D08, D14, D10, D11, D12 |
| POST | `/api/v1/realtime/tickets` | `createRealtimeTicket` | solo-first | D03, D04, D08, D14, D05 |
| GET | `/api/v1/admin/overview` | `adminOverview` | provisional | D03, D04, D08, D14, D11, D12, D15, D16 |
| GET | `/api/v1/admin/users` | `adminListUsers` | provisional | D03, D04, D08, D14, D11, D12, D15, D16 |
| GET | `/api/v1/admin/users/{user_id}` | `adminGetUser` | provisional | D03, D04, D08, D14, D11, D12, D15, D16 |
| PATCH | `/api/v1/admin/users/{user_id}/status` | `adminSetUserStatus` | provisional | D03, D04, D08, D14, D11, D12, D15, D16 |
| GET | `/api/v1/admin/rooms` | `adminListRooms` | provisional | D03, D04, D08, D14, D11, D12, D15, D16 |
| GET | `/api/v1/admin/rooms/{room_id}` | `adminGetRoom` | provisional | D03, D04, D08, D14, D11, D12, D15, D16 |
| POST | `/api/v1/admin/rooms/{room_id}/close` | `adminCloseRoom` | provisional | D03, D04, D08, D14, D11, D12, D15, D16 |
| GET | `/api/v1/admin/config` | `adminGetConfig` | provisional | D03, D04, D08, D14, D11, D12, D15, D16 |
| PATCH | `/api/v1/admin/config` | `adminPatchConfig` | provisional | D03, D04, D08, D14, D11, D12, D15, D16 |
| GET | `/api/v1/admin/health` | `adminHealth` | provisional | D03, D04, D08, D14, D11, D12, D15, D16 |
| GET | `/api/v1/admin/metrics` | `adminMetrics` | provisional | D03, D04, D08, D14, D11, D12, D15, D16 |
| GET | `/api/v1/admin/audit-events` | `adminListAudit` | provisional | D03, D04, D08, D14, D11, D12, D15, D16 |
| GET | `/api/v1/admin/audit-events/{event_id}` | `adminGetAudit` | provisional | D03, D04, D08, D14, D11, D12, D15, D16 |
| GET | `/api/v1/admin/actions/{action_id}` | `adminGetAction` | provisional | D03, D04, D08, D14, D11, D12, D15, D16 |

## 7. Inventory event và schema

| Hướng | Action/event | Schema |
| --- | --- | --- |
| Client → server | `session.subscribe` | `realtime.schema.json#/definitions/Command_session_subscribe` |
| Client → server | `session.unsubscribe` | `realtime.schema.json#/definitions/Command_session_unsubscribe` |
| Client → server | `room.subscribe` | `realtime.schema.json#/definitions/Command_room_subscribe` |
| Client → server | `room.unsubscribe` | `realtime.schema.json#/definitions/Command_room_unsubscribe` |
| Client → server | `app.ping` | `realtime.schema.json#/definitions/Command_app_ping` |
| Server → client | `session.subscribed` | `realtime.schema.json#/definitions/Event_session_subscribed` |
| Server → client | `session.unsubscribed` | `realtime.schema.json#/definitions/Event_session_unsubscribed` |
| Server → client | `room.snapshot` | `realtime.schema.json#/definitions/Event_room_snapshot` |
| Server → client | `room.unsubscribed` | `realtime.schema.json#/definitions/Event_room_unsubscribed` |
| Server → client | `ocr.result_available` | `realtime.schema.json#/definitions/Event_ocr_result_available` |
| Server → client | `ocr.job_failed` | `realtime.schema.json#/definitions/Event_ocr_job_failed` |
| Server → client | `session.source_changed` | `realtime.schema.json#/definitions/Event_session_source_changed` |
| Server → client | `session.ended` | `realtime.schema.json#/definitions/Event_session_ended` |
| Server → client | `room.member_joined` | `realtime.schema.json#/definitions/Event_room_member_joined` |
| Server → client | `room.member_left` | `realtime.schema.json#/definitions/Event_room_member_left` |
| Server → client | `room.closed` | `realtime.schema.json#/definitions/Event_room_closed` |
| Server → client | `request.failed` | `realtime.schema.json#/definitions/Event_request_failed` |
| Server → client | `app.pong` | `realtime.schema.json#/definitions/Event_app_pong` |

| Schema nguồn | Các kiểu chính / phạm vi |
| --- | --- |
| ocr-provider.schema.json | Success, Error, Paragraph, Word, BoundingBox — field shape hiện hữu |
| application.schema.json | Profile, Session/Source/CaptureLimits, Upload/Job, ResultManifest/PublicResult, Vocabulary/SharedWord/Review/Collection, Room/Membership, Playback/Stats, AdminConfig/Action/Audit và envelopes |
| lexicon.schema.json | Lookup data, KnownToken/UnknownToken, Reading, Meaning, Example, Source |
| realtime.schema.json | ClientCommand/ServerEvent oneOf và từng payload; tham chiếu DTO application |
| chime-chat.schema.json | chat_v1 riêng; byte budget là semantic rule |

## 8. Cách ba thành viên nhận và thay đổi contract

1. Đức đưa cùng package version + bundle_sha256 + CT-01 decisions hash cho cả ba AI; các file fixtures/manifest.json cùng version. Git HEAD hiện tại chưa chứa các file mới: không đưa HEAD cũ rồi nói consumer đã có CT-02.
2. Hoàng Bảo review HTTP/error/auth/permissions/room/pagination/state, Bảo Anh raw/public/worker/lexicon/code points, Đức kiểm UI fields/null/204/pending/retry và mapping. Ghi xác nhận cùng các quyết định còn thiếu trước freeze.
3. Sau khi package được commit theo quy trình nhóm, dùng **cùng contract commit SHA** và base branch để triển khai từng task. CT-02 draft không cấp quyền sửa frontend/server/infra hoặc deploy.
4. Thay path/field/unit/required/enum/auth/offset/box/state meaning là thay contract. Tạo CHANGELOG + fixtures + version mới, producer và consumer cùng review/test, không merge một phía rồi yêu cầu bên kia đoán.
5. Chạy validation contract và negative cases; tiếp đó CT-04/backend/worker/frontend tests và real-provider integration theo task. Fixture pass không cho chuyển integrated/accepted.

Đã thực hiện trong CT-02: chỉ contract/schema/docs/fixtures và công cụ validation tạm ngoài repo. Không sửa source hiện hữu, không cài dependency của app, không tạo database/AWS resources/login/mock server và không cập nhật approval của CT-01. Kết quả kiểm tra thực tế ở [VALIDATION](../contracts/VALIDATION.md).
