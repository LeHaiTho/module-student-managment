# Khóa schema F1, F2, F3 (Leader chốt ngày 20/11/2026)

Tài liệu này là hợp đồng giữa các agent. Không đổi tên model, field, state hoặc
giá trị selection dưới đây nếu leader chưa đồng ý. Field nào không nằm trong tài
liệu thì agent sở hữu module được tự đặt, miễn là không đụng file của agent khác.

## 0. Baseline đã đo (20/11/2026)

| Kiểm tra | Kết quả | Log |
|---|---|---|
| Cài mới 15 module trên DB sạch `sms_fresh` | Đạt, exit 0 | `test-results/baseline_fresh_install.log` |
| `-u all` trên bản sao `univ_sms_db` (`sms_upgrade`) | Đạt, exit 0 | `test-results/baseline_upgrade.log` |
| Automated test | Không có thư mục `tests` trong module nào | |
| Backup trước khi sửa | `backups/univ_sms_db_before_audit_20261120.dump` | |

## 1. Quy tắc chung

* Thông báo lỗi và lý do cho người dùng: tiếng Việt.
* Thao tác tạo dữ liệu phải lặp an toàn (chạy hai lần không sinh bản ghi trùng).
* Controller portal: lấy sinh viên từ user hiện tại; mọi ID gửi từ trình duyệt
  phải được kiểm tra thuộc phạm vi hợp lệ **trước** khi dùng `sudo()`.
* Tham số cấu hình dùng `ir.config_parameter`, khóa có tiền tố `univ_sms.`.
* Test: `addons/<module>/tests/`, kế thừa `odoo.tests.common.TransactionCase` hoặc
  `HttpCase`, gắn `@tagged('post_install', '-at_install', 'univ_sms')`.
* Chạy test: `tools/run_tests.sh <db_name> <module1,module2>`. Mỗi agent dùng DB
  riêng (`sms_t_f1`, `sms_t_f2`, `sms_t_f3`, …).

## 2. F1 Đăng ký môn thông minh (sở hữu: Agent F1)

Module: `univ_sms_registration`, `univ_sms_class`, `univ_sms_student`
(`enrollment.py`), `univ_sms_fee`, và phần đăng ký trong portal
(`univ_sms_portal/controllers/portal.py` các route `/my/academic/registration*`,
template `portal_registration` trong `portal_templates.xml`).

### 2.1 `univ.sms.registration` (sửa)
* `state`: giữ nguyên `draft`, `registered`, `confirmed`, `cancelled`.
* **Trạng thái chiếm chỗ**: `registered`, `confirmed`. `draft` không chiếm chỗ.
* Thêm `enrollment_id` (Many2one `univ.sms.enrollment`, readonly, copy=False).
* Thêm `result_message` (Char): lý do hoặc kết quả gần nhất, tiếng Việt.
* Ràng buộc `unique(student_id, offering_id)` giữ nguyên. Đăng ký lại sau khi hủy
  thì **kích hoạt lại bản ghi đã hủy**, không tạo bản ghi mới.
* Service: `register_student(student, offering, period)` (`@api.model`) trả về
  `dict(status, message, registration_id, waitlist_id, position)`, trong đó
  `status` ∈ `{'registered', 'waitlisted', 'rejected', 'already'}`.
  Thứ tự kiểm tra: sinh viên đang học → đợt mở và đúng thời gian → lớp thuộc
  học kỳ của đợt → trùng môn → tiên quyết → giới hạn tín chỉ tối đa → trùng lịch
  → còn chỗ (hết chỗ thì vào danh sách chờ).
* Hủy (`action_cancel`): enrollment liên kết chuyển `cancelled`, học phí tính
  lại, sau đó gọi `offering._promote_waitlist()`.

### 2.2 `univ.sms.registration.waitlist` (mới)
| Field | Kiểu | Ghi chú |
|---|---|---|
| student_id | M2O student, required | |
| offering_id | M2O course.offering, required | |
| period_id | M2O registration.period, required | |
| request_date | Datetime, default now | dùng để xếp hàng (FIFO, hòa thì so `id`) |
| position | Integer, compute | vị trí trong các bản ghi `waiting` của lớp |
| state | `waiting`, `promoted`, `cancelled`, `rejected` | |
| processed_date | Datetime | |
| registration_id | M2O registration | sau khi được nhận |
| note | Char | lý do khi `rejected` (ví dụ: lúc nhận thì bị trùng lịch) |

* Mỗi sinh viên chỉ có **một** bản ghi `waiting` trên một lớp (partial unique
  index `WHERE state = 'waiting'`, kèm constraint Python).
* Chính sách nhận người chờ: **tự động** nhận người `waiting` đầu tiên khi có chỗ.
  Kiểm tra lại toàn bộ điều kiện; trượt thì đánh dấu `rejected` kèm `note` rồi xét
  người kế tiếp.

### 2.3 `univ.sms.course.offering` (sửa)
* `registered_count` chỉ đếm trạng thái chiếm chỗ. Thêm `waitlist_count`.
* `_promote_waitlist()`.

### 2.4 Trùng lịch
* `univ.sms.timetable._overlaps(other)`: cùng `day_of_week` và
  `start < other.end and other.start < end`.
* Trùng lịch xét `offering.class_id.timetable_ids` với lịch của các đăng ký đang
  chiếm chỗ cùng học kỳ của sinh viên. Offering không có class hoặc không có lịch
  thì không xét.

### 2.5 Đồng bộ enrollment
* Đăng ký vào trạng thái chiếm chỗ: tìm enrollment
  `(student, subject, term)`. Có thì đặt `state='registered'`,
  `class_id=offering.class_id`; chưa có thì tạo. Ghi `enrollment_id`.
* Hủy: enrollment `state='cancelled'` (không xóa).

### 2.6 Học phí (`univ_sms_fee`)
* Thêm `univ.sms.fee.due_date` (Date) ← **F3 phụ thuộc field này**.
* `total_credits`: tính lại khi enrollment của (student, term) đổi. Chỉ cập nhật
  khi fee còn `state='draft'` (chưa lập hóa đơn); fee đã lập hóa đơn thì ghi
  chatter/log, không đổi số tiền.
* `action_create_invoice`: đã có hóa đơn khác `cancel` thì trả về hóa đơn đó,
  không tạo trùng.

## 3. F2 Điểm danh QR và điều kiện dự thi (sở hữu: Agent F2)

Module: `univ_sms_attendance`, `univ_sms_exam`, cùng các file portal **mới**
`univ_sms_portal/controllers/attendance_qr.py` và
`univ_sms_portal/views/portal_attendance_qr_templates.xml` (leader đã tạo sẵn
khung và khai báo trong manifest/`__init__`). Agent F2 được sửa template
`portal_attendance` trong `portal_templates.xml` (chỉ template đó).

### 3.1 `univ.sms.attendance.session` (mới)
| Field | Kiểu | Ghi chú |
|---|---|---|
| sheet_id | M2O attendance.sheet, required, ondelete cascade | |
| class_id | related sheet_id.class_id, store | |
| token_hash | Char, index, copy=False | SHA-256 hex của token; không lưu token thô |
| start_time | Datetime | |
| expire_time | Datetime | ≤ start_time + 10 phút (constraint) |
| late_after_minutes | Integer, mặc định 5 | quét sau start + n phút là `late` |
| state | `draft`, `active`, `closed` | |
| qr_url | Char, groups giảng viên, xóa khi đóng phiên | URL chứa token để hiển thị QR |
| checkin_count | Integer compute | |

* Token: `secrets.token_urlsafe(32)`. Ảnh QR lấy từ route có sẵn
  `/report/barcode/?barcode_type=QR&value=<url>`, không thêm thư viện.
* Mỗi phiếu chỉ có tối đa một phiên `active`.

### 3.2 `univ.sms.attendance.line` (sửa)
* Thêm `checkin_time` (Datetime), `checkin_source` (`manual`, `qr`; mặc định
  `manual`), `session_id` (M2O session).
* Phiếu `confirmed` thì không được sửa hoặc tạo dòng (chặn ở `write`/`create`,
  không chỉ ở view).

### 3.3 Route check-in
* `GET /attendance/qr/<string:token>`, `auth='user'` (chưa đăng nhập thì Odoo
  chuyển sang trang login). Chỉ đọc và ghi khi người dùng bấm xác nhận, hoặc ghi
  ngay nhưng phải idempotent. Agent tự chọn, có kèm CSRF nếu dùng POST.
* Kết quả: `ok_present`, `ok_late`, `already`, `expired`, `not_enrolled`,
  `not_student`, `invalid`, `closed`. Hiển thị tiếng Việt.

### 3.4 Chuyên cần và điều kiện dự thi
* Tỷ lệ vắng = số dòng `absent` / số phiếu `confirmed` của lớp × 100. `excused`
  không tính vắng, `late` tính có mặt. Phiếu `draft` không tham gia.
* Ngưỡng: `univ_sms.max_absence_rate`, mặc định `20` (%). Vượt ngưỡng (`>`) thì
  không đủ điều kiện.
* Trên `univ.sms.enrollment` (inherit trong `univ_sms_exam`): `exam_eligible`
  (Boolean, store, mặc định True), `exam_ineligible_reason` (Char),
  `eligibility_checked_at` (Datetime).
* `univ.sms.class.action_compute_exam_eligibility()` (đặt trong `univ_sms_exam`).
  `univ.sms.exam.action_load_students` chỉ nạp sinh viên đủ điều kiện, sau khi đã
  tính lại.

## 4. F3 Cảnh báo sớm (sở hữu: Agent F3)

Module **mới** `univ_sms_early_warning`. Depends: `univ_sms_student`,
`univ_sms_exam`, `univ_sms_attendance`, `univ_sms_fee`, `univ_sms_registration`,
`mail`. Lý do tách module: không đụng file của F1/F2, gỡ cài độc lập được.

### 4.1 `univ.sms.warning` (mới, `mail.thread`, `mail.activity.mixin`)
| Field | Kiểu | Ghi chú |
|---|---|---|
| name | Char compute store | |
| student_id | M2O student, required, index | |
| warning_type | `gpa`, `failed_subjects`, `attendance`, `debt`, `credit` | |
| severity | `high`, `medium`, `low` | gpa/failed/attendance = high, debt/credit = medium |
| state | `new`, `in_progress`, `closed` | tracking |
| term_id | M2O term | |
| evidence_value | Float | GPA / % vắng / số nợ / số tín chỉ tại thời điểm tạo |
| evidence_text | Text | mô tả bằng chứng (lớp, môn, hạn nộp…) |
| home_class_id, program_id | related student, store | phục vụ dashboard |
| advisor_partner_id | M2O res.partner, store | student.advisor_id, nếu trống thì home_class.advisor_id |
| detected_at | Datetime | |
| closed_at, closed_by_id | Datetime, M2O res.users | |
| consultation_ids | O2M `univ.sms.warning.consultation` | |

* Chống trùng: partial unique index `(student_id, warning_type)` với
  `state != 'closed'`. Chạy lại thì cập nhật bằng chứng của cảnh báo đang mở,
  không tạo mới.
* Đóng: ghi `closed_at`, `closed_by_id`. Mở lại: về `in_progress`.

### 4.2 `univ.sms.warning.consultation` (mới)
`warning_id`, `user_id` (mặc định user hiện tại), `date`, `note` (required),
`outcome` (`contacted`, `plan_agreed`, `referred`, `resolved`).

### 4.3 Bộ máy đánh giá
* `univ.sms.warning.run_evaluation(students=None)` trả về
  `{'created': n, 'updated': n}`. Có nút chạy thủ công (wizard hoặc action) và
  `ir.cron` chạy hằng ngày.
* Ngưỡng (`ir.config_parameter`): `univ_sms.warning_gpa_threshold` = 5.0
  (GPA học kỳ gần nhất, thang 10); `univ_sms.warning_failed_subjects` = 2
  (số dòng bảng điểm `final_score < 5.0` trong kỳ gần nhất);
  `univ_sms.max_absence_rate` = 20 (dùng chung với F2, đọc `enrollment.absence_rate`);
  công nợ: `fee.remaining_amount > 0` và `fee.due_date < hôm nay`;
  tín chỉ: tổng tín chỉ các đăng ký đang chiếm chỗ < `period.min_credit` của
  đợt `regular` gần nhất đã đóng hoặc đang mở.
* Chỉ đánh giá sinh viên `state='studying'`.

### 4.4 Phân quyền
* Cố vấn (`group_univ_advisor`): đọc và ghi cảnh báo có
  `advisor_partner_id = user.partner_id`.
* Phòng Đào tạo, Phòng CTSV, Admin: toàn quyền đọc và ghi.
* Portal: chỉ đọc cảnh báo của chính mình (`student_id.partner_id = user.partner_id`).
* Giảng viên thường: không có quyền.

### 4.5 Dashboard
Graph, pivot và list, lọc và nhóm theo lớp hành chính, ngành, loại, mức độ,
trạng thái. Menu "Cảnh báo sớm" dưới menu gốc University SMS.

## 5. Thứ tự merge
1. Leader: khung chung (tài liệu này, `tools/run_tests.sh`, khung file portal
   QR, `fee.due_date`).
2. F1, F2, F3 chạy song song trên các file không giao nhau.
3. Leader review diff và chạy toàn bộ test.
4. Bảo mật portal, record rule cho exam/transcript, test truy cập chéo.
5. Seed, demo, tài liệu.
