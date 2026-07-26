from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "BAO_CAO_DO_AN_TOT_NGHIEP_UNIV_SMS.md"


CHAPTER3 = r"""# CHƯƠNG 3. THIẾT LẬP FRAMEWORK ODOO VÀ MÔI TRƯỜNG VẬN HÀNH HỆ THỐNG

## 3.1 Tổng quan mục tiêu thiết lập

Chương này trình bày quy trình thiết lập môi trường Odoo 17 Community để vận hành hệ thống University Student Management System. Trọng tâm của chương không phải là mô tả thao tác sao chép source code, mà là thiết lập một hệ thống Odoo hoàn chỉnh gồm Odoo framework, PostgreSQL, cấu hình runtime, cơ sở dữ liệu, custom addons, dữ liệu mẫu và các điểm truy cập sau khi cài đặt.

Trong Odoo, một ứng dụng nghiệp vụ không chạy độc lập như một chương trình Python thông thường. Ứng dụng được nạp vào Odoo thông qua cơ chế module, sử dụng ORM, registry, XML data, security, menu, action, view, controller và report của framework. Vì vậy, việc cài đặt hệ thống cần được hiểu là quá trình chuẩn bị môi trường Odoo, khởi tạo database, nạp custom module vào registry và kiểm tra toàn bộ hệ thống sau khi framework đã nhận diện module.

### 3.1.1 Kiến trúc môi trường triển khai

Source code hiện tại sử dụng Docker Compose để đóng gói môi trường chạy. Kiến trúc gồm hai service chính:

- Service `odoo` chạy image `odoo:17.0`, cung cấp Odoo framework, HTTP server, ORM, view engine, controller và QWeb report.
- Service `db` chạy image `postgres:15`, lưu database `univ_sms_db` và toàn bộ dữ liệu nghiệp vụ.

Thư mục `addons/` trên máy host được mount vào container Odoo tại `/mnt/extra-addons`. Nhờ đó, Odoo có thể nạp các custom addon `univ_sms_*` mà không cần chỉnh sửa image Odoo gốc.

![Hình 3.1. Kiến trúc Docker Compose của University SMS](screenshots/hinh-3-1-docker-compose-architecture.png)

**Giải thích:** Hình 3.1 mô tả cách trình duyệt truy cập Odoo qua cổng `8069`, Odoo xử lý nghiệp vụ và kết nối PostgreSQL thông qua service `db`.  
**Ý nghĩa:** Kiến trúc này tách tầng ứng dụng và tầng dữ liệu, giúp hệ thống dễ khởi động, dừng, sao lưu và chuyển sang máy khác.  
**Vai trò:** Đây là nền tảng runtime cho toàn bộ module quản lý sinh viên.  
**Luồng xử lý:** Người dùng truy cập trình duyệt, request đi vào Odoo, Odoo dùng ORM đọc/ghi dữ liệu trong PostgreSQL.

### 3.1.2 Thành phần cần thiết của hệ thống

Một môi trường Odoo vận hành được hệ thống University SMS cần các thành phần sau:

| Thành phần | Vai trò | Cách triển khai trong dự án |
|---|---|---|
| Odoo Framework | Cung cấp ORM, view, menu, action, report, controller | Container `odoo:17.0` |
| PostgreSQL | Lưu dữ liệu nghiệp vụ và metadata Odoo | Container `postgres:15` |
| Custom Addons | Chứa module `univ_sms_*` | Mount `./addons:/mnt/extra-addons` |
| Cấu hình Odoo | Khai báo database, addons path, master password | File `odoo.conf` |
| Docker Compose | Điều phối Odoo và PostgreSQL | File `docker-compose.yml` |
| Trình duyệt | Truy cập backend và portal | `http://localhost:8069` |

## 3.2 Chuẩn bị môi trường trước khi khởi chạy Odoo

Trước khi khởi động Odoo, máy triển khai cần có Docker Desktop hoặc Docker Engine, Docker Compose plugin, trình duyệt web và dung lượng ổ đĩa đủ để lưu image cũng như database volume. Trên Windows, Docker Desktop cần được khởi động trước khi chạy các lệnh `docker compose`.

### 3.2.1 Yêu cầu phần cứng và phần mềm

Môi trường tối thiểu nên có CPU 2 nhân, RAM 4 GB, ổ cứng trống tối thiểu 5 GB và kết nối Internet trong lần chạy đầu tiên để tải image `odoo:17.0` và `postgres:15`. Với dữ liệu demo nhiều phân hệ, RAM 8 GB sẽ ổn định hơn.

Các phần mềm cần có:

- Docker Desktop hoặc Docker Engine.
- Docker Compose plugin.
- Chrome, Edge hoặc Firefox.
- VSCode hoặc trình soạn thảo tương đương để kiểm tra file cấu hình.
- Python local chỉ cần cho các script phụ trợ, không bắt buộc cho runtime Odoo vì Odoo chạy trong container.

Kiểm tra Docker:

```bash
docker --version
docker compose version
```

### 3.2.2 Cấu trúc thư mục triển khai

Thư mục triển khai cần giữ được các thành phần chính: `addons/`, `docker-compose.yml`, `odoo.conf` và tài liệu hướng dẫn. Các thư mục `__pycache__`, file tạm hoặc cookie không phải thành phần cốt lõi của hệ thống.

```text
Module_quan-ly-sinh-vien/
├── addons/
│   ├── univ_sms_base/
│   ├── univ_sms_student/
│   ├── univ_sms_registration/
│   ├── univ_sms_portal/
│   └── univ_sms_report/
├── docs/
├── docker-compose.yml
├── odoo.conf
└── HUONG_DAN_CAI_DAT.md
```

![Hình 3.2. Cấu trúc thư mục triển khai](screenshots/hinh-3-2-project-structure.png)

**Giải thích:** Hình 3.2 minh họa cấu trúc thư mục dùng để triển khai Odoo và custom addons.  
**Ý nghĩa:** Người triển khai cần đặt terminal tại thư mục chứa `docker-compose.yml` để các volume mount hoạt động đúng.  
**Vai trò:** Cấu trúc thư mục quyết định Odoo có đọc được custom addons hay không.  
**Luồng xử lý:** Docker Compose đọc `docker-compose.yml`, mount `./addons` vào container, Odoo đọc module từ `/mnt/extra-addons`.

## 3.3 Cấu hình Odoo framework bằng Docker Compose

Docker Compose là lớp điều phối môi trường. Thay vì cài thủ công Python, PostgreSQL, thư viện hệ thống và Odoo trên máy host, dự án dùng container để chuẩn hóa môi trường chạy. Cách làm này phù hợp với đồ án vì giảm lỗi khác biệt môi trường giữa các máy.

### 3.3.1 Cấu hình service PostgreSQL

Trong `docker-compose.yml`, service `db` sử dụng image `postgres:15`:

```yaml
db:
  image: postgres:15
  environment:
    POSTGRES_USER: odoo
    POSTGRES_PASSWORD: odoo
    POSTGRES_DB: postgres
  volumes:
    - db_data:/var/lib/postgresql/data
```

Service này tạo PostgreSQL server nội bộ cho Odoo. Volume `db_data` giúp dữ liệu database không bị mất khi container dừng hoặc restart. Odoo không kết nối PostgreSQL qua `localhost` mà kết nối qua hostname `db`, đúng theo tên service trong Docker Compose network.

### 3.3.2 Cấu hình service Odoo

Service `odoo` sử dụng image `odoo:17.0`, phụ thuộc service `db` và expose cổng `8069`:

```yaml
odoo:
  image: odoo:17.0
  depends_on:
    - db
  ports:
    - "8069:8069"
  volumes:
    - ./addons:/mnt/extra-addons
    - ./odoo.conf:/etc/odoo/odoo.conf
    - odoo_data:/var/lib/odoo
```

Cấu hình trên có ba điểm quan trọng. Thứ nhất, `8069:8069` cho phép truy cập Odoo từ trình duyệt tại `http://localhost:8069`. Thứ hai, `./addons:/mnt/extra-addons` đưa custom module vào Odoo framework. Thứ ba, `./odoo.conf:/etc/odoo/odoo.conf` bảo đảm Odoo chạy đúng cấu hình của hệ thống.

### 3.3.3 Cấu hình `odoo.conf`

File `odoo.conf` xác định cách Odoo kết nối database và nơi tìm addons:

```ini
[options]
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
db_host = db
db_user = odoo
db_password = odoo
db_name = univ_sms_db
admin_passwd = <hashed master password>
```

`addons_path` gồm hai phần. `/mnt/extra-addons` là nơi chứa custom module của đồ án, còn `/usr/lib/python3/dist-packages/odoo/addons` là nơi chứa addons chuẩn đi kèm Odoo. `db_host = db` cho biết Odoo kết nối đến service PostgreSQL trong Docker Compose. `db_name = univ_sms_db` xác định database mặc định của hệ thống.

![Hình 3.3. Cấu hình odoo.conf](screenshots/hinh-3-4-odoo-conf.png)

**Giải thích:** Hình 3.3 thể hiện các tham số quan trọng trong file cấu hình Odoo.  
**Ý nghĩa:** Nếu `addons_path` hoặc `db_host` sai, Odoo sẽ không nhận module hoặc không kết nối được database.  
**Vai trò:** Đây là điểm nối giữa Odoo framework, custom addons và PostgreSQL.  
**Luồng xử lý:** Khi container Odoo khởi động, Odoo đọc `odoo.conf`, kết nối database và scan addons path.

## 3.4 Khởi động Odoo framework và khởi tạo database

Sau khi chuẩn bị Docker Compose và `odoo.conf`, bước tiếp theo là khởi động các container. Đây là bước đưa Odoo framework và PostgreSQL vào trạng thái sẵn sàng để tạo database và cài module.

### 3.4.1 Khởi động container

Chạy lệnh sau tại thư mục chứa `docker-compose.yml`:

```bash
docker compose up -d
```

Lệnh này tải image nếu máy chưa có, tạo network, tạo volume và khởi động hai container `db`, `odoo`. Sau đó kiểm tra trạng thái bằng:

```bash
docker compose ps
```

Kết quả mong muốn là service `db` và `odoo` đều ở trạng thái `Up`, trong đó Odoo map cổng `8069`.

![Hình 3.4. Kiểm tra trạng thái container](screenshots/hinh-3-3-docker-compose-ps.png)

**Giải thích:** Hình 3.4 minh họa kết quả `docker compose ps` khi PostgreSQL và Odoo đã chạy.  
**Ý nghĩa:** Đây là bằng chứng môi trường framework đã hoạt động trước khi cài module.  
**Vai trò:** Giúp người triển khai xác định lỗi nằm ở container hay ở module.  
**Luồng xử lý:** Docker khởi động PostgreSQL trước, sau đó Odoo kết nối đến database thông qua service `db`.

### 3.4.2 Khởi tạo database Odoo

Database sử dụng trong dự án là `univ_sms_db`. Nếu database chưa tồn tại, người triển khai mở:

```text
http://localhost:8069
```

Sau đó tạo database mới với tên `univ_sms_db`. Tài khoản quản trị ban đầu có thể đặt là `admin/admin` trong môi trường demo. Khi database được tạo, Odoo sẽ tạo các bảng hệ thống như `ir_model`, `ir_ui_view`, `ir_module_module`, `res_users`, `res_partner` và các bảng metadata khác. Các bảng nghiệp vụ `univ_sms_*` chỉ xuất hiện sau khi custom module được cài đặt.

### 3.4.3 Kiểm tra log framework

Log Odoo giúp xác định framework có khởi động đúng không:

```bash
docker compose logs -f odoo
```

Log PostgreSQL:

```bash
docker compose logs -f db
```

Khi kiểm tra log, cần chú ý các lỗi như không kết nối được database, sai `addons_path`, lỗi XML view, lỗi external id hoặc lỗi Python khi Odoo nạp module.

## 3.5 Cài đặt module nghiệp vụ vào Odoo framework

Sau khi Odoo framework và database đã sẵn sàng, custom addon được cài vào database. Đây là bước Odoo đọc manifest, tạo model trong registry, tạo bảng PostgreSQL, nạp security, action, menu, view, report và dữ liệu cấu hình.

### 3.5.1 Cơ chế cài module trong Odoo

Khi cài một module, Odoo xử lý theo thứ tự chính:

1. Đọc file `__manifest__.py` để xác định tên module, dependencies và danh sách file data.
2. Kiểm tra dependency, ví dụ `univ_sms_student` phụ thuộc `univ_sms_base`.
3. Import Python model để cập nhật registry.
4. Tạo hoặc cập nhật bảng PostgreSQL tương ứng với model.
5. Nạp security groups, access rights và record rules.
6. Nạp XML view, action, menu, QWeb template và report.
7. Ghi trạng thái module vào bảng `ir_module_module`.

Vì hệ thống University SMS gồm nhiều module liên quan nhau, thứ tự dependency rất quan trọng. Module dữ liệu nền phải được cài trước module sinh viên; module sinh viên phải có trước lớp học, điểm danh, thi, học phí và đăng ký môn.

### 3.5.2 Lệnh cài toàn bộ module

Lệnh cài toàn bộ module trong database `univ_sms_db`:

```bash
docker compose exec -T odoo odoo -c /etc/odoo/odoo.conf -d univ_sms_db -i univ_sms_base,univ_sms_student,univ_sms_class,univ_sms_attendance,univ_sms_exam,univ_sms_fee,univ_sms_registration,univ_sms_notification,univ_sms_feedback,univ_sms_student_affairs,univ_sms_conduct,univ_sms_certificate,univ_sms_survey,univ_sms_portal,univ_sms_report --stop-after-init
```

Trong đó:

- `docker compose exec -T odoo`: chạy lệnh bên trong container Odoo.
- `odoo -c /etc/odoo/odoo.conf`: chạy Odoo với file cấu hình đã mount.
- `-d univ_sms_db`: chọn database cần cài module.
- `-i ...`: cài danh sách module.
- `--stop-after-init`: dừng tiến trình sau khi cài xong để tránh chạy song song nhiều Odoo process.

Khi cập nhật code module đã cài, dùng `-u` thay cho `-i`:

```bash
docker compose exec -T odoo odoo -c /etc/odoo/odoo.conf -d univ_sms_db -u univ_sms_base,univ_sms_student,univ_sms_class,univ_sms_attendance,univ_sms_exam,univ_sms_fee,univ_sms_registration,univ_sms_notification,univ_sms_feedback,univ_sms_student_affairs,univ_sms_conduct,univ_sms_certificate,univ_sms_survey,univ_sms_portal,univ_sms_report --stop-after-init
```

### 3.5.3 Seed dữ liệu mẫu và kiểm tra dữ liệu

Sau khi module được cài, hệ thống có thể seed dữ liệu mẫu realistic:

```bash
cmd /c 'docker compose exec -T odoo bash -lc "odoo shell -d univ_sms_db < /mnt/extra-addons/seed_university_realistic.py"'
```

Trên Windows, nên dùng `cmd` như lệnh trên để hạn chế lỗi encoding tiếng Việt khi pipe file vào container. Script seed tạo dữ liệu khoa, bộ môn, ngành, môn học, sinh viên, giảng viên, lớp, thời khóa biểu, điểm danh, điểm thi, học phí, đăng ký môn, giấy chứng nhận, rèn luyện, khảo sát, góp ý, thông báo và tài khoản theo role.

Sau khi seed, chạy audit:

```bash
cmd /c 'docker compose exec -T odoo bash -lc "odoo shell -d univ_sms_db < /mnt/extra-addons/audit_university_data.py"'
```

Kết quả mong muốn:

```text
[audit] OK: no broken text markers found
```

![Hình 3.5. Quy trình cài đặt và khởi chạy hệ thống](screenshots/hinh-3-5-install-flow.png)

**Giải thích:** Hình 3.5 tóm tắt luồng từ chuẩn bị môi trường, khởi động Docker, tạo database, cài module, seed dữ liệu đến kiểm tra truy cập.  
**Ý nghĩa:** Giúp người đọc hình dung cài đặt Odoo là một chuỗi thao tác có thứ tự, không chỉ là chạy một lệnh.  
**Vai trò:** Là quy trình chuẩn để tái tạo môi trường demo.  
**Luồng xử lý:** Chuẩn bị Docker, chạy container, tạo database, cài module, seed data, audit và truy cập ứng dụng.

## 3.6 Kiểm tra hệ thống sau khi thiết lập

Sau khi Odoo framework đã chạy và module đã được cài, cần kiểm tra cả backend, portal, dashboard và dữ liệu demo. Bước này bảo đảm hệ thống không chỉ khởi động được mà còn vận hành đúng nghiệp vụ.

### 3.6.1 Kiểm tra các đường dẫn chính

Các URL chính sau khi cài đặt:

| Khu vực | URL | Mục đích kiểm tra |
|---|---|---|
| Backend Odoo | `http://localhost:8069/web` | Đăng nhập admin, kiểm tra menu backend |
| Landing page | `http://localhost:8069/university` | Kiểm tra route public và thông báo |
| Portal học vụ | `http://localhost:8069/my/academic` | Kiểm tra portal sinh viên |
| Form đăng ký sinh viên | `http://localhost:8069/student/register` | Kiểm tra route tự đăng ký |
| Portal đăng ký môn | `http://localhost:8069/my/academic/registration` | Kiểm tra nghiệp vụ đăng ký môn |
| Portal bảng điểm | `http://localhost:8069/my/academic/transcript` | Kiểm tra dữ liệu điểm |

![Hình 3.6. Các điểm truy cập sau cài đặt](screenshots/hinh-3-6-access-links.png)

**Giải thích:** Hình 3.6 liệt kê các điểm truy cập quan trọng của hệ thống sau setup.  
**Ý nghĩa:** Đây là checklist nhanh để xác nhận Odoo framework, backend và portal đều hoạt động.  
**Vai trò:** Hỗ trợ người chấm hoặc người triển khai mở đúng màn hình demo.  
**Luồng xử lý:** Người dùng mở URL, Odoo xử lý route/action tương ứng và trả về backend hoặc portal view.

### 3.6.2 Tài khoản demo

Mật khẩu mặc định của các tài khoản seed là:

```text
123456
```

| Vai trò | Login | Mục đích kiểm tra |
|---|---|---|
| Admin SMS | `admin.sms` | Kiểm tra toàn bộ menu backend |
| Phòng Đào tạo | `dt.nguyenthilan` | Kiểm tra nghiệp vụ học vụ |
| Phòng Tài chính | `tc.phamquanghuy` | Kiểm tra học phí, hóa đơn |
| Phòng Công tác SV | `ctsv.levanhoa` | Kiểm tra BHYT, cư trú, giấy chứng nhận |
| Giảng viên | `gv.tranminhduc` | Kiểm tra lớp, điểm danh, điểm |
| Sinh viên | `sv.nguyenvanan` | Kiểm tra portal sinh viên |

### 3.6.3 Tiêu chí xác nhận cài đặt thành công

Hệ thống được xem là thiết lập thành công khi thỏa mãn các tiêu chí:

- `docker compose ps` hiển thị container `db` và `odoo` ở trạng thái `Up`.
- Truy cập được `http://localhost:8069/web`.
- Database `univ_sms_db` tồn tại.
- Các module `univ_sms_*` ở trạng thái installed.
- Backend hiển thị menu Quản lý sinh viên và các phân hệ liên quan.
- Portal `/my/academic` hiển thị thông tin sinh viên khi đăng nhập tài khoản sinh viên.
- Dữ liệu tiếng Việt không bị lỗi encoding.
- Các báo cáo QWeb có thể mở từ menu Print của bản ghi tương ứng.

## 3.7 Lỗi thường gặp và kết luận chương

Trong quá trình thiết lập Odoo framework, lỗi thường xuất hiện ở ba nhóm: lỗi môi trường Docker, lỗi kết nối database và lỗi nạp custom module. Việc kiểm tra log theo từng lớp giúp khoanh vùng nhanh nguyên nhân.

| Lỗi | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| Không vào được `localhost:8069` | Container Odoo chưa chạy hoặc port 8069 bị chiếm | Chạy `docker compose ps`, kiểm tra port, đổi mapping sang `8070:8069` nếu cần |
| Odoo không kết nối database | Sai `db_host`, service `db` chưa sẵn sàng | Kiểm tra `odoo.conf`, xem log `docker compose logs -f db` |
| Module không xuất hiện | Sai `addons_path` hoặc mount `./addons` lỗi | Kiểm tra volume mount và restart Odoo |
| Cài module lỗi XML | Sai external id, sai field trong view, thiếu dependency | Xem log Odoo, sửa XML, chạy lại `-u` |
| Lỗi quyền truy cập | Thiếu dòng trong `ir.model.access.csv` hoặc record rule sai | Kiểm tra security CSV và XML rule |
| Dữ liệu tiếng Việt bị lỗi | Pipe file seed qua PowerShell sai encoding | Chạy seed bằng lệnh `cmd /c` theo tài liệu |
| Portal không có dữ liệu sinh viên | User chưa gắn `partner_id` với `univ.sms.student` | Kiểm tra dữ liệu seed hoặc hồ sơ sinh viên |

Chương 3 đã trình bày quy trình thiết lập Odoo framework và môi trường vận hành cho hệ thống University SMS. Nội dung chương đi từ kiến trúc Docker Compose, chuẩn bị môi trường, cấu hình Odoo, khởi tạo database, cài custom module, seed dữ liệu đến kiểm tra sau cài đặt. Qua đó có thể thấy hệ thống không chỉ là một tập source code, mà là một ứng dụng Odoo hoàn chỉnh được nạp vào framework, vận hành trên Odoo 17 Community và PostgreSQL 15.
"""


def main() -> None:
    text = REPORT.read_text(encoding="utf-8")
    start_marker = "# CHƯƠNG 3. HƯỚNG DẪN CÀI ĐẶT FRAMEWORK ODOO"
    end_marker = "# CHƯƠNG 4. XÂY DỰNG MODULE QUẢN LÝ SINH VIÊN TRÊN NỀN TẢNG ODOO"
    start = text.index(start_marker)
    end = text.index(end_marker)
    new_text = text[:start] + CHAPTER3 + "\n\n\\pagebreak\n\n" + text[end:]
    REPORT.write_text(new_text, encoding="utf-8")
    print(f"rewrote chapter 3 in {REPORT}")


if __name__ == "__main__":
    main()
