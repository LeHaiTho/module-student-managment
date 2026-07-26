# Hướng dẫn đóng gói, cài đặt và chạy hệ thống University SMS trên máy mới

Tài liệu này hướng dẫn cách chuyển toàn bộ hệ thống Quản lý Sinh viên University SMS sang máy khác và chạy lại bằng Docker. Hệ thống sử dụng:

- Odoo 17 Community.
- PostgreSQL 15.
- Docker Compose.
- Addons nội bộ trong thư mục `addons/`.

## 1. Cần gửi những gì sang máy mới?

Khi chuyển hệ thống sang máy mới, hãy đóng gói toàn bộ thư mục dự án hiện tại:

```text
Module_quan-ly-sinh-vien/
├── addons/
├── docs/
├── docker-compose.yml
├── odoo.conf
├── HUONG_DAN_CAI_DAT.md
└── các file tài liệu/script khác nếu có
```

Nên zip cả folder dự án:

```powershell
Compress-Archive -Path .\Module_quan-ly-sinh-vien -DestinationPath .\Module_quan-ly-sinh-vien.zip
```

Không cần gửi:

- Thư mục `.git` nếu không cần lịch sử code.
- Docker volume cũ, trừ khi muốn chuyển nguyên database đang dùng.
- Thư mục `__pycache__`.
- File tạm hoặc file `nul` nếu có.

## 2. Máy mới cần cài gì?

Máy mới cần:

1. Docker Desktop nếu dùng Windows/macOS.
2. Docker Engine + Docker Compose plugin nếu dùng Linux.
3. Trình duyệt Chrome, Edge hoặc Firefox.
4. Dung lượng trống tối thiểu khoảng 5GB.
5. Internet trong lần đầu để Docker tải image `odoo:17.0` và `postgres:15`.

Kiểm tra Docker:

```bash
docker --version
docker compose version
```

## 3. Giải nén và mở terminal

1. Chép file zip sang máy mới.
2. Giải nén, ví dụ ra thư mục:

```text
D:\Module_quan-ly-sinh-vien
```

3. Mở CMD hoặc PowerShell tại thư mục có file `docker-compose.yml`.

Ví dụ Windows CMD:

```cmd
cd /d D:\Module_quan-ly-sinh-vien
```

## 4. Khởi động Docker containers

Chạy:

```bash
docker compose up -d
```

Kiểm tra container:

```bash
docker compose ps
```

Kết quả mong muốn:

- Service `db` chạy PostgreSQL.
- Service `odoo` chạy Odoo và map cổng `8069`.

Nếu máy mới đã có ứng dụng dùng cổng `8069`, sửa file `docker-compose.yml`:

```yaml
ports:
  - "8070:8069"
```

Sau đó truy cập bằng `http://localhost:8070`.

## 5. Cài database và toàn bộ module

Database mặc định trong `odoo.conf` là:

```text
univ_sms_db
```

Chạy lệnh cài toàn bộ module:

```bash
docker compose exec -T odoo odoo -c /etc/odoo/odoo.conf -d univ_sms_db -i univ_sms_base,univ_sms_student,univ_sms_class,univ_sms_attendance,univ_sms_exam,univ_sms_fee,univ_sms_registration,univ_sms_notification,univ_sms_feedback,univ_sms_student_affairs,univ_sms_conduct,univ_sms_certificate,univ_sms_survey,univ_sms_portal,univ_sms_report --stop-after-init
```

Nếu lệnh báo database chưa tồn tại, mở trình duyệt:

```text
http://localhost:8069
```

Tạo database mới:

- Database Name: `univ_sms_db`
- Email: `admin`
- Password: `admin`
- Language/Country: tùy chọn.

Sau đó chạy lại lệnh cài module ở trên.

## 6. Seed dữ liệu mẫu chuẩn

Sau khi module đã cài xong, chạy seed dữ liệu mẫu realistic:

```bash
cmd /c 'docker compose exec -T odoo bash -lc "odoo shell -d univ_sms_db < /mnt/extra-addons/seed_university_realistic.py"'
```

Lưu ý quan trọng trên Windows:

- Nên dùng lệnh trên bằng `cmd`.
- Không dùng `Get-Content ... | docker compose exec ...` để pipe file seed, vì có thể làm lỗi tiếng Việt trong database.

Script seed sẽ:

- Reset dữ liệu nghiệp vụ `univ_sms_*`.
- Tạo khoa, bộ môn, ngành, môn học.
- Tạo sinh viên, giảng viên, phòng ban.
- Tạo lớp, thời khóa biểu, điểm danh.
- Tạo điểm thi, bảng điểm, học phí.
- Tạo đăng ký môn, giấy chứng nhận, NVQS, khảo sát, góp ý.
- Tạo tài khoản thật theo role.
- Vô hiệu hóa tài khoản demo cũ `sinhvien`, `giangvien`.

## 7. Kiểm tra dữ liệu sau khi seed

Chạy audit:

```bash
cmd /c 'docker compose exec -T odoo bash -lc "odoo shell -d univ_sms_db < /mnt/extra-addons/audit_university_data.py"'
```

Kết quả mong muốn:

```text
[audit] OK: no broken text markers found
```

Xem mẫu dữ liệu:

```bash
cmd /c "type addons\audit_samples.sql | docker compose exec -T db psql -U odoo -d univ_sms_db"
```

Kiểm tra các dòng như:

- `Khoa Công nghệ thông tin`
- `Đại học K25 - Kỹ thuật phần mềm - Lớp 01`
- `Lập trình Web - Nhóm 01`
- `Nguyên lý kế toán - Nhóm 01`

Nếu thấy dạng `Nguy??n` hoặc `Khoa CÃ´ng`, hãy chạy lại seed bằng đúng lệnh `cmd` ở bước 6.

## 8. Restart Odoo

Sau khi cài module và seed data:

```bash
docker compose restart odoo
```

Mở trình duyệt:

```text
http://localhost:8069
```

Hoặc nếu đổi port:

```text
http://localhost:8070
```

## 9. Link sử dụng

| Khu vực | Link |
|---|---|
| Landing | `http://localhost:8069/university` |
| Backend Odoo | `http://localhost:8069/web` |
| Portal sinh viên | `http://localhost:8069/my/academic` |
| Đăng ký môn | `http://localhost:8069/my/academic/registration` |
| Thời khóa biểu | `http://localhost:8069/my/academic/timetable` |
| Bảng điểm | `http://localhost:8069/my/academic/transcript` |
| Điểm danh | `http://localhost:8069/my/academic/attendance` |
| Học phí | `http://localhost:8069/my/academic/fees` |
| Giấy chứng nhận | `http://localhost:8069/my/academic/certificates` |
| Công tác SV | `http://localhost:8069/my/academic/student-affairs` |
| Rèn luyện | `http://localhost:8069/my/academic/conduct` |
| Khảo sát | `http://localhost:8069/my/academic/surveys` |
| Góp ý | `http://localhost:8069/my/academic/feedback` |

## 10. Tài khoản mẫu

Mật khẩu mặc định của các tài khoản seed là:

```text
123456
```

| Role | Login |
|---|---|
| Admin SMS | `admin.sms` |
| Phòng Đào tạo | `dt.nguyenthilan` |
| Phòng Tài chính | `tc.phamquanghuy` |
| Phòng Công tác SV | `ctsv.levanhoa` |
| Giảng viên | `gv.tranminhduc` |
| Sinh viên | `sv.nguyenvanan` |
| Sinh viên | `sv.tranthibichngoc` |

Tài khoản Odoo admin mặc định nếu bạn tự tạo database:

```text
admin / admin
```

## 11. Nếu muốn chuyển nguyên database đang dùng

Nếu bạn muốn chuyển cả dữ liệu thật hiện tại, không chỉ code và seed mẫu, cần backup database ở máy cũ rồi restore ở máy mới.

### 11.1. Backup database trên máy cũ

Chạy trong thư mục dự án máy cũ:

```bash
docker compose exec -T db pg_dump -U odoo -d univ_sms_db > univ_sms_db_backup.sql
```

Zip thêm file:

```text
univ_sms_db_backup.sql
```

### 11.2. Restore database trên máy mới

Sau khi `docker compose up -d`, tạo database rỗng nếu chưa có:

```bash
docker compose exec -T db createdb -U odoo univ_sms_db
```

Restore:

```bash
type univ_sms_db_backup.sql | docker compose exec -T db psql -U odoo -d univ_sms_db
```

Nếu dùng PowerShell:

```powershell
Get-Content .\univ_sms_db_backup.sql | docker compose exec -T db psql -U odoo -d univ_sms_db
```

Với file SQL backup database, pipe không gây lỗi tiếng Việt trong code seed vì đây là SQL dump từ PostgreSQL. Tuy nhiên nếu file lớn, nên dùng CMD hoặc công cụ restore ổn định hơn.

Sau restore:

```bash
docker compose restart odoo
```

## 12. Lệnh vận hành thường dùng

Xem container:

```bash
docker compose ps
```

Xem log Odoo:

```bash
docker compose logs -f odoo
```

Xem log database:

```bash
docker compose logs -f db
```

Dừng hệ thống:

```bash
docker compose down
```

Chạy lại:

```bash
docker compose up -d
```

Restart Odoo:

```bash
docker compose restart odoo
```

Update module sau khi sửa code:

```bash
docker compose exec -T odoo odoo -c /etc/odoo/odoo.conf -d univ_sms_db -u univ_sms_base,univ_sms_student,univ_sms_class,univ_sms_attendance,univ_sms_exam,univ_sms_fee,univ_sms_registration,univ_sms_notification,univ_sms_feedback,univ_sms_student_affairs,univ_sms_conduct,univ_sms_certificate,univ_sms_survey,univ_sms_portal,univ_sms_report --stop-after-init
docker compose restart odoo
```

## 13. Lỗi thường gặp

### 13.1. Không vào được `localhost:8069`

Kiểm tra:

```bash
docker compose ps
docker compose logs -f odoo
```

Nếu port bị trùng, đổi `8069` thành `8070` trong `docker-compose.yml`.

### 13.2. Odoo báo database không tồn tại

Tạo database từ giao diện `http://localhost:8069` hoặc dùng Odoo database manager, sau đó chạy lại lệnh cài module.

### 13.3. Module không hiện trong Apps

Chạy update apps list hoặc cài bằng command line. Kiểm tra `odoo.conf` có:

```ini
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
```

### 13.4. Dữ liệu bị lỗi tiếng Việt

Nguyên nhân thường gặp: chạy seed bằng PowerShell pipe.

Cách xử lý:

```bash
cmd /c 'docker compose exec -T odoo bash -lc "odoo shell -d univ_sms_db < /mnt/extra-addons/seed_university_realistic.py"'
cmd /c 'docker compose exec -T odoo bash -lc "odoo shell -d univ_sms_db < /mnt/extra-addons/audit_university_data.py"'
docker compose restart odoo
```

### 13.5. Lỗi permission khi chạy Docker trên Windows

Mở Docker Desktop trước, chờ Docker chạy hoàn tất, sau đó chạy lại terminal với quyền bình thường hoặc Administrator nếu cần.

## 14. Quy trình nhanh nhất để demo trên máy mới

Tóm tắt:

```bash
docker compose up -d

docker compose exec -T odoo odoo -c /etc/odoo/odoo.conf -d univ_sms_db -i univ_sms_base,univ_sms_student,univ_sms_class,univ_sms_attendance,univ_sms_exam,univ_sms_fee,univ_sms_registration,univ_sms_notification,univ_sms_feedback,univ_sms_student_affairs,univ_sms_conduct,univ_sms_certificate,univ_sms_survey,univ_sms_portal,univ_sms_report --stop-after-init

cmd /c 'docker compose exec -T odoo bash -lc "odoo shell -d univ_sms_db < /mnt/extra-addons/seed_university_realistic.py"'

cmd /c 'docker compose exec -T odoo bash -lc "odoo shell -d univ_sms_db < /mnt/extra-addons/audit_university_data.py"'

docker compose restart odoo
```

Sau đó mở:

```text
http://localhost:8069/web
http://localhost:8069/my/academic
```

Đăng nhập thử:

```text
sv.nguyenvanan / 123456
dt.nguyenthilan / 123456
admin.sms / 123456
```
