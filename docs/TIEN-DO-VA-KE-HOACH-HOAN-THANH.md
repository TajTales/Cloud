# Tiến độ và kế hoạch hoàn thành OCR Learning / LinguaLive

Đối chiếu ngày 11/11/2026 với Báo cáo 2.pdf, đặc biệt trang 9–15, và mã nguồn hiện có trong workspace. Các dịch vụ hoặc repo bên ngoài workspace chưa được xác minh. Lượt cập nhật này chỉ sửa tài liệu, không chỉnh frontend, server, API hay hạ tầng. Các hợp đồng kỹ thuật phía dưới là **đề xuất để cả nhóm chốt trước khi giao AI**, chưa phải API đang tồn tại và chưa phải quyết định đã được ba thành viên xác nhận.

## Cách sử dụng tài liệu

Tài liệu chi tiết để chia task cho AI; không cần đọc lại từ đầu ở mọi lần giao việc.

- Cả nhóm đọc **mục 4–7** để biết ai làm gì, thứ tự và các quyết định chưa chốt.
- Trước khi viết code, chuẩn bị bộ hợp đồng ở **mục 8**, rồi đối chiếu **mục 9–13** khi chốt dữ liệu/API.
- Khi giao task, dùng **mục 14–15** cho phạm vi file, môi trường, cách bàn giao và prompt mẫu.
- Khi chạy thử, dùng **mục 16–18** để xác nhận kết quả và việc làm tiếp.
- Phần 1–3 giữ lại đối chiếu tiến độ hiện tại với PDF. Những phần sau đó là kế hoạch tương lai, không nâng trạng thái thành đã hoàn thành.

Trình tự ngắn: **chốt contract → từng AI làm module theo contract → test riêng → tích hợp sớm → cả nhóm chạy nghiệm thu → cập nhật trạng thái**.

## 1. Kết luận

Đã có giao diện đủ các màn chính, các tương tác học từ mẫu và khung server OCR độc lập. Chưa có luồng sản phẩm hoàn chỉnh từ chia sẻ màn hình → nhận chữ thật → tra/lưu từ → mở lại lịch sử. Chưa thể coi dự án đã hoàn thành chỉ vì các màn hình có mặt hoặc test dummy đạt.

## 2. Đối chiếu 17 hạng mục của báo cáo

| STT | Hạng mục trong báo cáo | Bằng chứng hiện có / phần còn thiếu |
| --- | --- | --- |
| 1 | Hạ tầng AWS | Có Docker/Nginx/systemd và hướng dẫn deploy OCR. Chưa có bằng chứng tài nguyên AWS đang chạy hoặc cấu hình hạ tầng hoàn chỉnh trong repo. |
| 2 | Thiết kế UI/UX sáng/tối | Đã có các màn chính, responsive và hover; người dùng đã chấp nhận giao diện hiện tại. |
| 3 | Đăng nhập, màn chính, Thư viện, Nhật ký | Có UI và điều hướng. Đăng nhập là timer + localStorage; lịch sử, thống kê, bộ sưu tập là dữ liệu mẫu. Chưa nối Cognito và API dữ liệu. |
| 4 | Phòng học và Chime SDK client | Có UI video, transcript, chat, từ vựng, micro/camera. Video là ảnh; chat và thành viên mẫu; nút thiết bị chỉ đổi state. Chưa tích hợp Chime/WebRTC. |
| 5 | Chụp/nén/gửi frame và hiển thị OCR | Chưa có getDisplayMedia, video thực, canvas capture hoặc client HTTP/WS OCR trong frontend hiện tại. Overlay dùng vị trí mẫu. |
| 6 | Phát hành qua CloudFront | Chạy Vite cục bộ và build đạt. Chưa xác minh deploy CloudFront. |
| 7 | Đăng ký/đăng nhập/token | Chưa có xác thực thật trong mã hiện tại. Cờ localStorage không phải phiên xác thực Cognito. |
| 8 | API Gateway REST/WS và token | Chưa có tích hợp/config xác minh được. WS aiohttp trực tiếp không đồng nghĩa đã hoàn thành luồng API Gateway trong báo cáo. |
| 9 | Chime backend, meeting/attendee, ghi hình | Chưa có API tạo meeting/attendee, token tham gia hoặc luồng ghi hình. |
| 10 | EC2 Auto Scaling và quản lý phòng | Có service OCR aiohttp; chưa có quản lý phòng, phân quyền chủ phòng/thành viên, phân phối tải hoặc Auto Scaling được xác minh. |
| 11 | DynamoDB phòng/kết nối | Chưa có schema/client/persistence tương ứng trong repo. |
| 12 | Đóng gói/kiểm thử OCR thật | Có interface/provider, package, Dockerfile và test CLI. Test trước đạt 6/6 với dummy; chưa kiểm chất lượng nhận dạng thật hoặc build/deploy Docker. |
| 13 | Server nhận ảnh WS, trả chữ | Có HTTP /ocr và WS /ws. Đã kiểm tra transport độc lập với dummy. Chưa nối frontend, phòng nhóm, Gateway hoặc provider thật thành một luồng. |
| 14 | Tối ưu OCR | Có tùy chọn low-bandwidth và xử lý của provider; chưa có số đo độ chính xác, độ trễ hoặc load test để xác nhận tối ưu đạt yêu cầu. |
| 15 | Lưu ký tự S3 và chỉ mục nhật ký | Chưa có luồng ghi S3/DynamoDB. |
| 16 | Kiểm thử tích hợp | Có build/TypeScript, kiểm tra Chromium các UI và kiểm tra server dummy riêng. Chưa có kiểm thử hệ thống nhiều người dùng qua dịch vụ thật. |
| 17 | Báo cáo và demo cuối | Đã có Báo cáo 2 và demo UI, ghi chú kỹ thuật. Cần demo chức năng thật, kết quả kiểm thử và báo cáo phản ánh bản triển khai cuối. |

Ngoài bảng 17 hạng mục, use case trang 9–10 có **Admin quản lý người dùng, hệ thống và theo dõi hoạt động**. Mã hiện tại chưa có chức năng này; bảng phân công cũng chưa tách một đầu việc riêng, cần bổ sung để hoàn thành đúng phạm vi.

## 3. Những tương tác frontend đã hoạt động

- Chuyển màn hình, mở hộp thoại tạo/nhập mã phòng (chưa tạo phòng trên server).
- Sáng/tối, thiết lập ngôn ngữ, hover, responsive và con trỏ mặc định.
- Chọn ô chữ OCR mẫu; xem thông tin và lưu vào danh sách từ trong state.
- Rê chuột/chạm từ Nhật hoặc romaji trong hai câu transcript mẫu để xem popup: loại từ, kana/romaji, nghĩa, dạng gốc, cách dùng, ví dụ.
- Gọi Web Speech API để phát âm thường/chậm. Giọng thực phụ thuộc trình duyệt/hệ điều hành.
- Lưu không trùng và xóa từ trong phiên. Chưa bền vững khi tải lại trang.

Popup đã được chuyển sang renderer/template mục từ thực của Yomitan, có furigana và layout từ điển; xem [ghi chú tích hợp](TICH-HOP-YOMITAN.md). Popup hiện dùng 18 mục từ được soạn sẵn, chưa phải dịch vụ từ điển cho văn bản bất kỳ. OCR không tự cung cấp dịch nghĩa, phân tích từ loại hoặc nhận dạng tiếng nói.

## 4. Cách đọc kế hoạch và phân công

### 4.1. Người chịu trách nhiệm

Theo bảng phân công trang 13–15 của PDF:

| Thành viên | Phạm vi gốc trong PDF | Vai trò trong kế hoạch tích hợp |
| --- | --- | --- |
| **Nguyễn Tài Đức** | Nhóm trưởng; frontend, UI/UX, Chime client, chụp/gửi frame, phát hành web | Chủ trì chốt hợp đồng chung; giữ thiết kế đã được chấp nhận; tích hợp frontend; tổ chức nghiệm thu và bản demo cuối. |
| **Nguyễn Hoàng Bảo** | Hạ tầng AWS, Cognito, API Gateway, Chime backend, EC2, DynamoDB | Chủ hợp đồng API ứng dụng, xác thực, quyền truy cập, phòng học và hạ tầng; cung cấp môi trường/API để hai phần còn lại tích hợp. |
| **Trần Nguyên Bảo Anh** | Đóng gói và kiểm thử OCR, nhận ảnh/trả chữ, tối ưu, lưu kết quả S3 và chỉ mục log | Chủ hợp đồng OCR, worker xử lý ảnh, chất lượng nhận dạng, lưu text OCR và phần từ điển/tách từ đề xuất bổ sung. |
| **Cả nhóm** | Kiểm thử tích hợp, báo cáo, demo | Mỗi người dùng AI cho phần của mình nhưng cùng chịu trách nhiệm rằng các phần thật sự chạy với nhau. |

**Từ điển, lưu từ, ôn tập và Admin chưa được chia riêng đầy đủ trong PDF.** Phân công những mục đó dưới đây là đề xuất bổ sung: Tài Đức làm UI; Hoàng Bảo làm API/quyền/lưu dữ liệu; Bảo Anh làm phân tích ngôn ngữ và dữ liệu từ điển. Cả nhóm cần xác nhận, không coi đây là phân công đã có sẵn trong báo cáo.

“Phụ trách chính” là người giao việc cho AI, kiểm tra đầu ra và bàn giao; không có nghĩa phải tự viết toàn bộ code. Một chức năng xuyên qua ba lớp vẫn phải có người đứng ra tích hợp, không chỉ ba đoạn code riêng lẻ.

### 4.2. Trạng thái và bằng chứng

Mỗi đầu việc dùng một trong các trạng thái: `todo` → `in_progress` → `ready_for_integration` → `integrated` → `accepted`. Nếu phụ thuộc chưa có thì dùng `blocked` và ghi rõ cần đầu ra nào.

- AI viết xong code + test riêng: tối đa `ready_for_integration`.
- Chạy qua frontend, backend và OCR thật trong môi trường chung: `integrated`.
- Người trong nhóm chạy ca nghiệm thu và lưu bằng chứng đạt: `accepted`.
- Mock/dummy chỉ chứng minh giao diện hoặc đường truyền, không chứng minh OCR/đăng nhập/học nhóm thật.
- Với các việc còn thiếu bên dưới, trạng thái ban đầu là `todo`; có thể tái sử dụng khung code hiện tại nhưng chưa mặc định hoàn thành việc tích hợp.

## 5. Gom các công việc còn thiếu theo tính chất

### G0 — Hợp đồng chung và tổ chức tích hợp

**Chính:** Tài Đức. **Cùng chốt:** Hoàng Bảo và Bảo Anh. **Làm đầu tiên.**

| Mã | Công việc | Đầu ra AI cần giao | Người thực hiện/kiểm tra |
| --- | --- | --- | --- |
| CT-01 | Chốt phạm vi, thuật ngữ, tiếng Nhật/Trung, OCR khác ASR, luồng solo/nhóm | Bảng quyết định mục 7 được điền; sơ đồ kiến trúc thống nhất | Đức tổng hợp; cả ba xác nhận |
| CT-02 | Chốt HTTP, WS, dữ liệu OCR/từ điển và lỗi | OpenAPI, AsyncAPI/JSON Schema, ví dụ request/response và error fixtures cùng một phiên bản | Hoàng Bảo API/WS; Bảo Anh OCR/từ điển; Đức kiểm tra đủ dữ liệu cho UI |
| CT-03 | Chia module, branch, mock và môi trường | CODEOWNERS hoặc bảng phạm vi; lệnh chạy; URL/port; cấu hình ví dụ; chiến lược merge | Đức chủ trì; Hoàng Bảo môi trường; cả ba áp dụng |
| CT-04 | Dựng bài test hợp đồng chạy chung | Một lệnh validate schema + test dữ liệu mẫu; mock server từ cùng hợp đồng | Hoàng Bảo cung cấp; Đức/Bảo Anh nối test phía mình |

**Nghiệm thu:** cả ba AI nhận cùng bộ hợp đồng, cùng commit/version và cùng fixtures; không còn mỗi người tự đặt tên endpoint/field. Chưa đạt G0 thì chỉ nghiên cứu provider hoặc dọn module độc lập, chưa viết các đầu nối theo suy đoán riêng.

### G1 — Tài khoản, phiên đăng nhập và phân quyền

**Chính:** Hoàng Bảo. **Frontend:** Tài Đức. **Bảo Anh:** dùng service identity khi gọi OCR nội bộ, không tự dựng đăng nhập thứ hai. Đối chiếu PDF: hạng 7, 8, một phần 1 và 3.

| Mã | Công việc | Ai giao AI làm | Điều kiện đạt |
| --- | --- | --- | --- |
| AU-01 | Cognito, app client cho browser, đăng ký/xác nhận/đăng nhập/quên mật khẩu/đăng xuất | Hoàng Bảo cấu hình/contract; Đức nối form | Đăng nhập bằng tài khoản thật; sai mật khẩu có lỗi đúng; không còn cờ localStorage làm bằng chứng xác thực |
| AU-02 | Auth adapter phía client, token refresh và phiên hết hạn | Đức theo contract Hoàng Bảo | Refresh chỉ chạy một lần đồng thời; hết phiên chuyển về đăng nhập; không lặp vô hạn |
| AU-03 | Xác thực HTTP/WS, quyền user/host/member/admin | Hoàng Bảo | API không tin user_id do client tự khai; từ chối user không thuộc phòng hoặc không sở hữu dữ liệu |
| AU-04 | Đồng bộ profile, tên hiển thị, ngôn ngữ, timezone | Hoàng Bảo API; Đức UI | Tài khoản khác có profile/dữ liệu khác; thiết lập được đọc/ghi lại đúng |

**Phụ thuộc:** CT-01…04. Có thể phát triển song song G2 sau khi hợp đồng đã chốt. Phải xong trước khi public dữ liệu hoặc nghiệm thu phân quyền học nhóm.

### G2 — Nguồn video, lấy frame và nhận dạng OCR

**Chủ tích hợp:** Tài Đức. **OCR:** Bảo Anh. **Gateway/job và quyền:** Hoàng Bảo. Đối chiếu: hạng 5, 12, 13, 14 và một phần 8, 10.

| Mã | Công việc | Ai giao AI làm | Điều kiện đạt |
| --- | --- | --- | --- |
| OC-01 | Chọn video, chia sẻ màn hình, xem trước, đổi/dừng nguồn | Đức | Có video thật; từ chối quyền không làm treo UI; rời phiên dừng track và thu hồi URL |
| OC-02 | Chụp canvas, nén, quản lý frame/time/nguồn, overlay theo ảnh thực | Đức; Bảo Anh cung cấp ảnh chuẩn | Resize/letterbox không lệch box; không chạy OCR mọi frame; không tích hàng đợi vô hạn |
| OC-03 | Sửa lỗi provider server, schema trang demo, kiểm tra ảnh/timeout/cleanup/concurrency | Bảo Anh | Các lỗi trong DANH-GIA-OCR.md được xử lý và có test; provider thật chạy được trên môi trường đã chọn |
| OC-04 | Upload/job API, worker orchestration, trả kết quả và chống trùng | Hoàng Bảo API/job storage; Bảo Anh worker OCR; Đức client | Một frame có thể đối chiếu bằng session_id/source_id/frame_id/job_id từ đầu tới cuối |
| OC-05 | Đo độ chính xác/độ trễ, bộ ảnh không chữ/chữ dọc/chữ nhỏ/ảnh hỏng | Bảo Anh chủ trì; Đức kiểm tra overlay | Có tập ảnh và kết quả đo; tách dummy khỏi real-provider test |
| OC-06 | Mất mạng, retry, kết quả cũ và đổi nguồn khi đang xử lý | Đức client; Hoàng Bảo job/events; Bảo Anh xử lý hủy/timeout | Kết quả nguồn cũ không nhảy lên video mới; lỗi không khiến stream/timer chạy ngầm |

**Nghiệm thu G2:** một nội dung mới ngoài dữ liệu mẫu được nhận chữ thật ngay trong giao diện hiện tại. Đây là mốc sản phẩm đầu tiên cần ưu tiên sau G0.

### G3 — Tách từ, từ điển, cách đọc và dịch

**Chính dữ liệu/ngôn ngữ:** Bảo Anh. **API/cache:** Hoàng Bảo. **Popup:** Tài Đức. Đây là phần bổ sung để UI đã có hoạt động với nội dung bất kỳ.

| Mã | Công việc | Ai giao AI làm | Điều kiện đạt |
| --- | --- | --- | --- |
| LX-01 | Chọn nguồn từ điển/tách từ, phạm vi ngôn ngữ, cách đọc/loại từ/dạng gốc | Bảo Anh đề xuất; cả nhóm chốt | Có nguồn và điều kiện sử dụng rõ; test từ chưa nằm trong 18 mục mẫu |
| LX-02 | Tách từ và ánh xạ về vị trí trong câu OCR | Bảo Anh | Offset khớp chuỗi gốc; không mất dấu câu; từ biến hình vẫn tìm được lemma |
| LX-03 | API tra từ, cache, timeout, not_found và thiếu bản dịch Việt | Hoàng Bảo adapter/API; Bảo Anh dữ liệu | Đầu ra theo một schema; không bịa nghĩa/từ loại khi thiếu dữ liệu |
| LX-04 | Thay dữ liệu mẫu của popup bằng dịch vụ; loading/error/retry | Đức | Hover/chạm/keyboard vẫn hoạt động; không tự phát âm; hỗ trợ từ không tìm thấy |
| LX-05 | Dịch câu và cách đọc theo ngữ cảnh nếu giữ UI hiện tại | Bảo Anh xác định dịch vụ; Hoàng Bảo API; Đức hiển thị | Có kết quả thật hoặc thông báo chưa có; không giả vờ là output OCR |

**Phụ thuộc:** hợp đồng từ/câu CT-02; có thể làm với fixtures trong khi G2 đang phát triển. Tích hợp sau khi có chữ OCR thật. Không tự mở rộng sang tiếng Pháp/Anh/Trung chỉ vì UI có lựa chọn; mỗi ngôn ngữ cần nghiệm thu riêng.

### G4 — Phòng học, video/thoại và chat thời gian thực

**Backend:** Hoàng Bảo. **Client/tích hợp:** Tài Đức. **Phát kết quả OCR theo phòng:** Bảo Anh phối hợp Hoàng Bảo. Đối chiếu: hạng 4, 9, 10, 11.

| Mã | Công việc | Ai giao AI làm | Điều kiện đạt |
| --- | --- | --- | --- |
| RM-01 | Tạo/tìm/tham gia/rời/đóng phòng, mã phòng và vai trò | Hoàng Bảo; Đức nối modal | Mã sai/phòng đầy/phòng đóng có lỗi; không dùng LINGO-3821 cố định |
| RM-02 | Tạo meeting/attendee, cấp thông tin tham gia Chime | Hoàng Bảo | Đúng thành viên mới lấy được thông tin tham gia; không lộ token trong log/API lịch sử |
| RM-03 | Chime client, nội dung chia sẻ, mic/camera, thiết bị và cleanup | Đức | Hai máy xem/nghe nhau; nút thiết bị phản ánh trạng thái thật, không chỉ đổi icon |
| RM-04 | Chat theo kênh duy nhất đã chốt; presence/thành viên thật | Đức client; Hoàng Bảo contract và quyền | Không có hai hệ chat song song; người mới vào thấy thành viên chính xác |
| RM-05 | OCR một nguồn phát, phân phối đúng phòng và đồng bộ mốc thời gian | Hoàng Bảo routing/connection; Bảo Anh kết quả; Đức render | Viewer không gửi OCR trùng cho cùng video; phòng khác không nhận nhầm dữ liệu |
| RM-06 | Chủ phòng mất mạng, rời phòng, reconnect, đóng meeting | Hoàng Bảo state machine; Đức UI | Không còn phòng/attendee “ma”; thành viên không có quyền đóng toàn bộ phòng |

**Phụ thuộc:** G1; session/frame schema G2; Chime spike của G7. Có thể làm client với meeting fixtures trước, nhưng phải nghiệm thu bằng hai browser/máy và tài khoản khác nhau.

### G5 — Lưu trữ, từ vựng, ôn tập, nhật ký và xem lại

**Schema/API:** Hoàng Bảo. **Text OCR và log:** Bảo Anh theo phân công PDF. **Giao diện dữ liệu thật:** Tài Đức. Đối chiếu: hạng 11, 15 và chức năng thư viện/nhật ký trong chương 1.

| Mã | Công việc | Ai giao AI làm | Điều kiện đạt |
| --- | --- | --- | --- |
| ST-01 | Schema dữ liệu, query/index DynamoDB và quyền sở hữu | Hoàng Bảo; Đức/Bảo Anh cùng review | Có access pattern cho từng endpoint, không chỉ tạo bảng trống |
| ST-02 | Lưu kết quả OCR vào S3, index phiên và chống ghi trùng | Bảo Anh làm writer/worker; Hoàng Bảo cấp adapter/IAM/schema | Truy ngược được frame/câu về phiên, ngôn ngữ, nguồn và thời gian |
| ST-03 | Lưu/xóa từ cá nhân, từ chung nếu bật, collections/ôn tập | Hoàng Bảo API; Đức UI; Bảo Anh dictionary identity | Refresh/đăng nhập lại còn từ; không trùng nghĩa đã lưu; ôn tập có trạng thái thật |
| ST-04 | Nhật ký, thời lượng, chuỗi ngày, mục tiêu tuần | Hoàng Bảo tính số liệu; Đức hiển thị | Không còn số 8.4 giờ/124 từ/12 ngày viết sẵn; quy tắc tính số liệu được chốt |
| ST-05 | Ghi/phát lại phòng Chime và video solo theo chính sách đã chọn | Hoàng Bảo pipeline/quyền; Đức player; Bảo Anh đồng bộ OCR | Lưu video thực, không chỉ lưu đường dẫn tạm trên máy; seek video khớp log OCR |
| ST-06 | Retention, xóa dữ liệu và truy cập playback tạm thời | Hoàng Bảo chính; Bảo Anh raw-frame cleanup | Người không có quyền không lấy được video; xóa không để lại link truy cập vô hạn |

**Lưu ý:** Media capture và ghép artifact thành file phát lại là phần việc riêng, không tự có chỉ vì tạo meeting hoặc có bucket. AWS mô tả [media capture](https://docs.aws.amazon.com/chime-sdk/latest/dg/capture-pipe-config.html) và [media concatenation](https://docs.aws.amazon.com/chime-sdk/latest/dg/create-concat-pipe.html) thành các luồng riêng.

**Phụ thuộc:** G1 và session schema G0; ST-02 theo G2; ST-05 nhóm theo G4. Lưu từ có thể làm độc lập từ dictionary fixtures trước.

### G6 — Admin, theo dõi hệ thống và độ ổn định

**Chính:** Hoàng Bảo. **UI Admin:** Tài Đức. **Số đo provider:** Bảo Anh. Phần bổ sung để khớp use case Admin trang 9–10.

| Mã | Công việc | Ai giao AI làm | Điều kiện đạt |
| --- | --- | --- | --- |
| AD-01 | Role Admin, API quản lý user, danh sách/đóng phòng | Hoàng Bảo; Đức UI | User thường bị chặn ở backend; không chỉ ẩn nút |
| AD-02 | Tình trạng provider, job lỗi, số phiên/độ trễ, nhật ký vận hành | Bảo Anh cung cấp metrics; Hoàng Bảo thu thập/API; Đức hiển thị | Truy được lỗi theo request_id/job_id, không log token hoặc nguyên ảnh nhạy cảm |
| AD-03 | Liveness/readiness, giới hạn tải, timeout/lease/cleanup | Bảo Anh OCR; Hoàng Bảo app | Health báo đúng model chưa sẵn sàng; quá tải có phản hồi thống nhất |
| AD-04 | Audit thao tác quản trị và xử lý lỗi dễ kiểm tra | Hoàng Bảo | Ai khóa user/đóng phòng có record; không đưa stack trace ra UI |

**Phụ thuộc:** G1, API/schema các nhóm liên quan. Phạm vi quản trị v1 cần chốt cụ thể: xem user, khóa/mở tài khoản, xem/đóng phòng, xem sức khỏe hệ thống; chưa tự thêm dashboard phức tạp ngoài nhu cầu môn học.

### G7 — Môi trường phát triển, AWS và phát hành

**Chính:** Hoàng Bảo. **Web/CloudFront client:** Tài Đức theo PDF. **Đóng gói provider/model:** Bảo Anh. Đối chiếu: hạng 1, 6, 8, 10, 12.

| Mã | Công việc | Ai giao AI làm | Điều kiện đạt |
| --- | --- | --- | --- |
| IF-01 | Chốt region, loại Gateway, Chime endpoint/media region, cách lưu ảnh/video | Hoàng Bảo khảo sát; cả nhóm xác nhận | Một bản thử nhỏ gọi được dịch vụ cần thiết trước khi làm đầy đủ |
| IF-02 | Lệnh chạy local, container/port, biến môi trường, dependency lock | Hoàng Bảo app; Bảo Anh OCR; Đức frontend | Người khác clone và chạy được bằng README, không cần sửa IP trong source |
| IF-03 | Cognito, S3, DynamoDB, Gateway, EC2/LB/Auto Scaling, IAM | Hoàng Bảo | Hạ tầng dựng lại được bằng cấu hình được version hóa; instance mới sẵn sàng trước nhận tải |
| IF-04 | Build web, CloudFront, route fallback và cấu hình API public | Đức; Hoàng Bảo domain/policy | URL triển khai mở được các luồng, HTTPS/WSS không lỗi mixed content |
| IF-05 | Pipeline ghi hình, model download/cache, log/metric và rollback | Hoàng Bảo AWS; Bảo Anh model; Đức bản web | Deploy lỗi có cách quay lại; Auto Scaling không mất job/connection metadata |

IF-01 và một môi trường dev tối thiểu làm sớm ngay sau G0, không đợi cuối dự án mới phát hiện region/API không phù hợp. IF-03…05 hoàn thiện khi từng luồng được tích hợp.

### G8 — Kiểm thử, nghiệm thu và báo cáo/demo

**Chủ trì:** Tài Đức. **Bằng chứng backend:** Hoàng Bảo. **Bằng chứng OCR:** Bảo Anh. Đối chiếu: hạng 16, 17.

| Mã | Công việc | Người phụ trách | Đầu ra |
| --- | --- | --- | --- |
| QA-01 | Schema/contract tests, frontend/backend/provider tests | Mỗi người cho phần mình; Đức chạy chung | Lệnh chạy, exit code, version fixture; không chỉ ảnh chụp “AI nói đã pass” |
| QA-02 | Tích hợp solo và phòng hai người/hai phòng | Đức chủ trì; cả nhóm chạy | Video thử và checklist kết quả, có tài khoản/nội dung mới |
| QA-03 | Quyền dữ liệu, mất mạng, retry, quá tải, lỗi provider | Hoàng Bảo API/quyền; Bảo Anh tải; Đức UI | Báo cáo lỗi và test chống tái diễn |
| QA-04 | Độ trễ, độ chính xác OCR, trình duyệt/thiết bị | Bảo Anh đo OCR; Đức UI; Hoàng Bảo hạ tầng | Số liệu có môi trường, tập ảnh, provider/version, số mẫu |
| QA-05 | Cập nhật PDF, hướng dẫn cài/chạy và demo cuối | Cả nhóm; Đức biên tập | Kiến trúc đúng triển khai, trách nhiệm đúng thực tế, demo tái lập được |

Kiểm thử được viết cùng chức năng; G8 là nghiệm thu chéo, không phải đợi mọi thứ xong mới bắt đầu test.

## 6. Thứ tự triển khai và các điểm dừng nghiệm thu

### 6.1. Lịch theo phụ thuộc, không gán ngày khi chưa biết deadline

| Chặng | Tài Đức làm | Hoàng Bảo làm | Bảo Anh làm | Chỉ chuyển chặng khi |
| --- | --- | --- | --- | --- |
| **M0 — Thống nhất** | CT-01…04, bảng UI cần dữ liệu gì, tích hợp repo | Draft API/auth/WS, IF-01, schema dữ liệu | Draft OCR/dictionary schema, xác nhận provider | Ba phần cùng dùng một contract version; kiến trúc hình ảnh/WS được chọn |
| **M1 — Dựng nền song song** | Auth/client adapter, video/share/capture, client gọi mock theo schema | Cognito, app API skeleton, storage local/cloud-dev, job/WS adapter, fixtures | Sửa OCR server được người phụ trách cho phép, real-provider test, dictionary prototype | Local chạy được; auth dev thật hoặc issuer test rõ ràng; provider thật có kết quả |
| **M2 — Solo chạy thật** | Nối video → frame → job → overlay, popup API | Upload/job API, auth, kết quả/poll/WS và trạng thái session | OCR worker và log, chất lượng box; từ điển ngoài dữ liệu mẫu | Một nội dung mới nhận chữ, tra và lưu từ đúng; đổi nguồn không hiện kết quả cũ |
| **M3 — Học nhóm** | Chime client, mic/camera/share/chat, membership UI | Room/meeting/attendee, presence, routing kết quả và quyền | Gắn session/frame vào kết quả nhóm; tránh xử lý trùng | Hai user cùng phòng chạy được; phòng khác không nhận nhầm |
| **M4 — Dữ liệu bền vững** | Thư viện/ôn tập/nhật ký/player thật | DynamoDB API/index, stats, quyền playback, recording pipelines | Lưu text OCR S3/index, đồng bộ timeline | Refresh còn dữ liệu; mở đúng phiên/video/log theo quyền |
| **M5 — Hoàn thiện** | Admin UI, E2E, CloudFront, biên tập PDF | Admin/metrics, AWS/Auto Scaling, hardening/rollback | Benchmark/provider packaging/load test | Demo cloud thật, quyền đúng, số liệu và tài liệu khớp triển khai |

ST-01/schema, ST-03/lưu từ và Admin skeleton có thể khởi động sớm hơn M4/M5 khi hợp đồng tương ứng ổn định. Mốc trong bảng là lúc nghiệm thu hoàn chỉnh, không phải cấm viết phần đó trước.

### 6.2. Các việc không nên làm độc lập rồi ghép ở cuối

- Không để Đức tự đặt JSON từ vựng còn Bảo Anh trả một cấu trúc khác.
- Không để AI backend tự đổi API hoặc enum vì “dễ dùng hơn” khi client đã tích hợp.
- Không để một AI đưa ảnh binary vào WS Gateway, AI khác triển khai Gateway chỉ nhận JSON.
- Không để mỗi người làm một cơ chế login, một bộ user_id hoặc một mã phòng khác nhau.
- Không để AI viết thêm một server chat riêng trong khi nhóm đã chọn Chime data messages.
- Không để provider OCR tự trở thành nơi quản lý user/phòng; cần lớp ứng dụng riêng.
- Không coi dữ liệu nằm trong state/localStorage hoặc file trên một EC2 instance là kho dữ liệu chung cho Auto Scaling.

## 7. Những quyết định phải chốt trước khi giao AI

**Toàn bộ giá trị trong cột “Đề xuất” là bản nháp thống nhất để nhóm duyệt.** Sau khi chốt, ghi vào hợp đồng và giao AI đúng bản đó. Nếu chọn phương án khác thì sửa tất cả ví dụ/schema/test liên quan trước; không vừa làm vừa giữ nhiều hợp đồng mâu thuẫn.

| Mã | Quyết định | Đề xuất để chốt | Người chốt | Trạng thái ban đầu |
| --- | --- | --- | --- | --- |
| D01 | Tên và phạm vi | LinguaLive là tên UI của OCR Learning; giữ thiết kế hiện tại; Nhật trước, Trung sau kiểm thử | Cả nhóm, Đức tổng hợp | Chưa xác nhận |
| D02 | Nghĩa “Phiên âm” | V1 là văn bản OCR + cách đọc; lời thoại âm thanh chỉ có khi thêm ASR; sửa mô tả PDF/UI nếu cần | Cả nhóm | Chưa xác nhận |
| D03 | Public API | `/api/v1`, JSON snake_case; một app backend phụ trách auth/room/job/storage | Hoàng Bảo + Đức | Chưa xác nhận |
| D04 | Frontend/provider boundary | Frontend chỉ gọi public app API; app/worker gọi OCR service nội bộ `/ocr`, `/health` | Cả ba | Chưa xác nhận |
| D05 | Truyền ảnh trên cloud | **Đề xuất:** HTTP/presigned upload cho ảnh; WS cho điều khiển/kết quả/thông báo. Điều chỉnh sơ đồ PDF nếu chọn | Cả ba | Chưa xác nhận |
| D06 | Chat | Chime meeting data messages cho chat trực tiếp; không mặc định có lịch sử chat bền vững | Hoàng Bảo + Đức | Chưa xác nhận |
| D07 | Ngôn ngữ/stack/version | React hiện tại; backend giữ stack repo backend đã có nếu có. Nếu chưa có, ưu tiên Python để đồng bộ OCR. Chốt phiên bản runtime/dependency bằng lockfile | Chủ từng phần, Đức ghi lại | Chưa xác nhận |
| D08 | ID/thời gian/tọa độ | UUID chuỗi; UTC ISO 8601; millisecond; box normalized; source_id cho từng lần đổi nguồn | Cả ba | Chưa xác nhận |
| D09 | Từ vựng riêng/chung | Mặc định riêng; từ chung chỉ khi room bật `shared_vocabulary_enabled`; API/quyền tách rõ | Cả ba | Chưa xác nhận |
| D10 | Lưu video | Group ghi qua Chime pipeline; solo video file chỉ xem lại trên cloud nếu upload được cho phép. Solo share có recording riêng hoặc lịch sử ghi rõ không có video | Cả ba | Chưa xác nhận |
| D11 | Region/dịch vụ/models | Một bảng region cho Cognito/API/S3/DynamoDB/Chime media và pipeline; kiểm tra provider thực trên EC2 | Hoàng Bảo + Bảo Anh | Chưa xác nhận |
| D12 | Mục tiêu tải/latency/retention | Chốt số phòng/user đồng thời, bộ ảnh, ngưỡng đo và thời gian lưu trước benchmark | Cả ba | Chưa xác nhận |
| D13 | Nguồn từ điển/dịch | Nguồn, license, cách đọc, từ loại, dịch Việt, phí/giới hạn nếu có; không để AI tự chọn khác nhau | Bảo Anh đề xuất; cả nhóm | Chưa xác nhận |
| D14 | Auth flow và lưu token | Giữ form hiện tại, một client auth adapter cho Cognito; public app client không có secret. Chốt SDK/flow và chính sách refresh/storage | Hoàng Bảo + Đức | Chưa xác nhận |

### 7.1. Điểm cần sửa trong kiến trúc PDF trước khi triển khai D05

PDF mô tả gửi frame qua WebSocket API Gateway. Server hiện tại nhận binary frame trực tiếp trong aiohttp. Đây là hai cách triển khai khác nhau.

AWS nêu Gateway WebSocket không nhận incoming binary frames; message/frame có giới hạn riêng. Vì vậy không dùng giới hạn 50 MB của aiohttp cho Gateway. Đề xuất D05 dùng upload ảnh qua HTTP/S3, gửi tham chiếu và kết quả nhỏ qua WS để tránh phải tự ghép ảnh thành nhiều mảnh. Nếu bắt buộc giữ ảnh đi qua WS như PDF, nhóm phải chốt protocol base64/chunk, timeout và ghép mảnh trước; bộ contract minh họa bên dưới phải sửa theo lựa chọn đó. Nguồn: [binary frames](https://docs.aws.amazon.com/apigateway/latest/developerguide/websocket-api-develop-binary-media-types.html), [quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-execution-service-websocket-limits-table.html).

Các chương tiếp theo minh họa **D05 theo phương án upload HTTP/S3**, không phải khẳng định nhóm đã đồng ý thay kiến trúc.

## 8. Bộ tài liệu chung phải đưa cho cả ba AI

Các đường dẫn sau là **đầu ra cần tạo ở CT-02/CT-04**, hiện chưa mặc định tồn tại:

| Tệp đề xuất | Nội dung | Người giữ chính |
| --- | --- | --- |
| `contracts/decisions.md` | D01…D14 đã chốt, lý do, ảnh hưởng PDF, version và người xác nhận | Đức |
| `contracts/openapi.yaml` | HTTP path/method/auth/request/response/errors và examples | Hoàng Bảo; Đức kiểm tra client; Bảo Anh kiểm tra OCR/lexicon |
| `contracts/asyncapi.yaml` | WS action/event, subscribe, reconnect, lỗi và version | Hoàng Bảo |
| `contracts/schemas/ocr-provider.schema.json` | Kết quả raw provider và tọa độ | Bảo Anh |
| `contracts/schemas/lexicon.schema.json` | Tokens, offset, lemma, senses, examples, reading/pos | Bảo Anh |
| `contracts/fixtures/` | Các JSON/ảnh kiểm thử chung cho thành công/lỗi/rỗng/trùng/nguồn cũ | Mỗi người thêm vào bộ chung |
| `contracts/CHANGELOG.md` | Ai đổi gì, breaking/additive, migration và consumer cần cập nhật | Người sửa hợp đồng |
| `docs/LOCAL-SETUP.md` | Runtime, port, env, lệnh chạy từng service và cả hệ thống | Hoàng Bảo; Đức/Bảo Anh xác nhận trên máy mình |
| `docs/ACCEPTANCE.md` | Checklist nghiệm thu và nơi lưu kết quả/log/video | Đức |

Không chỉ gửi PDF hoặc screenshot UI cho AI. Cần gửi contract version và commit SHA, các file liên quan, fixture mẫu, lệnh test và giới hạn phạm vi sửa. File này là kế hoạch/đề xuất, chưa thay thế OpenAPI/Schema có thể validate tự động.

## 9. Quy ước dữ liệu và HTTP API đề xuất v1

### 9.1. Quy tắc chung

| Mục | Quy ước |
| --- | --- |
| Base URL | Biến môi trường; ví dụ local `http://localhost:8081/api/v1`. Không hardcode IP AWS |
| Field JSON của app | `snake_case`; TypeScript có thể map ở một adapter duy nhất |
| AWS object | Riêng `meeting`/`attendee` giữ nguyên object SDK với PascalCase theo AWS; đánh dấu ngoại lệ trong schema, không đổi tên tùy ý |
| ID | Chuỗi UUID cho resource do app tạo; `user_id` lấy từ Cognito `sub`, không coi email là khóa bất biến |
| Mã phòng | Mã người dùng nhập, khác `room_id`; đề xuất 8 ký tự chữ hoa/số bỏ ký tự dễ nhầm, server sinh và kiểm tra trùng |
| Ngôn ngữ | Mã như `ja`, `zh`, `en`, `vi`, không dùng nhãn giao diện làm enum |
| Thời điểm | UTC ISO 8601 có `Z`; timezone hiển thị theo profile, mặc định `Asia/Ho_Chi_Minh` |
| Khoảng thời gian | Số nguyên millisecond, suffix `_ms`; pixel dùng suffix `_px`; không lẫn giây/phút |
| Thiếu dữ liệu | Mảng rỗng `[]`; giá trị chưa có `null` khi schema cho phép; không trả chuỗi `"null"` hoặc đổi kiểu giữa các lần gọi |
| Pagination | `limit` 1–100, mặc định 20; opaque `cursor`; response có `items`, `next_cursor` hoặc null |
| ID do client tạo | `frame_id`, `source_id`, `client_message_id`, idempotency key để đối chiếu/chống trùng; không dùng để quyết định quyền |
| Header | `Authorization: Bearer <access_token>` cho app API; `X-Request-Id` nếu có; `Idempotency-Key` cho thao tác tạo quan trọng |
| Version | HTTP `/api/v1`; WS `schema_version: "1.0"`; provider raw có schema riêng |

### 9.2. Response và lỗi

Response thành công có JSON body, trừ 204:

```json
{
  "data": { "session_id": "00000000-0000-4000-8000-000000000001", "status": "active" },
  "request_id": "req-demo-001"
}
```

Lỗi app thống nhất; lỗi string của OCR raw phải được adapter đổi về đây, không đưa nguyên exception lên UI:

```json
{
  "error": {
    "code": "ROOM_NOT_FOUND",
    "message": "Không tìm thấy phòng học.",
    "details": {},
    "retryable": false
  },
  "request_id": "req-demo-002"
}
```

| HTTP | Tình huống/mã điển hình |
| --- | --- |
| 400 | `VALIDATION_ERROR`, sai kiểu hoặc field bắt buộc |
| 401 | `AUTH_REQUIRED`, `TOKEN_EXPIRED` |
| 403 | `FORBIDDEN`, không phải thành viên/chủ phòng; thiếu quyền dữ liệu |
| 404 | `ROOM_NOT_FOUND`, `SESSION_NOT_FOUND`, `WORD_NOT_FOUND` |
| 409 | `ROOM_CLOSED`, `ROOM_FULL`, `SESSION_ENDED`, `STALE_SOURCE`, `IDEMPOTENCY_CONFLICT` |
| 413 / 415 | `IMAGE_TOO_LARGE` / `UNSUPPORTED_IMAGE_TYPE` |
| 422 | `INVALID_IMAGE`, nội dung không giải mã được hoặc metadata không khớp |
| 429 | `RATE_LIMITED`, `OCR_BUSY`; có `Retry-After` |
| 500 / 503 / 504 | `INTERNAL_ERROR` / `PROVIDER_UNAVAILABLE` / `OCR_TIMEOUT` |

`Không nhận ra chữ` là thành công với `paragraphs: []`, không phải lỗi. `Từ điển không tìm thấy` trả kết quả lookup `status: "not_found"`, không dùng 404 của một resource không tồn tại.

### 9.3. Endpoint và người cung cấp

Các path dưới đây là bản đề xuất để viết OpenAPI. Quyền phải kiểm tra trong backend, không chỉ dựa UI ẩn nút.

| Method/path sau `/api/v1` | Dùng để làm gì | Ai làm backend / ai dùng |
| --- | --- | --- |
| `GET /me`, `PATCH /me` | Profile, role và thiết lập | Hoàng Bảo / Đức |
| `POST /sessions` | Tạo phiên solo; tạo group session do backend room thực hiện | Hoàng Bảo / Đức |
| `GET /sessions/{session_id}` | Snapshot phiên, nguồn hiện tại, trạng thái quyền người xem | Hoàng Bảo / Đức |
| `POST /sessions/{session_id}/sources` | Đăng ký/đổi nguồn, server ghi source_id/current_source | Hoàng Bảo / Đức |
| `POST /sessions/{session_id}/end` | Kết thúc phiên solo hoặc host kết thúc phiên nhóm | Hoàng Bảo / Đức |
| `POST /sessions/{session_id}/uploads` | Cấp upload_id và URL PUT tạm cho frame | Hoàng Bảo / Đức |
| `POST /sessions/{session_id}/ocr-jobs` | Xác nhận ảnh đã upload, tạo job idempotent | Hoàng Bảo API; Bảo Anh worker / Đức |
| `GET /ocr-jobs/{job_id}` | Poll trạng thái/kết quả khi WS không sẵn | Hoàng Bảo + Bảo Anh / Đức |
| `GET /sessions/{session_id}/results` | Result manifests theo seq/time/cursor để xem lại hoặc phục hồi | Hoàng Bảo API, Bảo Anh log / Đức |
| `GET /results/{result_id}` | Một kết quả đầy đủ theo quyền; không ép JSON dài vào WS | Hoàng Bảo API, Bảo Anh nội dung / Đức |
| `POST /lexicon/lookups` | Phân tích câu và tra từ theo ngữ cảnh | Hoàng Bảo route/cache, Bảo Anh xử lý / Đức |
| `POST /translations` | Dịch câu nếu D02/phạm vi giữ bản dịch | Hoàng Bảo route, Bảo Anh adapter / Đức |
| `GET /vocabulary`, `POST /vocabulary`, `DELETE /vocabulary/{word_id}` | Từ cá nhân, lưu và xóa | Hoàng Bảo / Đức |
| `PATCH /vocabulary/{word_id}/review` | Cập nhật `new`, `learning`, `known` cho ôn tập v1 | Hoàng Bảo / Đức |
| `GET /collections`, `POST /collections`, `PATCH /collections/{collection_id}` | Bộ từ để thay các collection mẫu | Hoàng Bảo / Đức |
| `GET /history`, `GET /stats` | Nhật ký/số liệu thật của user đăng nhập | Hoàng Bảo / Đức |
| `POST /rooms`, `GET /rooms/{room_id}` | Tạo phòng và snapshot phòng | Hoàng Bảo / Đức |
| `POST /rooms/join` | Nhập `{ "code": "AB7K9M2Q" }`, trả room/session/membership | Hoàng Bảo / Đức |
| `POST /rooms/{room_id}/leave`, `POST /rooms/{room_id}/close` | Thành viên rời hoặc host đóng phòng | Hoàng Bảo / Đức |
| `POST /rooms/{room_id}/meeting-credentials` | Cấp object meeting/attendee cho thành viên đã xác thực | Hoàng Bảo / Đức |
| `GET /rooms/{room_id}/vocabulary`, `POST /rooms/{room_id}/vocabulary`, `DELETE /rooms/{room_id}/vocabulary/{word_id}` | Từ chung khi phòng cho phép | Hoàng Bảo / Đức |
| `POST /sessions/{session_id}/recording/start`, `POST /sessions/{session_id}/recording/stop` | Ghi hình theo quyền/chính sách D10 | Hoàng Bảo / Đức |
| `GET /sessions/{session_id}/playback` | Trạng thái video và URL phát lại có hạn | Hoàng Bảo / Đức |
| `POST /realtime/tickets` | Vé mở kết nối WS từ token HTTP | Hoàng Bảo / Đức |
| `GET /admin/users`, `PATCH /admin/users/{user_id}/status` | Quản lý tài khoản | Hoàng Bảo / Đức Admin |
| `GET /admin/rooms`, `POST /admin/rooms/{room_id}/close`, `GET /admin/health`, `GET /admin/metrics` | Quản trị phòng/vận hành | Hoàng Bảo; Bảo Anh metrics OCR / Đức Admin |

Không tự tạo `/login` trả token giả trong app backend khi đã chọn Cognito. Auth adapter dùng flow Cognito đã chốt ở D14. Resource chỉ cho admin không nằm lẫn trong API user mà bỏ kiểm tra role.

### 9.4. Các response dùng để ghép luồng

Chốt các schema này trong OpenAPI, không chỉ ghi tên endpoint:

- `POST /sessions` trả 201: `session_id`, `mode: "solo"`, `status: "active"`, `current_source_id: null`, `started_at`.
- `POST /rooms` trả 201: `room` (room_id, code, status, host_user_id, shared_session_id, shared_vocabulary_enabled), `membership` (user_id, role), không tự đưa attendee JoinToken vào response danh sách phòng.
- `POST /rooms/join` trả 200: cùng cấu trúc room/membership cho người tham gia, role do backend quyết định. Tạo lại cùng membership đang hoạt động là idempotent, không tăng member_count hai lần.
- `POST /sessions/{id}/sources` trả 201: source_id, kind (`local_video` hoặc `screen_share`), source_index, started_at, timeline_origin_ms. Backend lưu thứ tự nguồn; client không lấy source_id ngẫu nhiên để suy ra thứ tự.
- `POST /sessions/{id}/ocr-jobs` trả 202: job_id, frame_id, source_id, `status: "queued"`, poll_after_ms. Nếu cùng key/body đã có job thì trả 200 với cùng job_id và trạng thái hiện tại theo schema đã chốt, không tạo job mới. Cùng key nhưng body khác trả 409 IDEMPOTENCY_CONFLICT; backend cần unique constraint/conditional write, không chỉ kiểm tra trước rồi insert.
- `GET /ocr-jobs/{id}` trả 200: job_id, session_id, source_id, frame_id, status, result_id hoặc null, error hoặc null, created_at, updated_at. Succeeded phải có result_id; failed/expired phải có error code. Lỗi truy cập resource vẫn dùng HTTP error envelope, không trả job giả.
- `GET /results/{id}` trả 200: data là public result ở mục 10.3. Cả polling và WS dùng cùng result_id, không có hai format khác nhau.
- `GET /sessions/{id}/playback` trả 200: state, recording_id hoặc null, duration_ms hoặc null, playback_url hoặc null, expires_at hoặc null, timeline mapping. State ready mới có URL; không trả S3 object key như một URL công khai.
- `GET /history`, `GET /vocabulary`, `GET /collections` trả 200: data có items và next_cursor; từng item dùng resource ID nhất quán với endpoint chi tiết.
- `DELETE /vocabulary/{id}` trả 204 không body. Client không gọi response.json() vô điều kiện với 204.

Mọi trường bắt buộc/tùy chọn, nullable, HTTP status khi idempotent retry và enum phải nằm trong schema máy đọc được; danh sách này là đầu vào để tạo schema, không thay thế schema.

### 9.5. State machine và quyền

- **Solo session:** `active → ended` hoặc `failed`; chỉ owner xem/gửi frame/kết thúc.
- **Room:** `open → closed`; `member_count` lấy từ membership có hiệu lực, không lấy từ số socket hoặc mảng local của một client.
- **Group session:** một `shared_session_id`/nguồn hiện tại của host gắn vào room. Member có tham chiếu lịch sử riêng; không tự tạo thêm session xử lý OCR cho mỗi viewer.
- **Host:** được chia sẻ nguồn, gửi frame, bật ghi hình và đóng room. **Member:** xem/thoại/chat/tra từ/lưu từ; `leave` chỉ rời phiên của mình.
- **Host mất kết nối:** đề xuất grace 60 giây để reconnect; quá hạn đóng room và meeting. V1 chưa tự chuyển host nếu chưa có state machine/test cho việc đó.
- **Nguồn:** mỗi lần thay video/cửa sổ tạo UUID `source_id` mới; `frame_index` tăng trong nguồn; API từ chối nguồn không còn hiện hành.
- **OCR job:** `queued → processing → succeeded | failed | expired`. Retry không đổi thành một frame khác; completion trùng phải idempotent.
- **Từ chung:** ai thêm có `created_by`; đề xuất member xóa từ do mình thêm, host xóa từ chung bất kỳ; tắt tính năng thì API trả 403.
- **Admin:** role hệ thống độc lập host/member. Truy cập quản trị cần audit; không tự động phát JoinToken cho admin chỉ vì xem danh sách phòng. Khóa tài khoản phải có chính sách chặn request/socket đang hoạt động, không coi việc ẩn tài khoản trên UI là thu hồi phiên.

## 10. Hợp đồng ảnh, frame và kết quả OCR

### 10.1. Upload/job đề xuất

Ví dụ metadata gửi `POST /sessions/{session_id}/uploads`:

```json
{
  "source_id": "00000000-0000-4000-8000-000000000010",
  "frame_id": "00000000-0000-4000-8000-000000000011",
  "frame_index": 17,
  "media_time_ms": 102000,
  "captured_at": "2026-11-11T14:30:00.000Z",
  "width_px": 1280,
  "height_px": 720,
  "content_type": "image/jpeg",
  "size_bytes": 148000
}
```

Response `data`:

```json
{
  "upload_id": "00000000-0000-4000-8000-000000000012",
  "frame_id": "00000000-0000-4000-8000-000000000011",
  "upload": {
    "method": "PUT",
    "url": "https://storage.example.invalid/temporary-upload",
    "headers": { "Content-Type": "image/jpeg" },
    "expires_at": "2026-11-11T14:31:00.000Z"
  }
}
```

Trình tự cố định:

1. Frontend xin upload theo metadata; server kiểm tra quyền, nguồn, quota và tạo record liên kết upload/user/session/frame.
2. Frontend PUT đúng bytes và headers tới URL được cấp. Không tự thêm Bearer token của app vào URL S3. Cloud cần CORS bucket cho origin/method/headers đã chốt.
3. Upload xong mới `POST /sessions/{session_id}/ocr-jobs` với `{ "upload_id": "...", "frame_id": "..." }` và `Idempotency-Key`.
4. Backend kiểm tra object thuộc upload vừa cấp, byte/pixel thực, định dạng và ownership; không nhận URL tùy ý từ client để tải về.
5. Trả **202** với `job_id`, `status: "queued"`, `poll_after_ms`; worker xử lý ngoài request, không giữ HTTP chờ model mãi.
6. Worker gọi OCR raw → lưu kết quả → commit trạng thái → phát thông báo WS. Nếu WS thất lạc, GET job/result vẫn đọc được.
7. Frontend dùng một hàm xử lý result cho cả WS và polling; kiểm tra source/session/frame để bỏ dữ liệu cũ.

Local dùng upload adapter trả URL PUT của app/dev storage với cùng object `upload`, không bắt frontend viết hai pipeline khác nhau. Các dịch vụ này chưa tồn tại, là việc OC-04/IF-02 cần triển khai.

Job phải được lưu bền vững. Đề xuất v1 dùng DynamoDB job record + conditional claim/lease và worker poll có backoff; không chỉ `create_task` trong RAM. Lease phải có heartbeat/gia hạn và recovery khi EC2 chết; duplicate result phải an toàn. Nếu chọn SQS thay polling, ghi thành quyết định kiến trúc bổ sung, cập nhật IAM/infra/PDF trước khi các AI triển khai khác nhau.

### 10.2. Giới hạn khởi điểm để ba AI cùng dùng

Đây là **mức đề xuất của ứng dụng**, không phải giới hạn mặc định AWS/provider; phải đo và điều chỉnh cùng contract/config:

| Tham số | Đề xuất v1 |
| --- | --- |
| Frame | JPEG/PNG; khởi điểm JPEG quality khoảng 0,8, giữ tỷ lệ |
| Dung lượng frame | Tối đa 1 MiB sau nén |
| Số pixel ảnh | Tối đa 4 megapixel sau giải mã; frontend resize cạnh dài tối đa 1600 px |
| Tần suất | Khoảng 1 frame mỗi 2 giây khi có nguồn; chỉ một job in-flight trên mỗi nguồn |
| Bận/quá tải | Bỏ frame trung gian, backoff; không queue mọi frame video |
| Provider timeout | Khởi điểm 15 giây, job deadline 30 giây; lease gia hạn, không chồng retry vô hạn |
| Upload URL | Đề xuất TTL 60 giây, giới hạn theo user/session; không đồng nghĩa PUT URL tự dùng một lần |
| Media timeline | Video file dùng `currentTime × 1000`; share dùng monotonic elapsed kể từ source start |
| Đổi nguồn | source_id mới, timeline bắt đầu lại; hủy capture/request cũ, kết quả muộn bị bỏ ở UI |
| Crop | V1 gửi toàn frame đã resize, không crop để tránh phải thêm phép biến đổi tọa độ |

Chime room chỉ host gửi OCR. Mic/camera được Chime xử lý theo media path; không đưa audio/video live vào API OCR.

### 10.3. Kết quả raw provider được giữ tương thích

`meikipop-ocr-server` đã có schema sau; trước mắt adapter dùng đúng tên trường, không tùy ý đổi sang `text`/`bounding_box`:

```json
{
  "paragraphs": [
    {
      "full_text": "静かな喫茶店",
      "is_vertical": false,
      "box": { "center_x": 0.5, "center_y": 0.4, "width": 0.4, "height": 0.08 },
      "words": [
        {
          "text": "喫茶店",
          "separator": "",
          "box": { "center_x": 0.6, "center_y": 0.4, "width": 0.2, "height": 0.08 }
        }
      ]
    }
  ],
  "elapsed_ms": 234.5
}
```

Ví dụ chỉ minh họa schema, không phải output nhận dạng đã đo. Chuỗi `words` của từng provider có thể là ký tự/cụm chữ, không coi đó mặc nhiên là token ngữ pháp của từ điển.

Public result thêm metadata trong lớp bọc, không bắt provider nhận biết room/user:

```json
{
  "result_id": "00000000-0000-4000-8000-000000000013",
  "job_id": "00000000-0000-4000-8000-000000000014",
  "session_id": "00000000-0000-4000-8000-000000000001",
  "source_id": "00000000-0000-4000-8000-000000000010",
  "frame_id": "00000000-0000-4000-8000-000000000011",
  "frame_index": 17,
  "media_time_ms": 102000,
  "language": "ja",
  "provider": "meikiocr",
  "image": { "width_px": 1280, "height_px": 720 },
  "ocr": { "paragraphs": [], "elapsed_ms": 234.5 }
}
```

Trong ví dụ public, `paragraphs: []` minh họa ca thành công không có chữ; ca có chữ dùng đầy đủ các paragraph theo schema raw. Tọa độ thuộc frame gửi đi, normalized; yêu cầu kiểm tra số hữu hạn và box trong ảnh, không chỉ kiểm tra center 0–1. Overlay đặt theo vùng ảnh thực sau letterbox, không theo cả container. Nếu sau này crop/rotate thì phải thêm transform/original dimensions vào version schema mới.

`elapsed_ms` hiện ở raw provider chỉ đo phần xử lý scan, không coi là latency đầu-cuối. Đo riêng upload/queue/scan/broadcast và tổng thời gian client nhận được.

### 10.4. API nội bộ và người chịu trách nhiệm

- Hoàng Bảo giữ public API/job repository, quyền, routing/persistence adapters và connection registry.
- Bảo Anh giữ provider raw, worker OCR và writer text/index log theo schema chung. Worker sử dụng helper storage/routing do backend cung cấp, không tự tạo bảng hoặc quy tắc quyền mới.
- Đức chỉ dùng public contract và `ocrClient` adapter; không import đường dẫn Python hay gọi URL provider từ browser ở bản tích hợp cuối.
- Raw provider `/ocr` vẫn có thể được kiểm thử riêng bằng CLI. Nếu phải thay schema cũ, cần version/adapter và test tương thích, không sửa âm thầm.

## 11. Hợp đồng WebSocket và chat

### 11.1. Xác thực kết nối

Đề xuất: HTTP có token hợp lệ gọi `POST /realtime/tickets` để lấy vé opaque, một lần, TTL 60 giây; browser mở `wss://...?...ticket=...`. Không đưa refresh token hay khóa AWS lên query. Log proxy/Gateway phải che ticket. Endpoint lấy vé trả `expires_at`, `ws_url` và thời hạn phiên WS.

Gateway dùng authorizer ở `$connect`; sau đó **mỗi action vẫn cần kiểm tra quyền/phòng/phiên**. Khi token hết hạn hoặc quyền bị thu hồi, backend phải đóng/revoke connection và client xin vé mới. Không mặc định quyền được kiểm tra lại tự động cho từng message bởi authorizer. Nguồn: [AWS WebSocket Lambda authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api-lambda-auth.html).

### 11.2. Envelope và danh mục sự kiện

Client gửi:

```json
{
  "schema_version": "1.0",
  "action": "session.subscribe",
  "request_id": "req-ws-001",
  "payload": { "session_id": "00000000-0000-4000-8000-000000000001", "after_seq": 0 }
}
```

Server phát:

```json
{
  "schema_version": "1.0",
  "type": "ocr.result_available",
  "event_id": "00000000-0000-4000-8000-000000000015",
  "seq": 18,
  "occurred_at": "2026-11-11T14:30:01.000Z",
  "session_id": "00000000-0000-4000-8000-000000000001",
  "request_id": null,
  "data": {
    "job_id": "00000000-0000-4000-8000-000000000014",
    "result_id": "00000000-0000-4000-8000-000000000013",
    "source_id": "00000000-0000-4000-8000-000000000010",
    "frame_id": "00000000-0000-4000-8000-000000000011"
  }
}
```

Kết quả đầy đủ đọc bằng `GET /results/{result_id}`; mỗi event app giữ dưới 24 KiB UTF-8 bằng cách gửi tham chiếu/snapshot nhỏ, không nhét ảnh hay bản OCR dài vào message. Đây là giới hạn thiết kế nội bộ đề xuất, không phải quota AWS.

| Client action | Server event tương ứng | Payload và ý nghĩa |
| --- | --- | --- |
| `session.subscribe` | `session.subscribed` | Snapshot source/session, `latest_seq`, membership; request_id khớp request |
| `session.unsubscribe` | `session.unsubscribed` | Dừng subscription, không tự kết thúc session |
| `room.subscribe` | `room.snapshot` | room_id, member_count, vai trò; danh sách lớn lấy REST |
| `room.unsubscribe` | `room.unsubscribed` | Dừng nhận trạng thái room, không thay cho API leave |
| `app.ping` | `app.pong` | Heartbeat ứng dụng, không phải native WebSocket ping frame |
| Không có action riêng | `ocr.result_available` | Manifest nhỏ của kết quả đã lưu |
| Không có action riêng | `ocr.job_failed` | job/frame/source + error code/retryable |
| Không có action riêng | `session.source_changed`, `session.ended` | Đổi nguồn hoặc kết thúc phiên |
| Không có action riêng | `room.member_joined`, `room.member_left`, `room.closed` | Membership/presence có hiệu lực |
| Action sai/không có quyền | `request.failed` | request_id + error theo cấu trúc chung |

`seq` tăng trong một session. Event chỉ thuộc room dùng `session_id: null`, `seq: null` và `room_id`/`room_version` trong data; không áp bộ đếm session cho room. `request.failed` dùng `data.error` theo error object ở mục 9.2; heartbeat/ack không có session dùng null ở các field đó. Event_id chống lặp. Không hứa giao đúng một lần hoặc đúng thứ tự qua mọi kết nối. Server commit result/job trước rồi mới phát event; client bỏ trùng, bỏ nguồn cũ, không để frame_index nhỏ ghi đè frame_index lớn của cùng source.

Reconnect: heartbeat khởi điểm 30 giây; mất kết nối thì backoff 1/2/4/8… tối đa 30 giây có jitter, xin vé mới và subscribe lại. `after_seq` là gợi ý phục hồi: nếu server không còn event cũ thì trả `resync_required: true` và `latest_seq`; client đọc session snapshot/results theo cursor. Có polling GET job/result dự phòng. Không dựa vào một socket sống vĩnh viễn hoặc registry chỉ trong RAM một EC2.

### 11.3. Chat chọn một đường duy nhất

Theo D06 đề xuất: chat trực tiếp qua Chime meeting data messages, topic `chat_v1`; WS app dành cho OCR và trạng thái phòng. AWS hỗ trợ data messages tới 2 KB để làm chat và tương tác cuộc họp; app nên giới hạn envelope chat dưới 1.500 byte UTF-8, không chỉ đếm ký tự. Nguồn: [Using the Amazon Chime SDK](https://docs.aws.amazon.com/chime-sdk/latest/dg/meetings-sdk.html).

Payload chat v1 gồm `schema_version`, `client_message_id`, `body`, `sent_at`. Client nhận xác định người gửi từ attendee metadata của SDK đã ánh xạ sang user, không tin tên/user_id tự khai trong body. Render text thuần, không chèn HTML. Gửi lại cùng client_message_id phải chống lặp.

Không dùng tên topic `chat.v1` nếu SDK yêu cầu tập ký tự khác; `chat_v1` là đề xuất để tránh lệch quy ước. Lịch sử chat sau rời phòng không được coi đã có; nếu nhóm muốn lưu lâu dài cần endpoint/persistence và tiêu chí riêng. Thứ tự tin dùng timestamp/metadata nhận từ SDK khi có, không tin đồng hồ client trong sent_at để quyết định quyền hoặc thứ tự tuyệt đối. Nếu chọn Chime Messaging hoặc chat qua app WS thay vì data messages thì phải sửa D06, schema, test và mô tả PDF, không triển khai cả ba cùng lúc.

## 12. Hợp đồng tách từ/từ điển cho popup đã có

### 12.1. Đầu vào và đầu ra tối thiểu

Request đề xuất `POST /lexicon/lookups`:

```json
{
  "language": "ja",
  "text": "静かな喫茶店",
  "session_id": "00000000-0000-4000-8000-000000000001",
  "result_id": "00000000-0000-4000-8000-000000000013",
  "paragraph_index": 0
}
```

`text` phải khớp paragraph được tham chiếu. Lookup ngoài ngữ cảnh phiên có thể cho phép bỏ các reference theo OpenAPI, nhưng không nhận reference sai quyền.

Response `data` đề xuất:

```json
{
  "status": "found",
  "language": "ja",
  "text": "静かな喫茶店",
  "offset_unit": "unicode_code_point",
  "normalization": "none",
  "tokens": [
    {
      "surface": "静かな",
      "start": 0,
      "end": 3,
      "lemma": "静か",
      "reading": { "kana": "しずかな", "romaji": "shizuka na" },
      "lemma_reading": "しずか",
      "pos": ["adjective_na"],
      "inflection": "attributive_na",
      "entry_id": "provider:entry-001",
      "sense_id": "sense-001",
      "meanings": [{ "language": "vi", "text": "Yên tĩnh; êm ả.", "origin": "dictionary" }],
      "usage_note": "Thêm な khi đứng trước danh từ.",
      "examples": [{ "text": "静かな部屋です。", "translation": "Đây là một căn phòng yên tĩnh.", "translation_language": "vi" }],
      "source": { "provider": "to-be-selected", "attribution": "Nguồn phải chốt ở D13" }
    }
  ]
}
```

Ví dụ entry minh họa schema, không khẳng định đã có provider hoặc dữ liệu bản quyền cụ thể. Response thật phải có toàn bộ tokens của câu hoặc mô tả những đoạn chưa phân tích; không suy ra câu chỉ có token minh họa trên.

Các điểm phải thống nhất:

- `start` bao gồm, `end` không bao gồm; đếm Unicode code point. Python và JavaScript khác nhau với emoji/ký tự ngoài BMP; frontend cần map bằng `Array.from(text)`, không slice UTF-16 trực tiếp theo offset code point.
- Không trim/normalize câu trước khi trả offset; nếu provider normalize thì adapter phải ánh xạ về chuỗi gốc. Fixture có emoji, dấu câu và dấu kết hợp.
- POS dùng enum máy: `noun`, `verb`, `adjective_i`, `adjective_na`, `adverb`, `particle`, `pronoun`, `determiner`, `conjunction`, `interjection`, `expression`, `unknown`. Nhãn tiếng Việt do UI map, không so sánh chuỗi “Danh từ” trong logic.
- `pos` có thể nhiều giá trị; ưu tiên nghĩa trong ngữ cảnh, không giả vờ chắc chắn nếu có nhiều khả năng.
- Từ chưa tìm thấy: vẫn có surface/offset, `entry_id: null`, `sense_id: null`, `pos: ["unknown"]`, meanings/examples rỗng. `status` của toàn request là `found`, `partial` hoặc `not_found`; không bỏ từ khỏi câu.
- Dạng gốc và dạng đang thấy phải tách. Lưu 曲がる thì nghĩa phải là nghĩa dạng gốc, không lưu nghĩa “đã rẽ” của 曲がった vào entry gốc.
- Dictionary reading và tiếng nói tự động là hai nguồn khác nhau; Web Speech API frontend không thay cho kana/romaji/từ loại từ backend.
- Chưa có nghĩa Việt: trả ngôn ngữ thực và nguồn dịch; UI hiện rõ thay vì gắn nhãn tiếng Việt cho chuỗi tiếng Anh.
- Nếu có LLM sinh usage/example/translation thì ghi provenance `generated` và tình trạng chưa kiểm chứng; không thay dữ liệu từ điển bằng câu trả lời tự tin không có nguồn.

### 12.2. Gắn vào frontend hiện tại

Đức giữ component popup đã được duyệt và tạo `lexiconClient`/adapter, không sửa toàn bộ thiết kế. Bảo Anh cung cấp schema/fixtures + kết quả cho câu mới; Hoàng Bảo cung cấp API có cache và lỗi. Một adapter map schema server sang model UI, thay dữ liệu cục bộ `transcriptVocabulary` khi ở real mode.

Hover không được gọi API dồn theo từng pixel: cache theo ngôn ngữ/câu/token + context, debounce hợp lý, hủy request cũ và không hiển thị kết quả từ trước cho từ vừa đổi. Cần có loading, no_result, provider_error và retry; không để popup trống vì undefined.

## 13. Lưu dữ liệu, phát lại và thống kê: thống nhất trước schema

### 13.1. Các thực thể cần có

| Thực thể | Field nghiệp vụ tối thiểu | Người sở hữu logic |
| --- | --- | --- |
| User/Profile | Cognito sub, display_name, role, locale, timezone | Hoàng Bảo |
| Room | room_id, code, host_user_id, shared_session_id, status, language, shared_vocabulary_enabled, version, created_at/closed_at | Hoàng Bảo |
| Membership | room_id, user_id, role, joined_at/left_at, trạng thái hiệu lực | Hoàng Bảo |
| Session | session_id, mode, owner_user_id, room_id nullable, current_source_id, status, started_at/ended_at | Hoàng Bảo; Đức dùng |
| Source | source_id, session_id, kind, width/height, started_at, timeline policy | Hoàng Bảo + Đức |
| Upload/Job | upload_id/job_id/frame_id, owner/session/source, state, lease/deadline, object ref, idempotency digest | Hoàng Bảo + Bảo Anh |
| OCRResult | metadata mục 10, object key, checksum, schema/provider version, created_at | Bảo Anh; Hoàng Bảo query/index |
| SavedWord | word_id, owner hoặc shared room scope, entry_id/sense_id, lemma/reading/meaning, language, review_state, created_at | Hoàng Bảo; Bảo Anh identity từ |
| WordOccurrence | word_id, session/result/source/media_time, surface đang thấy | Hoàng Bảo + Bảo Anh |
| UserSessionIndex | user_id, session_id, participation duration, title và quyền xem lại | Hoàng Bảo; Bảo Anh ghi từ log contract |
| Connection | connection_id, user_id, subscribed scopes, auth expiry, lease/last_seen | Hoàng Bảo |
| Recording | recording_id, session/source scope, state, object/manifest refs, permissions, duration/timeline mapping | Hoàng Bảo |
| Audit | admin_user_id, action, resource_id, outcome, occurred_at, request_id | Hoàng Bảo |

Đây là thực thể logic, **không yêu cầu tạo đúng từng ấy bảng DynamoDB**. Hoàng Bảo thiết kế PK/SK/GSI theo query: phòng theo code, thành viên theo room, lịch sử theo user/time, result theo session/seq, word theo owner/language/collection. Cả ba AI dùng schema đã chốt, không tự thiết kế GSI trong module riêng.

### 13.2. Lưu trữ và thời gian

- S3 lưu OCR JSON/JSONL, raw frame tạm và video/manifest; DynamoDB lưu metadata/chỉ mục. Không đẩy ảnh/video hoặc một transcript lớn vào một item DynamoDB.
- Prefix đề xuất: `frames/tmp/{session_id}/{source_id}/{frame_id}.jpg`, `ocr/{session_id}/{source_id}/{frame_id}.json`, `recordings/{session_id}/...`. Client chỉ dùng ID/URL được cấp; không tự dựng object key để truy cập.
- Raw frame có lifecycle ngắn theo D12; xóa theo hạn không được xóa nhầm kết quả học đang giữ. TTL DB không thay cho lifecycle object hoặc kiểm tra token expiry lúc request.
- SavedWord chống trùng theo owner/scope + language + entry_id + sense_id. Lưu lại ở phiên khác thì thêm occurrence, không tạo vô hạn cùng một từ. Với entry unknown chưa có ID, server cấp canonical key theo chính sách đã chốt.
- `media_time_ms` thuộc source; mỗi source có thời điểm bắt đầu trong session. Replay phải map source timeline sang recording timeline, không chỉ dùng captured_at của đồng hồ client.
- Playback trả `state: unavailable | processing | ready | failed`, duration và URL có expires_at. UI không hiện nút xem lại hoạt động nếu chỉ có text, file cục bộ đã mất hoặc video chưa xử lý xong.
- Ghi hình group cần capture và xử lý/ghép artifact theo pipeline; thay file trên máy bằng URL ký có hạn không đồng nghĩa đã upload video solo. D10 phải chốt riêng hai chế độ.

Trạng thái playback `unavailable` giúp UI phản ánh đúng thực tế, nhưng **không được coi là hoàn thành yêu cầu xem lại video trong PDF**. Muốn hoàn thành đầy đủ phải có đường ghi/upload/phát lại cho các loại nguồn thuộc phạm vi. Nếu quyết định không hỗ trợ một loại ở bản nộp, cả nhóm cần chốt giảm phạm vi và sửa báo cáo, không chỉ để AI bỏ chức năng đó.

### 13.3. Thống kê đề xuất

Cả nhóm phải chốt cách tính trước, không để frontend/backend cộng số liệu khác nhau:

- Thời lượng học: server ghi participation/heartbeat có giới hạn, không tính chồng hai tab thành hai lần thời gian.
- Ngày có học: đề xuất phiên có ít nhất 60 giây hoạt động; timezone của profile, mặc định Việt Nam. Đây là quy tắc sản phẩm đề xuất, có thể đổi trước khi chốt contract.
- Streak: chuỗi ngày có học liên tiếp; thống nhất việc hôm nay chưa học thì giữ chuỗi đến hôm qua hay hiện 0.
- Mục tiêu tuần: mặc định 5 buổi nếu nhóm giữ UI hiện tại; dùng đầu tuần/thời gian theo timezone, không cố định vòng 4/5.
- Từ đã lưu: số entry/sense chưa bị xóa, không đếm lặp occurrence; từ chung và từ riêng hiển thị tách rõ.
- Ôn tập v1: lật mặt từ, xem nghĩa/ví dụ, đánh dấu `learning`/`known` và lưu lại; chưa tự thêm thuật toán SRS phức tạp nếu chưa đưa vào phạm vi.

## 14. Môi trường, module và cách bàn giao giữa các AI

### 14.1. Phạm vi file đề xuất

Giữ repo backend riêng nếu nhóm đã có; nếu làm monorepo thì áp dụng bảng tương đương. Không di chuyển thư mục hàng loạt trước khi cả nhóm đồng ý.

| Phần | Chủ thay đổi | Ranh giới |
| --- | --- | --- |
| `src/` frontend, UI, API clients, media hooks | Đức/AI frontend | Không đổi provider Python, IAM hoặc contract tùy ý |
| App backend mới hoặc repo backend đã có | Hoàng Bảo/AI backend | User/room/session/job API, auth, storage helpers, realtime gateway |
| `meikipop-ocr-server/`, OCR worker, lexicon adapters | Bảo Anh/AI OCR | Không tự sửa UI, token model hoặc public route của app |
| Hạ tầng AWS/CI | Hoàng Bảo; Đức phần build web, Bảo Anh container model | Giữ interface deploy/env đã chốt |
| `contracts/` | Chủ schema đề xuất, hai consumer review | Thay đổi breaking phải xử lý consumer/test trước khi merge |
| Integration tests, fixtures, PDF/README | Đức điều phối, cả nhóm đóng góp | Fixture không có secret; không thay dữ liệu để che test fail |

Bảng này là quy trình cho lần phát triển tiếp theo. Yêu cầu trước đó “không sửa server OCR” vẫn được giữ trong workspace hiện tại; tài liệu không cấp quyền cho AI tự sửa server. Khi Bảo Anh giao task sửa OCR, cần nêu rõ repo/phạm vi được phép trong phiên làm việc của bạn ấy.

### 14.2. Runtime/port/env đề xuất

- Frontend hiện tại theo `.mise.toml`: Node 22, pnpm 10.34.3; xác nhận bản đang dùng rồi khóa thống nhất. Không để mỗi AI đổi package manager/lockfile.
- OCR Docker hiện chọn Python 3.12; kiểm thử thật trên Python đó, không chỉ dựa vào venv thử trước bằng 3.14.
- Port local: frontend 8443, app API 8081, OCR nội bộ 8080. Vite proxy `/api` sang app API; đường WS giữ adapter/path đã chốt.
- Public frontend: `VITE_API_BASE_URL`, `VITE_REALTIME_URL`, `VITE_COGNITO_USER_POOL_ID`, `VITE_COGNITO_CLIENT_ID`, `VITE_COGNITO_REGION`, `VITE_DATA_MODE=mock|real`.
- Backend/worker: `APP_ENV`, `AWS_REGION`, cấu hình bảng/bucket đã thống nhất, `OCR_SERVICE_URL`, `OCR_PROVIDER`, `ALLOWED_ORIGINS`, WS callback endpoint, timeouts/lease/rate limits. Chỉ service cần gì mới có quyền/biến đó.
- `VITE_*` là dữ liệu đi ra browser: không đặt AWS secret, client secret, private provider key hoặc refresh token vào đó. Runtime AWS dùng role phù hợp, không commit khóa vào code.
- `.env.example` chỉ chứa placeholder; `.gitignore` hiện bỏ `.env*`, nên phải thêm ngoại lệ có chủ đích cho file example nếu muốn version hóa. Không bỏ ignore để tiện commit secret.
- Mock mode hiện banner/nhãn và dùng cùng schema. Chế độ real không được âm thầm fallback sang mock khi API hỏng, vì sẽ tạo demo giả đạt.

### 14.3. Bộ bàn giao bắt buộc của mỗi task AI

1. Task ID, contract version/commit và branch base.
2. Danh sách file đổi, migration/env/dependency mới và lý do.
3. Cách chạy service, cách gọi thử, fixtures và response minh họa.
4. Test đã chạy với log/exit code; ghi rõ mock, dummy hay provider thật.
5. Những phần chưa làm và phần cần bên khác cung cấp; không đánh dấu hoàn thành bằng lời hứa.
6. Checklist tương thích: API/error/enum/ID/time/offset/box/auth đã theo contract.
7. Nếu thay contract, kèm thay đổi schema, fixture, consumer và migration; không bàn giao code mới kèm yêu cầu người khác tự đoán cách sửa.

### 14.4. Branch và thay đổi hợp đồng

- Mỗi task một branch từ cùng mốc đã tích hợp, ví dụ `feat/OC-02-frame-capture`, `feat/AU-03-api-auth`, `feat/LX-02-token-offsets`.
- Một branch không đồng thời chỉnh UI, provider và infra không liên quan. AI không tự sửa file nằm ngoài phạm vi để làm test riêng của nó pass.
- Tên field, unit, required field, enum meaning, auth và event payload là hợp đồng. Thêm required field hoặc đổi ms sang giây cũng là breaking change dù path vẫn v1.
- Quy trình đổi: nêu lý do + ví dụ trước/sau → owner và consumers thống nhất → cập nhật schema/fixtures → producer/consumer cùng test → merge theo thứ tự tương thích. Nếu cần breaking release thì thêm version/adapter v2, không ghi đè v1 đang được dùng.
- Đức tích hợp thường xuyên từng nhánh nhỏ; merge khi contract tests đạt, chạy smoke toàn hệ thống rồi mới giao task tiếp theo trên base mới.
- Không để ba AI cùng sửa `App.tsx`, cùng đổi OpenAPI hoặc cùng chạy migration ở một môi trường tại một thời điểm.

## 15. Giao việc cho AI: prompt mẫu dùng được ngay

### 15.1. Khối chỉ dẫn chung cho mọi AI

Copy khối này rồi điền thông tin cụ thể. Không gửi prompt chung kiểu “làm backend cho frontend này” mà thiếu hợp đồng.

```text
Bạn triển khai task <TASK_ID> cho dự án OCR Learning/LinguaLive.

Nguồn chuẩn:
- Kế hoạch: docs/TIEN-DO-VA-KE-HOACH-HOAN-THANH.md.
- Quyết định đã chốt: contracts/decisions.md.
- Contract version: <VERSION>, commit SHA: <SHA>.
- API/schema/fixtures liên quan: <PATHS>.
- Branch base và môi trường chạy: <BASE, ENV, COMMANDS>.

Phạm vi được sửa: <FILES/MODULES>.
Phạm vi không được sửa: <OTHER MODULES, CURRENT UI, CONTRACTS WITHOUT REVIEW>.

Yêu cầu:
1. Đọc code đang có và contract trước khi viết. Tái sử dụng module hiện hữu.
2. Không tự đặt endpoint/field/enum/auth/port mới, không đổi unit hoặc schema.
3. Nếu contract thiếu hay mâu thuẫn, chỉ ra chính xác trước khi làm phần phụ thuộc;
   tiếp tục phần độc lập, không tự dựng dữ liệu thay thế rồi tuyên bố tích hợp xong.
4. Mock phải cùng schema và được phân biệt; real mode không fallback mock im lặng.
5. Viết/running tests cần thiết theo acceptance bên dưới, có error/empty/retry case.
6. Không đổi thiết kế giao diện đã chốt khi task chỉ yêu cầu nối dữ liệu.
7. Không ghi secret vào source, URL ví dụ, log hoặc VITE_*.
8. Cuối task giao file list, cách chạy, test logs, env/migration và giới hạn còn lại.

Đầu vào cụ thể: <INPUT, FIXTURES>.
Đầu ra cụ thể: <ENDPOINT/COMPONENT/EVENT/ARTIFACT>.
Phụ thuộc đã có: <PROVIDER/CONSUMER VERSIONS>.
Acceptance: <SCENARIOS WITH EXPECTED RESULTS>.
```

### 15.2. Prompt cho AI của Tài Đức — frontend/media/integration

```text
Task OC-01 + OC-02: nối nguồn học thật vào UI đã chốt, chưa thay bố cục.
Được sửa src/media, src/api, hooks và phần App cần tích hợp; không sửa OCR server.
Dùng session/upload/job/result contracts phiên bản <VERSION> và fixture <PATHS>.

Làm chọn video và chia sẻ màn hình, preview, capture/nén theo giới hạn đã chốt,
source_id mới khi đổi nguồn, một job in-flight, bỏ kết quả nguồn cũ.
Dùng ocrClient thay vì rải fetch/WebSocket trực tiếp vào nhiều component.
Overlay theo vùng video thật sau object-fit contain; có empty/error/retry states.
Dừng track/timer/request khi rời phiên; không giữ ảnh hoặc JSON mẫu ở real mode.

Acceptance: ảnh mới có box đúng; resize/đổi nguồn/rời room không lệch hoặc leak;
mock test theo contract đạt, sau đó chạy smoke với app API + provider thật.
Bàn giao ảnh/video thử, lệnh test và yêu cầu backend còn thiếu.
```

Task frontend cho G1/G3/G4/G5 được giao riêng sau đó với cùng khối chung, không yêu cầu một AI viết lại toàn ứng dụng trong một lượt.

### 15.3. Prompt cho AI của Hoàng Bảo — app backend/auth/rooms/infra

```text
Task AU-03 + OC-04 backend theo OpenAPI/AsyncAPI <VERSION>, commit <SHA>.
Được sửa app backend, job/storage/WS adapters và contract fixtures đã phân công.
Không sửa layout frontend, không đổi raw OCR provider schema.

Tạo session/source/upload/job endpoints và trạng thái/lỗi đúng contract.
Kiểm tra Cognito subject, membership/host, source hiện hành và image metadata.
Job lưu bền vững, claim có lease, idempotency có unique key;
commit result trước khi phát WS result_available. Poll result vẫn hoạt động khi mất WS.
Cấp URL upload và WS ticket theo contract; không nhận URL tải ảnh tùy ý từ client.

Acceptance: hai user không xem/chạy job hộ nhau; retry không nhân đôi job;
provider down có trạng thái failed đúng; instance/worker chết job có thể phục hồi;
GET result và WS manifest trỏ cùng kết quả. Có local setup/env examples và test logs.
```

Task AWS/Chime được giao thành phần riêng; không tự chạy deploy/migration phá dữ liệu của môi trường khác ngoài quyền task đã cho.

### 15.4. Prompt cho AI của Bảo Anh — OCR/lexicon/log

```text
Task OC-03 + OC-05 trên repo OCR do Bảo Anh phụ trách.
Được sửa <EXPLICIT OCR PATHS>; đọc đánh giá OCR và raw schema <VERSION> trước.
Không tự thêm tài khoản/phòng/public app API vào provider.

Giữ full_text, words[].text/separator/box, is_vertical và elapsed_ms.
Phân biệt no-text [], bad-image, provider failure và timeout.
Giới hạn ảnh, kiểm tra concurrency, cleanup và readiness model;
không để dùng chung session/socket của provider sai cách khi nhiều worker.
Real-provider test trên runtime/container đã chốt, có tập ảnh và số đo;
không dùng dummy để báo độ chính xác hoặc latency thật.

Worker/text writer dùng job metadata và storage interfaces do app backend cung cấp,
không tự đặt S3 prefix, DynamoDB keys, role hoặc event name khác contract.
Đầu ra phải kèm raw result fixtures, test ảnh dọc/ngang/rỗng/hỏng và lệnh chạy.
```

Task LX-01…03 riêng cho từ điển: bắt buộc offset code point, POS enum, nguồn dữ liệu, lemma/sense và missing-data policy đúng mục 12; không biến 18 mục demo thành “từ điển tự động”.

## 16. Kiểm thử để ba thành phẩm ghép được với nhau

### 16.1. Fixtures tối thiểu dùng chung

| Fixture | Bắt lỗi gì | Người tạo chính |
| --- | --- | --- |
| `ocr-horizontal`, `ocr-vertical`, `ocr-empty` | Schema/box/hướng chữ/no-text | Bảo Anh |
| `ocr-invalid-image`, `ocr-too-large`, `ocr-timeout`, `ocr-busy` | Lỗi và retry/backpressure | Bảo Anh + Hoàng Bảo |
| `frame-old-source`, `frame-out-of-order`, `job-duplicate` | Kết quả cũ/trùng/đảo thứ tự | Đức + Hoàng Bảo |
| `token-expired`, `forbidden-session`, `forbidden-room` | Auth/permission | Hoàng Bảo |
| `room-closed`, `member-left`, `host-disconnected` | State machine phòng | Hoàng Bảo + Đức |
| `lexicon-inflected`, `lexicon-unknown`, `lexicon-unicode`, `lexicon-polysemy` | Dạng gốc, không tìm thấy, offset, nhiều nghĩa | Bảo Anh |
| `vocabulary-duplicate`, `shared-word-forbidden`, `history-empty` | Lưu trữ và ownership | Hoàng Bảo + Đức |
| `playback-processing`, `playback-unavailable`, `playback-ready` | Tránh nút xem lại giả | Hoàng Bảo + Đức |

Schema test cả success lẫn error. Producer xuất được JSON không đủ: consumer phải render và thao tác được từ đúng fixture đó. CI ghi rõ test nào mock và test nào cần cloud/provider thật.

### 16.2. Các tầng test

1. **Contract:** validate OpenAPI/JSON Schema/AsyncAPI, example requests/responses, generated types. AI sửa producer không được làm consumer cũ fail mà bỏ qua.
2. **Module:** component hover/media cleanup; auth/API validation; provider image handling, token offsets và storage writer.
3. **Integration local:** frontend + app + OCR thật + storage phù hợp; Cognito/Chime dùng dev environment khi cần. Không gọi là end-to-end nếu phần chính vẫn mock.
4. **Integration cloud-dev:** Gateway, Cognito, Chime, S3/DynamoDB thực; kiểm tra CORS/HTTPS/WS và role.
5. **Nghiệm thu thủ công:** hai tài khoản/hai browser hoặc hai máy, dữ liệu mới, người trong nhóm chạy theo checklist.

### 16.3. Kịch bản nghiệm thu cuối

| Kịch bản | Kết quả phải quan sát được | Ai xác nhận |
| --- | --- | --- |
| User A đăng ký/đăng nhập, user B riêng | Profile/quyền và dữ liệu tách biệt | Hoàng Bảo + Đức |
| A chia sẻ nội dung Nhật chưa dùng trong fixture | Chữ thật + tọa độ đúng; không có text hardcode | Bảo Anh + Đức |
| Đổi nguồn khi OCR đang chờ | Không vẽ kết quả nguồn cũ lên nguồn mới | Đức + Bảo Anh |
| Hover/chạm một từ mới, lưu rồi tải lại trang | Nghĩa/loại từ/cách đọc thật; từ còn trong thư viện | Cả ba |
| Tạo phòng, B nhập mã | A/B cùng xem và nói/chat, đếm người đúng | Hoàng Bảo + Đức |
| C tạo phòng khác | C không nhận video/text/data của A/B | Hoàng Bảo |
| Member rời/host mất mạng/reconnect | Cleanup/quyền/grace đúng state machine | Hoàng Bảo + Đức |
| Lịch sử và playback | Đúng user/phiên/video/log; có trạng thái nếu không ghi hình | Cả ba |
| User thường mở API Admin | Bị từ chối; admin có audit và theo dõi được lỗi | Hoàng Bảo + Đức |
| Mạng chập chờn/provider lỗi/worker chết | UI báo đúng; job phục hồi hoặc fail rõ; không treo vô hạn | Cả ba |
| URL cloud sau deploy/rollback | Luồng vẫn chạy đúng contract/version đã ghi | Đức + Hoàng Bảo |

Lưu bằng chứng vào thư mục test/report riêng không chứa token, URL ký còn hạn, ảnh riêng tư hoặc dữ liệu tài khoản thật không cần thiết. Kết quả benchmark ghi tập ảnh, runtime/model/provider, môi trường, số lần chạy, tỷ lệ nhận đúng và p50/p95; đặt ngưỡng pass sau khi D12 đã chốt, không tự tạo số liệu để đẹp báo cáo.

## 17. Nếu nhóm chủ yếu giao AI làm, người trong nhóm cần làm gì?

AI có thể viết code, test, adapters, cấu hình hạ tầng và tài liệu. Vai trò con người vẫn có bốn việc để tránh “ba AI báo xong nhưng ghép không chạy”:

1. **Chốt yêu cầu:** cả ba xác nhận D01…D14; Đức giữ một bản chuẩn. AI không thể tự biết nhóm muốn giữ nguyên sơ đồ PDF hay điều chỉnh đường truyền ảnh.
2. **Giao quyền/phạm vi:** từng người chỉ định repo, file, môi trường, task, contract và acceptance. Ai giữ OCR mới giao quyền sửa OCR; không cấp quyền lan sang frontend/infra vô tình.
3. **Chạy nghiệm thu chéo:** Đức thử backend mà không nhờ AI backend “tự chứng nhận”; Hoàng Bảo thử quyền và dữ liệu; Bảo Anh thử chữ thật/hiệu năng. Khi fail, gửi request_id/job_id/log đúng bộ, tránh chỉ gửi “không chạy”.
4. **Xác nhận kết quả và báo cáo:** chỉ chuyển accepted khi có bằng chứng thật; ghi rõ mock/dummy, giới hạn provider và phần chưa làm. Không cần tự viết mọi dòng code, nhưng cần hiểu luồng dữ liệu và giải thích được khi trình bày môn học.

Mỗi buổi tích hợp ghi: base/contract version → task vừa merge → lệnh chạy → ca pass/fail → log IDs → việc chặn → người xử lý tiếp. Giữ một danh sách lỗi chung thay vì ba cuộc chat AI tự đưa ra ba cách sửa khác nhau.

## 18. Việc cụ thể nên làm ngay sau khi đọc file này

1. **Đức:** tạo bảng quyết định thực tế từ mục 7, gửi cho hai bạn xác nhận; chốt việc giữ thiết kế và dữ liệu UI cần.
2. **Hoàng Bảo:** điền stack/region/repo backend hiện có; chuẩn bị OpenAPI/WS draft và local setup theo mẫu; chứng minh Cognito/Chime/Gateway dev khả thi.
3. **Bảo Anh:** xác nhận raw OCR schema/provider/runtime, chạy bộ ảnh thật và đề xuất từ điển. Liệt kê lỗi OCR sẽ sửa theo phạm vi repo của mình.
4. **Cả nhóm:** đóng băng contract v1 + fixtures; Đức lưu version/commit và giao prompt theo từng task nhỏ.
5. **Làm M1 song song rồi ghép M2:** mục tiêu đầu tiên là solo OCR thật, không đầu tư thêm hiệu ứng giao diện trong lúc đường dữ liệu chưa chạy.
6. **Sau mỗi mốc:** cập nhật trạng thái ready/integrated/accepted và phần còn thiếu; không xóa bảng đối chiếu PDF chỉ vì một AI đã tạo đủ file.

## 19. Nguồn và giới hạn của kế hoạch

- Báo cáo 2.pdf: use case/trách nhiệm/kiến trúc ở trang 9–15; bảng phân công gốc là căn cứ gắn người phụ trách.
- Code hiện tại và các ghi chú: [đánh giá OCR](DANH-GIA-OCR.md), [giao diện/hover](NANG-CAP-HOVER-VA-HINH-ANH.md), [popup tra từ](TRA-TU-TRONG-PHIEN-AM.md).
- Tài liệu AWS chính thức đã đối chiếu cho những điểm có thể làm ba phần không tương thích: [WS binary payload](https://docs.aws.amazon.com/apigateway/latest/developerguide/websocket-api-develop-binary-media-types.html), [WS quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-execution-service-websocket-limits-table.html), [WS authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api-lambda-auth.html), [Chime meetings/data messages](https://docs.aws.amazon.com/chime-sdk/latest/dg/meetings-sdk.html), [capture](https://docs.aws.amazon.com/chime-sdk/latest/dg/capture-pipe-config.html), [concatenation](https://docs.aws.amazon.com/chime-sdk/latest/dg/create-concat-pipe.html).

Không có API v1, contract files, cloud resource hoặc worker mới nào được triển khai chỉ vì tài liệu này mô tả chúng. Đây là kế hoạch và bộ đề xuất để chốt; việc triển khai tiếp cần theo task/owner/phạm vi đã xác nhận.
