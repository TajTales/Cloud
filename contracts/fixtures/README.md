# Fixtures CT-02 — DRAFT / SYNTHETIC ONLY

Nguồn chuẩn là [manifest.json](manifest.json). Mỗi record có file, schema JSON Pointer, kind, expect_valid và data_mode; metadata không được nhét vào raw OCR payload để đổi schema provider.

- `http/`: request/success/error examples, job queued/succeeded/timeout, duplicate/idempotency/old-source, auth/permission, room create/join và lỗi. HTTP provider timeout sau khi job được chấp nhận là GET job **200 + status failed**, không phải polling 504.
- `ocr/`: raw success/no-text/error/invalid-image và out-of-bounds box vẫn shape-compatible. Không coi elapsed_ms synthetic là benchmark.
- `lexicon/`: found/partial/not_found và Unicode có emoji + dấu kết hợp. Nghĩa là `SYNTHETIC_GLOSS_A`, provider fixture.synthetic; không nhập corpus hoặc tuyên bố tra từ thật.
- `ws/`: 5 client commands, 13 server events và một bản lặp event cố ý để kiểm dedup.
- `chime/`: chat_v1 riêng, không có WS chat thứ hai.
- `negative/`: **16 trường hợp phải bị từ chối**; 11 lỗi schema và 5 lỗi ngữ nghĩa (tọa độ, Unicode/gap, byte budget). Không load chúng như API responses hợp lệ.

144 fixtures gồm 128 positive và 16 negative. Fixtures cùng loại có thể là các nhánh thay thế, không phải toàn bộ một phiên tuyến tính: cùng một job trong ví dụ success và failure không có nghĩa job thật được chuyển succeeded → failed. Chỉ ghép các file được khai báo trong manifest.scenarios.

Ba scenarios chỉ xác minh sự nhất quán của fixtures: retry job giữ cùng ID, late result không thuộc current source, duplicate event giữ cùng event_id. Chưa kiểm tra idempotency/authorization/dedup của một implementation thật. Nội dung token/credential đều là placeholder đã che, không phải API phát token giả.

Đọc [VALIDATION](../VALIDATION.md) trước khi dùng fixture để test. Không sửa fixture để che producer/consumer sai contract; sửa contract và cập nhật version/consumer cùng nhau sau review.
