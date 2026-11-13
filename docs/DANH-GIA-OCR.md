# Đánh giá OCR và hợp đồng tích hợp với LinguaLive

**Triển khai tiếp theo, 13/11/2026:** task nhóm backend 4–5 đã cho phép thực hiện OCR. [Bản bàn giao mới](GROUP-05-OCR-PIPELINE.md) ghi source/upload/job/result, provider CPU Nhật/Trung, giới hạn/admission/timeout/cleanup/errors/readiness và static field mapping đã sửa; raw field shape giữ nguyên. Các nhận xét và hướng dẫn “không sửa server” bên dưới là phạm vi lượt review 11/11, không phải kết quả sau implementation. Docker/nginx/AWS/Gateway/Chime chưa nghiệm thu; không coi mọi đề xuất lịch sử đều đã hoàn tất.

Cập nhật: 11/11/2026. Chỉ đánh giá và đề xuất; **không sửa bất kỳ tệp nào trong `meikipop-ocr-server/`**.

## 1. Kết luận và giao diện cần phục vụ

Server hiện đủ cơ sở cho OCR ảnh/khung hình qua HTTP và WebSocket trực tiếp. Chưa phải backend quản lý phòng, tài khoản, truyền video hay lưu lịch sử.

Giao diện giữ bố cục Figma đã được người dùng chấp nhận, với nâng cấp hover và popup Yomitan. Theo cập nhật User/Admin, `useRoomMedia` đã mở được video hoặc chia sẻ màn hình để xem trước cục bộ. Nguồn thật chưa được chụp canvas/nén/gửi tới OCR; khi mở nguồn thật, overlay mẫu được ẩn. Chữ nhận dạng, phiên âm và bản dịch vẫn là dữ liệu mẫu. Khi tích hợp tiếp cần client frame/upload/job/result và overlay theo kết quả thật, không coi dữ liệu demo là output server. Xem [ghi chú User/Admin](GIAO-DIEN-USER-VA-ADMIN.md) cho phần UI mới.

Cần giữ tên LinguaLive trong frontend và dùng tên này khi ghi tài liệu tích hợp. Báo cáo môn học gọi hệ thống là OCR Learning; có thể chú thích “LinguaLive – giao diện của OCR Learning” để thống nhất mà không đổi thương hiệu đã có.

## 2. Những lỗi cần sửa và đề xuất

### Những phần hợp lý

- Có interface provider chung và dataclass kết quả; hỗ trợ thay bộ nhận dạng.
- Lazy-load provider giúp thử dummy mà không cần model cục bộ.
- Có HTTP `/ocr`, WebSocket `/ws`, health `/health`.
- Trả đoạn, từ và tọa độ; phù hợp việc hiển thị overlay trên frontend.
- Đưa xử lý đồng bộ vào thread pool để không chặn event loop.
- Có test CLI, Dockerfile và cấu hình proxy WebSocket.

### Các vấn đề ưu tiên sửa

| Ưu tiên | Vị trí / bằng chứng | Vấn đề và hướng xử lý |
| --- | --- | --- |
| P0 trước demo OCR | `static/index.html`: `renderResults`, `renderBoundingBoxes` | UI đọc `p.text`, `p.bounding_box`, `p.direction`, trong khi server trả `full_text`, `box`, `is_vertical`. Thử bằng trình duyệt: API trả 2 đoạn nhưng nội dung đoạn rỗng và số overlay bằng 0. Copy cũng dùng `p.text`. Đồng bộ schema ở toàn bộ nơi đọc kết quả. |
| P0 trước nối HTTP khác origin | `server.py`: `create_app`; frontend chưa có proxy API | Browser gọi từ 8443 sang 8080 bị CORS; preflight `/ocr` trả 405. Dùng reverse proxy cùng origin hoặc middleware CORS giới hạn origin cụ thể. WebSocket khác origin ping thành công, nên phải xem riêng quyền truy cập WS. |
| P0 trước triển khai kiến trúc báo cáo | `/ws` hiện là kết nối WebSocket trực tiếp với aiohttp | Không thể đặt API Gateway WebSocket phía trước như một proxy WS thông thường. Cần adapter route/connect/disconnect và gửi kết quả qua connection ID; xử lý kiểu payload, kích thước và xác thực. Xem mục 6. |
| P1 trước public | `server.py`, `docker-compose.yml` | Không có kiểm tra token, phân quyền phòng, giới hạn tần suất hoặc Origin WS. Compose publish cả 8080 và 80. Nếu public cần auth ở gateway/service, hạn chế đường truy cập bỏ qua proxy, quota từng user và bảo vệ phiên. |
| P1 | `create_app`, `_extract_image_bytes`, `nginx.conf` | Nginx cho 50 MB, WS cho 50 MB nhưng app HTTP dùng giới hạn mặc định. Thử raw và multipart 1 MiB + 1 byte đều trả 400 “Content Too Large”. Cần giới hạn thống nhất theo mục đích, giữ HTTP 413 cho quá kích thước, kiểm tra kích thước ảnh sau giải mã. |
| P1 | `ThreadPoolExecutor(max_workers=2)` và cùng một đối tượng provider | Nhiều request/socket dùng chung provider. Đặc biệt owocr giữ một WebSocket đồng bộ có thể bị dùng đồng thời. Cần lock hoặc instance riêng theo worker và kiểm thử concurrency. Đây là nguy cơ từ mã, chưa tái hiện bằng load test. |
| P1 | Executor, provider session/socket | Chưa có cleanup khi app dừng; hàng đợi executor chưa có admission control cho nhiều client. Bổ sung cleanup context, giới hạn công việc chờ và timeout xử lý. |
| P1 | `_run_ocr`, xử lý lỗi HTTP/WS | Exception nội bộ được trả thẳng cho client; lỗi input/provider có mã phản hồi chưa nhất quán. Chuẩn hóa error code, thông báo dễ hiểu, giữ chi tiết trong log server. |
| P1 | Provider `glensv2` | Có khóa API ghi trực tiếp và gọi endpoint Lens bên ngoài. Cần xác minh nguồn/quyền sử dụng khóa, đưa cấu hình ra môi trường; không coi đây là dịch vụ có cam kết ổn định. Ảnh sẽ gửi tới bên thứ ba, cần chọn provider và thông tin cho người dùng phù hợp. Không chép khóa vào ghi chú. |
| P1 phạm vi sản phẩm | Bộ lọc `JAPANESE_REGEX` trong glensv2/meikiocr | Các dòng không khớp bộ ký tự này bị loại; nội dung EN/FR trên UI chưa được chứng minh hỗ trợ. Tiếng Trung cũng cần bộ ảnh kiểm thử riêng, không suy ra hỗ trợ đầy đủ chỉ vì có Han characters. |
| P2 | `health`, provider meikiocr | Health hiện báo server sống; meikiocr bắt lỗi khởi tạo mà không làm startup fail, nên có thể health OK trong khi model chưa sẵn sàng. Tách liveness và readiness. |
| P2 | `pyproject.toml`, Dockerfile | Provider local nặng được cài bắt buộc dù dùng glensv2/dummy. Tách dependency theo extras, khóa phiên bản đã kiểm chứng. Chưa build Docker trong lượt này. |
| P2 | DEPLOY.md và nginx.conf | Hướng dẫn systemd copy nginx.conf của Compose nhưng upstream là hostname `ocr-server`, còn systemd bind trên host. Với cài trực tiếp cần upstream `127.0.0.1:8080`; không dùng nguyên cấu hình Docker. |
| P2 | dummy provider, test CLI | Tọa độ dummy dùng pixel cố định rồi chia kích thước ảnh, có thể vượt 0–1 ở ảnh test 400×200. Test hiện chủ yếu kiểm tra schema/status, chưa kiểm tra chất lượng OCR hay mọi response streaming. Bổ sung ảnh chuẩn và assertion phù hợp. |
| P2 | Repository | Có các file `__pycache__/*.pyc` được Git theo dõi. Nên bỏ khỏi version control trong một thay đổi riêng và bổ sung ignore; lượt review đã hoàn trả bytecode phát sinh do kiểm thử. |


## 3. Hợp đồng dữ liệu cần thống nhất với frontend

Giữ schema server hiện có làm chuẩn, sửa trang demo server để đọc đúng tên trường; tránh đổi server sang schema riêng của UI cũ.

```ts
type Box = { center_x: number; center_y: number; width: number; height: number };
type OcrResult = {
  paragraphs: {
    full_text: string;
    is_vertical: boolean;
    box: Box;
    words: { text: string; separator: string; box: Box }[];
  }[];
  elapsed_ms: number;
};
```

| Dữ liệu server | Nơi dùng trên giao diện | Hướng xử lý |
| --- | --- | --- |
| `paragraphs[].full_text` | Panel Văn bản nhận dạng | Render text thuần, không HTML; kết quả rỗng có thông báo riêng |
| `paragraphs[].box`, `words[].box` | Overlay trên video | Tọa độ normalized theo vùng ảnh thực, bù letterbox khi `object-fit: contain` |
| `words[].text` | Chọn chữ và lưu từ | Giữ nguyên text; chỉ thêm vào Từ vựng đã lưu khi người dùng chọn lưu |
| `is_vertical` | Chữ Nhật viết dọc | Dùng hướng chữ khi hiển thị, không tự hiểu là bản dịch |
| `elapsed_ms` | Thông tin xử lý | Chỉ hiển thị khi có kết quả, không dùng thay trạng thái kết nối |
| `error` | Thông báo lỗi và thử lại | Phân biệt lỗi đầu vào, timeout, mất kết nối và lỗi provider |

Không có trường nghĩa tiếng Việt, romaji, phát âm, phụ đề lời nói. Cần dịch vụ từ điển/dịch/nhận dạng giọng nói riêng trước khi thêm lại những nội dung đó. OCR đọc chữ trên ảnh, không nghe âm thanh.

Nên bổ sung request metadata `session_id`, `frame_id`, `captured_at`, `source_width`, `source_height` và echo trong response để frontend bỏ kết quả cũ khi đổi nguồn. Phải thống nhất version và backward compatibility trước khi thay protocol; đây chỉ là đề xuất, server chưa có các trường này.

## 4. Thứ tự xử lý để tích hợp

1. Sửa mapping trang demo: `text → full_text`, `bounding_box → box`, `direction → is_vertical`; sửa cả copy/tooltip/export nếu dùng schema cũ. Test phải kiểm tra có chữ và overlay, không chỉ HTTP 200.
2. Chốt đường truy cập API. Phát triển có thể proxy `/api/ocr` và `/api/ws` trên Vite sang `/ocr` và `/ws` của aiohttp; production dùng reverse proxy cùng origin hoặc CORS allowlist. Chưa thêm proxy hoặc API client vào frontend trong lượt sửa giao diện.
3. Test bằng ảnh có chữ thật, xác nhận thứ tự đọc/tọa độ rồi mới đưa khung hình video vào. Dummy chỉ kiểm tra đường truyền, không chứng minh chất lượng OCR.
4. Frontend cần bổ sung thẻ video và chọn nguồn để chụp canvas, nén và gửi khoảng 0,5–1 frame/giây ban đầu; chỉ một frame chờ xử lý, đo lại trước khi tăng tần suất. Không OCR mọi frame và không tích hàng đợi vô hạn.
5. Giới hạn kích thước byte lẫn pixel ảnh; thống nhất HTTP/WS/proxy, trả mã 413 khi quá lớn. Chuẩn hóa lỗi để UI hiển thị đang kết nối/đang nhận dạng/không tìm thấy chữ/mất kết nối.
6. Xử lý concurrency provider và cleanup; test nhiều client, reconnect, đổi nguồn khi request đang chờ, rời phòng và dừng chia sẻ. Quyền truy cập phải áp dụng cả HTTP lẫn WS.
7. Bổ sung auth, API quản lý phòng, broadcast theo phòng, từ điển, lưu từ và lịch sử ở dịch vụ phù hợp; không nhét toàn bộ vào OCR provider. Chỉ chủ nguồn gửi frame, thành viên khác nhận kết quả cùng mốc thời gian.
8. Chọn kiến trúc AWS theo mục 5 rồi mới đưa lên cloud; kiểm thử thật và cập nhật báo cáo theo hệ thống đã chạy.

## 5. Đối chiếu kiến trúc AWS trong báo cáo

Server hiện là OCR service độc lập, chưa có Cognito, Chime SDK, DynamoDB, S3, broadcast kết quả cho phòng hay API quản lý phòng. Đây là phần việc còn thiếu, không phải bằng chứng server OCR đang sai vai trò.

Điểm lệch đáng chú ý là API Gateway WebSocket:

- Theo [AWS: Binary media types for WebSocket APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/websocket-api-develop-binary-media-types.html), incoming binary frame không được hỗ trợ và bị đóng kết nối với code 1003; có thể dùng text base64 với cách tích hợp thích hợp.
- Theo [AWS: WebSocket quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-execution-service-websocket-limits-table.html), frame tối đa 32 KB, message tối đa 128 KB; base64 làm tăng kích thước. Không dùng giới hạn 50 MB của aiohttp để suy ra giới hạn trên API Gateway.
- Server giữ WS của chính client trong aiohttp và trả trực tiếp qua socket. Luồng Gateway cần quản lý connection ID, route, quyền phòng và cơ chế trả kết quả tương ứng; chưa có trong mã hiện tại.

Hai hướng triển khai cần chọn rõ:

1. **Demo OCR trước:** trình duyệt ↔ reverse proxy HTTPS/WSS ↔ aiohttp. Có thể tận dụng server hiện tại, bổ sung auth và giới hạn tải. Nếu dùng hướng này cho sản phẩm/báo cáo thì cập nhật sơ đồ cho đúng luồng thực tế.
2. **Giữ API Gateway WebSocket như báo cáo:** bổ sung adapter và quản lý connection; thiết kế payload ảnh đáp ứng giới hạn hoặc upload ảnh qua HTTP/S3 rồi gửi tham chiếu qua WS. Không đưa toàn bộ ảnh 50 MB vào một WS message.

## 6. Kiểm chứng OCR từ lượt đánh giá trước

| Kiểm tra | Kết quả | Giới hạn |
| --- | --- | --- |
| Bộ test sẵn có | 6/6 pass với provider dummy | Không chứng minh OCR chữ thật, chất lượng, tải hoặc provider production |
| JSON base64 HTTP | 200 với ảnh hợp lệ, dummy trả kết quả | Chỉ kiểm tra transport |
| Ảnh hỏng | 400 | Thông báo còn lộ exception |
| Raw/multipart > 1 MiB | 400 Content Too Large | Cần chuẩn hóa thành 413 và thống nhất giới hạn |
| HTTP từ origin frontend sang OCR | Browser `TypeError: Failed to fetch`; thiếu CORS, OPTIONS 405 | Có thể giải quyết bằng proxy cùng origin |
| WS từ browser frontend sang OCR | Ping → pong | Không đồng nghĩa đã tích hợp video/nhận dạng |
| Trang demo server nhận response thật từ dummy | 2 paragraphs, 2 phần text rỗng, 0 bbox | Xác nhận lỗi tên trường |
| Import provider glensv2 / serialization methods | Thành công trong môi trường kiểm thử | Chưa gọi dịch vụ Lens hay đo độ chính xác |

Chưa kiểm thử: nhận dạng thật glensv2/meikiocr/screenai/owocr, nhiều người đồng thời, tải dài hạn, build Docker, triển khai AWS, Chime, Cognito, lưu S3/DynamoDB. Môi trường test Python là 3.14 với các dependency tối thiểu trong `/private/tmp/ocr-review-venv`, khác Python 3.12 trong Dockerfile; không phải kiểm chứng đầy đủ môi trường production.


Các kết quả kiểm thử OCR trên thuộc lượt đánh giá 10/11/2026; lượt 11/11 chỉ chỉnh frontend và tài liệu, không chạy lại hay sửa server. Các đề xuất chưa được áp dụng vào server.
