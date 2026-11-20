# Hướng dẫn cài đặt, vận hành, backup và deploy University SMS

## 1. Thành phần
| Thành phần | Phiên bản |
|---|---|
| Odoo Community | 17.0 (image Docker `odoo:17.0`) |
| PostgreSQL | 15 (local), Neon/Render Postgres (cloud) |
| Module | 16 module `univ_sms_*` trong `addons/` |

## 2. Chạy local bằng Docker Compose
```powershell
docker compose up -d
```
Mở http://localhost:8069. Database cấu hình trong `odoo.conf` là `univ_sms_db`.

### Cài mới trên database sạch
```bash
tools/build_deploy_db.sh univ_sms_demo    # cài 16 module + seed demo + xuất file dump
```
Sau đó đổi `db_name` trong `odoo.conf` thành `univ_sms_demo` (hoặc chọn DB khi đăng nhập).

### Nâng cấp module sau khi cập nhật source
```bash
tools/backup_restore.sh backup univ_sms_db          # luôn backup trước khi nâng cấp
MSYS_NO_PATHCONV=1 docker compose run --rm -T odoo odoo -c /etc/odoo/odoo.conf -d univ_sms_db -u all --stop-after-init
```

### Nạp lại dữ liệu demo (an toàn khi chạy nhiều lần)
```bash
MSYS_NO_PATHCONV=1 docker compose run --rm -T odoo odoo shell -c /etc/odoo/odoo.conf -d univ_sms_demo --no-http < tools/seed_demo.py
```

## 3. Automated test
```bash
tools/run_tests.sh sms_t_full univ_sms_base,univ_sms_student,univ_sms_class,univ_sms_attendance,univ_sms_exam,univ_sms_fee,univ_sms_registration,univ_sms_portal,univ_sms_notification,univ_sms_feedback,univ_sms_student_affairs,univ_sms_conduct,univ_sms_certificate,univ_sms_survey,univ_sms_report,univ_sms_early_warning
```
Script tạo DB tạm mới, cài module, chạy test có tag `univ_sms`. Log ghi vào `test-results/<db>.log`; dòng cuối có dạng `0 failed, 0 error(s) of N tests`.

## 4. Backup và restore
```bash
tools/backup_restore.sh backup univ_sms_db                          # -> backups/univ_sms_db_<thời gian>.dump
tools/backup_restore.sh restore backups/xxx.dump univ_sms_restore   # khôi phục vào DB MỚI, không ghi đè
```
Trên cloud, dùng chuỗi kết nối của Postgres:
```bash
pg_dump -Fc --no-owner --no-acl "$DATABASE_URL" > backup.dump
pg_restore --no-owner --no-acl -d "$DATABASE_URL" backup.dump
```
File đính kèm của bản deploy được lưu trong database (`ir_attachment.location = db`), nên một file dump là đủ.

## 5. Deploy demo miễn phí (Render + Neon)

### Kiến trúc
```
Người dùng ──HTTPS──> Render Web Service (free, Docker, 512MB) ──SSL──> Neon Postgres (free)
```
* Odoo chạy chế độ đa luồng (`workers = 0`) với 1 luồng cron, đủ cho khoảng 5 đến 10 người dùng đồng thời.
* File đính kèm nằm trong database vì Render free không có ổ đĩa bền.
* `list_db = False` và `dbfilter` khóa đúng một database; mật khẩu master đọc từ biến môi trường.

### Các bước
1. **Neon**: tạo project (region Singapore), lấy chuỗi kết nối **Direct** (không dùng pooler):
   `postgresql://user:pass@ep-xxx.ap-southeast-1.aws.neon.tech/univ_sms?sslmode=require`
2. **Nạp database đã dựng sẵn**:
   ```bash
   tools/build_deploy_db.sh univ_sms_demo
   pg_restore --no-owner --no-acl -d "<chuỗi Neon>" backups/univ_sms_demo_<thời gian>.dump
   ```
   (`pg_restore` chạy được qua container: `docker run --rm -i postgres:15 pg_restore --no-owner --no-acl -d "<chuỗi Neon>" < file.dump`)
3. **Render**: New → Blueprint → chọn repo GitHub → `render.yaml`. Nhập `DATABASE_URL` là chuỗi Neon ở bước 1.
4. Đợi build xong, mở `https://<tên>.onrender.com/web/login`.
5. **Chống ngủ**: Render free tắt dịch vụ sau 15 phút không có truy cập (khởi động lại mất khoảng 1 phút). Tạo monitor miễn phí trên UptimeRobot hoặc cron-job.org gọi `https://<tên>.onrender.com/web/health` mỗi 10 phút.
6. Đặt `web.base.url` đúng tên miền public (Thiết lập → Tham số hệ thống), để mã QR điểm danh trỏ đúng địa chỉ.

### Cập nhật phiên bản
Push lên nhánh deploy để Render tự build. Nếu có thay đổi model, đặt biến `ODOO_UPDATE_MODULES=all` cho một lần deploy, rồi xóa biến đi.

### Giới hạn của gói miễn phí
| Giới hạn | Ảnh hưởng | Cách xử lý |
|---|---|---|
| Render ngủ sau 15 phút | Lần truy cập đầu chờ khoảng 1 phút | Monitor ping 10 phút |
| RAM 512MB | Không chịu được tải lớn | Đủ cho demo khoảng 5 đến 10 người |
| Neon free 0.5GB | Dung lượng | Dữ liệu demo khoảng 100MB |
| Phiên đăng nhập lưu trên đĩa tạm | Restart thì người dùng phải đăng nhập lại | Chấp nhận cho demo |
| Không có SMTP | Email không gửi đi | Thông báo nằm trong hệ thống (portal, activity) |

## 6. Triển khai trên server công ty (Windows + Docker Desktop + Cloudflare Tunnel)

Mô hình giống server DIAMOND VN: Odoo chạy bằng Docker, **chỉ nghe ở 127.0.0.1**, còn
Cloudflare Tunnel đưa ra Internet qua HTTPS. Không mở cổng nào trên firewall hay router.

```
Người dùng ─HTTPS─> Cloudflare ─tunnel─> cloudflared.exe (server) ─> 127.0.0.1:8070 (Odoo) ─> Postgres (Docker)
```

### Cài lần đầu
```powershell
copy .env.prod.example .env.prod      # rồi điền mật khẩu dài ngẫu nhiên
powershell -ExecutionPolicy Bypass -File tools\prod_init.ps1 -DumpFile backups\univ_sms_demo_deploy.dump
powershell -ExecutionPolicy Bypass -File tools\prod_tunnel.ps1
```
* `prod_init.ps1`: build image, khởi động Postgres, nạp database demo nếu chưa có (đã có thì giữ nguyên), khởi động Odoo, đợi health check.
* `prod_tunnel.ps1`: mở quick tunnel, in link `https://….trycloudflare.com`, ghi link vào `backups\PUBLIC_URL.txt` và cập nhật `web.base.url`.
* Mã QR điểm danh lấy đúng địa chỉ giảng viên đang dùng (kể cả HTTPS sau tunnel), nên vẫn đúng khi link đổi.

### Quick tunnel và named tunnel
| | Quick tunnel (mặc định) | Named tunnel (khuyên dùng lâu dài) |
|---|---|---|
| Cần gì | Không cần tài khoản | Tài khoản Cloudflare + tên miền trên Cloudflare |
| Link | Đổi mỗi lần chạy lại tunnel / khởi động lại máy | Cố định, ví dụ `https://sms.ten-mien.com` |
| Cài | `tools\prod_tunnel.ps1` | Dashboard Zero Trust → Tunnels → Public hostname → `http://127.0.0.1:8070`; `cloudflared.exe service install <TOKEN>`; rồi `tools\prod_tunnel.ps1 -Hostname sms.ten-mien.com` |

### Cập nhật phiên bản
```powershell
git pull
powershell -ExecutionPolicy Bypass -File tools\prod_backup.ps1      # luôn backup trước
docker compose -f docker-compose.prod.yml --env-file .env.prod build odoo
# Nếu bản cập nhật có đổi model: đặt ODOO_UPDATE_MODULES=all trong .env.prod cho lần khởi động này
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --force-recreate odoo
```
Code module nằm trong image ở `/opt/univ_sms/addons`. Không đặt ở `/mnt/extra-addons`: image gốc khai báo `VOLUME` tại đó, Docker sẽ giữ volume cũ và container mới vẫn chạy code cũ.

### Backup
```powershell
powershell -ExecutionPolicy Bypass -File tools\prod_backup.ps1            # chạy ngay
powershell -ExecutionPolicy Bypass -File tools\prod_backup.ps1 -Schedule  # lịch 02:00 hằng ngày, giữ 14 bản
```
Đã diễn tập khôi phục ngày 20/11/2026: nạp bản backup vào database tạm, số sinh viên, đăng ký, dòng điểm danh và người dùng khớp 100%.

### Khởi động lại máy
* Docker Desktop: bật "Start Docker Desktop when you sign in". Container có `restart: unless-stopped` nên tự chạy lại.
* Quick tunnel không tự chạy lại: chạy `tools\prod_tunnel.ps1` sau khi đăng nhập, hoặc đặt Task Scheduler "At log on". Named tunnel cài dạng Windows service thì tự chạy.
