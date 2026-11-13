# CT-03 — Môi trường local và tích hợp

**Nhóm 4–5, 13/11/2026:** thêm hai provider OCR CPU: Nhật 8080 và Trung 8083, mỗi provider có venv/lock riêng; API 8081 có 26 handlers + durable worker; FE 8443 đã nối chụp frame/upload/job/polling/overlay/history. [Hướng dẫn cài/chạy/kiểm thử hiện tại](GROUP-05-OCR-PIPELINE.md), [phạm vi API](GROUP-04-APPLICATION-API.md). Không cần Docker/AWS; không reset DB, không auto fallback mock. Các mô tả thiếu API/OCR integration phía dưới là bản ghi lịch sử.

**Nhóm 3, 13/11/2026:** local auth đã có mã xác nhận qua mailbox trên máy, reset/change password/email, refresh/revoke và quyền Admin server-controlled. Không cần SMTP/Docker/AWS hoặc dependency mới. Chạy service như hướng dẫn local bên dưới; [hướng dẫn đầy đủ và lệnh auth-admin](GROUP-03-AUTH-AND-AUTHORIZATION.md). Cognito/email internet/realtime chưa nghiệm thu.

**Tích hợp FE local 13/11/2026:** bật DB bằng `./scripts/dev-db`; init nếu là checkout mới; chạy `./scripts/dev-local-api` thay cho foundation API; FE tại `http://127.0.0.1:8443` mặc định gọi API thật qua Vite proxy. Không chạy hai API trên cùng cổng. Đăng ký tài khoản local trên web, không dùng login demo cũ. [Các ca thử và giới hạn hiện tại](FE-DB-INTEGRATION-TESTS.md). Những nhận xét “chưa có FE client/proxy” trong các mốc lịch sử bên dưới không còn mô tả trạng thái mới này.

**Cập nhật 13/11/2026 — nhóm 2:** storage local đã triển khai bằng DynamoDB Local 3.3.2 (Java 21 có sẵn, loopback 8000, telemetry tắt) và local object store. Chạy `./scripts/dev-db`, `./scripts/db-admin init`, rồi `PERSISTENCE_ENABLED=1 ./scripts/dev-api`. Test backend hiện cần DB đang chạy; chỉ tạo/xóa bảng test riêng. Config, private data directories, dependencies SDK local, backup và giới hạn ở [nhóm 2](GROUP-02-DATABASE-AND-STORAGE.md). Không cần Docker/AWS account; chưa có cloud deployment.

**Cập nhật 12/11/2026 — nhóm 1 chạy trực tiếp, không cần Docker/AWS.** Application backend hiện có ở `application-backend/`, venv Python 3.12 riêng tại `.venv` bên trong module. Không thay venv OCR/Python toàn máy/pnpm/frontend.

Từ root repo, trên workspace đã cài dependencies:

```bash
./scripts/dev-api --check
./scripts/test-api
./scripts/dev-api
```

Checkout mới: `python3.12 -m venv application-backend/.venv`, rồi `application-backend/.venv/bin/python -m pip install -r application-backend/requirements.lock`. Config chỉ từ environment export, mẫu ở [backend .env.example](../application-backend/.env.example), không tự load dotenv. Chi tiết ở [backend README](../application-backend/README.md).

API bind `127.0.0.1:8081`; `GET /health/live` 200, `/health/ready` 503 khi nghiệp vụ chưa cấu hình; public API thiếu token 401, token bất kỳ không được cấp quyền. Hai health routes nằm ngoài public contract. Đây là foundation thật, **0 business handlers**; database, Cognito, OCR jobs, realtime/media và FE integration chưa triển khai trong nhóm 1. Header contract vẫn DRAFT. Đổi port bằng `APP_PORT=8082 ./scripts/dev-api` khi cần, không kill service khác.

Frontend tiếp tục preview 8443, raw OCR giữ cấu hình 8080. Không có Docker/AWS/database/model nào cần chạy để kiểm nền tảng. Các hướng dẫn container/AWS ở bản ghi CT-03 dưới đây là tùy chọn cho bước sau.

## Bản ghi môi trường CT-03 ngày 11/11/2026

**DRAFT — ready_for_review, 11/11/2026.** Tài liệu mô tả cấu hình hiện hữu và cách chuẩn bị bước tích hợp; không khẳng định stack đầy đủ đã chạy. CT-03 không cài lại môi trường, đổi dependency/runtime, khởi động service, deploy, migration, commit hoặc push.

Đọc cùng [ownership](OWNERSHIP.md), [Git workflow](GIT-WORKFLOW.md), [CT-01 audit](G0-CURRENT-STATE.md), [CT-02 contract](../contracts/README.md) và [hướng dẫn adapter](CT-02-INTEGRATION-GUIDE.md). Lệnh ở các mục cài/chạy là hướng dẫn **chưa thực thi trong CT-03**; các lệnh thực sự đã chạy được ghi riêng ở mục 10.

## 1. Những gì thực sự có trong workspace

| Thành phần | Có sẵn | Chưa có/chưa xác minh |
| --- | --- | --- |
| Frontend | React/Vite/Tailwind, source, package/lockfile, `.figma/make/dev/install/deploy`, node_modules; Vite đang listen cổng 8443 | API/auth/Chime client thật, Vite app API/WS proxy và mock/real switch |
| OCR | `meikipop-ocr-server/`, Python package, `/ocr`/raw `/ws`/`/health`, providers, CLI test, Docker/Compose/Nginx/systemd | Full dependencies trên Python 3.12 ở máy này, model/corpus thật, container build/readiness/concurrency/load |
| Application backend | Chỉ public contract DRAFT; chưa tìm thấy source/README/runtime trong workspace | Repo riêng nếu có: **NOT_ACCESSIBLE**; phải lấy path/branch/SHA và lệnh chạy từ Hoàng Bảo |
| Worker/lexicon | Raw provider adapters và UI dictionary fixture có sẵn | Worker durable job/lexicon thật chưa thấy ở đây; repo ngoài chưa truy cập |
| AWS/storage/auth | Hướng dẫn EC2 thủ công, API/schema đề xuất | Account/resources/credentials/regions, Cognito/Chime/S3/DynamoDB/Gateway/ASG thật chưa được kiểm chứng |
| Orchestration | OCR Compose có `ocr-server` và `nginx` | Không có Compose cho frontend+app+worker, Makefile hoặc CI workflow hệ thống được tìm thấy |

Git hiện là `main @ 81be4b4a5a7baf24db0c9fdc5bbd2d72fed87340` cộng working tree chưa commit. Không có nested Git repo được tìm thấy. Giữ layout hiện tại, không tạo `backend/` giả hoặc ép các repo khác vào monorepo.

## 2. Runtime: repo khai báo, máy đang dùng, hướng thống nhất

| Phần | Căn cứ trong repo | Máy CT-03 | Đề xuất, chưa tự áp dụng |
| --- | --- | --- | --- |
| Node | [.mise.toml:2](../.mise.toml#L2): `22`; Vite 8.0.5 cài hiện tại yêu cầu engine `^20.19.0 || >=22.12.0` | `v22.23.4` | Giữ Node đang hoạt động; nhóm chốt patch Node 22 phù hợp engine trước khi pin trên các máy/CI |
| pnpm | [.mise.toml:3](../.mise.toml#L3): `10.34.3`; [lockfile](../pnpm-lock.yaml#L9) format 9 | `12.18.0` trên PATH | Dùng 10.34.3 theo repo trong checkout mới/CI sau xác nhận; không regenerate lock bằng pnpm 12 hoặc thay global pnpm ở CT-03 |
| Build/UI | [lockfile:11](../pnpm-lock.yaml#L11): React/DOM `19.2.4`, Vite `8.0.5`, React plugin `6.0.1`, Tailwind `4.2.2` | Installed khớp các bản trên | Giữ package.json/pnpm-lock; task runtime riêng nếu thực sự cần nâng |
| TypeScript | [lockfile:39](../pnpm-lock.yaml#L39): `5.9.3`; [tsconfig:9](../tsconfig.json#L9): ignoreDeprecations `6.0` | `5.9.3` | Có lệch cấu hình đã biết: tsc chuẩn lỗi TS5103 ở CT-01/02, override 5.0 đạt. Chưa sửa config trong CT-03; Đức chốt PR sửa tương thích riêng, không nâng TS hàng loạt |
| Python OCR | [pyproject:9](../meikipop-ocr-server/pyproject.toml#L9): `>=3.10`; [Dockerfile:2](../meikipop-ocr-server/Dockerfile#L2): `3.12-slim` | Default `3.14.7`; `python3.12` có sẵn bản **3.12.16**, chưa có aiohttp/Pillow/meikiocr trong interpreter đó | Dùng Python 3.12 làm mục tiêu kiểm container/provider; tạo venv riêng khi được giao cài, không đổi python3 toàn máy |
| Python lock/model | [pyproject:10](../meikipop-ocr-server/pyproject.toml#L10) chủ yếu ranges, chưa có Python lock | Default Python cũng chưa có các dependency OCR; venv dummy/validation cũ chỉ ở `/private/tmp` | Bảo Anh kiểm dependency/model/runtime rồi đề xuất lock/extras; không lấy venv dummy tối thiểu 3.14 làm production lock |
| Docker/mise | Có Dockerfile/Compose và .mise.toml | `docker` và `mise` không có trong PATH; Corepack `0.36.0` có | Không cài Docker/mise hoặc đổi shims ở CT-03; việc chuẩn bị công cụ do owner giao riêng |
| App backend | Chưa có repo/runtime kiểm chứng | Không biết | Không tự viết lệnh uvicorn/python/server.js hoặc chọn framework để lấp chỗ trống |

`mise` chưa có trên PATH và package.json chưa khai báo packageManager; chỉ có .mise.toml không làm mọi terminal tự đổi pnpm sang 10.34.3. Các công cụ ở /private/tmp là môi trường kiểm thử từ lượt trước, có thể bị dọn và không thay local setup chuẩn của từng repo.

## 3. Frontend: cài dependency và chạy

Chạy từ root repo hoặc worktree đã được giao. Trong Figma Make, [AGENTS.md](../AGENTS.md#L5) cho biết preview server đã được quản lý; CT-03 xác nhận có listener 8443 và **không chạy server thứ hai**.

### Checkout mới, khi đã thống nhất toolchain

Nếu pnpm đang chọn đúng `10.34.3`, lệnh cài dependency đề xuất:

```bash
node --version
pnpm --version
pnpm install --frozen-lockfile
```

`--frozen-lockfile` không cập nhật lockfile và sẽ fail nếu manifest/lock lệch; không bỏ flag để tiện pass. Nguồn: [pnpm 10 install](https://pnpm.io/10.x/cli/install). `.figma/make/install` hiện dùng `--prefer-offline --no-frozen-lockfile`; đó là script scaffold có sẵn, CT-03 không đổi. Không chạy lại script này khi chỉ nhận docs/contracts.

Nếu dùng Corepack đã có để chọn pnpm theo từng lệnh, có thể dùng **một trong hai cách**, không cài hai lần; lệnh dưới có thể tải/cache pnpm khi máy chưa có, **chưa chạy trong CT-03**:

```bash
COREPACK_ENABLE_AUTO_PIN=0 corepack pnpm@10.34.3 install --frozen-lockfile
```

Không dùng `corepack use/up`, enable shims hoặc nâng global pnpm để xử lý task docs. Cú pháp chọn package manager theo lệnh được mô tả trong [Corepack utility commands](https://github.com/nodejs/corepack#utility-commands); lựa chọn thực tế vẫn cần nhóm thống nhất.

Chỉ khởi động khi chưa có dev server của task đó và port được giao còn trống:

```bash
PORT=8443 pnpm dev
```

Nếu đang dùng Corepack theo từng lệnh thì dùng pnpm được chỉ định tương ứng, không quay lại pnpm 12 trên PATH chỉ cho bước dev/build. Config hiện đọc process.env.PORT/default 8443, host/default 0.0.0.0 và strictPort=true tại [vite.config.ts:33](../vite.config.ts#L33); port bận phải báo owner/chọn port đã giao, không kill tiến trình khác.

Các check frontend có sẵn hoặc gọi trực tiếp từ dependency hiện hữu:

```bash
pnpm build
node node_modules/typescript/bin/tsc --noEmit --pretty false
```

Tsc chuẩn hiện có baseline config fail. Lệnh chẩn đoán tạm đã dùng ở CT-01/02 là `node node_modules/typescript/bin/tsc --noEmit --ignoreDeprecations 5.0 --pretty false`; không biến kết quả override thành báo cáo check chuẩn đạt. Việc sửa ignoreDeprecations tương thích TS 5.9.3 hoặc nâng TS có chủ đích phải là task được review riêng.

## 4. OCR: cài/chạy độc lập, không nhầm với app backend

### Python trên host

Hướng dẫn cho môi trường mới **khi được giao cài dependencies**; chưa tạo/cài venv này trong CT-03. Dùng venv ngoài repo để tránh vô tình đưa dependency vào Git:

```bash
python3.12 -m venv /private/tmp/lingualive-ocr-py312
/private/tmp/lingualive-ocr-py312/bin/python -m pip install -e ./meikipop-ocr-server
```

Pyproject hiện cài cả dependency model, kể cả khi chỉ chọn dummy. Chưa có lock/container test đầy đủ; không tuyên bố cài đặt tái lập production chỉ từ lệnh pip này. Venv mới phải riêng cho task/người dùng, không ghi đè venv có sẵn của người khác.

Terminal OCR, sau khi cài xong và port trống, chạy dummy có chủ đích để kiểm transport:

```bash
/private/tmp/lingualive-ocr-py312/bin/meikipop-ocr-server --provider dummy --host 127.0.0.1 --port 8080 --workers 1
```

Terminal test, từ root repo:

```bash
/private/tmp/lingualive-ocr-py312/bin/python meikipop-ocr-server/test_server.py --host http://localhost:8080
```

Lệnh trên dùng CLI thật có sẵn; không tạo app API/mock login. Dummy chỉ kiểm HTTP/WS transport, không accuracy/readiness/tải/box đúng; audit đã tái hiện box dummy vượt ảnh ở ảnh 400×200. Không dùng port/provider này làm backend sản phẩm.

CLI/server defaults là glensv2, 0.0.0.0:8080, workers=2 tại [server.py:246](../meikipop-ocr-server/src/meikipop_ocr_server/server.py#L246). Không thay provider chỉ bằng env `OCR_PROVIDER`: server hiện không đọc biến đó. Chọn provider thật là task Bảo Anh sau D11; MeikiOCR model, ScreenAI native assets hoặc owocr service ngoài đều cần bằng chứng riêng.

### Docker khi máy đã có Docker

Các lệnh đề xuất theo Compose hiện hữu, **chưa chạy được/kiểm chứng trong CT-03** vì docker không có trong PATH:

```bash
docker compose -f meikipop-ocr-server/docker-compose.yml config
docker compose -f meikipop-ocr-server/docker-compose.yml build ocr-server
docker compose -f meikipop-ocr-server/docker-compose.yml run --rm --service-ports ocr-server --host 0.0.0.0 --port 8080 --provider dummy --workers 1
```

Không chạy host OCR và container OCR cùng port. Chỉ start service OCR để không tự chiếm port 80 của Nginx. Compose hiện có default glensv2 trong command; lệnh run ở trên override cho transport test, không sửa file. Nginx Compose chuyển tới raw OCR/demo, không ghép frontend/app API; cấu hình đó dùng hostname `ocr-server`, khác cài host/systemd. Không chạy các lệnh EC2/systemd/certbot trong DEPLOY.md như một phần local setup.

## 5. URL/port và kết nối dự kiến

| Đường | Hiện trạng | Ý nghĩa |
| --- | --- | --- |
| `http://localhost:8443` | Có Vite listener; không restart trong CT-03 | Frontend demo, không chứng minh API/đăng nhập thật |
| `http://localhost:8081/api/v1` | **Đề xuất**, chưa có app process/route được kiểm chứng | Public app API cho frontend, chưa thể chạy theo repo này |
| WS app, ví dụ `ws://localhost:8081/realtime` | **Đề xuất local adapter**, chưa có implementation; cloud endpoint chưa truy cập | URL thật lấy từ ticket response `ws_url` theo CT-02, không mặc định cùng port nếu owner chọn adapter khác |
| `http://localhost:8080/ocr`, `/health`, `/` | Có implementation OCR; port chỉ nghe khi owner chạy service | HTTP raw OCR/health/demo độc lập |
| `ws://localhost:8080/ws` | Raw aiohttp protocol | Nhận binary/base64 ảnh; không phải Gateway app WS schema 1.0 |
| `http://localhost:80` | Nginx tùy chọn trong Compose, chưa chạy CT-03 | Raw OCR proxy, không phải frontend/API Gateway |
| `ws://127.0.0.1:7331` | Chỉ owocr adapter default, service ngoài chưa xác minh | Không phải app WS hoặc Chime |

### Frontend → app API sau khi được triển khai

- Đề xuất same-origin API base `/api/v1`, Vite/reverse proxy route **`/api` → app host:8081, giữ nguyên `/api/v1`**, không strip prefix mà app contract đang dùng. Vite hiện **chưa có proxy**; đổi VITE_API_BASE_URL không tự tạo route này.
- App WS có route/protocol riêng; chỉ proxy `/realtime` sau khi Hoàng Bảo cung cấp local WS adapter và ticket/authorization. Không rewrite app `/realtime` sang raw OCR `/ws` để coi đã tích hợp Gateway.
- Nếu gọi trực tiếp `http://localhost:8081/api/v1` từ browser 8443, backend cần CORS cho đúng origin/header/method; chưa có backend để kiểm. Chốt dùng localhost thống nhất khi làm auth/callback; không trộn IP/hostname bằng suy đoán.
- Preview Figma và cloud dùng origin/host của môi trường đó; localhost của browser/container không mặc nhiên là máy backend. Ưu tiên proxy cùng origin và HTTPS/WSS phù hợp, không hardcode IP AWS trong source.
- Ticket response cấp base `ws_url` không kèm vé; client append ticket một lần. `VITE_REALTIME_URL` là biến đề xuất, không được ghi đè tùy ý URL đã được backend cấp.

### App/worker → OCR nội bộ

- App/worker chạy trên host: endpoint đề xuất `OCR_SERVICE_URL=http://127.0.0.1:8080`; biến này chỉ có trong **template backend dự kiến**, chưa có code backend đọc nó.
- App container đã join **cùng network được duyệt** với service OCR: dùng `http://ocr-server:8080`. App repo Compose khác không tự có DNS/network này; Hoàng Bảo cần cung cấp wiring riêng sau khi thống nhất, không tự nhập các repo lại.
- App/worker gọi POST `/ocr` nội bộ, map raw error thành application error/job status và bọc public metadata. Không gửi bearer token user, room ownership hoặc dictionary meanings vào raw provider. Frontend sản phẩm chỉ gọi app API; không mở provider trực tiếp để vượt auth/jobs.

Lệnh chạy/cài app backend, health/readiness, local upload/storage emulator và WS adapter **chưa thể điền đáng tin cậy**. Hoàng Bảo phải cung cấp từ repo thật: runtime/lockfile, command, env schema, local auth/storage mode và tests; CT-03 không tạo lệnh chạy giả.

## 6. Env templates và cách chúng thực sự được đọc

| Template | Biến hiện có consumer | Phần chỉ đề xuất |
| --- | --- | --- |
| [Root .env.example](../.env.example) | PORT/FIGMA_DEV_SERVER_HOST nếu export vào shell trước khi chạy Vite | VITE_API_BASE_URL/VITE_REALTIME_URL/VITE_DATA_MODE/Cognito đều comment, chưa có app consumer |
| [OCR .env.example](../meikipop-ocr-server/.env.example) | OWOCR_WEBSOCKET_URI trong owocr provider; OCR_SERVER_URL/OCR_WS_URL trong **test CLI** | Không biến chúng thành server host/port/provider; server dùng flags |
| [Backend proposal](env/application.env.example) | Không có backend để đọc | Tất cả assignments comment; app/region/storage/auth/contract settings chờ Hoàng Bảo xác nhận |

Root PORT nằm trong `.env.local` **không tự vào process.env khi vite.config.ts đang đọc config**; code hiện không gọi loadEnv. Vì vậy dùng shell prefix cho port hoặc sửa config trong task được giao sau, không hứa copy template sẽ đổi cổng. Nguồn: [Vite config/environment loading](https://vite.dev/config/#using-environment-variables-in-config).

VITE_* được đưa vào cấu hình browser khi app dùng chúng; chỉ đặt metadata public, không secret. Nguồn: [Vite env variables](https://vite.dev/guide/env-and-mode). Biến không có consumer chưa tạo được tính năng dù Vite có expose nó.

Python hiện không có dotenv loader và Compose chưa có env_file: chỉ tạo `.env.local` không làm Python/container nhận biến. Export đúng biến vào shell hoặc cấu hình environment trong task riêng khi owner triển khai; không source một file env không được kiểm tra. Template CT-03 không có token/key thật và không có `.env.local` nào được tạo.

`.gitignore` giữ `.env*` và chỉ thêm ngoại lệ chính xác `/.env.example`, `/meikipop-ocr-server/.env.example`. `docs/env/application.env.example` không khớp pattern basename `.env*` nên tự được theo dõi; không nới ignore toàn thư mục. Env thật ở root/OCR/docs vẫn bị bỏ qua.

## 7. Mock, dummy và real

| Chế độ | Hiện tại / yêu cầu |
| --- | --- |
| UI demo | State/localStorage/fixtures có sẵn; dev role picker chỉ preview. Production build không biến local login thành xác thực thật |
| Mock theo contract | Có JSON fixtures tổng hợp + manifest CT-02; chưa có mock server/adapter switch chạy bằng env. Negative fixtures phải bị từ chối, không render như response thật |
| OCR dummy | Provider flag `--provider dummy` có thật, chỉ transport; giữ nhãn và không dùng số elapsed_ms làm benchmark |
| Real | Chưa có frontend adapter/app API/Cognito/worker/storage/lexicon/Chime tích hợp; chỉ đặt VITE_DATA_MODE=real **không** bật được |

Task tích hợp sau phải đọc mode tường minh, chặn dev role trong real kể cả DEV=true, dùng verified identity, không fallback fixture khi lỗi. CT-02 đề xuất response header X-Data-Mode do server cấp; dictionary origin fixture/provider fixture.synthetic chỉ ở mock. Không tạo fake token hoặc mock API để làm smoke real trông như đạt.

## 8. Smoke test tối thiểu theo từng mức

Các ca bên dưới là hướng dẫn cho owner chạy khi có dependency/service; không phải kết quả CT-03 đã chạy hết.

| Mức | Cách chạy/quan sát | Điều kiện đạt / giới hạn |
| --- | --- | --- |
| UI hiện tại | Mở preview/localhost:8443; login demo, bốn thẻ, nguồn local, hover/Yomitan sáng/tối | Chỉ chứng minh UI; giữ đúng banner mẫu và không coi login/room/chat là thật |
| Bundle contract | Chạy snippet hash dưới; spec/schema/fixtures theo [VALIDATION](../contracts/VALIDATION.md) | Cùng version/hash; 128 positive/16 negative có kỳ vọng riêng; không dùng tên PASS thay approval |
| OCR riêng | Start dummy có chủ đích, chạy `test_server.py --host http://localhost:8080` | Transport/status có thể đạt, chưa accuracy/model; health ok chưa là readiness |
| Solo real — chưa thể chạy ở đây | Verified login → /me → session/source → một upload/job → result → lookup/save → reload | Nội dung mới, state/lỗi/IDs đúng, không fixture, đổi nguồn bỏ result cũ; cần app/auth/storage/provider/lexicon thật |
| Group real — chưa thể chạy ở đây | Hai tài khoản/hai phòng, join/share/chat/OCR/reconnect/leave/close | Không cross-room/user leak; Chime và membership thật, không năm thành viên mẫu |

Kiểm bundle hiện có bằng standard library, không cần cài lại tools:

```python
from pathlib import Path
import hashlib, json
root = Path.cwd()
version = json.loads((root / 'contracts/contract-version.json').read_text())
for filename, expected in version['files'].items():
    assert hashlib.sha256((root / filename).read_bytes()).hexdigest() == expected, filename
lines = ''.join(f'{name} {digest}\n' for name, digest in sorted(version['files'].items()))
assert hashlib.sha256(lines.encode()).hexdigest() == version['bundle_sha256']
print(version['contract_version'], version['status'], version['bundle_sha256'])
```

Contract hiện là `0.1.0-draft.1`, hash `bcfd39b6a2fd85d74cd5efd53e7a6bff753f60bf7e286246c27ef696c1c6bfd2`, contract_commit_sha=null. Head repo cũ không chứa trọn các file chưa commit. Chưa có approval ba thành viên hoặc contract v1 chính thức.

## 9. Thứ tự tích hợp và các điểm cần xác nhận

1. Đức ghi ownership/file chung/base SHA; Hoàng Bảo cung cấp backend/infra repo và README thật; Bảo Anh cung cấp worker/lexicon path/runtime/model. Giữ repo riêng nếu nhóm dùng riêng.
2. Chốt D01–D16 còn mở, contract draft additions và cách phát hành version/hash/commit cho cả ba. CT-03 không tự xác nhận thay nhóm.
3. Chốt Node patch/pnpm, sửa TS config ở task riêng, kiểm Python 3.12/container và lock. Không reinstall môi trường đang hoạt động chỉ vì đọc tài liệu này.
4. Contract/unit checks tại mỗi repo; PR chủ module + consumer review; Đức tích hợp từng thay đổi nhỏ trên cùng SHA set. [Git workflow](GIT-WORKFLOW.md) ghi điều kiện merge/conflict/handover.
5. Solo đầu cuối trước, rồi room/Chime, history/recording/Admin; smoke phù hợp mỗi lần ghép. Chỉ chuyển integrated/accepted khi có evidence theo luồng thật và người nhóm nghiệm thu.

Các việc chưa thể chuẩn hóa bằng config file đơn thuần: backend command/auth dev, real/mock adapters, upload/job persistence, WS registry/ticket, model/corpus/dictionary, cloud access/region/credentials và recording. Không thay bằng server giả; đánh dấu NOT_ACCESSIBLE/NOT_VERIFIED và ghi owner cung cấp.

## 10. Lệnh và kiểm tra thực sự chạy trong CT-03

| Lệnh/phép kiểm | Kết quả thực tế |
| --- | --- |
| `git status --short --branch`, `git branch -vv`, `git log -1 --format=...` | main @ 81be4b4, 7 tracked modified/181 untracked trước CT-03; không fetch/pull |
| `git worktree list --porcelain` | Một worktree root, không tạo mới |
| `command -v node pnpm python3 python3.12 docker mise corepack` | Node/pnpm/Python/Corepack có; docker/mise không trong PATH |
| `node --version`, `pnpm --version` | v22.23.4 và 12.18.0; không cài/switch |
| `python3 --version`, `python3.12 --version` | 3.14.7 và 3.12.16; không tạo venv/cài packages |
| `node node_modules/typescript/bin/tsc --version` | 5.9.3; chỉ hỏi version, không báo typecheck mới đạt |
| `corepack --version`, `corepack --help` | 0.36.0, đọc CLI help; không chạy install/use/enable hoặc tải pnpm |
| `lsof -nP -iTCP:8443 -sTCP:LISTEN` | Có Node listener 8443, giữ nguyên; không khởi động/restart/kill |
| `rg`/đọc config/source/README; metadata node_modules | Xác nhận versions/env consumers/CLI defaults/Compose; không đọc credential store |
| Python `find_spec` trên default và 3.12 | Chưa có aiohttp/Pillow/meikiocr ở hai interpreter global; không import model |
| Snippet hash bundle bằng Python standard library | Tất cả file contract khớp bundle CT-02; không sửa package/hash |
| Parse env template và `git check-ignore` theo paths mẫu | PASS: 10 paths đúng kỳ vọng; root template có 2 biến shell, OCR có 3 biến adapter/test, backend proposal không có assignment hoạt động; env thật vẫn ignored |
| Links/code fences/whitespace + hash so baseline | PASS: 28 links nội bộ, 9 khối Bash chỉ kiểm cú pháp (không thực thi); 292/293 file có sẵn giữ nguyên, file cũ duy nhất sửa là .gitignore; 6 file mới đúng phạm vi; bundle CT-02 không đổi |

Kết quả build/tsc override/dummy tests trong CT-01/02 là lịch sử đã dẫn, không chạy lại để tạo chứng nhận CT-03. Không chạy pnpm/pip install, build/Docker/model/cloud/real-system smoke, branch/worktree mutation, commit hoặc push trong lượt này.

**Bàn giao CT-03:** ba tài liệu LOCAL-SETUP/OWNERSHIP/GIT-WORKFLOW, ba env templates và `.gitignore` thêm hai ngoại lệ template. Quy trình sẵn sàng review; môi trường real vẫn chờ repo/service và các quyết định được nhóm xác nhận.
