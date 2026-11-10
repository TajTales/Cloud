# Bảng tra từ trong phần phiên âm

Ngày: 11/11/2026. Phạm vi: frontend; không chỉnh server OCR.

Cập nhật: phần dựng mục từ đã chuyển sang renderer/template thực của Yomitan. Xem [ghi chú tích hợp Yomitan](TICH-HOP-YOMITAN.md) để biết mã nguồn, giấy phép và những điều chỉnh. Tương tác hover/keyboard và nguồn dữ liệu mẫu mô tả bên dưới vẫn được giữ.

## Cách sử dụng

- Rê chuột vào từ trong câu tiếng Nhật hoặc dòng romaji: bảng nhỏ xuất hiện cạnh từ.
- Di chuột vào bảng để nghe hoặc lưu từ; bảng không đóng ngay khi rời khỏi chữ.
- Bấm/chạm vào từ để giữ bảng mở; bấm lại từ, bấm ra ngoài, nút đóng hoặc Escape để đóng.
- Dùng Tab để tới từ, Enter/Space để giữ bảng, mũi tên xuống để chuyển focus vào bảng. Escape đóng bảng và trả focus khi cần.
- Khi chuyển sang tab trò chuyện hoặc rời màn hình phòng học, component và bảng tra từ được gỡ.

## Thông tin hiển thị

- Chữ gốc, cách đọc kana và romaji.
- Loại từ: danh từ, động từ, tính từ な, trợ từ, từ chỉ định hoặc cách nói lịch sự.
- Nghĩa tiếng Việt phù hợp câu đang xem.
- Dạng từ điển nếu từ đã biến đổi, chẳng hạn 曲がった → 曲がる và 静かな → 静か.
- Giải thích ngắn về ngữ pháp/cách dùng và một câu ví dụ kèm nghĩa.
- Nút nghe bình thường, nghe chậm và lưu từ. Từ đã có trong danh sách hiển thị “Đã lưu”; không tạo bản trùng.

## Các tệp thay đổi

- `src/data/transcriptVocabulary.ts`: 18 mục từ được soạn cho hai câu transcript mẫu hiện có. Tách từ theo các mục đã biết, ưu tiên chuỗi dài, giữ nguyên dấu câu, khoảng trắng và nội dung câu gốc. Romaji kiểm tra ranh giới để không nhận nhầm các chữ nằm trong từ khác.
- `src/components/TranscriptVocabulary.tsx`: render từ có tương tác, quản lý hover/click/focus, bảng tra từ, portal và vị trí theo viewport. Có thời gian chờ đóng để chuột đi từ từ sang bảng.
- `src/components/TranscriptVocabulary.css`: kiểu chữ, nhấn từ đang chọn, bảng tra từ theo bộ màu sáng/tối, kích thước theo viewport, focus và reduced motion.
- `src/App.tsx`: dùng component cho phần transcript, nối nút lưu vào danh sách từ hiện tại, cho hàm phát âm nhận tốc độ đọc.

Popup dùng portal vào body nên không bị cắt bởi vùng cuộn transcript. Vị trí được tính lại khi cuộn, đổi kích thước cửa sổ hoặc kích thước bảng; bảng đóng nếu từ đã ra khỏi vùng transcript đang thấy. Trên mobile bảng bị giới hạn trong màn hình và cuộn được nếu chiều cao không đủ.

## Giới hạn dữ liệu

Đây là tra từ cho hai câu mẫu của giao diện hiện tại. Chưa gọi từ điển trực tuyến, chưa phân tích từ loại tự động và chưa nối OCR; không suy đoán loại từ cho chữ chưa có trong dữ liệu. Khi có transcript thật cần một dịch vụ tách từ/từ điển phù hợp và trạng thái chưa tìm thấy kết quả.

Phát âm dùng Web Speech API, đặt tiếng Nhật `ja-JP`, tốc độ 0,85 hoặc 0,6. Giọng đọc thực tế phụ thuộc trình duyệt và hệ điều hành. Nút nghe bị vô hiệu hóa nếu API không có. Không tự phát âm khi chỉ rê chuột.

Từ được lưu theo dạng từ điển nếu có, vào React state như danh sách cũ; chưa lưu lâu dài hay ghi lên máy chủ.

## Kiểm tra và ảnh

Kiểm tra TypeScript/build và Chromium: câu gốc được giữ nguyên; hover và di chuột sang bảng; click giữ bảng; loại từ/dạng gốc; lưu không trùng; tham số phát âm thường/chậm; bàn phím/Escape; gỡ bảng khi đổi tab; sáng/tối; bảng nằm trong viewport mobile 390×844. Phát âm được kiểm tra bằng lời gọi API, không đánh giá âm thanh/giọng đọc trên máy người dùng.

- [Bảng tra từ sáng](review-assets/transcript-vocabulary-light.png)
- [Bảng tra từ tối](review-assets/transcript-vocabulary-dark.png)
- [Bảng tra từ trên mobile](review-assets/transcript-vocabulary-mobile.png)
