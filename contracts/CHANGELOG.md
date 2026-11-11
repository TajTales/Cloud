# Contract changelog

## 0.1.0-draft.1 — 11/11/2026 — DRAFT ONLY

- Tạo bộ CT-02 để review theo yêu cầu mới; giữ nguyên CT-01 decisions và toàn bộ source. Chưa có phê duyệt ba thành viên, chưa freeze/phát hành v1.
- Thêm OpenAPI 3.1.0 với 50 operations thuộc đủ 10 nhóm; Solo upload/job/result có model/state/errors/examples/idempotency/poll/resync chi tiết. Nhóm còn phụ thuộc dùng provisional + decision dependencies.
- Thêm AsyncAPI 3.0.0 với 5 commands/13 events; JSON manifests/control, auth/ticket/heartbeat/reconnect/dedup, không binary image hoặc WS chat.
- Giữ raw OCR field shape/error string và không thêm session/job IDs vào provider. Public OCR wrapper/strict geometry là model mới, không đổi raw service.
- Thêm lexicon Draft-07 với known/unknown, POS enum, code point offsets và provenance; corpus/dịch/provider thật chưa chọn.
- Tách personal review khỏi shared word; save unknown entry đang chờ policy D13. Thêm source version/snapshot limits, bounded result resync through_seq và đề xuất header X-Data-Mode.
- Thêm 144 synthetic fixtures (128 positive/16 negative), inventory, bundle hashes, hướng dẫn adapter/owner và validation tái lập. Không có backend/mock server/login hoặc AWS/DB resource được tạo.
- Breaking/mapping: consumer dùng text/bounding_box/direction không đọc được raw full_text/box/is_vertical; frontend demo cần adapter IDs/timeline/enums/ownership. Đây chưa phải breaking release của API ứng dụng vì API đó chưa tồn tại trong workspace.
