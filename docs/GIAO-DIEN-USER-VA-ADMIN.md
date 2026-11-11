# Giao diện User và Admin theo Báo cáo 2

Ngày: 11/11/2026. Căn cứ sơ đồ use case và bảng tác nhân/chức năng ở trang 8–10 của PDF. Lượt này chỉ chỉnh frontend và tài liệu; không sửa server OCR, không tạo API hay triển khai quyền Admin thật.

## 1. Vì sao Admin có khu vực riêng?

User tập trung vào học cá nhân/nhóm, xem video, chữ nhận dạng, trò chuyện, gọi thoại và nhật ký. Admin tập trung vào quản lý người dùng, quản lý hệ thống và theo dõi hoạt động. Vì vậy giữ giao diện học của User, bổ sung một khu vực quản trị cùng bảng màu/kiểu chữ thay vì đưa tất cả nút quản lý vào phòng học.

Vai trò hệ thống User/Admin khác vai trò trong phòng host/member. Một người tạo phòng không vì thế trở thành Admin hệ thống.

## 2. Cách xem thử Admin

1. Mở ứng dụng ở Vite development server, ví dụ localhost:8443.
2. Nếu đang đăng nhập, dùng menu tài khoản → Đăng xuất.
3. Trong màn hình đăng nhập, chọn **Quản trị viên** ở **Vai trò xem trước**.
4. Nhập email hợp lệ và mật khẩu ít nhất 6 ký tự như luồng đăng nhập demo hiện tại.
5. Sau khi vào, dùng **Về giao diện người học** để trở lại User hoặc **Đăng xuất** để chọn lại vai trò.

Chọn vai trò này chỉ xuất hiện khi `import.meta.env.DEV` là true. State role xem trước lưu trong sessionStorage để refresh dev vẫn mở đúng giao diện. Đây **không phải kiểm tra quyền**; email/mật khẩu demo không xác thực với server. Bản production không cho chọn vai trò qua bộ chọn này. Khi tích hợp Cognito/API, vai trò phải lấy từ danh tính đã xác thực và backend kiểm tra từng thao tác; không lấy sessionStorage/localStorage làm căn cứ cấp quyền.

## 3. Khu vực Admin đã thêm

| Màn hình | Tương tác đã làm | Phạm vi thực tế |
| --- | --- | --- |
| Tổng quan | Thẻ số liệu, phòng đang mở, sự kiện gần đây, chuyển nhanh tới chức năng | Số liệu được tính từ bộ mẫu, có ghi rõ minh họa |
| Người dùng | Tìm theo tên/email không phân biệt dấu, lọc vai trò/trạng thái, xem chi tiết, khóa/mở khóa | Chỉ thay đổi bản sao tài khoản mẫu; không tác động tài khoản đăng nhập User |
| Phòng học | Tìm tên/mã/chủ phòng, lọc mở/đóng, xem chi tiết, đóng phòng | Chỉ thay đổi room fixture, không gọi Chime hoặc làm người thật rời phòng |
| Hệ thống | Form provider/frame interval/worker/giới hạn ảnh, lưu mẫu, bật/tắt bảo trì mẫu | Không thay cấu hình provider hoặc server; các dịch vụ thực đều hiện chưa kết nối |
| Nhật ký hoạt động | Tìm sự kiện, lọc mức độ, xem chi tiết; thêm log khi thao tác quản trị mẫu | Log nằm trong state của phiên giao diện, chưa là audit log server |

- Khóa/mở khóa, đóng phòng, bảo trì và đặt lại dữ liệu yêu cầu nhập lý do/xác nhận trong dialog.
- Không cho tự khóa tài khoản Admin đang dùng; tài khoản chưa xác nhận có trạng thái riêng.
- Không cung cấp nút tự nâng quyền user hoặc sửa mật khẩu thật từ giao diện mẫu.
- Dữ liệu được giữ khi chuyển tab quản trị, đặt lại khi rời/unmount khu vực quản trị; có nút đặt lại bộ mẫu.
- Có trạng thái danh sách rỗng, thông báo kết quả, dialog chi tiết, bàn phím/Escape, sáng/tối và bố cục mobile. Bảng rộng cuộn ngang bên trong panel.
- “Làm mới bản xem trước” chỉ làm mới phần hiển thị và thời gian xem, không giả vờ kiểm tra được backend đang sống.

## 4. Các phần User đã bổ sung

### 4.1. Học cá nhân và vai trò trong nhóm

- Giữ bốn thẻ chức năng, phong cách hover, thư viện/lịch sử và popup Yomitan đang có.
- Solo có nhãn Học cá nhân; ẩn mã phòng, thành viên, chat, micro/camera của học nhóm.
- Tạo phòng mẫu đặt vai trò host; nhập mã mẫu đặt vai trò member. Mã chưa được server xác thực, hiển thị là mã mẫu.
- Host/solo thấy chọn nguồn học; member không có nút thay nguồn của chủ phòng.
- Thêm dialog thành viên mẫu, phân biệt chủ phòng/thành viên.
- Sao chép mã phòng chỉ báo thành công sau khi Clipboard API thành công; có thông báo nếu không chép được.

### 4.2. Chọn nguồn thật để xem trước

- Mở video cục bộ qua file input, native video controls và `object-fit: contain`.
- Chia sẻ màn hình qua `getDisplayMedia`, người dùng tự cấp quyền trong trình duyệt.
- Hiển thị tên nguồn, đổi/dừng nguồn, lỗi định dạng/quyền/trình duyệt không hỗ trợ.
- Thu hồi object URL, dừng media track và bỏ kết quả cấp quyền muộn khi rời phiên.
- Không giữ dialog chờ vô hạn chỉ vì video chưa phát frame đầu tiên.
- Nguồn cục bộ chưa upload, chưa chia sẻ qua Chime và chưa gửi OCR. Có banner giải thích; overlay, phụ đề và điều khiển video mẫu được ẩn khi chọn nguồn thật.
- Panel phiên âm vẫn có câu mẫu để thử popup; nhãn và banner nêu rõ dữ liệu mẫu, không dùng “đang nhận dạng” cho nguồn chưa nối backend.

### 4.3. Trò chuyện, từ vựng, ôn tập và nhật ký

- Chat nhóm có form gửi tin nhắn thử trong state, chặn rỗng và giới hạn 500 ký tự; render text thuần, không chèn HTML. Tin nhắn chưa truyền cho người khác.
- Nút ôn từ trong phòng và thư viện mở flashcard, lật thẻ, đánh dấu đã nhớ/cần ôn và tổng kết lượt. Bộ Nhật dùng từ đã lưu trong phiên; bộ Pháp/Anh có ba mục mẫu riêng.
- Kết quả ôn chỉ trong phiên dialog, chưa có thuật toán SRS hay lưu lên tài khoản.
- “Xem lại” mở chi tiết nhật ký mẫu. Ghi rõ chưa có bản ghi video; có thể mở giao diện phiên mẫu nhưng không giả vờ phát lại video thật.
- Nút xem lại được giữ truy cập trên mobile.

### 4.4. Hồ sơ và luồng tài khoản

- Hồ sơ sửa tên hiển thị/email dùng thử; cài đặt ngôn ngữ học/múi giờ.
- Những thiết lập công khai này lưu ở `lingualive-demo-profile` trong localStorage; không lưu password.
- Avatar/tên/email phản ánh hồ sơ đã lưu. Profile không có điều khiển cấp quyền Admin.
- Thêm dialog đăng ký mẫu với kiểm tra xác nhận mật khẩu, và dialog quên mật khẩu mẫu; ghi rõ chưa tạo tài khoản/gửi email vì Cognito chưa nối.
- Sửa reset trạng thái đăng nhập sau logout để có thể đăng nhập thử lần nữa.
- Các nút Google/Facebook còn là UI cũ, chưa tích hợp OAuth. Đăng nhập hiện vẫn là demo, chưa có token thật.

## 5. Tệp đã thêm/sửa

- `src/admin/AdminWorkspace.tsx`: khu vực quản trị và thao tác/state UI.
- `src/admin/adminDemo.ts`: fixtures tài khoản/phòng/nhật ký, cấu hình mẫu, helper tìm kiếm.
- `src/admin/AdminWorkspace.css`: layout và theme quản trị.
- `src/components/AppDialog.tsx`, `AppDialog.css`: native dialog dùng chung cho những màn mới; focus/modal/Escape và form/button styles.
- `src/components/AccountPanels.tsx`: hồ sơ/cài đặt/đăng ký/quên mật khẩu dùng thử.
- `src/components/ReviewCards.tsx`: ôn thẻ từ.
- `src/hooks/useRoomMedia.ts`: nguồn video/screen và lifecycle cleanup.
- `src/userFeatures.css`: phần mở rộng UI User, bộ chọn vai trò dev và flashcard.
- `src/App.tsx`: nối vai trò dev, màn Admin, các chức năng User; giữ renderer Yomitan.
- Tài liệu tiến độ và đánh giá OCR cập nhật để phân biệt chức năng đã có UI với phần backend còn thiếu.

## 6. Kiểm tra đã chạy

- `pnpm build`: đạt.
- TypeScript: đạt với `pnpm exec tsc --noEmit --ignoreDeprecations 5.0`.
- Lưu ý cấu hình có sẵn: người dùng đã thêm `ignoreDeprecations: "6.0"` vào tsconfig.json trước lượt này, trong khi TypeScript đang cài không chấp nhận giá trị đó. Đã dùng override dòng lệnh khi kiểm tra; không sửa hoặc hoàn tác thay đổi tsconfig của người dùng. Lệnh tsc mặc định vẫn cần giải quyết tương thích phiên bản/cấu hình riêng.
- Chromium: chọn role preview, đăng nhập Admin; tìm/lọc user, khóa/mở khóa có lý do, tự khóa bị chặn; đóng phòng; lưu cấu hình/bảo trì; kiểm tra log; chuyển User và logout/login lại.
- Admin không tràn ngang trang tại 390, 768, 1440 px ở tổng quan, người dùng và hệ thống; bảng cuộn riêng.
- User solo/member: đúng điều khiển nguồn và nhóm; chat text có chuỗi giống HTML vẫn là text; ôn flashcard hoàn tất; hồ sơ cập nhật và thiết lập được lưu.
- Tạo video WebM thử bằng canvas và xác minh mở file có metadata/chiều rộng 640 px; dừng nguồn đưa về UI mẫu.
- Dùng canvas stream giả lập API chia sẻ để kiểm tra gắn nguồn và thu hồi track khi rời phiên. Không tự chọn màn hình thật hoặc thay quyền trình duyệt của người dùng.
- Đăng ký mẫu kiểm tra mật khẩu không trùng/trùng; reset mẫu; xem chi tiết nhật ký trên mobile; Yomitan vẫn render được sau tích hợp.
- Không có JavaScript pageerror trong các luồng đã chạy; kiểm tra Git không có thay đổi trong server OCR.

## 7. Việc backend cần làm tiếp

Cognito và role claims thật; API user/admin với kiểm tra quyền phía server; quản lý phòng/meeting/attendee; Chime thoại/video/chat; chụp/nén/gửi frame và OCR thật; từ điển, lưu từ/ôn tập/nhật ký bền vững; số liệu/health/audit thật. Các thao tác UI mới không được coi là đã hoàn thành những hạng mục backend đó.

## 8. Ảnh minh chứng

- [Admin tổng quan sáng](review-assets/admin-overview-light.png)
- [Admin tổng quan tối](review-assets/admin-overview-dark.png)
- [Quản lý người dùng](review-assets/admin-users.png)
- [Cấu hình/giám sát hệ thống](review-assets/admin-system.png)
- [Admin mobile](review-assets/admin-mobile.png)
- [Đăng nhập và chọn vai trò](review-assets/login-desktop.png)
- [Chọn nguồn học](review-assets/user-source-picker.png)
- [Phòng học User](review-assets/room-desktop.png)
- [Phòng học User mobile](review-assets/room-mobile.png)
- [Chi tiết nhật ký mobile](review-assets/user-history-detail.png)
