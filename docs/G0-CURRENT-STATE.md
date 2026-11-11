# CT-01 — Audit hiện trạng OCR Learning / LinguaLive

Ngày audit: **11/11/2026**. Trạng thái báo cáo: **ready_for_review**. Đây là kết quả audit và đề xuất để review, chưa phải nghiệm thu sản phẩm hoặc xác nhận kiến trúc của cả nhóm.

Đọc tiếp: [D01–D14](../contracts/decisions.md), [kiến trúc draft](G0-INTEGRATION-ARCHITECTURE.md), [các điểm cần xác nhận](G0-OPEN-QUESTIONS.md). Tài liệu đối chiếu là [kế hoạch hiện hành](TIEN-DO-VA-KE-HOACH-HOAN-THANH.md), bản `draft-2026-11-11-user-admin-2`.

## 1. Phạm vi và cách kết luận

- Audit working tree thực tế, gồm cả file chưa commit; không chỉ đọc HEAD. Đọc cấu hình, source frontend, OCR service/provider, test CLI, snapshot Yomitan, công cụ Figma và tài liệu; tìm API/auth/storage/infra trên các file ẩn và file source ngoài thư mục dependency/cache.
- `EVIDENCED`: có bằng chứng code/cấu hình hoặc phép kiểm ghi rõ bên dưới. Không có nghĩa đã integrated/accepted.
- `LOCAL_ONLY` / `MOCK_ONLY`: hành vi thực thi cục bộ hoặc dữ liệu cố định, chưa phải chức năng nhiều người dùng/bền vững.
- `NOT_FOUND_IN_WORKSPACE`: không tìm thấy implementation trong phạm vi repo đã quét. Không suy ra tình trạng repo khác.
- `NOT_ACCESSIBLE`: repo/tài nguyên bên ngoài chưa được cung cấp quyền hoặc checkout; không kết luận chưa phát triển. `NOT_VERIFIED`: có code/hướng dẫn nhưng chưa kiểm chứng triển khai/chất lượng.
- Không đọc credential store/AWS account, không fetch/pull Git, không deploy, cài dependency hoặc chạy migration. Giá trị giống credential trong provider không được chép vào báo cáo.

Các tham chiếu `#L...` bên dưới chỉ dòng trong working tree tại thời điểm audit. Thay đổi chưa commit được ghi riêng, vì HEAD chưa tái tạo được toàn bộ UI hiện tại.

## 2. Snapshot Git và cấu trúc

| Thuộc tính | Kết quả đọc tại máy |
| --- | --- |
| Workspace | `/Users/ducen/VScode/Video Stream Language Learning` |
| Repo origin | `https://github.com/duchb1212/Cloud.git` |
| Branch | `main`, theo dõi `origin/main`; không có branch local khác |
| HEAD | `81be4b4a5a7baf24db0c9fdc5bbd2d72fed87340` |
| Commit | `clone yomitan and change FE`, thời gian commit `2026-11-11T01:32:50+07:00` |
| So với remote | `git branch -vv` không báo ahead/behind với remote-tracking ref local; **chưa fetch để xác nhận remote trực tiếp** |
| Trước CT-01 | **7 file tracked bị sửa, 17 file untracked**; giữ nguyên toàn bộ |
| OCR directory | Có trong repo gốc, 42 file tracked; không có nested `.git`/submodule riêng được tìm thấy |

Lệnh bằng chứng: `git status --short --branch`, `git status --short --untracked-files=all`, `git branch -vv`, `git log -1 --format='%H%n%h %s%n%aI'`, `git diff --stat`, `git ls-files meikipop-ocr-server`.

```text
.
├── AGENTS.md, CLAUDE.md                 hướng dẫn workspace
├── package.json, pnpm-lock.yaml         frontend dependencies/scripts
├── .mise.toml, tsconfig.json, vite.config.ts, index.html
├── .figma/make/                         dev/install/deploy/deploy-preview,
│                                       analyze-routes/langserver/dev.json/site.json
├── src/
│   ├── main.tsx, App.tsx                entry, màn hình và state demo
│   ├── index.css, cinematic.css, userFeatures.css
│   ├── admin/                          AdminWorkspace + CSS + adminDemo
│   ├── hooks/useRoomMedia.ts            video/share cục bộ
│   ├── components/                     AppDialog, AccountPanels, ReviewCards,
│   │                                   TranscriptVocabulary, YomitanEntry + CSS
│   └── data/transcriptVocabulary.ts     từ và tokenizer mẫu
├── public/                             favicon, giấy phép Yomitan
├── third_party/yomitan/                 renderer/template/CSS, 23 JS modules,
│                                       manifest commit/hashes và ghi chú patch
├── meikipop-ocr-server/
│   ├── README.md, DEPLOY.md, pyproject.toml, MANIFEST.in
│   ├── Dockerfile, docker-compose.yml, nginx.conf, meikipop-ocr.service
│   ├── test_server.py                   CLI + 6 transport checks
│   └── src/meikipop_ocr_server/
│       ├── server.py, static/index.html
│       └── ocr/                        interface, postprocessing,
│                                       glensv2/meikiocr/owocr/screenai/dummy
├── docs/                               6 tài liệu trước CT-01 + review-assets/
├── node_modules/, dist/                dependency/artifact có sẵn, không là source chuẩn
└── contracts/                          chưa tồn tại trước CT-01;
                                        lượt này chỉ thêm decisions.md
```

Không có README tại root. README vận hành hiện nằm trong OCR; [AGENTS.md](../AGENTS.md#L1) mô tả scaffold/frontend. Không thấy app backend riêng, IaC, migration, DB client, CI workflow hoặc test frontend được version hóa trong danh mục đã quét. Dẫn chứng hỗ trợ: [dependencies frontend](../package.json#L6), [OCR dependencies](../meikipop-ocr-server/pyproject.toml#L10), [toàn bộ route OCR](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L231), [Vite server config](../vite.config.ts#L43).

### Thay đổi có sẵn trước audit

```text
 M docs/DANH-GIA-OCR.md
 M docs/TIEN-DO-VA-KE-HOACH-HOAN-THANH.md
 M docs/review-assets/login-desktop.png
 M docs/review-assets/room-desktop.png
 M docs/review-assets/room-mobile.png
 M src/App.tsx
 M tsconfig.json
?? docs/GIAO-DIEN-USER-VA-ADMIN.md
?? docs/review-assets/admin-mobile.png
?? docs/review-assets/admin-overview-dark.png
?? docs/review-assets/admin-overview-light.png
?? docs/review-assets/admin-system.png
?? docs/review-assets/admin-users.png
?? docs/review-assets/user-history-detail.png
?? docs/review-assets/user-source-picker.png
?? src/admin/AdminWorkspace.css
?? src/admin/AdminWorkspace.tsx
?? src/admin/adminDemo.ts
?? src/components/AccountPanels.tsx
?? src/components/AppDialog.css
?? src/components/AppDialog.tsx
?? src/components/ReviewCards.tsx
?? src/hooks/useRoomMedia.ts
?? src/userFeatures.css
```

Lượt CT-01 không gộp hoặc commit các thay đổi trên. Diff cũ đã được xem bằng `git diff --stat` và nội dung source/tài liệu tương ứng; bốn file được phép tạo đều chưa tồn tại, nên không có tài liệu đích cũ để ghi đè.

## 3. Tiến độ thực tế dựa trên code

| Hạng mục / task kế hoạch | Hiện trạng có bằng chứng | Mức chứng minh / việc còn thiếu |
| --- | --- | --- |
| UI sáng/tối, điều hướng, bốn thẻ | [main.tsx:3](../src/main.tsx#L3), [App:378](../src/App.tsx#L378), CSS và component hiện hữu | `EVIDENCED` frontend; giữ thiết kế. Build đạt, chưa nghiệm thu toàn hệ thống |
| AU-01/02 đăng nhập, đăng ký/reset | Login timer ghi `lingualive-auth`: [App:473](../src/App.tsx#L473); [AccountPanels:11](../src/components/AccountPanels.tsx#L11) chỉ validate form | `MOCK_ONLY`; không kiểm tra mật khẩu, không token/email/xác nhận. Google/Facebook [App:564](../src/App.tsx#L564) chưa có handler auth |
| AU-03 phân quyền | Dev role từ sessionStorage [App:365](../src/App.tsx#L365), render Admin [App:576](../src/App.tsx#L576) | `MOCK_ONLY`; không có identity/authorization thật, kể cả login production vẫn là local flag |
| AU-04 hồ sơ/cài đặt | [App:366](../src/App.tsx#L366), [App:404](../src/App.tsx#L404) localStorage; [AccountPanels:16](../src/components/AccountPanels.tsx#L16) chọn ngôn ngữ/timezone | `LOCAL_ONLY`; không có `/me`, cache chưa phân user, email đổi cục bộ chưa được xác minh |
| OC-01 nguồn video/share | [useRoomMedia:13](../src/hooks/useRoomMedia.ts#L13) cleanup, [25](../src/hooks/useRoomMedia.ts#L25) getDisplayMedia, [36](../src/hooks/useRoomMedia.ts#L36) file/object URL | Có browser API thật cho preview cục bộ; chưa upload, Chime content share hoặc capture OCR; không chứng nhận picker thật trên mọi OS |
| OC-02/04/06 capture → OCR frontend | [App:747](../src/App.tsx#L747) nói rõ preview; [video:753](../src/App.tsx#L753); overlay mẫu [760](../src/App.tsx#L760) | `NOT_FOUND_IN_WORKSPACE`: không thấy app API client/fetch/WS/canvas capture trong `src/`; không có source/job IDs hay result routing |
| OC-03 OCR service | [server:104](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L104), [routes:231](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L231) | HTTP/WS có implementation; 6/6 dummy transport checks chạy lại đạt. Chưa chứng minh provider thật |
| OC-05 model/chất lượng/tối ưu | [MeikiOCR:32](../meikipop-ocr-server/src/meikipop_ocr_server/ocr/providers/meikiocr/provider.py#L32), [Lens:34](../meikipop-ocr-server/src/meikipop_ocr_server/ocr/providers/glensv2/provider.py#L34) | Có adapter và xử lý ảnh; model/network/container/accuracy/concurrency thật `NOT_VERIFIED` |
| LX-01…03 từ điển/tách từ | [18 mục từ:15](../src/data/transcriptVocabulary.ts#L15), [tokenizer:39](../src/data/transcriptVocabulary.ts#L39) khớp chuỗi | `MOCK_ONLY`; không dictionary DB, morphological engine hoặc dịch tự động cho câu mới |
| LX-04 popup | [YomitanEntry:4](../src/components/YomitanEntry.tsx#L4), [renderer call:54](../src/components/YomitanEntry.tsx#L54), [hover:102](../src/components/TranscriptVocabulary.tsx#L102) | Renderer upstream thật được dùng; nội dung vẫn demo. Không đánh đồng renderer với toàn bộ extension/từ điển |
| Phát âm / D02 | [App:269](../src/App.tsx#L269) SpeechSynthesis `ja-JP` | TTS browser thật; không phải ASR, không đảm bảo giọng chất lượng/tiếng Trung |
| RM-01…03 tạo/join/phát nhóm | [enterRoom:457](../src/App.tsx#L457), [mã cố định:402](../src/App.tsx#L402), [mic/camera:798](../src/App.tsx#L798) | `MOCK_ONLY`; chỉ đổi state, không room API, meeting/attendee/presence/voice/video peer thật |
| RM-04 chat | [App:847](../src/App.tsx#L847) localMessages; submit UUID/time client [849](../src/App.tsx#L849) | `LOCAL_ONLY`; không gửi người khác, không Chime SDK. 500 ký tự không đồng nghĩa giới hạn bytes |
| ST-03 lưu/ôn từ | [state:392](../src/App.tsx#L392), [save:825](../src/App.tsx#L825), [ReviewCards:5](../src/components/ReviewCards.tsx#L5) | `LOCAL_ONLY`; chống trùng theo chữ trong state, không theo dictionary sense/owner; reload mất thay đổi |
| ST-04/05 lịch sử/thống kê | [previousSessions:278](../src/App.tsx#L278) cố định; dialog dùng item mẫu | `MOCK_ONLY`; không API/index dữ liệu hoặc số liệu học thật |
| ST-06 recording/playback | [nguồn local:39](../src/hooks/useRoomMedia.ts#L39), không thấy MediaRecorder/capture pipeline client trong source | `NOT_FOUND_IN_WORKSPACE`; phát file hiện tại không là lịch sử video lưu cloud |
| AD-01/02/04/05 Admin | [fixture init:38](../src/admin/AdminWorkspace.tsx#L38), [mutations:59](../src/admin/AdminWorkspace.tsx#L59), [config:103](../src/admin/AdminWorkspace.tsx#L103) | `MOCK_ONLY`; khóa/đóng/bảo trì/audit chỉ setState. Không sửa worker/tài khoản/tài nguyên thật |
| IF-02 đóng gói OCR | [Dockerfile:2](../meikipop-ocr-server/Dockerfile#L2), [Compose:4](../meikipop-ocr-server/docker-compose.yml#L4), [systemd:9](../meikipop-ocr-server/meikipop-ocr.service#L9) | Cấu hình có thật; Docker executable không có trong PATH hiện tại; chưa build/run container |
| IF-01/03/04/05 AWS | [DEPLOY:32](../meikipop-ocr-server/DEPLOY.md#L32) là hướng dẫn; [.figma deploy:3](../.figma/make/deploy#L3) gọi Figma CLI | Không có implementation AWS/IaC tìm thấy ở đây. Account/deployment/repo hạ tầng bên ngoài: `NOT_ACCESSIBLE` |
| QA-01…05 | [test_server:266](../meikipop-ocr-server/test_server.py#L266), [UI test notes](GIAO-DIEN-USER-VA-ADMIN.md#L89) | Test CLI có source; browser checks được ghi nhận từ lượt trước, không nằm trong test suite của repo. Chưa có E2E nhiều người qua AWS/OCR thật |

### Endpoint và storage thực sự có trong workspace

| Thành phần | Bằng chứng | Phạm vi thật |
| --- | --- | --- |
| `GET /`, `/static/*` | [server:231](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L231) | Demo OCR HTML riêng, không phải React app |
| `POST /ocr` | [server:110](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L110), [payload:76](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L76) | Raw bytes/multipart/base64 → raw OCR JSON; synchronous request chờ thread pool |
| `GET /ws` upgrade | [server:141](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L141) | Binary ảnh hoặc JSON base64, trả kết quả trên cùng socket, text ping/pong; chưa broadcast theo room |
| `GET /health` | [server:210](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L210) | Trả `status: ok` và provider name; chưa là model readiness |
| Public `/api/v1`, WS Gateway | [plan:389](TIEN-DO-VA-KE-HOACH-HOAN-THANH.md#L389) chỉ là danh sách đề xuất, route source không có | `NOT_FOUND_IN_WORKSPACE`; ngoài workspace `NOT_ACCESSIBLE` |
| Persistence hiện tại | [App:364](../src/App.tsx#L364), [Admin:38](../src/admin/AdminWorkspace.tsx#L38) | localStorage/sessionStorage + React state; không database/shared repository |
| S3/DynamoDB/Cognito/Chime/CloudFront/EC2 ASG | Không có SDK/client/infra tương ứng trong dependency và file inventory | Không có bằng chứng triển khai trong repo; tài nguyên account ngoài chưa truy cập |

API OCR hiện không có auth/membership/CORS middleware hoặc durable jobs. Căn cứ: [create_app:104](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L104) đến routes. Đây là service OCR độc lập cần lớp ứng dụng bảo vệ khi tích hợp, không nên nhét thêm quản lý user/room vào provider.

### Những phần ngoài workspace

| Phần | Trạng thái / kết luận được phép |
| --- | --- |
| Repo app backend/hạ tầng của Hoàng Bảo nếu có | `NOT_ACCESSIBLE`: chưa có path/checkout/link được xác nhận; không nói chưa phát triển |
| AWS account và deployment đang chạy | `NOT_ACCESSIBLE`: không có account read session/deployment manifest; DEPLOY.md không chứng minh tài nguyên đã tồn tại |
| Toàn bộ owocr/meikipop upstream nêu PDF trang 15 | `NOT_ACCESSIBLE` dưới dạng checkout local; chỉ thấy adapter đã trích xuất. Không kết luận tình trạng upstream từ snapshot này |
| Model assets và dịch vụ owocr ngoài repo | `NOT_ACCESSIBLE`/`NOT_VERIFIED`; không tải model hoặc gọi endpoint bên ngoài trong audit |

## 4. Dependency và runtime đọc được

| Lớp | Repo yêu cầu/khóa | Máy audit / điểm cần xử lý |
| --- | --- | --- |
| Node | [.mise:2](../.mise.toml#L2): major 22; Vite cài hiện tại khai báo engine `^20.19.0 || >=22.12.0` | Node `v22.23.4` phù hợp engine. Cần khóa patch được cả nhóm dùng, không coi mọi Node 22 đều hợp lệ |
| pnpm | [.mise:3](../.mise.toml#L3): `10.34.3`; lockfile format 9 | PATH đang là `12.18.0`; chưa chạy install hay sửa lockfile để “khớp” |
| React/DOM | [lock:11](../pnpm-lock.yaml#L11): `19.2.4` | Installed trùng; package.json chỉ khai báo range `^19.0.0` |
| Build/CSS | [lock:18](../pnpm-lock.yaml#L18): Vite `8.0.5`, plugin React `6.0.1`, Tailwind/plugin `4.2.2` | Installed trùng lock; không cần đổi thiết kế/framework |
| TypeScript | [lock:39](../pnpm-lock.yaml#L39): `5.9.3`; [tsconfig:9](../tsconfig.json#L9): ignoreDeprecations `6.0` | Tsc mặc định lỗi TS5103; override `5.0` đạt. Cần xử lý riêng CT-03, không đánh dấu mặc định đã pass |
| Python | [pyproject:9](../meikipop-ocr-server/pyproject.toml#L9): `>=3.10`; [Docker:2](../meikipop-ocr-server/Dockerfile#L2): `3.12-slim` | Máy/venv thử là `3.14.7`; chưa xác minh 3.12. Phần lớn dependencies là `>=`/không pin, chưa có Python lock |
| Provider | [registry:38](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L38) có 5 adapter | CLI/Docker/Compose/systemd đều mặc định `glensv2`; Admin demo mặc định `meikiocr` [adminDemo:5](../src/admin/adminDemo.ts#L5). Chưa có một provider vận hành thống nhất |
| AWS/auth/Chime/dictionary SDK | [package.json:13](../package.json#L13), [pyproject:10](../meikipop-ocr-server/pyproject.toml#L10) | Chưa có dependencies trực tiếp cho các lớp này. CT-01 không chọn/cài package mới; phải review phiên bản/flow trước task triển khai |
| Yomitan | [README:3](../third_party/yomitan/README.md#L3), upstream SHA `ee81f8dcf13e985bb4d7961009fb49a764b4d924` | Snapshot renderer đã có metadata/giấy phép; không có dictionary corpus. Giữ nguồn/notice, kiểm tra license dữ liệu riêng khi chọn D13 |

## 5. Kiểm chứng thực hiện trong CT-01

| Phép kiểm | Kết quả lần này | Giới hạn |
| --- | --- | --- |
| `node node_modules/vite/bin/vite.js build --outDir /private/tmp/ct01-lingualive-build-20261111` | Exit 0, 55 modules, Vite 8.0.5 | Build artifact nằm ngoài repo; bundling thành công không bao gồm typecheck/E2E |
| `node node_modules/typescript/bin/tsc --noEmit --pretty false` | Exit 2, TS5103 tại tsconfig.json(9,27) | Lỗi cấu hình đã có; không sửa source/config trong audit |
| Cùng tsc với `--ignoreDeprecations 5.0` | Exit 0 | Kiểm tra có override, không được báo lệnh mặc định đạt |
| 6 test có sẵn từ test_server.py, aiohttp TestServer loopback + DummyProvider | **6/6 đạt**, exit 0 | Gọi đúng các test có sẵn, không thêm API/test fixture vào repo. Python 3.14.7, aiohttp 3.14.5, Pillow 13.0.0 trong venv tạm có sẵn; không full production dependencies |
| Đọc `create_app(...)._client_max_size` của runtime thử | `1048576` bytes | Default HTTP này khác WS `50 * 1024 * 1024` và Nginx 50M; không suy ra multipart/WS đều được chặn như raw body |
| DummyProvider với ảnh 400×200 như CLI | **2/2 paragraph boxes ra ngoài ảnh** | Đã tái hiện phép tính fixture; 6/6 transport checks vẫn đạt vì không kiểm tra hình học/chất lượng |
| Source Python | Đọc mã/route/provider; không import/chạy provider thật | Không tải model, không gửi ảnh lên Lens, không gọi owocr bên ngoài |
| Browser/UI | Đọc [bằng chứng lần trước](GIAO-DIEN-USER-VA-ADMIN.md#L89) và component hiện tại | Không chạy lại Chromium trong CT-01; screenshot không chứng minh auth/backend thật |
| AWS/Docker/real OCR/load/recording | **Chưa kiểm chứng** | Không account access; không Docker trong PATH; không triển khai dịch vụ |

Wrapper kiểm thử chỉ đặt trong `/private/tmp/ct01-run-ocr-suite.py`, gọi `create_app(DummyProvider())` và `test_server.run_suite()` qua cổng loopback tự cấp; log `/private/tmp/ct01-ocr-dummy.log`. Sandbox ban đầu không cho bind socket; chạy lại phép kiểm loopback được công cụ phê duyệt và đạt. Không công bố port tạm là endpoint dự án.

## 6. Mâu thuẫn và khoảng trống cần xử lý

| Mã | Bằng chứng / mâu thuẫn | Hướng xử lý đề xuất, chưa áp dụng |
| --- | --- | --- |
| C01 | PDF tr.11–12 gửi frame qua WS Gateway; [aiohttp:153](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L153) nhận binary trực tiếp/50 MiB | Chốt D05, ưu tiên HTTP/S3; nếu giữ ảnh qua Gateway phải thiết kế protocol khác. Xem phân tích D05 trong decisions |
| C02 | PDF tr.6 gọi “bản ghi lời thoại trực tiếp”; code chỉ OCR/TTS và [transcript cố định](../src/App.tsx#L243) | D02: chốt OCR-derived text/readings hay thêm ASR thành task riêng; không gọi OCR là nhận dạng giọng nói |
| C03 | PDF tr.4/9 yêu cầu Nhật/Trung; [MeikiOCR:95](../meikipop-ocr-server/src/meikipop_ocr_server/ocr/providers/meikiocr/provider.py#L95) lọc regex Nhật/CJK, corpus UI chỉ Nhật | D01/D11/D13: Nhật là mốc đầu; Trung vẫn là yêu cầu nếu chưa chốt giảm phạm vi. Regex có Han không chứng minh OCR/nghĩa/cách đọc Trung đúng |
| C04 | [static demo:737](../meikipop-ocr-server/src/meikipop_ocr_server/static/index.html#L737) đọc `bounding_box`, [787](../meikipop-ocr-server/src/meikipop_ocr_server/static/index.html#L787) đọc `text`; [interface:26](../meikipop-ocr-server/src/meikipop_ocr_server/ocr/interface.py#L26) trả `box/full_text/is_vertical` | Giữ raw schema và sửa consumer trong task OCR riêng; không đổi provider để chiều field sai |
| C05 | [Nginx:14](../meikipop-ocr-server/nginx.conf#L14) 50M, WS 50 MiB, HTTP default 1 MiB, [Admin form:104](../src/admin/AdminWorkspace.tsx#L104) 1–10 MiB | Cần một limit config + byte/pixel validation; app draft đề xuất 1 MiB chưa phải policy triển khai |
| C06 | Health [server:210](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L210) luôn ok; [MeikiOCR init:43](../meikipop-ocr-server/src/meikipop_ocr_server/ocr/providers/meikiocr/provider.py#L43) nuốt lỗi | Readiness riêng/model warmup; không dùng health xanh làm bằng chứng OCR chạy |
| C07 | [ThreadPool:107](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L107) chia sẻ provider; [owocr:30](../meikipop-ocr-server/src/meikipop_ocr_server/ocr/providers/owocr/provider.py#L30) giữ một socket | Nguy cơ concurrency, chưa load-test tái hiện; cần serialize hoặc instance-per-worker và bounded jobs/lease |
| C08 | [DEPLOY:179](../meikipop-ocr-server/DEPLOY.md#L179) copy Nginx cho systemd; [nginx:7](../meikipop-ocr-server/nginx.conf#L7) hostname Compose | Config host phải dùng upstream phù hợp; tài liệu deploy không đồng nghĩa đã deploy |
| C09 | CLI/container mặc định Lens; UI Admin MeikiOCR; model/region chưa cấu hình | D11 chốt provider sau real-provider test, không tự đổi mặc định lúc audit |
| C10 | [plan D08](TIEN-DO-VA-KE-HOACH-HOAN-THANH.md#L288) tóm tắt UUID chung; [chi tiết ID:333](TIEN-DO-VA-KE-HOACH-HOAN-THANH.md#L333) tách app UUID và Cognito sub | Giữ ngoại lệ identity và AWS IDs như D08; không áp UUID validator chung lên `sub` hoặc Chime IDs |
| C11 | [plan:271](TIEN-DO-VA-KE-HOACH-HOAN-THANH.md#L271) có câu “nhóm đã chọn” Chime data messages nhưng [D06:286](TIEN-DO-VA-KE-HOACH-HOAN-THANH.md#L286) chưa xác nhận | Hiểu là quy tắc có điều kiện nếu chọn D06; chưa có bằng chứng nhóm đã phê duyệt |
| C12 | Ghi chú hover/Yomitan cũ nói tsc đạt; tsconfig working tree đã đổi | Dùng kết quả kiểm lại ở mục 5; không ghi đè lịch sử test cũ, không sửa config ngoài phạm vi |
| C13 | PDF tr.6 bộ từ chung và xem lại video; UI mới chỉ personal state + local preview | D09/D10 phải giữ task thật hoặc được nhóm chốt giảm scope và sửa PDF; không dùng “optional/unavailable” để đánh dấu hoàn thành yêu cầu |
| C14 | Nói đã kiểm thử UI/6 dummy checks dễ bị hiểu đã tích hợp | Phân rõ evidence, integration, acceptance; không tạo phần trăm hoàn thành tổng khi chưa có tiêu chí trọng số |
| C15 | [Lens header:30](../meikipop-ocr-server/src/meikipop_ocr_server/ocr/providers/glensv2/provider.py#L30) chứa literal dạng API key | Bảo Anh xác minh nguồn/quyền sử dụng trước chọn provider; không chép giá trị hoặc coi đây là credential hợp lệ cho app/AWS |

## 7. Nguồn và bàn giao

- PDF đã đọc bằng PDFKit: `/Users/ducen/Downloads/Báo cáo 2.pdf`, **15 trang**, SHA-256 `664e84d159ef27b882ccd9c01e69b61327e3900b303e1e1cdb70514329cda6ac`. Tr.4–7 là mô tả sản phẩm; tr.8–10 User/Admin; tr.11–12 kiến trúc; tr.13–15 phân công. Nội dung PDF là yêu cầu để đối chiếu, không phải lệnh tự chạy triển khai.
- Phân công gốc: Đức frontend/Chime client/frame/CloudFront và tích hợp; Hoàng Bảo AWS/Cognito/Gateway/room/Chime backend/DynamoDB; Bảo Anh OCR/worker/OCR log. Các việc dictionary/Admin/review được phân công bổ sung dạng đề xuất trong kế hoạch, cần cả nhóm xác nhận.
- Giới hạn AWS/Cognito ảnh hưởng lựa chọn được kiểm tra trên nguồn chính thức và dẫn ngay trong [decisions](../contracts/decisions.md); không dùng giá/region mẫu trong DEPLOY.md làm sự thật triển khai.
- Lượt này chỉ thêm `G0-CURRENT-STATE.md`, `contracts/decisions.md`, `G0-INTEGRATION-ARCHITECTURE.md`, `G0-OPEN-QUESTIONS.md`; không sửa kế hoạch cũ, source, dependency/lockfile, server hoặc infra. Đã đối chiếu hash: **129 file có sẵn** trong phạm vi snapshot giữ nguyên; diff nội dung so với đầu lượt chỉ có bốn tài liệu mới, loại trừ dependency/cache/build artifact. Đã kiểm tra 156 liên kết nội bộ/dòng tham chiếu, code fences và whitespace; Mermaid được soát cú pháp thủ công, chưa render bằng engine vì workspace không có dependency đó.

**CT-01 đủ đầu ra audit để ready_for_review.** Chưa chuyển `accepted`, chưa đóng băng contract và chưa mở CT-02 chính thức. Các quyết định cần người xác nhận và giới hạn truy cập nằm ở [OPEN-QUESTIONS](G0-OPEN-QUESTIONS.md).
