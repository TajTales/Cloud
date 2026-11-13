# Nhóm 2 — Database và kho lưu trữ local

**Sau nhóm 2, ngày 13/11/2026:** đã nối FE local cho profile/vocabulary/review/Solo/history bằng API và xác thực local thật. [Hướng dẫn thao tác và kiểm thử hiện tại](FE-DB-INTEGRATION-TESTS.md). Các số 79 tests và scope bên dưới là mốc bàn giao nhóm 2; chưa bao gồm lượt tích hợp mới. Không nâng trạng thái Cognito/OCR/AWS từ kết quả local.

**13/11/2026 — triển khai persistence local, chưa nghiệm thu AWS hoặc API nghiệp vụ.** Tiếp nối [nhóm 1](GROUP-01-BACKEND-FOUNDATION.md), giữ FE và contract `0.1.0-draft.1`. Không chuyển sang Supabase/PostgreSQL/Jitsi. Dùng **DynamoDB Local 3.3.2 + kho file local** để giữ hướng DynamoDB/S3 khi triển khai AWS sau này. Nguyễn Tài Đức vẫn là owner duy nhất.

## 1. Đã có gì

- Database thật chạy bằng Java 21 có sẵn, bind **127.0.0.1:8000**, telemetry tắt. Không Docker, AWS CLI, IAM account hoặc cloud credentials.
- Bảng ứng dụng `lingualive-local`, PK/SK và GSI `gsi1`, storage model **v1**. Init là lệnh chủ động, lặp lại được, không reset dữ liệu khi API khởi động.
- Repository có scope user/session/room/system, kiểm schema, quyền owner/member/host/admin, CAS revision và transaction. Child references được kiểm khi ghi; một số lifecycle tổng thể vẫn thuộc service nghiệp vụ sau.
- Dữ liệu từ vựng chống trùng theo scope + language + entry_id + sense_id; trạng thái ôn tập được lưu bền vững; bộ từ chung không có personal review_state.
- Cursor HMAC có binding scope/filter/order/watermark, khóa lưu riêng 0600; query kết quả theo seq có `through_seq`.
- Durable idempotency reservation/fencing, conflict và replay **resource reference**; không cache access token, mật khẩu, signed URLs hoặc body HTTP.
- Kho object immutable: stream, giới hạn byte, SHA-256, atomic publish directory, retry cùng dữ liệu, phát hiện corruption, đường dẫn traversal/symlink bị chặn. DB giữ reference, không nhét video/frame/full OCR vào item.
- Backend có thể bật kết nối storage và báo dependency ready; auth chưa cấu hình và không có business handlers, nên `/health/ready` vẫn **503** trung thực.

## 2. Chạy lại trên máy hiện tại

Database và API đã được chạy trong lượt làm nhóm 2. Không start thêm nếu cổng đang bận. Trên terminal mới sau khi đã dừng các process cũ:

```bash
# Terminal A — database ghi xuống đĩa, không dùng -inMemory
./scripts/dev-db
```

```bash
# Terminal B — init một lần, những lần sau có thể dùng check
./scripts/db-admin init
./scripts/db-admin check
PERSISTENCE_ENABLED=1 ./scripts/dev-api
```

```bash
# Terminal C — test thật trên bảng test mới và kho file tạm
./scripts/test-api
curl -i http://127.0.0.1:8081/health/ready
```

`test-api` hiện gồm cả nhóm 1 và nhóm 2, vì vậy cần DynamoDB Local đang chạy. Thiếu DB là test fail rõ ràng, không tự skip hoặc dùng in-memory mock. Test tự tạo/xóa bảng `lingualive-test-*`; không seed fixture vào bảng ứng dụng. Các identity/DTO/image/video bytes synthetic chỉ dùng để kiểm persistence, không phải OCR/model/Cognito/recording thật.

Foundation mode vẫn chạy độc lập với `PERSISTENCE_ENABLED=0` (mặc định). `./scripts/dev-api --check` không mở kết nối DB; khi bật persistence, config endpoint phải hợp lệ trước startup.

## 3. Cài trên checkout mới

```bash
python3.12 -m venv application-backend/.venv
application-backend/.venv/bin/python -m pip install -r application-backend/requirements.lock
./scripts/setup-local-db
```

Máy này đã có Temurin Java 21.0.12.1; không cài/đổi Java toàn máy. Source launcher cần JDK có compiler để chạy file `.java`. Vendor archive được tải từ CDN chính thức, kiểm SHA-256 và JAR version, không cần đăng nhập AWS. [local-tools.lock.json](../application-backend/local-tools.lock.json) pin archive/JAR của **3.3.2**; URL do AWS công bố có nhãn `v2.x` nhưng JAR thực báo 3.3.2. Không tự lấy latest mới nếu checksum thay đổi. JAR/native libs ~43 MB archive ở `.local-tools/`, không đưa vào Git.

**Sửa cấu hình IDE 13/11/2026:** [`.vscode/settings.json`](../.vscode/settings.json) khai báo `java.project.referencedLibraries` cho DynamoDB Local JAR và các dependency JAR. VS Code mặc định chỉ tìm `lib/**/*.jar`, trong khi launcher dùng thư viện ở `.local-tools/`, dẫn đến không resolve được import Jetty/ServerRunner. Đã tái hiện 8 lỗi khi thiếu classpath và biên dịch thành công với thư viện hiện có; không cần sửa mã launcher hoặc cài dependency mới. Cấu hình dùng đường dẫn tương đối và giữ pattern mặc định. Trên checkout mới phải chạy `scripts/setup-local-db` trước; nếu IDE giữ diagnostics cũ, dùng `Java: Clean Java Language Server Workspace` để nạp lại. Kiểm tra biên dịch không thay thế việc xác nhận diagnostics trong IDE.

SDK `boto3==1.44.1`/`botocore==1.44.1` được thêm vì cần DynamoDB protocol; 6 dependency mới trong venv riêng, tổng lock runtime **24 packages**. Không cài package toàn máy hoặc đổi dependency frontend/OCR/QA. Adapter bắt buộc endpoint HTTP loopback, không nhận cloud URL, tắt proxy, không đọc AWS profile/credential files, ký request bằng giá trị local không phải AWS credentials thật. Không có mode tự fallback cloud.

## 4. Cấu hình và vị trí dữ liệu

| Biến / đường dẫn | Giá trị / ý nghĩa |
| --- | --- |
| `PERSISTENCE_ENABLED` | `0` hoặc `1`, mặc định 0 |
| `DYNAMODB_ENDPOINT` | `http://127.0.0.1:8000`; chỉ literal loopback hoặc localhost được normalize |
| `DYNAMODB_TABLE` | `lingualive-local` |
| `APP_DATA_DIR` | Mặc định `application-backend/.local-data`, chứa objects và cursor key |
| `DYNAMODB_DATA_DIR` | Mặc định `.local-data/dynamodb`; chỉ cho launcher Java, dùng thư mục riêng |
| `DYNAMODB_PORT` | Mặc định 8000; khi đổi phải đặt DYNAMODB_ENDPOINT tương ứng cho API/CLI/test |
| `.local-data/dynamodb/` | SQLite backing file của DynamoDB Local; dừng process không làm mất dữ liệu |
| `.local-data/objects/` | Body + metadata từng object, tên thư mục theo hash key |
| `.local-data/cursor.key` | Secret 32 bytes cho cursor, mode 0600, không commit/export vào report |
| `.local-tools/dynamodb/` | Runtime vendor đã pin, không phải source |

Các thư mục `.local-data/` và `.local-tools/` được ignore ở module. Không xóa thư mục database để “reset” nếu có dữ liệu cần giữ. CORS của database không mở cho FE; FE phải đi qua application API. Launcher giới hạn Jetty về loopback bằng wrapper nhỏ theo JAR đã pin; thiếu connector/API đúng thì fail, không fallback bind toàn mạng. Vendor JAR không bị sửa.

## 5. Mô hình dữ liệu

Physical table definition và danh mục entity ở [schema/dynamodb-v1.json](../application-backend/schema/dynamodb-v1.json); code field projection/validation ở [catalog.py](../application-backend/src/lingualive_api/persistence/catalog.py). Đây là **schema persistence nội bộ**, không thay OpenAPI/AsyncAPI/JSON Schema public.

Envelope có `pk`, `sk`, `entity_kind`, `entity_id`, `scope_kind`, `scope_id`, `revision`, `model_version`, `payload` JSON canonical, optional expiry/index fields. UUID ứng dụng và opaque user identity giữ nguyên; scope/reference keys hash để tránh delimiter injection. Metadata item bị chặn trước giới hạn 400 KiB; blob lớn ở kho object.

| Entity | Nơi lưu / truy vấn chính | Điểm cần giữ |
| --- | --- | --- |
| Profile | USER scope, PROFILE; ref theo subject; GSI PROFILE#all | roles/permissions/status/email authority không cho learner tự sửa |
| Session | SESSION scope, META; global ref theo session_id | owner/room/current_source/version/latest_seq; bỏ capabilities/capture_limits/current_source view |
| Source | SESSION, SOURCE prefix; ref theo source_id | register_source transaction cập nhật session và thứ tự nguồn cùng lúc |
| Upload | SESSION, UPLOAD prefix | IDs/frame metadata/object key/state/expiry; không persist upload URL/headers |
| Job | SESSION, JOB prefix; ref theo job_id; GSI JOB#status; unique source/frame | upload/frame/source, deadline, lease owner/token/until, attempts; worker thực làm ở nhóm OCR |
| Result manifest | SESSION, RESULT#seq#id; ref result_id, uniqueness seq | cùng frame/job/source; trỏ OCR JSON + checksum/schema version |
| Room | ROOM, META; global ref; UNIQUE room code; GSI ROOM#all | tạo room/session/host membership trong một transaction; member_count là view |
| Membership | ROOM, MEMBERSHIP#hash(user) | role/capabilities/joined/left, làm guard cho write trong phòng |
| Personal word | USER, WORD prefix; canonical uniqueness | owner + language + entry + sense, review_state/version |
| Shared word | ROOM, SHARED_WORD prefix; canonical uniqueness | active membership, creator/host, không review_state cá nhân |
| Collection | USER, COLLECTION prefix | title/language/version; word_count tính tại service |
| History index | USER, HISTORY#UTC#session | private metadata; duration/count/playback state tính ở service |
| Occurrence | USER/ROOM, OCCURRENCE#word#digest | tham chiếu word/session/result/source/media time; helper giữ original surface |
| Recording metadata | SESSION, RECORDING prefix | object ref, state/duration/timeline; không persist signed playback URL |
| Object reference | SESSION, OBJECT_REF prefix | server-generated key/sha/size/content_type; file chưa đăng ký không đọc qua bundle |
| Audit/config/admin action | SYSTEM scope | admin/service authority; dữ liệu theo public schema tương ứng |
| Connection/ticket hash | SYSTEM scope | expiry epoch seconds; ticket thô/token không được lưu |
| Idempotency | partition theo caller/method/path, key digest | pending/completed, request digest, fencing token, expiry, resource reference |

Các trường public được dùng lại bằng schema refs; projection loại các field view/URL trước khi ghi. Khi làm API, phải dựng DTO public đầy đủ, tính lại capabilities theo caller và cấp URL sau kiểm quyền; không trả nguyên internal record.

Primary access paths dùng GetItem/Query mạnh nhất quán; không Scan trong request thông thường. GSI dành cho queue/admin là eventually consistent: operational_page re-read base row trước dùng, claim vẫn cần conditional lease. Scan chỉ có ở export maintenance.

## 6. Tính nhất quán và phạm vi bảo vệ

- Create/update/delete cần conditional revision; transaction gộp resource/reference/unique guards. Cursor không cho thay scope/filter/watermark. Native TTL không thay kiểm expiry tại request; bản local không chứng minh cleanup TTL cloud.
- Room write gắn ConditionCheck vào membership/room revision, nên revoke xảy ra giữa authorize và write sẽ abort. Quyền ở đây nhận **Identity đã xác minh**; chưa có JWT verifier, API vẫn fail closed. Không dùng role/profile snapshot làm chứng cứ đăng nhập.
- `save_word` giữ một tài nguyên cho mỗi dictionary sense; occurrence lưu riêng. Hai nghĩa khác nhau không bị gộp chỉ vì cùng chữ. Review chỉ đổi trạng thái/version, chưa phải thuật toán SRS.
- `register_source` khóa phiên bản session, thứ tự nguồn, source ID. Manifest seq có uniqueness; worker nhóm sau phải commit result/job/session watermark và notification theo state machine, không suy từ CRUD đơn lẻ là job pipeline đã xong.
- File put là immutable/atomic ở filesystem; file + database **không có distributed transaction**. DB write thất bại có thể để orphan file; read service từ chối file không có DB ref. Chưa có lifecycle tự xóa orphan/retention khi D12 chưa chốt.
- CRUD là lớp persistence nội bộ. Transfer host/rejoin, account suspension, counter/aggregate, cleanup reference/occurrence, full source/job/result state machine và quyền playback sau leave cần service/lifecycle tương ứng ở nhóm sau. Không mở một generic CRUD endpoint cho browser.

## 7. Backup và chuyển lên AWS sau này

```bash
mkdir -p application-backend/.local-data/backups
./scripts/db-admin export --output application-backend/.local-data/backups/metadata.ndjson
```

Export tạo file mới mode 0600, không overwrite. Dừng/quiesce writes để có snapshot nhiều trang ổn định; export scan không phải PITR/transaction toàn bảng. File chứa metadata thật nên để trong vùng private/ignored. Backup object bodies/metadata ở `.local-data/objects` riêng; giữ key/checksum và định danh khi chuyển. Chưa thực hiện import/restore cloud hoặc migration dữ liệu thật.

AWS sau này cần client adapter có IAM role/region, table/index/TTL deployment, S3 object adapter và kiểm quyền/URL thực. Local adapter hiện **chặn cloud URL có chủ đích**; không chỉ thay env để vô tình gọi AWS. Repository/model/public contract có thể tái sử dụng. Cần test IAM, GSI lag/throttling/transaction conflicts, lifecycle, backup/restore và hạ tầng thực trên AWS; local pass không thay các phép kiểm đó.

## 8. Kiểm chứng và bàn giao

[group02-results.json](group02-results.json) ghi commands/exit, versions/dependencies, số test, actual process-restart durability, HTTP smoke, export checksum và scope audit. Các test local dùng fixture synthetic để kiểm lưu trữ, không là kết quả từ điển/OCR/video thật. Bảng ứng dụng không được seed các fixture đó.

Nhóm 2 hoàn thành ở mức **local persistence**. Chưa có API nghiệp vụ/FE integration, Cognito, OCR worker, meeting/media/recording hay AWS được nghiệm thu. Bước tiếp theo là nhóm 3 xác thực và phân quyền, rồi nhóm API nghiệp vụ/OCR theo kế hoạch.

Nguồn: [DynamoDB Local setup](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html), [local/cloud differences và disableTelemetry](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.UsageNotes.html), [Boto3 1.44.1](https://pypi.org/project/boto3/1.44.1/).
