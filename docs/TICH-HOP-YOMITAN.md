# Tích hợp popup Yomitan vào LinguaLive

Ngày: 11/11/2026. Chỉ chỉnh phần frontend tra từ; server OCR giữ nguyên.

## 1. Đã clone và dùng phần nào?

Đã clone [yomidevs/yomitan](https://github.com/yomidevs/yomitan) bằng Git, chốt commit `ee81f8dcf13e985bb4d7961009fb49a764b4d924`.

Yomitan là extension, không phải component React có thể import toàn bộ rồi chạy trên website. Phiên bản tích hợp này lấy **renderer thật `DisplayGenerator`, template mục từ và các module phụ thuộc**, gồm xử lý furigana, sang một snapshot trong `third_party/yomitan/`.

Khi người dùng chọn từ, adapter đổi dữ liệu hiện có thành term entry của Yomitan và gọi `createTermEntry`. DOM `.entry`, `.headword`, `.definition-item`, `.tag` và ruby/furigana được tạo bởi mã upstream. Đây không chỉ là vẽ lại popup cũ cho giống hình Yomitan.

## 2. Những điều đã điều chỉnh cho website

- Một patch nhỏ trong `DisplayGenerator.prepare`: nhận HTML template đã bundle bằng Vite, tránh gọi loader dựa trên `chrome.runtime` của extension.
- Giữ cấu trúc mục từ: headword/furigana, chuỗi biến đổi về dạng gốc, thẻ từ loại/nguồn, danh sách nghĩa đánh số.
- Trích 25 quy tắc CSS upstream, giới hạn selector trong popup, rồi điều chỉnh theo bảng màu sáng/tối của LinguaLive. Không nạp toàn bộ CSS extension lên ứng dụng.
- Nút cộng/lưu dùng danh sách từ hiện tại; nút loa dùng Web Speech API; nút `0.6×` nghe chậm. Không tự gọi dịch vụ âm thanh của Yomitan khi chưa có cấu hình nguồn.
- Giữ phần giải thích cách dùng, ví dụ Việt/Nhật và đọc romaji của dự án.
- Giữ hover, chạm, click giữ bảng, Escape, bàn phím và định vị popup theo viewport của component hiện có.
- Bỏ điều khiển Anki/menu/điều hướng chữ Hán chưa được nối, cùng phần tần suất/pitch accent không có dữ liệu. Không tạo nút giả hoặc số liệu giả.
- Chỉ đưa glossary dạng text vào renderer; không render HTML dictionary tùy ý. Các SVG nút là hằng số nội bộ, không nhận từ dữ liệu từ điển.
- Popup có link nguồn và giấy phép; có nhãn nguồn nghĩa là dữ liệu mẫu để không gây nhầm rằng đã tải JMDict hay từ điển đầy đủ.

## 3. Những phần chưa được tích hợp

- Chưa đưa toàn bộ extension, background service, scanner, database IndexedDB hoặc công cụ import dictionary vào website.
- Chưa tải từ điển bên ngoài. Nghĩa/cách dùng/ví dụ hiện vẫn là 18 mục từ được soạn cho hai câu transcript mẫu của LinguaLive.
- Chưa có từ điển tự động cho video/OCR mới, chưa có AnkiConnect, stroke order, pitch accent hoặc frequency database.
- Nút lưu vẫn dùng React state theo chức năng hiện có; chưa lưu backend.

Muốn tra nội dung bất kỳ, bước tiếp theo là nối nguồn từ điển/tách từ theo hợp đồng lexicon trong kế hoạch chung, rồi map kết quả thật sang adapter. Yomitan renderer không tự biến dữ liệu OCR thành nghĩa/từ loại.

## 4. Các tệp liên quan

| Vị trí | Vai trò |
| --- | --- |
| `third_party/yomitan/` | 23 module JS upstream và HTML/CSS gốc, GPL, manifest phiên bản/hashes, ghi chú patch |
| `third_party/yomitan/js/display/display-generator.js` | Renderer upstream, chỉ đổi đường chuẩn bị template cho web |
| `third_party/yomitan/js/display/display-generator.d.ts` | Interface TypeScript hẹp cho adapter |
| `src/components/YomitanEntry.tsx` | Map dữ liệu demo, gọi renderer, nối nút nghe/lưu, xử lý loading/error |
| `src/components/YomitanEntry.css` | CSS trích từ upstream có scope và phần điều chỉnh theme/layout |
| `src/components/TranscriptVocabulary.tsx` | Dùng YomitanEntry bên trong popup thay phần headword/nghĩa/controls tự dựng trước đây |
| `public/licenses/yomitan-GPL-3.0.txt` | Bản GPL được phục vụ cùng web build |

Không cần checkout tạm còn tồn tại hoặc cài extension Yomitan trên trình duyệt để app chạy. Không thêm dependency npm, không chạy build/install script của repo extension và không sửa cấu hình server OCR.

## 5. Giấy phép và nguồn

Yomitan dùng **GPL-3.0-or-later**, đã giữ copyright/header và full license. Mã adapter/CSS trích xuất có SPDX cùng giấy phép. Ghi rõ commit và thay đổi để có thể đối chiếu; không đổi tên mã upstream thành mã tự viết.

Khi phân phối bản frontend có mã GPL này, cần đi kèm các thông báo và đáp ứng điều kiện về mã nguồn tương ứng của bản kết hợp theo giấy phép. Link upstream không thay thế mã nguồn của những phần đã sửa tại dự án. Phần OCR server riêng không bị chỉnh giấy phép trong lượt này. Nguồn chuẩn: [LICENSE upstream](https://github.com/yomidevs/yomitan/blob/ee81f8dcf13e985bb4d7961009fb49a764b4d924/LICENSE), [README snapshot](../third_party/yomitan/README.md).

## 6. Kiểm tra

- TypeScript và Vite build đạt; renderer được bundle vào web, template được import `?raw`.
- Xác minh hashes: 24 tệp upstream giữ nguyên, duy nhất `display-generator.js` có patch được mô tả.
- Chromium: renderer tạo ruby/furigana thật, giữ câu transcript; hover/chuyển chuột sang bảng, click giữ, loại từ/dạng gốc, lưu không trùng, gọi phát âm thường/chậm, Escape/focus/bàn phím và gỡ bảng khi đổi tab đều hoạt động.
- Kiểm tra đầy đủ 18 mục từ; glossary có chuỗi giống HTML vẫn là text, không tạo phần tử img hoặc thực thi handler.
- Kiểm tra sáng/tối và popup nằm trong viewport mobile 390×844; không có JavaScript pageerror trong các luồng đã chạy.
- Phát âm chỉ kiểm tra lời gọi API, không chứng nhận chất lượng âm thanh/giọng đọc trên thiết bị người dùng.

Ảnh minh chứng:

- [Popup sáng](review-assets/yomitan-popup-light.png)
- [Popup tối](review-assets/yomitan-popup-dark.png)
- [Popup mobile](review-assets/yomitan-popup-mobile.png)
