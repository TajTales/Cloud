# Nhóm 4 — API ứng dụng local

Ngày bàn giao: 13/11/2026. Owner: Nguyễn Tài Đức. “Nhóm 4” ở đây theo thứ tự backend đang thực hiện: nền tảng → DB → auth → API → OCR. Không đồng nhất với G4 phòng học thời gian thực trong kế hoạch gốc.

Trạng thái: **LOCAL_IMPLEMENTED / READY_FOR_MANUAL_REVIEW** cho phạm vi bên dưới. Không tuyên bố toàn bộ backend hoặc 50 endpoints đã hoàn thành. Public contract `0.1.0-draft.1` vẫn **DRAFT**, 159 file original bundle giữ nguyên; SHA-256 `bcfd39b6a2fd85d74cd5efd53e7a6bff753f60bf7e286246c27ef696c1c6bfd2`. Không approve D01…D14/D15/D16 thay chủ dự án, không deploy/AWS/Docker/migration/commit/push.

## Các API có handler thật

Đều dùng `/api/v1`, Bearer local đã xác minh, JSON snake_case, UTC ISO 8601, UUID tài nguyên, error envelope và request/response validation theo OpenAPI gốc. ID user vẫn opaque `local:<UUID>` của adapter phát triển, chưa phải Cognito sub. Các mutation theo contract tiếp tục dùng Idempotency-Key hoặc expected_version.

| Nhóm | Method/path tương đối | Tình trạng |
| --- | --- | --- |
| Profile | GET/PATCH `/me` | Đã có từ tích hợp trước, giữ CAS và fields authority chỉ đọc |
| Từ cá nhân | GET/POST `/vocabulary`; DELETE `/vocabulary/{word_id}`; PATCH `/vocabulary/{word_id}/review` | Giữ lưu/xóa/review thật; thêm collection_id có kiểm scope/ngôn ngữ. Catalog mẫu vẫn được ghi origin=fixture, chưa phải lexicon thật |
| Phiên Solo | POST `/sessions`; GET `/sessions/{session_id}`; POST `/sessions/{session_id}/end` | Current source, watermark và capability thật; end chống version race với OCR worker |
| History/stats | GET `/history`, GET `/stats` | Đọc dữ liệu caller; không thay null bằng số mẫu. Private history metadata vẫn đọc được sau rời phòng; content phòng vẫn theo membership |
| Nguồn học | POST `/sessions/{session_id}/sources` | Client source UUID, server source_index/version/CAS; snapshot current_source đầy đủ |
| Frame/job | POST `/sessions/{session_id}/uploads`; POST `/sessions/{session_id}/ocr-jobs`; GET `/ocr-jobs/{job_id}` | [Luồng OCR](GROUP-05-OCR-PIPELINE.md), upload thật, worker/job thật |
| Kết quả | GET `/sessions/{session_id}/results`; GET `/results/{result_id}` | Manifests phân trang có through_seq, cursor bind filter; chi tiết từ object storage |
| Bộ từ | GET/POST `/collections`; PATCH `/collections/{collection_id}` | CRUD trong contract, version và quyền sở hữu; word_count tính từ từ đã lưu, không số giả |
| Phòng metadata | POST `/rooms`, POST `/rooms/join`, GET `/rooms/{room_id}` | Mã 8 ký tự ngẫu nhiên đúng alphabet contract; room/session/host/history/counter tạo atomic |
| Thành viên/vòng đời | GET `/rooms/{room_id}/members`; POST `/rooms/{room_id}/leave`; POST `/rooms/{room_id}/close` | Host/member thật; join lặp không tăng count; leave/rejoin, host leave đóng phòng; đóng session cùng transaction |

Tổng: **26/50 public operations có handlers** (11 cũ + 15 mới). 16 routes auth local của nhóm 3 và PUT upload vận hành local là overlay riêng, không cộng vào 50 operations.

Các public operations khác còn trả lỗi chưa cấu hình có chủ đích: lexicon/translation, shared vocabulary, realtime ticket/events, Chime meeting credentials, recording/playback và Admin business APIs. Không phát token, meeting hoặc dữ liệu minh họa để làm các endpoint này trông như đã hoạt động.

## Các quy tắc đã áp dụng

- Profile do verifier đọc từ DB mỗi request; endpoint người học luôn kiểm owner/membership kể cả caller có role Admin. Quyền repository của internal worker không được truyền thẳng cho browser Admin. Quản trị local nhóm 3 vẫn qua route/permission riêng.
- Chỉ chủ phiên/chủ nguồn được đăng ký nguồn hoặc gửi frame. Thành viên phòng khác/đã rời không lấy được nguồn/job/result. Phòng đóng read-only cho người vẫn có membership lịch sử; không tạo capability gọi/ghi hình giả.
- Phòng metadata có giới hạn local **8 người**, ghi rõ là guard triển khai local, không tự approve D12 cho cloud. Counter CAS cùng room/membership transaction để join/leave/close không làm số thành viên sai do concurrency. Mã phòng được giữ bằng unique record.
- Khi chủ phòng rời, phòng/session đóng. `left_at` của membership còn hiện diện được suy từ closed_at khi room đóng; không cần rewrite hàng loạt membership. Presence phòng đóng bằng 0. Khi member tự rời, membership left_at lưu thật và quyền nội dung bị thu hồi.
- Danh sách thành viên trả **RoomMember** gồm display_name theo schema, không trả nhầm Membership nội bộ. Public RoomSnapshot chứa room/membership/session đúng schema gốc.
- Idempotency lưu resource reference, không lưu signed upload capability hoặc token. Completion cùng transaction với domain writes. Reservation mới được release nếu mutation atomic thất bại; cùng key có thể retry sau validation/CAS fail mà không bị kẹt pending 24 giờ.
- Through_seq cố định snapshot kết quả; after_seq exclusive. Cursor bind session/source/after/through; không tái sử dụng cursor khi đổi filter.
- Lưu một nghĩa từ cá nhân vẫn duy nhất theo language/entry_id/sense_id; collection_id là một collection của record, không giả định một từ thuộc nhiều collection khi schema hiện tại chưa mô tả như vậy.

## Module và dữ liệu mới

| File | Vai trò |
| --- | --- |
| [media.py](../application-backend/src/lingualive_api/media.py) | Source/upload/job/result services, upload capability, frame order và queue slot |
| [rooms.py](../application-backend/src/lingualive_api/rooms.py) | Room metadata lifecycle, membership/count/permission |
| [collections.py](../application-backend/src/lingualive_api/collections.py) | Collections và word count |
| [learning.py](../application-backend/src/lingualive_api/learning.py) | Bổ sung source/capability, collection guard, history và end-session version handling |
| [local_integration.py](../application-backend/src/lingualive_api/local_integration.py) | Đăng ký 26 handlers, signed PUT và worker cleanup context |
| [app.py](../application-backend/src/lingualive_api/app.py) | Giữ ranh giới authority giữa learner API và internal worker |
| [idempotency.py](../application-backend/src/lingualive_api/persistence/idempotency.py) | Release có fencing cho pending reservation thất bại |

Không đổi physical table/GSI/model version hoặc reset dữ liệu. Primitive records bổ sung: `LOCAL_ROOM#MEMBER_COUNT`, `LOCAL_OCR#SLOT`, `LOCAL_OCR#FRAME_ORDER`. Domain rows tiếp tục qua catalog/schema gốc. Tất cả test tạo/xóa bảng `lingualive-test-*`, không seed account/room/job vào bảng ứng dụng.

## Kiểm thử và sử dụng

```bash
# DB phải đang chạy; không chạy thêm instance trên cùng port.
./scripts/test-api
# Khi chỉ kiểm module đang sửa:
./scripts/test-api -k BusinessIntegrationTests
./scripts/test-api -k MediaIntegrationTests
```

[Business tests](../application-backend/tests/test_business_integration.py) kiểm room create/join/leave/rejoin/close, quyền host/member, meeting unavailable, idempotency, collection version/scope/word_count. [Media tests](../application-backend/tests/test_media_integration.py) kiểm API/worker/DB, consumer TypeScript và các lỗi/stale/duplicate. Kết quả thực ở [report chung](group04-05-results.json); không đổi kết quả lịch sử nhóm 1–3 thành kết quả mới.

FE đã nối **Solo source/upload/job/polling/result và xem chữ trong history**. UI nhóm vẫn báo chưa sẵn sàng vì chưa nối meeting/media; phòng metadata API pass không có nghĩa gọi nhóm/chat pass. Collections API được kiểm qua HTTP; UI bộ từ tùy chỉnh chưa nối, không coi các deck minh họa là collection DB.

Các mục còn thuộc bước sau: lexicon thật để lưu từ OCR/occurrences, shared vocabulary; Chime/presence/realtime và host reconnect policy; recording/playback; Admin business API; chốt quy tắc streak/weekly goal và thời lượng nhiều lần rejoin; retention và AWS adapter/IAM/HTTPS/Cognito. Không tự đổi những mục đó thành completed từ kết quả local này.
