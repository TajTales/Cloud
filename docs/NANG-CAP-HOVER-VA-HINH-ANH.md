# Nâng cấp hình ảnh và hover trên giao diện gốc

Ngày: 11/11/2026.

## Phạm vi

Giữ bố cục Figma gốc, bốn thẻ chức năng, các màn hình đăng nhập, phòng học, thư viện, lịch sử và những thao tác đã có. Không thay bằng bản thiết kế tối giản đã bị hoàn tác. Không chỉnh `meikipop-ocr-server` hay nối API OCR.

## Những gì đã thay đổi

- Thêm `src/cinematic.css`, được nạp sau CSS gốc trong `src/main.tsx`. Các điều chỉnh hình ảnh được đặt riêng để dễ xem lại và điều chỉnh.
- Bản sáng dùng trắng ngà, xanh rêu, cam đất; bản tối dùng xanh than, bề mặt xanh đậm và cam san hô. Đồng bộ màu chữ, panel, menu và form theo bộ biến màu.
- Thanh điều hướng nổi có nền kính mờ, đường nhấn cam cho mục đang chọn; giữ vị trí và chức năng điều hướng cũ.
- Bốn thẻ có phần minh họa riêng: ảnh phố Nhật cho học cá nhân, thẻ giấy cho tạo phòng, vòng kết nối cho tham gia và chồng nhật ký cho lịch sử. Ảnh tái sử dụng nguồn Unsplash có sẵn trên trang đăng nhập; các hình còn lại dựng bằng CSS.
- Giữ tiêu đề/nội dung gốc; chia dòng tiêu đề theo chuỗi VI/EN đã có, thay hiệu ứng chữ bị làm mờ bằng chữ đọc được ngay.
- Hover thẻ nâng 4 px, nghiêng tối đa khoảng 1,5° mỗi trục, viền và ánh sáng mềm theo vị trí chuột; icon và mũi tên dịch chuyển nhẹ. Thời gian phản hồi khoảng 180–250 ms.
- Nút bấm đứng yên khi rê chuột, đổi nền/viền và phản hồi nén nhẹ khi bấm. Bỏ tính hút nút theo chuột.
- Gỡ component con trỏ tùy chỉnh và vòng lặp requestAnimationFrame; chỉ giữ listener cập nhật vị trí spotlight. Con trỏ chuột dùng mặc định.
- Bỏ hiệu ứng chữ sáng chạy/làm mờ, tia sáng khi bấm và scan line; làm nền trang đăng nhập dịu hơn. Hover vẫn được giữ ở thẻ, nút, bộ từ và hàng lịch sử.
- Video được làm rõ vai trò trung tâm, viền và thanh điều khiển gọn hơn. Panel transcript phân biệt chữ gốc, cách đọc và nghĩa; tăng độ tương phản ở bản tối.
- Các ô OCR mẫu có thể chọn để mở khung xem từ; khung có nút nghe bằng Web Speech API, lưu từ vào state và đóng bằng nút hoặc Escape. Không cho lưu trùng. Hàng từ đã lưu tương ứng được nhấn màu.
- Hàng từ có nút nghe khi hover hoặc focus; trên thiết bị cảm ứng nút luôn hiện. Có thể chọn lại từ từ danh sách để mở khung thông tin. Chất lượng/khả năng phát âm tiếng Nhật tùy giọng có sẵn trong trình duyệt và hệ điều hành.
- Không thay ảnh giả lập bằng video thật trong lượt này. OCR, transcript, từ vựng mẫu và đăng nhập demo vẫn giữ bản chất hiện tại; lưu từ mới chỉ trong React state, chưa lưu máy chủ.
- Mobile giữ bố cục xếp dọc gốc; giảm kích thước phụ đề, giới hạn chiều rộng để không chiếm hết video. Hỗ trợ reduced motion, focus-visible và không dùng nghiêng thẻ trên thiết bị không có hover.

## Kiểm tra

- TypeScript `pnpm exec tsc --noEmit` và `pnpm build` đạt.
- Chromium: vẫn đủ bốn thẻ và các màn hình cũ; kiểm tra hover có transform và tọa độ spotlight, sáng/tối, chọn chữ OCR, lưu từ và nhấn màu từ tương ứng.
- Đo không tràn ngang ở phòng học và trang chính tại 390, 768 và 1440 px.
- Kiểm tra lại thẻ nhật ký để khung buổi gần nhất không chồng lên tiêu đề.
- Kiểm tra reduced motion tắt transform của thẻ; không còn DOM con trỏ tùy chỉnh. Không ghi nhận JavaScript pageerror trong các luồng đã kiểm tra.
- Kiểm tra Git không có thay đổi trong thư mục server. Thay đổi có sẵn `.figma/make/format` bị xóa được giữ nguyên.

## Ảnh hiện tại

Ảnh trong `review-assets` đã được chụp lại theo phiên bản này:

- [Trang chính sáng](review-assets/lobby-desktop.png)
- [Trang chính tối](review-assets/lobby-dark.png)
- [Hover trên thẻ](review-assets/lobby-hover.png)
- [Trang chính mobile](review-assets/lobby-mobile.png)
- [Phòng học sáng](review-assets/room-desktop.png)
- [Phòng học tối](review-assets/room-dark.png)
- [Khung xem/lưu từ](review-assets/room-word-detail.png)
- [Phòng học mobile](review-assets/room-mobile.png)
- [Đăng nhập](review-assets/login-desktop.png)
- [Thư viện](review-assets/library-desktop.png)
- [Lịch sử](review-assets/history-desktop.png)

## Sửa lỗi nền biến mất khi hover ở chế độ tối

Quy tắc cũ `[data-theme="dark"] .mode-card::before` đặt nền đặc lên lớp spotlight. Khi hover tăng opacity lên 1, lớp này che phần minh họa. Đã sửa selector trong `cinematic.css` cho cả thẻ thường và thẻ học cá nhân, giữ gradient trong suốt ở hai chế độ. Kiểm tra bằng Chromium: cả bốn thẻ đều có lớp phủ trong suốt khi hover ở sáng/tối; build đạt. [Ảnh kiểm tra hover tối](review-assets/lobby-dark-hover.png).
