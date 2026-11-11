# CT-01 — Điểm mở, người xác nhận và điều kiện qua G0

**DRAFT, 11/11/2026.** [Audit](G0-CURRENT-STATE.md), [D01–D14](../contracts/decisions.md) và [kiến trúc đề xuất](G0-INTEGRATION-ARCHITECTURE.md) đã đủ để **ready_for_review**. Không có xác nhận kiến trúc từ cả ba thành viên trong lượt này; không gán các đề xuất thành quyết định đã duyệt.

## 1. Quyết định cần xác nhận trước CT-02 chính thức

Các giá trị trong bảng là phương án đề xuất để chọn, không là mặc định đã chốt.

| Ưu tiên / mã | Cần nhóm trả lời gì | Đề xuất để review | Ai phải chuẩn bị / xác nhận | Ảnh hưởng nếu chưa chốt |
| --- | --- | --- | --- | --- |
| P0 Q01 / D03,D07 | Có repo app backend/hạ tầng riêng không; path/link/branch/commit nào, ai có quyền đọc? | Cung cấp checkout hoặc snapshot đã che secret; tái sử dụng nếu phù hợp. Nếu chưa có mới chốt Python 3.12/aiohttp | Hoàng Bảo chuẩn bị; cả ba xác nhận | Không chọn framework/server trùng hoặc kết luận backend chưa phát triển |
| P0 Q02 / D01 | Tên sản phẩm/báo cáo; Nhật và Trung có cùng phải chạy ở bản nộp không? Anh/Pháp trong UI có thuộc scope thật không? | Giữ LinguaLive/OCR Learning; Nhật tích hợp trước, Trung vẫn là yêu cầu cuối nếu chưa chốt giảm; Anh/Pháp là demo | Đức tổng hợp; cả ba | Không thể định nghĩa languages/dataset/acceptance cuối |
| P0 Q03 / D02 | “Phiên âm” lấy từ chữ trên ảnh hay lời nói; có yêu cầu ASR ở bản nộp không? | Mốc đầu OCR-derived text/readings; ASR chỉ thêm khi có task/budget; chỉnh PDF nếu bỏ lời thoại | Đức + Bảo Anh đề xuất; cả ba | Tránh AI làm audio transcript khác nguồn với OCR contract |
| P0 Q04 / D05 | Có đồng ý đổi mũi tên ảnh từ WS Gateway sang HTTP/S3 không? | HTTP upload/job, WS manifest/control; giữ raw service nội bộ | Hoàng Bảo + Bảo Anh phân tích; cả ba | Chưa viết transport/schema chính thức; binary aiohttp không tương thích trực tiếp Gateway |
| P0 Q05 / D14 | Giữ form Cognito SDK/SRP hay Managed Login/PKCE; cần nhớ phiên qua reload không? Token storage/rotation/lifetime thế nào? | Giữ form, public client/SRP, memory v1; nếu bắt buộc nhớ phiên cần chốt storage/BFF trước | Hoàng Bảo + Đức; cả ba | Chưa chọn SDK/authorizer/token contract hoặc coi checkbox hiện có đã chạy |
| P0 Q06 / D03,D04,D08 | Một public API/naming/envelope; ai sinh source_id/frame_id; thứ tự nguồn/timeline/offset/box theo chuẩn nào? | `/api/v1`, snake_case, app UUID; client đề xuất source/frame UUID, server đăng ký và cấp source_index; Cognito/AWS opaque; UTC/ms; offset code point | Hoàng Bảo DTO, Bảo Anh box/offset, Đức consumer; cả ba | Tránh ba AI đặt IDs/fields/thời gian khác nhau |
| P0 Q07 / D09 | Từ mặc định lưu cá nhân hay chung; ai thêm/xóa; identity entry/sense? | Personal mặc định, shared scope có quyền; vẫn triển khai bộ chung theo PDF | Cả ba, Hoàng Bảo giữ schema | Không thể khóa API quyền/lưu trùng/history/review |
| P0 Q08 / D06 | Chat qua meeting data messages hay app WS/Messaging; có lịch sử sau phiên không? | Chime meeting data messages, `chat_v1`, không persisted chat ở v1 nếu nhóm xác nhận | Hoàng Bảo + Đức; cả ba | Không triển khai nhiều transport chat hoặc nhầm buffer thành database |
| P0 Q09 / D10 | Playback bắt buộc cho group/solo-file/solo-share ở bản cuối? Giới hạn video/consent/quota? | Đủ đường recording/upload theo nguồn để hoàn thành PDF; `unavailable` chỉ là state, không thay chức năng | Hoàng Bảo + Đức; cả ba | Chưa khóa Recording/Source DTO và acceptance; không tự giảm phạm vi |
| P0 Q10 / D11 | AWS account/dev region/control/media/pipeline region, deployment hiện có, budget và model/provider thật là gì? | Khảo sát `ap-southeast-1`; benchmark MeikiOCR Nhật, Lens lựa chọn rõ; không đổi default source lúc audit | Hoàng Bảo account/region, Bảo Anh model/version; cả ba | **BLOCKED phần kiểm chứng D11** cho đến có input; không thể tuyên bố cloud ready |
| P0 Q11 / D12 | Chốt tải, dataset/accuracy, p95/deadline, byte/pixel/interval và retention? | Pilot 10 user/2 nguồn, 1 frame/2s, 1 MiB/4 MP; p95 ≤4s và CER ≤10% trên subset thống nhất là mục tiêu thử | Cả ba; Bảo Anh benchmark, Hoàng Bảo capacity, Đức UX | Không có tiêu chí pass hoặc giới hạn thống nhất cho API/config/worker |
| P0 Q12 / D13 | Corpus/tokenizer/reading/POS/dịch Việt từ đâu, version/quyền dùng, unknown/failure xử lý thế nào? | Backend lexicon adapter; khảo sát corpus Nhật/Trung; giữ Yomitan renderer, không LLM bịa entry | Bảo Anh cung cấp sample/nguồn; cả ba | Chưa freeze lexicon/saved-word identity; 18 mục demo không đủ |
| P0 Q13 / D15 kế hoạch | Nguồn role Admin, cấp/thu hồi quyền, khóa user/pending/self/last-admin; membership khác role hệ thống? | Role kiểm chứng ở backend; preview tắt trong real mode; profile không sửa role/email tùy ý; revoke có deadline | Hoàng Bảo + Đức; cả ba | Admin UI chưa thể nối mutations thật an toàn/đúng chức năng |
| P0 Q14 / D16 kế hoạch | Config OCR thực sự áp dụng theo instance thế nào; maintenance chặn việc nào; audit/action pending/failed? | Desired/effective/version/action, worker ack, reason/audit; số worker không là ASG size; hard limit không lấy từ form demo | Hoàng Bảo + Bảo Anh + Đức | Không thể coi setState/lưu DB là provider đã đổi; tránh race và false success |
| P1 Q15 / D07,CT-03 | Toolchain chuẩn và test commands; tsc config 6.0 với TS 5.9.3 giải quyết ra sao? | Chốt Node patch + pnpm repo 10.34.3, sửa tương thích ở PR riêng; Python 3.12 test thật/lock | Đức + chủ từng phần | Build pass nhưng check chuẩn fail; không nâng/hạ dependencies tùy AI |
| P1 Q16 / D05,D12 | Durable job DDB lease có đủ pilot hay cần SQS; notification phục hồi thế nào? | DDB claim/lease/backoff + polling/resync; commit-before-notify và retry. Đo trước khi thêm queue mới | Hoàng Bảo + Bảo Anh; Đức kiểm reconnect | Không dùng thread pool/RAM làm durable queue hoặc hứa exactly-once |

P0 là cổng trước contract chính thức. P1 phải chốt trước khi giao module tương ứng; chúng không cấp phép bắt đầu CT-02 khi P0 còn chưa rõ. Mỗi owner có thể nghiên cứu/đo phần độc lập trong phạm vi task riêng, không tự triển khai interface theo suy đoán.

## 2. Bằng chứng đang thiếu, cách gỡ và người giữ

| Input | Trạng thái audit | Bằng chứng cần có để gỡ | Người cung cấp |
| --- | --- | --- | --- |
| Repo app backend/infra ngoài workspace | `NOT_ACCESSIBLE` | Path/link được phép đọc, branch/SHA, README, routes/auth/storage/test/deployment config đã che secret | Hoàng Bảo |
| AWS dev environment | `NOT_ACCESSIBLE` | Account alias/region, resource inventory không secret, issuer/client ID public, Gateway/Chime/storage setup và kết quả smoke read-only/được giao quyền | Hoàng Bảo |
| Provider thật/model assets/container | `NOT_VERIFIED` | Runtime/container có lock, model version/checksum, startup/readiness, OCR ảnh thật/độ trễ/tọa độ và concurrency; không dùng dummy | Bảo Anh |
| ScreenAI/owocr external runtime | `NOT_ACCESSIBLE` | Native model assets/service/version hoặc chốt không dùng trong v1; không coi import adapter là service sẵn sàng | Bảo Anh |
| Dictionary/tokenizer/translation | `NOT_VERIFIED` | Corpus sample + nguồn/version/quyền dùng, câu mới có lemma/reading/POS/nghĩa/unknown; API cost nếu dùng provider | Bảo Anh |
| Nguồn chia sẻ/phát nhóm/recording thật | `NOT_VERIFIED` | Hai browser/tài khoản, content-share/voice/chat, source/frame/result IDs, recording/playback test theo quyền | Đức + Hoàng Bảo |
| Nghiệm thu hệ thống | Chưa có | Checklist từ dữ liệu mới, cloud/provider version và log request/job IDs; bằng chứng failed/retry/reconnect/cross-room | Cả ba |

Không cần gửi AWS secret, password, token, private provider key hoặc ảnh riêng tư để trả lời các câu hỏi. Metadata/version và quyền đọc phù hợp là đủ cho bước audit/ra quyết định.

## 3. Công việc giao tiếp theo sau review, không thực hiện trong CT-01

| Nhóm việc | Đã có để tái sử dụng | Việc kế tiếp / người phụ trách | Thứ tự |
| --- | --- | --- | --- |
| Xác nhận scope/architecture | Kế hoạch + bốn tài liệu CT-01 | Đức ghi lựa chọn từng Dxx và evidence; cả ba xác nhận; xử lý Q01–Q14 | Đầu tiên |
| Contract/toolchain/fixtures | Runtime manifests, raw OCR interface, nhu cầu UI đã có | CT-02/03/04 sau gate: Hoàng Bảo API/auth/WS, Bảo Anh OCR/lexicon, Đức consumers/toolchain/handover | Sau xác nhận |
| Auth/profile/Admin identity | Forms, User/Admin layout | Hoàng Bảo identity/quyền và `/me`; Đức adapter/challenge/error/real-mode role | Nền trước mutations |
| Solo OCR thật | Media hook, OCR service/provider, renderer | Đức capture/client/overlay; Hoàng Bảo upload/job/storage/WS; Bảo Anh provider/worker/readiness/lexicon | Luồng tích hợp đầu |
| Room/Chime/chat | Create/join dialog, roles/composer UI | Hoàng Bảo meeting/membership/permissions; Đức Chime media/chat; Bảo Anh shared OCR mapping | Sau solo hoặc nền song song theo contract |
| Dữ liệu/history/recording | Save/review/detail UI | Hoàng Bảo persistence/playback, Bảo Anh OCR logs, Đức ID/state/player adapter | Tích hợp sớm lưu từ; hoàn thiện replay sau |
| Admin/config/audit thật | Dashboard và reason dialogs mẫu | Hoàng Bảo read/actions/version/audit; Bảo Anh worker ack/metrics; Đức pending/error/DTO adapter | Read API sớm, config sau worker protocol |
| Cloud/tải/nghiệm thu | Docker/Compose/manual guide, CLI tests | Hoàng Bảo infra, Bảo Anh benchmark/container, Đức regression/deploy web khi được giao; cả nhóm nghiệm thu | Theo từng mốc, không đợi cuối |

Không giao lại task “thiết kế lại giao diện”. Không sửa OCR provider từ prompt frontend. Không tạo fake login/API hoặc dữ liệu mẫu để đóng task integrated.

## 4. Mẫu ghi nhận để nhóm trả lời

```text
Decision: Dxx / Qxx
Chọn: A / B / phương án khác (mô tả cụ thể)
Phạm vi bản nộp và phần hoãn:
Giá trị/đơn vị/giới hạn đã chốt:
Repo/branch/commit bằng chứng (nếu có):
Module/contract/PDF phải cập nhật:
Nguyễn Tài Đức xác nhận: <ngày, bằng chứng hoặc chưa xác nhận>
Nguyễn Hoàng Bảo xác nhận: <ngày, bằng chứng hoặc chưa xác nhận>
Trần Nguyên Bảo Anh xác nhận: <ngày, bằng chứng hoặc chưa xác nhận>
Điều kiện còn thiếu / ai cung cấp:
```

Chưa có dòng xác nhận thực tế nào được điền thay nhóm. Không dùng thời gian chờ phản hồi hoặc việc AI đã viết code làm bằng chứng đồng ý.

## 5. Trạng thái CT-01 và gate CT-02

| Hạng mục | Kết quả |
| --- | --- |
| Snapshot repo/working tree và cấu trúc | Đã ghi nhận, gồm các thay đổi chưa commit |
| Phân loại implementation/mock/không truy cập | Đã có path/dòng và giới hạn kiểm chứng |
| Đối chiếu PDF/kế hoạch/code | Đã liệt kê mâu thuẫn; không sửa PDF/kế hoạch ngoài phạm vi |
| D01–D14, phương án/đề xuất/module/owner/status | Đã lập, chưa xác nhận thay nhóm |
| Sơ đồ hiện trạng và draft đích; solo/group flows | Đã lập, thành phần E/P/U phân biệt rõ |
| Kiểm chứng tối thiểu | Vite build đạt; tsc mặc định fail/override đạt; 6/6 OCR dummy transport đạt; box fixture lỗi được ghi riêng |
| CT-01 | **ready_for_review**, chưa accepted; truy cập ngoài thiếu không ngăn bàn giao audit có giới hạn rõ ràng |
| Phần bị blocked | Kiểm chứng D11/deployment/model và backend ngoài chờ owner cung cấp đầu vào; không đánh dấu cả dự án đã dừng |
| CT-02 chính thức | **Chưa được chuyển sang** khi quyết định nền tảng chưa chốt; chưa có OpenAPI/AsyncAPI/fixtures v1 được tạo trong CT-01 |

Sau review cần xác nhận lựa chọn và điều kiện còn thiếu, cập nhật đồng bộ decisions/architecture/questions rồi mới giao CT-02. Không cần viết lại audit để giả như các resource ngoài đã được kiểm tra.
