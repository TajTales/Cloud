# CT-03 — Git workflow và quy trình tích hợp

**Cập nhật 12/11/2026 — quy trình một người.** Nguyễn Tài Đức là owner và người xác nhận của tất cả module, theo [ownership hiện hành](OWNERSHIP.md). Codex review diff/test trong phạm vi task; peer review là tùy chọn, không còn bắt buộc ba thành viên hoặc reviewer khác tác giả. Các quy ước branch theo task, contract-first, pin SHA, version/hash, test và rollback ở CT-03 tiếp tục dùng.

- Mỗi task giữ phạm vi riêng; làm lần lượt khi đụng App.tsx/schema/lockfile. Không cần tạo ba luồng code cho ba người.
- Owner chốt thay đổi nền tảng/breaking, có evidence theo [approval policy](../contracts/approval-policy.json). Không ghi chữ ký thay hai thành viên cũ và không đổi trạng thái DRAFT chỉ từ việc thay ownership.
- Trước nghiệm thu ghi source SHA thực, working-tree diff, contract version/bundle/policy hash, commands/exit và mode local/mock/real. Contract SHA vẫn null cho đến khi có commit thật chứa package tương ứng.
- Commit/push/PR/merge/deploy chỉ thực hiện khi task đã giao cho phép; nhóm 1 hiện chỉ sửa source/docs và kiểm thử local. Không dùng thay đổi governance để cấp quyền thao tác remote.

## Bản ghi CT-03 ngày 11/11/2026

Phần dưới lưu workflow khi dự án còn phân công ba người; các yêu cầu reviewer/ba xác nhận được thay bằng quy trình một người ở trên. Những giới hạn được ghi riêng cho CT-03 là lịch sử task đó, không cấm implementation đã được chủ dự án giao ở nhóm 1.

**DRAFT — ready_for_review, 11/11/2026.** Đây là quy trình đề xuất cho ba thành viên dùng Codex. Không branch/worktree/PR/commit/push hoặc cấu hình remote nào được tạo bởi CT-03. [Ownership](OWNERSHIP.md) xác định owner/reviewer; [local setup](LOCAL-SETUP.md) ghi môi trường thực tế.

## 1. Trạng thái repo cần giữ

Tại đầu CT-03: `main`, HEAD `81be4b4a5a7baf24db0c9fdc5bbd2d72fed87340`, theo dõi `origin/main`; **7 tracked files bị sửa và 181 untracked files**. Chỉ có một worktree. Không fetch nên remote-tracking ref không là bằng chứng remote mới nhất.

UI mới và package CT-02 chưa được commit; `contracts/contract-version.json` có `contract_commit_sha: null`. Vì thế HEAD trên **không tái tạo được toàn bộ working tree hiện tại** và chưa được gọi là integrated base đã nghiệm thu.

Giữ thay đổi có sẵn. Không tự `git pull`, switch/reset/clean, stash toàn bộ hoặc chọn “ours/theirs” cho file chung để làm branch sạch. Chủ repo cần review/snapshot/commit phần muốn bàn giao trong một task được giao rõ; CT-03 không thực hiện bước commit đó.

## 2. Quy ước branch

| Mục đích | Convention | Ví dụ |
| --- | --- | --- |
| Tính năng | `feat/<TASK_ID>-<slug>` | `feat/OC-02-frame-capture` |
| Sửa lỗi | `fix/<TASK_ID>-<slug>` | `fix/AU-03-access-guard` |
| Contract | `contract/<TASK_ID>-<slug>` | `contract/CT-02-solo-errors` |
| Runtime/test/tooling | `chore/<TASK_ID>-<slug>` | `chore/CT-04-contract-checks` |
| Tài liệu | `docs/<TASK_ID>-<slug>` | `docs/CT-03-local-setup` |

Một branch nên có một task/đầu ra review được; task lớn chia backend/client/worker và ghi phụ thuộc. Không dùng branch theo tên người làm nơi gom mọi thay đổi của nhiều task. Task chỉ cần nghiên cứu có thể bàn giao tài liệu, không phải viết code để đủ tên feature branch.

## 3. Integrated base và branch từ đâu

**Đề xuất:** dùng commit cuối của `main` đã qua checks/được ghi nhận làm integrated base; không tạo thêm branch integration dài hạn khi chưa có nhu cầu. Đức quản lý bản ghi base. Nếu nhóm chọn `integration/solo`, phải ghi rõ nó là branch thật nào, base/contract và tiêu chí đưa về main; hiện branch đó chưa có.

Với nhiều repo riêng, integrated base là **một bộ SHA**, không phải một SHA giả dùng cho tất cả:

```text
integration_id: <mốc đã kiểm tra>
frontend_repo / branch / full_commit_sha:
application_repo / branch / full_commit_sha: <NOT_ACCESSIBLE cho đến khi cung cấp>
ocr_repo / branch / full_commit_sha: <hiện cùng repo root, ghi rõ nếu sau này tách>
contract_version / status / bundle_sha256:
contract_commit_sha: <null nếu chưa commit, không điền HEAD cũ thay thế>
runtime/provider/model/corpus versions:
environment + URLs + mock/real/dummy:
checks/smoke log + người xác nhận:
```

Trước task mới: owner đồng bộ remote trong checkout phù hợp, xác nhận base commit và contract thực sự có ở đó, rồi giao cùng thông tin cho các AI. Không dùng “latest main” thay full SHA trong handover. Sau squash/merge, ghi **SHA kết quả trên integrated branch**, không tiếp tục gọi PR head trước squash là SHA của base.

### Worktree hoặc checkout riêng cho mỗi task

Worktree giúp mỗi task có working directory/index/branch riêng; không cần đổi branch trong preview đang chạy. Nguồn: [Git worktree](https://git-scm.com/docs/git-worktree). Nếu repo riêng chưa checkout, owner chỉ định repo/path thật trước; không tự chuyển sang monorepo.

Các lệnh sau là **ví dụ chưa chạy**, chỉ dùng sau khi thay base bằng commit đã được nhóm ghi nhận và thư mục đích chưa tồn tại:

```bash
CT03_BASE_SHA='<full-approved-integrated-commit>'
git rev-parse --verify "${CT03_BASE_SHA}^{commit}"
git worktree add -b feat/OC-02-frame-capture /private/tmp/lingualive-oc02 "$CT03_BASE_SHA"
```

Không dùng `-f` để bỏ qua xung đột branch/worktree. Worktree mới chỉ có file đã commit: không tự có UI/contract đang untracked ở preview hiện tại. Khi base chưa chứa các phần cần dùng, xử lý bàn giao/snapshot với owner trước, không âm thầm copy cả working tree hoặc git add tất cả.

Mỗi worktree có dependency/env local riêng, không dùng chung node_modules/venv qua symlink tự đặt. Khi cần chạy nhiều service cùng loại, ghi port riêng trong task; preview chính vẫn 8443, không kill/restart tiến trình của task khác để lấy port.

## 4. Làm việc theo contract

1. Nhận task ID, phạm vi file, base SHA, contract version/status/bundle và schema pointers. Đọc mã hiện hữu trước khi viết, tái sử dụng UI/media/provider.
2. Đăng ký file chung qua Đức: một người viết App.tsx, schema/OpenAPI/AsyncAPI, lockfile hoặc config chung tại một thời điểm. Bên còn lại cung cấp DTO/fixture/module và patch nhỏ sau khi nhánh trước được tích hợp.
3. Không tự đổi required field, enum, casing, đơn vị, ownership/auth, code point offset, bbox/timeline hoặc state machine. Nếu thiếu/mâu thuẫn, chỉ ra điểm thiếu và đề xuất; vẫn làm phần độc lập đã được giao.
4. Muốn thay contract: PR contract riêng, chủ schema + consumer review, thay examples/fixtures/catalog/CHANGELOG/version/hashes cùng nhau. Breaking/nền tảng/freeze v1 cần cả ba xác nhận. Consumer triển khai trên commit contract đã được ghi nhận; dependency draft phải ghi rõ là draft, không gọi là v1 đã được duyệt.
5. `contracts/contract-version.json` hash cả các file docs/fixtures thuộc bundle, kể cả decisions và guide CT-02. Sửa một file được hash là thay package; không sửa bằng PR docs ngầm mà bỏ cập nhật hash/version. CT-03 giữ nguyên toàn bộ package CT-02 và hash của nó.

## 5. Pull request và review

PR đề xuất dùng tiêu đề `<TASK_ID>: <hành vi thay đổi>`, liên kết task/phụ thuộc. Không tạo hoặc gửi PR trong CT-03.

```text
Task / owner:
Problem và hành vi sau thay đổi:
Repo / base SHA / PR head SHA:
Contract version / status / bundle hash / contract commit SHA:
Producer và consumers bị ảnh hưởng:
Phạm vi file; phần giữ nguyên:
Env/dependency/model/corpus/migration thay đổi (hoặc không có):
Validation commands + exit code + môi trường mock/dummy/real:
Smoke/acceptance đã chạy và bằng chứng:
Phần chưa làm / blockers / giới hạn:
Rollback/revert tương thích (nếu thay đổi tích hợp):
Reviewer cần: <owner + consumer; không dùng username đoán>
```

- Frontend client/auth/media: Hoàng Bảo review API/quyền; Bảo Anh review OCR/lexicon mapping khi liên quan. UI/CSS đơn thuần Đức chỉ định peer reviewer phù hợp.
- Backend/job/storage/auth: Hoàng Bảo chủ phần; Đức review client, Bảo Anh review worker/result boundary. Nếu Hoàng Bảo là tác giả thì cần reviewer khác, không tự ký thay các bên.
- OCR/worker/lexicon: Bảo Anh chủ phần; Hoàng Bảo review integration/storage, Đức review box/offset/rendering khi liên quan.
- Contract/transport/token policy/ID/units/breaking change: review theo ownership matrix, cả ba cho các quyết định nền tảng. Chưa có GitHub usernames để tự động gắn CODEOWNERS/required reviewers.

## 6. Điều kiện merge và kiểm tra phù hợp

| Loại PR | Check cần có | Chưa đủ để kết luận |
| --- | --- | --- |
| Docs/env template | Links, syntax, không secret, ignore rules đúng, bundle contract không bị thay ngoài task | Không cần viết unit test cho nội dung tài liệu; không tuyên bố backend đã chạy |
| Frontend/API adapter | Type/build và test hành vi liên quan, fixture schema, null/error/204/pending/retry/source cleanup | Screenshot hoặc build riêng không chứng minh backend/auth thật |
| App backend | Schema/error/permission/idempotency/transaction/state tests, chạy được theo README của repo thật | Không fake token hoặc chỉ trả fixture rồi báo real |
| OCR/worker/lexicon | Runtime/container phù hợp, raw compatibility, image/box/offset/error/concurrency và real-provider checks khi task yêu cầu | Dummy transport không chứng minh accuracy/readiness/load |
| Contract | Validate spec/schema/refs/examples/negative cases, consumers review và version/hash đồng bộ | Validation PASS không duyệt thay scope/architecture |
| Tích hợp | Các module cùng contract, smoke phù hợp thay đổi, không cross-room/user leak, ghi trạng thái thật | Một repo pass không tự làm cả hệ thống accepted |

Đề xuất merge khi phạm vi đúng, checks liên quan đạt trên base hiện tại, reviewer cần thiết đã xác nhận và phụ thuộc đã có. Không cần mở rộng/repeat testing khi không có thay đổi hoặc rủi ro mới. Docs-only không phải dựng lại AWS hay chạy OCR model.

Baseline TypeScript hiện lỗi ignoreDeprecations 6.0 với TS 5.9.3; chưa sửa. Không báo check chuẩn xanh vì dùng override. PR implementation cần xử lý config trong task riêng hoặc ghi ngoại lệ kiểm tra tạm **đã được nhóm thống nhất**, kèm check override và issue theo dõi; không che lỗi bằng skipLibCheck/tắt kiểm tra/nâng runtime ngoài scope. PR docs ghi rõ baseline này, không tự sửa config để “đủ điều kiện merge”.

**Đức thực hiện tích hợp sau review theo quyền task được giao**, từng PR nhỏ theo thứ tự phụ thuộc: contract được chốt → producer/client/worker → smoke trên base chung → cập nhật integration record. Squash merge là đề xuất mặc định cho feature task; chiến lược merge và quyền remote phải được nhóm xác nhận, không tự bật branch protection hoặc merge trong CT-03.

## 7. Conflict, hồi phục và cập nhật trạng thái

- Cập nhật nhánh theo base mới ở worktree của chính task; nếu conflict ở schema/App/lockfile, mời owner giải quyết từng thay đổi có nghĩa. Không chọn nguyên file “ours/theirs” hoặc regenerate lockfile bằng pnpm khác phiên bản rồi bỏ review.
- Sau giải quyết conflict phải review diff và chạy lại checks bị tác động. Không cherry-pick một phần producer schema mà bỏ consumer/fixtures/migration liên quan.
- Revert/rollback cần giữ producer và consumer tương thích; nếu đã có dữ liệu thay đổi thì owner backend ghi cách xử lý. CT-03 không chạy migration/rollback hoặc force push.
- Trạng thái: `todo → in_progress → ready_for_integration → integrated → accepted`. Frontend mock ready không làm backend accepted; integrated cần luồng qua các phần thật; accepted cần người nhóm chạy nghiệm thu và evidence. Repo/tài nguyên ngoài chưa đọc dùng NOT_ACCESSIBLE, không tự kết luận chưa phát triển.
- Sau mỗi merge, Đức ghi integration ID/SHA set mới, contract hash/status, check/smoke và phần còn thiếu; giao task tiếp theo từ mốc đó, không để ba AI tiếp tục trên ba base cũ.

## 8. Những gì chưa được cấu hình

Chưa tạo CI/PR template/CODEOWNERS/branch protection, integration branch/worktree hoặc GitHub usernames. Chưa có backend repo/access/commands. Quy trình này cần cả nhóm xác nhận trước áp dụng; các quyết định CT-01/CT-02 vẫn DRAFT, không được nâng trạng thái chỉ vì CT-03 đã có tài liệu.
