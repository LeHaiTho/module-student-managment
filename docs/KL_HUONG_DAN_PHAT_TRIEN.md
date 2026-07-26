# 📘 KẾ HOẠCH TỔNG THỂ DỰ ÁN — Hệ thống Quản lý Sinh viên Đại học (univ_sms)

> Dựa trên toàn bộ tài liệu hiện có trong thư mục `docs/` và cấu trúc `addons/` đã triển khai.

---

## 1. TỔNG QUAN DỰ ÁN

**Tên dự án:** Module Quản lý Sinh viên (University Student Management System — univ_sms)  
**Nền tảng:** Odoo 17.0 Community (Python 3.10+, PostgreSQL 15)  
**Môi trường dev:** Docker Compose (`odoo:17.0` + `postgres:15`)  
**Mục tiêu:** Xây dựng hệ thống quản lý sinh viên cho 1 trường đại học, bao gồm:

- Quản lý hồ sơ sinh viên, khoa/ngành, môn học, lớp học
- Điểm danh, thi cử, bảng điểm
- Học phí, hóa đơn
- Cổng tra cứu sinh viên (Portal)
- Báo cáo, dashboard
- Các module mở rộng: Đăng ký môn học, Thông báo, Phản hồi, Công tác sinh viên, Điểm rèn luyện, Giấy chứng nhận, Khảo sát

---

## 2. KIẾN TRÚC HỆ THỐNG

### 2.1. Mô hình tổ chức (Organization Hierarchy)

```
Trường (res.partner / implicit)
  └── Khoa (univ.sms.faculty)           — VD: Khoa Công nghệ Thông tin
        └── Bộ môn (univ.sms.department)  — VD: Bộ môn Khoa học Máy tính
              └── Ngành (univ.sms.program) — VD: Cử nhân CNTT (hệ đào tạo)
```

### 2.2. Mô hình dữ liệu (Data Model) — Các Model Chính

| Model | Module | Mô tả | Ghi chú |
|---|---|---|---|
| `univ.sms.faculty` | univ_sms_base | Khoa | Cấp 1 |
| `univ.sms.department` | univ_sms_base | Bộ môn | Cấp 2 |
| `univ.sms.program` | univ_sms_base | Ngành đào tạo | Cấp 3 |
| `univ.sms.subject` | univ_sms_base | Môn học | Có tín chỉ (credit) |
| `univ.sms.academic.year` | univ_sms_base | Năm học | VD: 2025-2026 |
| `univ.sms.term` | univ_sms_base | Học kỳ | Thuộc năm học |
| `univ.sms.student` | univ_sms_student | Sinh viên | Kế thừa `res.partner` |
| `univ.sms.enrollment` | univ_sms_student | Đăng ký học môn (gốc) | |
| `univ.sms.class` | univ_sms_class | Lớp học | |
| `univ.sms.timetable` | univ_sms_class | Thời khóa biểu | |
| `univ.sms.attendance.sheet` | univ_sms_attendance | Phiếu điểm danh | |
| `univ.sms.attendance.line` | univ_sms_attendance | Chi tiết điểm danh | |
| `univ.sms.exam` | univ_sms_exam | Kỳ thi | |
| `univ.sms.exam.result` | univ_sms_exam | Kết quả thi | |
| `univ.sms.transcript` | univ_sms_exam | Bảng điểm | |
| `univ.sms.fee.term` | univ_sms_fee | Học phí theo kỳ | |
| `account.move` | univ_sms_fee (kế thừa) | Hóa đơn học phí | |
| `univ.sms.registration.period` | univ_sms_registration | Đợt đăng ký môn | Phase 6 |
| `univ.sms.course.offering` | univ_sms_registration | Lớp môn học mở | Phase 6 |
| `univ.sms.registration` | univ_sms_registration | Đăng ký môn học (DKMH) | Phase 6 |
| `univ.sms.elective.wish` | univ_sms_registration | Nguyện vọng chọn môn | Phase 6 |
| `univ.sms.notification` | univ_sms_notification | Thông báo | Phase 6 |
| `univ.sms.feedback` | univ_sms_feedback | Phản hồi ý kiến | Phase 6 |
| `univ.sms.health.insurance` | univ_sms_student_affairs | BHYT | Phase 7 |
| `univ.sms.residence.info` | univ_sms_student_affairs | Ngoại trú | Phase 7 |
| `univ.sms.military.service` | univ_sms_student_affairs | NVQS | Phase 7 |
| `univ.sms.conduct.period` | univ_sms_conduct | Kỳ rèn luyện | Phase 7 |
| `univ.sms.conduct.criteria` | univ_sms_conduct | Tiêu chí rèn luyện | Phase 7 |
| `univ.sms.conduct.score` | univ_sms_conduct | Điểm rèn luyện | Phase 7 |
| `univ.sms.certificate.type` | univ_sms_certificate | Loại giấy chứng nhận | Phase 7 |
| `univ.sms.certificate.request` | univ_sms_certificate | Yêu cầu cấp giấy | Phase 7 |
| (kế thừa `survey.survey`) | univ_sms_survey | Khảo sát | Phase 7 |

### 2.3. RBAC — Nhóm người dùng (Groups)

| Group | Code | Quyền cao nhất |
|---|---|---|
| Super Admin (CNTT) | `group_univ_admin` | Toàn quyền |
| Phòng Đào tạo | `group_univ_academic_office` | CRUD master data, lớp, điểm |
| Phòng Tài chính | `group_univ_finance_office` | Học phí, hóa đơn |
| Phòng CTSV | `group_univ_student_affairs_office` | BHYT, NVQS, rèn luyện |
| Trưởng Khoa | `group_univ_dean` | Xem báo cáo khoa |
| Giảng viên | `group_univ_lecturer` | Điểm danh, nhập điểm |
| Cố vấn HT | `group_univ_advisor` | Kế thừa lecturer + duyệt NV |
| Sinh viên | `base.group_portal` | Tra cứu Portal |

---

## 3. CHIẾN LƯỢC DATABASE (SỬ DỤNG DB NHƯ THẾ NÀO)

### 3.1. Cơ chế ORM của Odoo

- **Odoo dùng PostgreSQL làm database duy nhất**, không dùng ORM nào khác.
- Mỗi model Odoo là 1 table PostgreSQL (trừ các model abstract).
- Mỗi field Char/Integer/Float/Date/Boolean là 1 column trong table.
- **Many2one** → tạo column `field_name_id` kiểu INT + foreign key.
- **One2man**y → không tạo column (chỉ khai báo ngược từ Many2one).
- **Many2many** → tạo table trung gian riêng.
- **Fields Selection** → lưu dạng VARCHAR chứa value string.
- **Computed fields** có `store=True` → lưu vào cột thật.
- **Inheritance** (`_inherits`): dùng `res.partner` cho `univ.sms.student` — cơ chế delegation, không tạo bảng mới cho partner, chỉ thêm cột `partner_id`.

### 3.2. Database Schema — Các table chính

```
res_partner                        # Odoo core — lưu thông tin liên hệ/email
  └── univ_sms_student             # _inherits res.partner — thêm student_code, program_id, state
univ_sms_faculty                   # name, code, dean_id, active
univ_sms_department                # name, code, faculty_id
univ_sms_program                   # name, code, department_id, total_credits, duration_years
univ_sms_subject                   # name, code, credit, is_active
univ_sms_academic_year             # name, date_start, date_end
univ_sms_term                      # name, academic_year_id, date_start, date_end
univ_sms_class                     # name, subject_id, term_id, lecturer_id, max_seats
univ_sms_timetable                 # class_id, day_of_week, start_time, end_time, room
univ_sms_attendance_sheet          # class_id, date, state
univ_sms_attendance_line           # sheet_id, student_id, status
univ_sms_exam                      # subject_id, term_id, exam_date, exam_type
univ_sms_exam_result               # student_id, exam_id, score, is_passed
univ_sms_transcript                # student_id, summary
univ_sms_fee_term                  # student_id, term_id, total_fee, paid_amount, state
account_move                       # Odoo core — hóa đơn
  └── (kế thừa bởi univ_sms_fee)
```

### 3.3. Các bảng cho Phase 6-7 (sẽ tạo thêm)

```
univ_sms_registration_period       # name, term_id, date_start, date_end, reg_type, min/max_credit, state
univ_sms_course_offering           # subject_id, term_id, lecturer_id, class_id, max_seats
  └── subject_prerequisite_rel     # Many2many: subject_id ↔ prerequisite_id
univ_sms_registration              # student_id, offering_id, period_id, state
univ_sms_elective_wish             # student_id, offering_id, priority, state
univ_sms_notification              # subject, message, state (kế thừa mail.thread)
univ_sms_feedback                  # student_id, content, state
univ_sms_health_insurance          # student_id, insurance_code, date_start/end, payment_state
univ_sms_residence_info            # student_id, residence_type, address, state
univ_sms_military_service          # student_id, registration_status, declared_date
univ_sms_conduct_period            # name, term_id, date_start, date_end, state
univ_sms_conduct_criteria          # name, max_score, category
univ_sms_conduct_score             # period_id, student_id, criteria_id, self_score, class_score, final_score
univ_sms_certificate_type          # name, template, fee
univ_sms_certificate_request       # student_id, type_id, state (draft→approved→issued)
```

### 3.4. Sequence & Auto-increment

- **MSSV** (student_code): dùng trường `ir.sequence` của Odoo để tự sinh tuần tự (ví dụ: `202500001`, `202500002`...)
- Mỗi module có thể khai báo sequence riêng trong `data/` folder

### 3.5. Audit Trail

- Dùng `tracking=True` trên các field trạng thái để Odoo tự ghi log vào `mail.message`
- Phase 10 (Hardening) sẽ bổ sung `mail.thread` inheritance cho toàn bộ model trọng yếu

---

## 4. CẤU TRÚC MODULES & LUỒNG PHỤ THUỘC

### 4.1. Dependency Chain (Manifest depends)

```
univ_sms_base (không phụ thuộc module univ nào)
  └── univ_sms_student (depends: univ_sms_base, mail)
        ├── univ_sms_class (depends: univ_sms_student)
        │     └── univ_sms_attendance (depends: univ_sms_class)
        ├── univ_sms_exam (depends: univ_sms_student)
        ├── univ_sms_fee (depends: univ_sms_student, account)
        ├── univ_sms_registration (depends: univ_sms_base, univ_sms_student, univ_sms_class, univ_sms_exam)
        ├── univ_sms_notification (depends: univ_sms_base, univ_sms_student, mail)
        ├── univ_sms_feedback (depends: univ_sms_base, univ_sms_student, mail)
        ├── univ_sms_student_affairs (depends: univ_sms_base, univ_sms_student)
        ├── univ_sms_conduct (depends: univ_sms_base, univ_sms_student)
        ├── univ_sms_certificate (depends: univ_sms_base, univ_sms_student)
        └── univ_sms_survey (depends: univ_sms_base, univ_sms_student, survey)
              └── univ_sms_portal (depends: tất cả module trên, portal)
                    └── univ_sms_report (depends: tất cả)
```

### 4.2. Quy tắc cấu trúc file (mỗi module)

```
addons/univ_sms_xxx/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── *.py
├── security/
│   ├── ir.model.access.csv
│   └── *.xml (groups, record rules)
├── views/
│   ├── *_views.xml
│   └── menu_views.xml
├── data/
│   └── *.xml (data mẫu, sequence)
├── wizard/          (nếu có)
│   └── __init__.py
│   └── *.py
├── controllers/     (nếu có Portal)
│   └── __init__.py
│   └── *.py
└── static/
    └── src/
        ├── css/
        ├── js/
        └── scss/
```

---

## 5. PHASES & TIẾN ĐỘ TRIỂN KHAI

### ✅ Phase 1 — Master Data (đã code)
**Modules:** `univ_sms_base`, `univ_sms_student`  
**Output:**
- `univ.sms.faculty` — Khoa
- `univ.sms.department` — Bộ môn
- `univ.sms.program` — Ngành
- `univ.sms.subject` — Môn học
- `univ.sms.academic.year` / `univ.sms.term` — Năm học / Học kỳ
- `univ.sms.student` — Sinh viên (`_inherits res.partner`)
- `univ.sms.enrollment` — Đăng ký học môn
- Menu + Security groups + Views cơ bản

### ✅ Phase 2 — Lớp & Điểm danh (đã code)
**Modules:** `univ_sms_class`, `univ_sms_attendance`  
**Output:**
- `univ.sms.class` — Lớp học
- `univ.sms.timetable` — Thời khóa biểu
- `univ.sms.attendance.sheet` + `.line` — Điểm danh

### ✅ Phase 3 — Thi & Học phí (đã code)
**Modules:** `univ_sms_exam`, `univ_sms_fee`  
**Output:**
- `univ.sms.exam` + `.result` — Kỳ thi & kết quả
- `univ.sms.fee.term` — Học phí theo kỳ
- Kế thừa `account.move` cho hóa đơn

### ✅ Phase 4 — Portal cơ bản (đã code)
**Module:** `univ_sms_portal`  
**Output:**
- Routes cho sinh viên tra cứu: TKB, điểm danh, bảng điểm, học phí
- QWeb templates kế thừa `portal.portal_layout`

### ✅ Phase 5 — Security mở rộng (đã code)
**Module:** `univ_sms_base` (mở rộng)  
**Output:**
- RBAC groups: Phòng Đào tạo, Tài chính, CTSV, Trưởng khoa, Giảng viên, CVHT
- Record rules cho từng role

### ⏳ Phase 6 — Đăng ký môn, Thông báo, Phản hồi (chưa code)
**Modules:** `univ_sms_registration`, `univ_sms_notification`, `univ_sms_feedback`
- **CẦN trả lời OPEN_Q1, OPEN_Q2 trước khi code**
- Đợt đăng ký môn (registration_period) + Lớp mở (course_offering) + DKMH/DKMNV
- Thông báo từ PĐT → sinh viên
- Form phản hồi ý kiến

### ⏳ Phase 7 — CTSV, Rèn luyện, Giấy CN, Khảo sát (chưa code)
**Modules:** `univ_sms_student_affairs`, `univ_sms_conduct`, `univ_sms_certificate`, `univ_sms_survey`
- **CẦN trả lời OPEN_Q3, Q4, Q5, Q8 trước khi code**
- BHYT, Ngoại trú, NVQS
- Điểm rèn luyện (workflow 3 cấp)
- Giấy chứng nhận (workflow duyệt)
- Khảo sát (kế thừa survey gốc)

### ⏳ Phase 8 — E-learning *(optional)*
**Module:** `univ_sms_elearning`
- **CẦN OPEN_Q7:** tích hợp Odoo eLearning hay link LMS ngoài

### ⏳ Phase 9 — Dashboard & Báo cáo mở rộng (chưa code)
**Module:** `univ_sms_report` (mở rộng)
- Dashboard theo role (Admin, PĐT, Khoa, Giảng viên)
- Portal widget cho SV
- QWeb PDF: bảng điểm, hóa đơn, giấy chứng nhận

### 📋 Phase 10 — Hardening (tương lai)
- Tối ưu performance
- Audit log (mail.thread cho mọi model quan trọng)
- Data migration scripts

---

## 6. CÁC OPEN QUESTIONS CẦN GIẢI QUYẾT

> Các câu hỏi này cần được trả lời TRƯỚC KHI code Phase 6-7.

### OPEN_Q1 — Giới hạn tín chỉ đăng ký môn
> Đăng ký môn học: có giới hạn số tín chỉ tối thiểu/tối đa mỗi kỳ không? Có kiểm tra môn tiên quyết tự động không?

- Ảnh hưởng: Model `univ.sms.registration.period` có field min_credit, max_credit, và `univ.sms.registration` có constraint check prerequisite.

### OPEN_Q2 — Khảo sát: dùng survey gốc hay custom
> Khảo sát: dùng module survey gốc Odoo (kế thừa) hay xây model riêng?

- Ảnh hưởng: Cấu trúc module `univ_sms_survey` — có thể chỉ là wrapper kế thừa, hoặc mất nhiều effort custom UI.

### OPEN_Q3 — Giấy chứng nhận: có ký số không?
> Giấy chứng nhận: cần ký số (digital signature) hay chỉ xuất PDF + xác nhận thủ công?

- Ảnh hưởng: Workflow `draft → approved → issued` có thêm bước ký số hay không.

### OPEN_Q4 — Điểm rèn luyện: thang điểm & workflow
> Điểm rèn luyện: thang 100 (5 nội dung) theo TT16/2024 hay quy chế riêng? Workflow 3 cấp?

- Ảnh hưởng: Cấu trúc model `univ.sms.conduct.criteria` và workflow duyệt.

### OPEN_Q5 — Cố vấn học tập
> CVHT phụ trách 1 lớp hay theo nhóm SV? Có duyệt đăng ký môn không?

- Ảnh hưởng: Quyền `group_univ_advisor` và luồng duyệt registration.

### OPEN_Q6 — Dashboard: loại biểu đồ?
> Cần loại biểu đồ cụ thể nào? VD: tỷ lệ SV theo trạng thái, GPA theo lớp, công nợ, điểm danh.

- Ảnh hưởng: Thiết kế dashboard views (graph/pivot) cho Phase 9.

### OPEN_Q7 — E-learning: tích hợp thật hay link ngoài?
> E-learning: tích hợp Odoo website_slides hay chỉ link ra LMS ngoài (Moodle...)?

- Ảnh hưởng: Phase 8 có cần module mới hay không.

### OPEN_Q8 — NVQS: chỉ lưu hay có báo cáo?
> NVQS: chỉ form khai báo lưu trữ, hay có workflow báo cáo định kỳ + export file?

- Ảnh hưởng: Model `univ.sms.military.service` có cần thêm wizard export.

---

## 7. HƯỚNG LÀM CỤ THỂ (STEP-BY-STEP WORKFLOW)

### Bước 1: Xác nhận Open Questions
- Trả lời 8 câu hỏi trong mục 6 ở trên
- Ghi vào file `docs/OPEN_QUESTIONS_RESOLVED.md` hoặc cập nhật trực tiếp vào spec

### Bước 2: Triển khai Phase 6
1. Tạo module `univ_sms_registration`:
   - Models: registration_period, course_offering, registration, elective_wish
   - Inheritance: thêm prerequisite_ids, subject_type vào `univ.sms.subject` (file mới trong module này, KHÔNG sửa file Phase 1)
   - Security: ir.model.access.csv + record rules
   - Views: form, list, search, menu
   - Portal route cho SV đăng ký môn

2. Tạo module `univ_sms_notification`:
   - Model: notification (kế thừa mail.thread)
   - Views + portal route

3. Tạo module `univ_sms_feedback`:
   - Model: feedback
   - Views + portal route

### Bước 3: Triển khai Phase 7
1. `univ_sms_student_affairs`: health_insurance, residence_info, military_service
2. `univ_sms_conduct`: conduct_period, criteria, score (workflow 3 cấp)
3. `univ_sms_certificate`: certificate_type, certificate_request
4. `univ_sms_survey`: kế thừa survey gốc
5. Cập nhật `univ_sms_portal`: thêm routes cho các chức năng mới

### Bước 4: Triển khai Phase 9 (Dashboard & Report)
1. Dashboard views: admin, lecturer, student
2. QWeb PDF reports: transcripts, invoices, certificates
3. Portal widgets

### Bước 5: Cập nhật mock data
- Chạy script `create_mock_data_v4.py` (phiên bản mới) để generate dữ liệu test cho toàn bộ Phase 6-7

### Bước 6: Kiểm thử
- `-u` tất cả module
- Kiểm tra quyền từng group
- Test Portal routes

---

## 8. LƯU Ý KỸ THUẬT QUAN TRỌNG

1. **Không sửa code Phase cũ:** Mọi mở rộng model Phase 1-5 phải dùng Class Inheritance trong file riêng ở module mới.

2. **Security đi trước View:** Luôn tạo `ir.model.access.csv` + record rules trước khi tạo views.

3. **Naming convention:**
   - Model name: `univ.sms.*` (dấu chấm)
   - Module name: `univ_sms_*` (dấu gạch dưới)
   - File name: snake_case
   - Class name: PascalCase (VD: `UnivSmsFaculty`)

4. **Translate:** Field có `translate=True` cho name — dùng cho đa ngôn ngữ sau này.

5. **Test command:** Sau mỗi Phase, chạy:
   ```
   docker exec -it odoo-container odoo -u univ_sms_xxx --stop-after-init
   ```

6. **Git branch:** Mỗi module/bugfix nên tạo branch riêng:
   ```
   feature/univ_sms_registration
   feature/univ_sms_notification
   ...
   ```

---

## 9. FILE CẦN TẠO/SỬA KHI BẮT ĐẦU CODE PHASE 6

### Module: univ_sms_registration
```
addons/univ_sms_registration/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── registration_period.py
│   ├── course_offering.py
│   ├── registration.py
│   ├── elective_wish.py
│   └── subject_inherit.py          # MỞ RỘNG univ.sms.subject (không sửa file Phase 1)
├── security/
│   ├── ir.model.access.csv
│   └── security_rules.xml
├── views/
│   ├── registration_period_views.xml
│   ├── course_offering_views.xml
│   ├── registration_views.xml
│   └── menu_views.xml
├── data/
│   └── registration_data.xml
└── wizard/
    ├── __init__.py
    └── registration_wizard.py
```

### Module: univ_sms_notification
```
addons/univ_sms_notification/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── notification.py
├── security/
│   ├── ir.model.access.csv
│   └── security_rules.xml
├── views/
│   ├── notification_views.xml
│   └── menu_views.xml
└── data/
    └── notification_data.xml
```

### Module: univ_sms_feedback
```
addons/univ_sms_feedback/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── feedback.py
├── security/
│   ├── ir.model.access.csv
│   └── security_rules.xml
├── views/
│   ├── feedback_views.xml
│   └── menu_views.xml
└── data/
    └── feedback_data.xml
```

---

> 📌 **Kết luận:** Đây là kế hoạch tổng thể để phát triển hệ thống. Bước tiếp theo là **trả lời 8 câu hỏi OPEN** ở mục 6, sau đó sẽ code lần lượt Phase 6 → Phase 7 → Phase 9 theo đúng spec đã định nghĩa trong docs/.