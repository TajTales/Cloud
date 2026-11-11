# CT-04 — Fixtures bổ sung để review

**DRAFT / synthetic / chưa nghiệm thu.** Bộ này được tách khỏi 144 fixtures CT-02 và không thay đổi hash của package `0.1.0-draft.1`. [manifest.json](manifest.json) trỏ đúng `source_bundle_sha256` của package gốc; chứa 13 JSON mới, 24 mục coverage và 15 mock scenarios. Mọi case còn `DRAFT` cho tới khi cả nhóm xác nhận contract và đóng gói một release mới.

Các fixture mới chỉ dùng field, enum và HTTP status đã có trong draft CT-02. Validator kiểm tra cấu trúc để review, không chứng nhận behavior của backend/provider. Không dùng chúng làm kết quả OCR/từ điển thật.

| File mới | Mục đích |
| --- | --- |
| `ocr-vertical.json` | Raw paragraph có `is_vertical: true`, giữ nguyên schema provider |
| `image-too-large.json`, `ocr-busy.json` | Error envelope 413 / 429 cho operations được khai báo |
| `forbidden-session.json`, `forbidden-room.json`, `forbidden-shared-vocabulary.json` | Ba scope quyền khác nhau, cùng envelope 403 |
| `room-closed.json` | Join phòng đóng trả 409 theo draft |
| `job-processing.json` | Polling 200/processing, chưa có result hoặc error |
| `out-of-order-frame.json`, `out-of-order-event.json` | Event seq 3 đến sau seq 2 nhưng frame index 16 cũ hơn 17; WS tham chiếu đúng result mới nhận |
| `lexicon-inflected.json` | Surface biến hình và lemma khác nhau, offset code point |
| `lexicon-polysemy-a.json`, `lexicon-polysemy-b.json` | Hai kết quả chọn nghĩa khác nhau cho cùng entry, giữ `sense_id` riêng |

Polysemy chỉ kiểm tra định danh hai nghĩa trong **hai response riêng**. Schema hiện có một `entry_id`/`sense_id` mỗi token; hiển thị đồng thời nhiều nghĩa/entry vẫn `PENDING_D13`. Không tạo token chồng lấn hoặc field `alternative_senses` để che giới hạn này.

Nguồn liên kết: [hướng dẫn chạy](../../../docs/CONTRACT-TESTING.md), [nghiệm thu](../../../docs/ACCEPTANCE.md). Không chỉnh manifest gốc hoặc đổi trạng thái approval chỉ để mock khởi động.
