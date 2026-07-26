from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "BAO_CAO_DO_AN_TOT_NGHIEP_UNIV_SMS.md"


CH4_TEMPLATE = r"""# CHƯƠNG 4. XÂY DỰNG MODULE QUẢN LÝ SINH VIÊN TRÊN NỀN TẢNG ODOO

## 4.1 Tổng quan giải pháp xây dựng module

Chương này trình bày giải pháp xây dựng hệ thống University Student Management System dưới dạng các custom addon trên Odoo 17 Community. Trọng tâm của chương là cách hệ thống được thiết kế, cài vào framework Odoo, tổ chức cơ sở dữ liệu, xây dựng giao diện backend/portal, phân quyền, xử lý nghiệp vụ và kiểm thử bằng dữ liệu demo. Khác với một ứng dụng web viết độc lập, hệ thống này vận hành bên trong Odoo framework nên mọi thành phần như model, view, menu, action, security, controller và report đều tuân theo chuẩn mở rộng của Odoo.

Về nghiệp vụ, hệ thống tập trung vào quản lý sinh viên và các hoạt động liên quan trong trường đại học: dữ liệu nền đào tạo, hồ sơ sinh viên, lớp hành chính, lớp học phần, thời khóa biểu, điểm danh, kỳ thi, bảng điểm, học phí, đăng ký môn, giấy chứng nhận, công tác sinh viên, điểm rèn luyện, khảo sát, góp ý, thông báo, dashboard và báo cáo in ấn.

### 4.1.1 Mục tiêu xây dựng module

Mục tiêu của hệ thống là tạo một bộ module có thể cài đặt vào Odoo để phục vụ quản lý sinh viên theo hướng tập trung dữ liệu, phân quyền theo vai trò và hỗ trợ cả backend lẫn portal. Hệ thống cần đáp ứng các yêu cầu:

- Quản lý dữ liệu đào tạo gồm khoa, bộ môn, ngành, môn học, năm học và học kỳ.
- Quản lý hồ sơ sinh viên, lớp hành chính, lớp học phần và thời khóa biểu.
- Cho phép sinh viên đăng ký môn học qua portal.
- Hỗ trợ giảng viên điểm danh, nhập điểm và theo dõi lớp phụ trách.
- Hỗ trợ phòng tài chính quản lý học phí, hóa đơn.
- Hỗ trợ phòng công tác sinh viên xử lý BHYT, cư trú, NVQS, giấy chứng nhận, khảo sát và góp ý.
- Cung cấp dashboard, QWeb report và dữ liệu demo để trình bày hệ thống.

### 4.1.2 Phạm vi module và phân hệ

Source code hiện có 15 custom addon chính theo tiền tố `univ_sms_*`. Các module được chia theo nhóm nghiệp vụ thay vì gom toàn bộ vào một module lớn. Cách chia này giúp việc bảo trì, cài đặt và mở rộng rõ ràng hơn.

| Nhóm phân hệ | Module | Vai trò |
|---|---|---|
| Nền tảng dữ liệu | `univ_sms_base` | Khoa, bộ môn, ngành, môn học, năm học, học kỳ |
| Sinh viên | `univ_sms_student` | Hồ sơ sinh viên, lớp hành chính, enrollment |
| Lớp học | `univ_sms_class` | Lớp học phần, thời khóa biểu, mở rộng enrollment |
| Điểm danh | `univ_sms_attendance` | Phiếu điểm danh và dòng điểm danh |
| Thi và điểm | `univ_sms_exam` | Kỳ thi, kết quả thi, bảng điểm |
| Tài chính | `univ_sms_fee` | Học phí, hóa đơn học phí |
| Đăng ký môn | `univ_sms_registration` | Đợt đăng ký, lớp môn học, đăng ký môn, nguyện vọng |
| Portal | `univ_sms_portal` | Landing, portal học vụ, form đăng ký sinh viên |
| Báo cáo | `univ_sms_report` | QWeb report, dashboard graph/pivot |
| Mở rộng CTSV | `univ_sms_student_affairs`, `univ_sms_conduct`, `univ_sms_certificate`, `univ_sms_survey`, `univ_sms_feedback`, `univ_sms_notification` | Công tác sinh viên, rèn luyện, giấy chứng nhận, khảo sát, góp ý, thông báo |

### 4.1.3 Kiến trúc phụ thuộc custom addons

Các module có quan hệ phụ thuộc theo hướng từ dữ liệu nền đến nghiệp vụ mở rộng. Module `univ_sms_base` là nền tảng vì chứa các bảng dùng chung như khoa, bộ môn, ngành, môn học, năm học và học kỳ. Module `univ_sms_student` phụ thuộc dữ liệu nền để tạo hồ sơ sinh viên. Các module lớp học, điểm danh, thi, học phí và đăng ký môn phụ thuộc tiếp vào sinh viên và lớp.

```mermaid
flowchart LR
    Base[univ_sms_base]
    Student[univ_sms_student]
    Class[univ_sms_class]
    Attendance[univ_sms_attendance]
    Exam[univ_sms_exam]
    Fee[univ_sms_fee]
    Registration[univ_sms_registration]
    Portal[univ_sms_portal]
    Report[univ_sms_report]
    Affairs[CTSV/Rèn luyện/Giấy CN/Khảo sát]

    Base --> Student
    Student --> Class
    Class --> Attendance
    Attendance --> Exam
    Attendance --> Fee
    Base --> Registration
    Student --> Registration
    Class --> Registration
    Exam --> Registration
    Student --> Affairs
    Class --> Affairs
    Registration --> Portal
    Affairs --> Portal
    Fee --> Report
    Exam --> Report
    Registration --> Report
```

**Hình 4.1. Kiến trúc phụ thuộc custom addons**  
**Giải thích:** Sơ đồ thể hiện thứ tự phụ thuộc giữa các module trong hệ thống.  
**Ý nghĩa:** Khi cài đặt hoặc nâng cấp, module nền tảng phải được xử lý trước module nghiệp vụ.  
**Vai trò:** Giúp người phát triển hiểu vì sao manifest cần khai báo `depends` chính xác.  
**Luồng xử lý:** Odoo đọc manifest, cài dependency trước, sau đó mới nạp module phụ thuộc.

### 4.1.4 Chiến lược xây mới và kế thừa Odoo

Hệ thống được xây dựng theo hướng **xây mới nghiệp vụ quản lý sinh viên** nhưng **kế thừa hạ tầng chuẩn của Odoo**. Các model nghiệp vụ theo namespace `univ.sms.*` được tạo mới hoàn toàn để phục vụ bài toán đào tạo. Tuy nhiên hệ thống không viết lại các thành phần đã có sẵn trong Odoo như contact, chatter, portal, action, view, report, access rights hay kế toán.

| Thành phần | Xây mới | Kế thừa/mở rộng Odoo | Nhận xét |
|---|---|---|---|
| Hồ sơ sinh viên | Có | `_inherits = {'res.partner': 'partner_id'}` | Kế thừa dữ liệu liên hệ từ `res.partner` |
| Chatter/activity | Không | `_inherit = ['mail.thread', 'mail.activity.mixin']` | Dùng tracking/activity chuẩn |
| Partner | Không | `_inherit = 'res.partner'` | Bổ sung liên kết sinh viên |
| Enrollment | Có | `_inherit = 'univ.sms.enrollment'` trong module lớp | Mở rộng enrollment bằng lớp học phần |
| Môn học | Có | `_inherit = 'univ.sms.subject'` trong đăng ký môn | Bổ sung môn tiên quyết |
| Portal | Có giao diện riêng | Kế thừa `CustomerPortal` | Tận dụng cơ chế portal/user |
| Hóa đơn học phí | Có nghiệp vụ riêng | Liên kết `account.move` | Tận dụng kế toán Odoo |
| Report | Có template riêng | Dùng QWeb report chuẩn Odoo | Không viết engine in ấn riêng |

Như vậy, đề tài không sửa core Odoo. Toàn bộ tùy biến nằm trong `addons/`, phù hợp nguyên tắc triển khai ERP: mở rộng bằng addon, không can thiệp trực tiếp vào framework gốc.

## 4.2 Phân tích nghiệp vụ và luồng xử lý chính

Hệ thống phục vụ nhiều nhóm người dùng: quản trị viên SMS, phòng đào tạo, giảng viên, phòng tài chính, phòng công tác sinh viên, cố vấn học tập, trưởng khoa và sinh viên portal. Mỗi nhóm được cấp quyền khác nhau và thao tác trên các phân hệ tương ứng.

### 4.2.1 Quy trình nghiệp vụ tổng thể

Quy trình vận hành chính của hệ thống gồm các bước:

1. Quản trị viên hoặc phòng đào tạo tạo dữ liệu nền: khoa, bộ môn, ngành, môn học, năm học, học kỳ.
2. Phòng đào tạo tạo hồ sơ sinh viên, lớp hành chính, lớp học phần và thời khóa biểu.
3. Phòng đào tạo mở đợt đăng ký và tạo các lớp môn học.
4. Sinh viên đăng nhập portal để đăng ký môn.
5. Hệ thống kiểm tra điều kiện đăng ký: trạng thái sinh viên, thời gian, học kỳ, trùng môn, môn tiên quyết, tín chỉ và số chỗ.
6. Giảng viên điểm danh, nhập điểm và theo dõi lớp phụ trách.
7. Hệ thống tổng hợp bảng điểm, GPA và trạng thái đạt/không đạt.
8. Phòng tài chính tạo học phí và hóa đơn theo học kỳ.
9. Sinh viên xem điểm, điểm danh, học phí, thời khóa biểu và gửi yêu cầu hành chính.
10. Phòng ban xử lý giấy chứng nhận, NVQS, khảo sát, góp ý và điểm rèn luyện.
11. Admin hoặc phòng ban xem dashboard, in báo cáo.

### 4.2.2 Use Case tổng thể

```mermaid
flowchart TB
    Admin((Admin SMS))
    Academic((Phòng Đào tạo))
    Lecturer((Giảng viên))
    Finance((Phòng Tài chính))
    Affairs((Phòng CTSV))
    Advisor((Cố vấn HT))
    Dean((Trưởng khoa))
    Student((Sinh viên))

    UC1[Quản lý dữ liệu nền]
    UC2[Quản lý hồ sơ sinh viên]
    UC3[Quản lý lớp & TKB]
    UC4[Đăng ký môn]
    UC5[Điểm danh]
    UC6[Nhập điểm & bảng điểm]
    UC7[Học phí & hóa đơn]
    UC8[Giấy chứng nhận]
    UC9[BHYT, cư trú, NVQS]
    UC10[Rèn luyện]
    UC11[Khảo sát & góp ý]
    UC12[Thông báo]
    UC13[Dashboard & báo cáo]
    UC14[Portal học vụ]

    Admin --> UC1
    Admin --> UC13
    Academic --> UC1
    Academic --> UC2
    Academic --> UC3
    Academic --> UC4
    Academic --> UC6
    Lecturer --> UC5
    Lecturer --> UC6
    Finance --> UC7
    Affairs --> UC8
    Affairs --> UC9
    Affairs --> UC11
    Advisor --> UC10
    Dean --> UC10
    Student --> UC14
    Student --> UC4
    Student --> UC8
    Student --> UC9
    Student --> UC11
```

**Hình 4.2. Use Case tổng thể**  
**Giải thích:** Sơ đồ thể hiện actor và nhóm chức năng chính.  
**Ý nghĩa:** Xác định phạm vi triển khai của hệ thống trong đồ án.  
**Vai trò:** Là cơ sở ánh xạ actor sang group bảo mật và menu Odoo.  
**Luồng xử lý:** Người dùng đăng nhập, Odoo kiểm tra group, sau đó hiển thị menu/action tương ứng.

### 4.2.3 Luồng đăng ký môn trên portal

Đăng ký môn là nghiệp vụ tiêu biểu vì đi qua cả portal controller, model ORM, constraint và database. Sinh viên không thao tác trực tiếp trên backend mà dùng route portal `/my/academic/registration`.

```mermaid
flowchart TD
    A[Bắt đầu] --> B[Sinh viên đăng nhập portal]
    B --> C[Mở trang đăng ký môn]
    C --> D{Có đợt đăng ký mở?}
    D -- Không --> E[Thông báo không có đợt mở]
    D -- Có --> F[Hiển thị lớp môn học]
    F --> G[Sinh viên chọn đăng ký]
    G --> H[Controller tạo univ.sms.registration]
    H --> I{Kiểm tra trạng thái sinh viên}
    I -- Không hợp lệ --> X[Trả lỗi]
    I -- Hợp lệ --> J{Kiểm tra thời gian và học kỳ}
    J -- Không hợp lệ --> X
    J -- Hợp lệ --> K{Kiểm tra trùng môn}
    K -- Trùng --> X
    K -- Không trùng --> L{Kiểm tra tiên quyết}
    L -- Thiếu --> X
    L -- Đủ --> M{Kiểm tra tín chỉ và số chỗ}
    M -- Không đạt --> X
    M -- Đạt --> N[Lưu đăng ký trạng thái registered]
    N --> O[Cập nhật danh sách đã đăng ký]
    E --> Z[Kết thúc]
    X --> Z
    O --> Z
```

**Hình 4.3. Activity đăng ký môn học**  
**Giải thích:** Mô tả điều kiện kiểm tra trước khi tạo đăng ký môn.  
**Ý nghĩa:** Phản ánh trực tiếp các `@api.constrains` trong `registration.py`.  
**Vai trò:** Giúp kiểm thử luồng thành công và các nhánh lỗi.  
**Luồng xử lý:** Portal gọi controller, controller tạo model, model tự kiểm tra ràng buộc.

```mermaid
sequenceDiagram
    actor SV as Sinh viên
    participant Portal as portal.py
    participant Reg as univ.sms.registration
    participant Offering as univ.sms.course.offering
    participant Exam as univ.sms.exam.result
    participant DB as PostgreSQL

    SV->>Portal: JSON /my/academic/registration/add
    Portal->>DB: Tìm sinh viên theo partner_id
    Portal->>DB: Tìm đợt đăng ký open
    Portal->>Reg: create(student_id, offering_id, period_id)
    Reg->>Offering: Kiểm tra học kỳ, số chỗ
    Reg->>Exam: Kiểm tra môn tiên quyết đã đạt
    Reg->>DB: Lưu bản ghi đăng ký
    Reg-->>Portal: Success hoặc ValidationError
    Portal-->>SV: JSON success/error
```

**Hình 4.4. Sequence đăng ký môn học trên portal**  
**Giải thích:** Mô tả tương tác giữa sinh viên, controller, model và database.  
**Ý nghĩa:** Cho thấy business logic nằm chủ yếu ở model, controller chỉ điều phối request.  
**Vai trò:** Hỗ trợ debug khi sinh viên không đăng ký được môn.  
**Luồng xử lý:** Request JSON được xử lý bởi route portal, sau đó ORM gọi constraint của model đăng ký.

## 4.3 Thiết kế cơ sở dữ liệu và model ORM

Thiết kế dữ liệu của hệ thống dựa trên ORM của Odoo. Mỗi class Python kế thừa `models.Model` tương ứng một model Odoo; nếu có `_name`, Odoo tạo bảng PostgreSQL tương ứng bằng cách thay dấu chấm bằng dấu gạch dưới. Ví dụ `univ.sms.student` tương ứng bảng `univ_sms_student`.

### 4.3.1 ERD tổng quát

```mermaid
erDiagram
    univ_sms_faculty ||--o{ univ_sms_department : has
    univ_sms_department ||--o{ univ_sms_program : has
    univ_sms_academic_year ||--o{ univ_sms_term : has
    univ_sms_program ||--o{ univ_sms_student : enrolls
    univ_sms_home_class ||--o{ univ_sms_student : contains
    univ_sms_student ||--o{ univ_sms_enrollment : has
    univ_sms_subject ||--o{ univ_sms_enrollment : selected
    univ_sms_class ||--o{ univ_sms_enrollment : contains
    univ_sms_class ||--o{ univ_sms_timetable : scheduled
    univ_sms_class ||--o{ univ_sms_attendance_sheet : has
    univ_sms_attendance_sheet ||--o{ univ_sms_attendance_line : includes
    univ_sms_exam ||--o{ univ_sms_exam_result : has
    univ_sms_student ||--o{ univ_sms_exam_result : receives
    univ_sms_student ||--o{ univ_sms_fee : pays
    univ_sms_fee ||--o{ univ_sms_fee_invoice : invoices
    univ_sms_registration_period ||--o{ univ_sms_registration : opens
    univ_sms_course_offering ||--o{ univ_sms_registration : target
```

**Hình 4.5. ERD dữ liệu đào tạo và sinh viên**  
**Giải thích:** ERD biểu diễn các bảng và quan hệ chính trong PostgreSQL.  
**Ý nghĩa:** Cho thấy các khóa ngoại cốt lõi phát sinh từ field `Many2one`.  
**Vai trò:** Hỗ trợ thiết kế truy vấn, báo cáo và kiểm thử dữ liệu.  
**Luồng xử lý:** Dữ liệu nền liên kết xuống sinh viên, lớp, đăng ký, điểm và học phí.

### 4.3.2 Nhóm bảng dữ liệu chính

| Nhóm dữ liệu | Model tiêu biểu | Bảng PostgreSQL | Vai trò |
|---|---|---|---|
| Dữ liệu nền | `univ.sms.faculty`, `univ.sms.department`, `univ.sms.program`, `univ.sms.subject` | `univ_sms_faculty`, `univ_sms_department`, `univ_sms_program`, `univ_sms_subject` | Cấu trúc đào tạo |
| Thời gian học | `univ.sms.academic.year`, `univ.sms.term` | `univ_sms_academic_year`, `univ_sms_term` | Năm học, học kỳ |
| Sinh viên | `univ.sms.student`, `univ.sms.home.class`, `univ.sms.enrollment` | `univ_sms_student`, `univ_sms_home_class`, `univ_sms_enrollment` | Hồ sơ, lớp hành chính, đăng ký học |
| Lớp học | `univ.sms.class`, `univ.sms.timetable` | `univ_sms_class`, `univ_sms_timetable` | Lớp học phần, thời khóa biểu |
| Điểm danh | `univ.sms.attendance.sheet`, `univ.sms.attendance.line` | `univ_sms_attendance_sheet`, `univ_sms_attendance_line` | Buổi học, trạng thái chuyên cần |
| Thi và điểm | `univ.sms.exam`, `univ.sms.exam.result`, `univ.sms.transcript` | `univ_sms_exam`, `univ_sms_exam_result`, `univ_sms_transcript` | Kỳ thi, điểm, bảng điểm |
| Tài chính | `univ.sms.fee`, `univ.sms.fee.invoice` | `univ_sms_fee`, `univ_sms_fee_invoice` | Học phí và hóa đơn |
| Đăng ký môn | `univ.sms.registration.period`, `univ.sms.course.offering`, `univ.sms.registration` | `univ_sms_registration_period`, `univ_sms_course_offering`, `univ_sms_registration` | Đợt đăng ký, lớp mở, phiếu đăng ký |

Mỗi bảng Odoo đều có khóa chính `id` và các cột hệ thống như `create_uid`, `create_date`, `write_uid`, `write_date`. Các field `Many2one` tạo cột khóa ngoại dạng `<field>_id`. Các ràng buộc duy nhất được khai báo bằng `_sql_constraints`.

### 4.3.3 Model, field và quan hệ ORM

Các model được thiết kế theo đúng phong cách Odoo: dữ liệu nghiệp vụ đặt trong model, field mô tả dữ liệu và relation thể hiện quan hệ giữa bảng. Ví dụ model sinh viên có các nhóm field: mã sinh viên, thông tin cá nhân, liên hệ, gia đình, học vụ, trạng thái và quan hệ enrollment.

| Loại field | Ví dụ trong source | Ý nghĩa |
|---|---|---|
| `fields.Char` | `student_code`, `id_number`, `personal_email` | Chuỗi ký tự |
| `fields.Selection` | `state`, `gender`, `training_system` | Danh sách trạng thái/giá trị cố định |
| `fields.Many2one` | `program_id`, `home_class_id`, `term_id` | Khóa ngoại đến model khác |
| `fields.One2many` | `enrollment_ids`, `line_ids`, `invoice_ids` | Quan hệ ngược từ model con |
| `fields.Many2many` | `program_ids`, `prerequisite_ids` | Quan hệ nhiều-nhiều |
| `fields.Float` | `credit`, `score`, `total_amount` | Số thực |
| `fields.Monetary` | Dùng trong nghiệp vụ học phí/hóa đơn nếu cần tiền tệ | Giá trị tiền |

Một số quan hệ quan trọng:

- `univ.sms.department.faculty_id` liên kết bộ môn với khoa.
- `univ.sms.program.department_id` liên kết ngành với bộ môn.
- `univ.sms.student.program_id` liên kết sinh viên với ngành.
- `univ.sms.student.partner_id` liên kết sinh viên với `res.partner`.
- `univ.sms.enrollment.student_id` liên kết lịch sử học với sinh viên.
- `univ.sms.class` liên kết lớp học phần với môn, học kỳ, giảng viên.
- `univ.sms.registration.offering_id` liên kết phiếu đăng ký với lớp môn học mở.
- `univ.sms.exam.result.student_id` liên kết kết quả thi với sinh viên.
- `univ.sms.fee.student_id` liên kết học phí với sinh viên.

### 4.3.4 Constraint, computed field và onchange

Ràng buộc dữ liệu được đặt ở cả SQL constraint và Python constraint. SQL constraint đảm bảo tính duy nhất ở cấp database, còn `@api.constrains` xử lý điều kiện nghiệp vụ phức tạp.

| Model | Constraint | Ý nghĩa |
|---|---|---|
| `univ.sms.faculty` | `unique(code)` | Mã khoa duy nhất |
| `univ.sms.department` | `unique(code)` | Mã bộ môn duy nhất |
| `univ.sms.program` | `unique(code)` | Mã ngành duy nhất |
| `univ.sms.subject` | `unique(code)` | Mã môn duy nhất |
| `univ.sms.student` | `unique(student_code)` | MSSV duy nhất |
| `univ.sms.student` | `unique(id_number)` | CCCD/CMND duy nhất |
| `univ.sms.enrollment` | `unique(student_id, subject_id, term_id)` | Không trùng môn cùng kỳ |
| `univ.sms.registration` | `unique(student_id, offering_id)` | Không đăng ký trùng lớp môn học |
| `univ.sms.exam.result` | `unique(exam_id, student_id)` | Một kết quả cho mỗi kỳ thi/sinh viên |

Computed field chính gồm `school_email`, `student_count`, `enrollment_count`, `absence_rate`, `is_passed`, `term_gpa`, `cumulative_gpa`, `total_credits`, `total_amount`, `paid_amount`, `remaining_amount`, `available_seats`, `self_total`, `advisor_total`, `final_total`. Các field này giúp giảm thao tác nhập liệu và tự động tổng hợp dữ liệu theo nghiệp vụ.

`@api.onchange('period_id')` trong `univ.sms.registration` được dùng để xóa `offering_id` khi đổi đợt đăng ký. Mục đích là tránh trường hợp người dùng chọn lớp môn học thuộc học kỳ cũ sau khi đã thay đổi kỳ đăng ký.

## 4.4 Bảo mật, phân quyền và kiểm soát dữ liệu

Hệ thống sử dụng security chuẩn của Odoo gồm nhóm người dùng, access rights và record rules. Thiết kế này giúp phân tách người dùng backend theo phòng ban và giới hạn dữ liệu portal theo sinh viên hiện tại.

### 4.4.1 Nhóm người dùng nghiệp vụ

Các group nghiệp vụ được khai báo trong `univ_sms_base/security/security_groups.xml` và `security_groups_v2.xml`. Nhóm `group_univ_admin` có quyền cao nhất, kế thừa nhóm phòng đào tạo; phòng đào tạo kế thừa nhóm giảng viên trong file group cơ bản.

```xml
<record id="group_univ_lecturer" model="res.groups">
    <field name="name">Giảng viên</field>
    <field name="category_id" ref="module_category_university"/>
</record>

<record id="group_univ_academic_officer" model="res.groups">
    <field name="name">Cán bộ Phòng đào tạo</field>
    <field name="category_id" ref="module_category_university"/>
    <field name="implied_ids" eval="[(4, ref('group_univ_lecturer'))]"/>
</record>
```

| Group | Vai trò |
|---|---|
| `group_univ_admin` | Quản trị toàn hệ thống SMS |
| `group_univ_academic_officer` | Phòng đào tạo |
| `group_univ_lecturer` | Giảng viên |
| `group_univ_finance_office` | Phòng tài chính |
| `group_univ_student_affairs_office` | Phòng công tác sinh viên |
| `group_univ_advisor` | Cố vấn học tập |
| `group_univ_dean` | Trưởng khoa |
| `base.group_portal` | Sinh viên portal |

### 4.4.2 Access rights và record rules

Access rights được khai báo trong `security/ir.model.access.csv` của từng module. Ví dụ module đăng ký môn cấp quyền khác nhau cho admin, phòng đào tạo, giảng viên và portal:

```csv
access_registration_admin,registration.admin,model_univ_sms_registration,univ_sms_base.group_univ_admin,1,1,1,1
access_registration_officer,registration.officer,model_univ_sms_registration,univ_sms_base.group_univ_academic_officer,1,1,1,0
access_registration_portal,registration.portal,model_univ_sms_registration,base.group_portal,1,1,1,0
```

Record rules giới hạn dữ liệu theo người dùng. Nhóm portal chỉ được xem dữ liệu có `student_id.partner_id = user.partner_id`. Cách làm này đặc biệt quan trọng vì sinh viên không được xem điểm, học phí, điểm danh hoặc giấy chứng nhận của sinh viên khác.

| Nghiệp vụ | Record rule chính | Mục đích |
|---|---|---|
| Enrollment | `student_id.partner_id = user.partner_id` | Sinh viên xem học phần của mình |
| Attendance | `student_id.partner_id = user.partner_id` | Sinh viên xem chuyên cần của mình |
| Fee/Invoice | `student_id.partner_id = user.partner_id` | Sinh viên xem công nợ của mình |
| Registration | `student_id.partner_id = user.partner_id` | Sinh viên quản lý đăng ký của mình |
| Certificate | `student_id.partner_id = user.partner_id` | Sinh viên xem yêu cầu giấy của mình |
| Conduct | `student_id.partner_id = user.partner_id` | Sinh viên xem điểm rèn luyện của mình |

### 4.4.3 Nhận xét bảo mật

Thiết kế security hiện phù hợp với phạm vi đồ án. Tuy nhiên controller portal có dùng `sudo()` ở một số route để đảm bảo demo hoạt động ổn định, sau đó tự lọc theo `student_id`. Khi triển khai production, nên giảm `sudo()` hoặc bổ sung kiểm tra domain nghiêm ngặt hơn để hạn chế rủi ro truy cập vượt quyền.

## 4.5 Giao diện, menu, action, portal và hình ảnh minh họa

Giao diện của hệ thống được xây dựng chủ yếu bằng XML view của Odoo. Backend dùng tree, form, search, kanban, graph và pivot view. Portal dùng QWeb template và controller HTTP/JSON. Không có JavaScript custom trong source code hiện tại.

### 4.5.1 Backend view, action và menu

Mỗi phân hệ backend thường gồm view XML, action `ir.actions.act_window` và menuitem. Ví dụ màn hình sinh viên khai báo action:

```xml
<record id="action_univ_sms_student" model="ir.actions.act_window">
    <field name="name">Sinh viên</field>
    <field name="res_model">univ.sms.student</field>
    <field name="view_mode">tree,form</field>
    <field name="search_view_id" ref="view_univ_sms_student_search"/>
    <field name="context">{'search_default_studying': 1}</field>
</record>
```

Tree view phục vụ tra cứu nhanh, form view phục vụ nhập liệu và xử lý workflow, search view phục vụ lọc/nhóm dữ liệu. Kanban được dùng ở một số dữ liệu nền như Khoa. Graph/pivot được dùng ở dashboard.

### 4.5.2 Portal sinh viên

Portal nằm trong module `univ_sms_portal`, controller kế thừa `CustomerPortal`. Các route chính gồm landing `/university`, form đăng ký sinh viên `/student/register`, dashboard học vụ `/my/academic`, các trang transcript, attendance, fees, registration, timetable, certificates, affairs, conduct, surveys và feedback.

```python
class UnivSmsPortal(CustomerPortal):

    @route(['/my/academic'], type='http', auth='user', website=True)
    def portal_academic_home(self, **kw):
        student = self._get_student()
        return request.render('univ_sms_portal.portal_academic_home', {
            'student': student,
            'page_name': 'academic_home',
        })
```

Portal giúp sinh viên tự phục vụ các nghiệp vụ cá nhân thay vì phải truy cập backend. Đây là điểm khác biệt quan trọng giữa người dùng nội bộ và sinh viên.

### 4.5.3 API nội bộ và các thành phần không áp dụng

Source code không có REST API riêng. Route JSON chính là:

```python
@route(['/my/academic/registration/add'], type='json', auth='user', website=True)
def portal_registration_add(self, offering_id=None, **kw):
```

Route này nhận `offering_id`, tìm sinh viên hiện tại, tìm đợt đăng ký mở và tạo bản ghi `univ.sms.registration`. Ngoài route JSON phục vụ portal, hệ thống không có API public độc lập.

Các thành phần không áp dụng theo source code:

| Thành phần | Kết luận | Căn cứ |
|---|---|---|
| Wizard | Không áp dụng | Không có thư mục `wizard/`, không có `models.TransientModel` |
| Calendar view | Không áp dụng | Không có XML calendar view |
| Cron/Scheduler | Không áp dụng | Không có khai báo `ir.cron` |
| JavaScript custom | Không áp dụng | Không có file `.js` |
| REST API riêng | Không áp dụng | Chỉ có route HTTP/JSON cho portal |

### 4.5.4 Danh mục hình ảnh giao diện minh họa

Các screenshot đã được chụp trực tiếp từ Odoo đang chạy tại `http://localhost:8069` và lưu trong thư mục `docs/screenshots/`. Bộ hình bao phủ login, landing, portal, menu backend, list view, form view, dashboard, report, import và export.

{{SCREENSHOT_TABLE}}

## 4.6 Business logic, giải thuật và source code tiêu biểu

Business logic của hệ thống được đặt chủ yếu trong Python model. Đây là cách thiết kế đúng trong Odoo vì controller hoặc button chỉ kích hoạt thao tác, còn model chịu trách nhiệm kiểm tra nghiệp vụ, cập nhật trạng thái và bảo toàn dữ liệu.

### 4.6.1 Manifest và cấu trúc khai báo module

Manifest là điểm vào của mỗi module. Ví dụ module `univ_sms_registration`:

```python
{
    'name': 'University SMS - Registration',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'depends': ['base', 'mail', 'univ_sms_base', 'univ_sms_student', 'univ_sms_class', 'univ_sms_exam'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'views/registration_period_views.xml',
        'views/course_offering_views.xml',
        'views/registration_views.xml',
        'views/elective_wish_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
}
```

Manifest cho Odoo biết module phụ thuộc những module nào và cần nạp file nào khi cài đặt. Nếu thiếu dependency hoặc thiếu file data, module có thể lỗi khi cài.

### 4.6.2 Kế thừa `res.partner` và sinh mã sinh viên

Model sinh viên là ví dụ rõ nhất về kết hợp xây mới và kế thừa:

```python
class UnivSmsStudent(models.Model):
    _name = 'univ.sms.student'
    _description = 'Sinh viên'
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'student_code'
```

`_inherits` cho phép `univ.sms.student` dùng lại dữ liệu liên hệ của `res.partner`. Trong khi đó `_inherit = ['mail.thread', 'mail.activity.mixin']` giúp hồ sơ sinh viên có chatter và activity.

Mã sinh viên được sinh tự động bằng sequence:

```xml
<record id="seq_student_code" model="ir.sequence">
    <field name="name">Mã số sinh viên</field>
    <field name="code">univ.sms.student</field>
    <field name="padding">4</field>
    <field name="number_next">1</field>
    <field name="number_increment">1</field>
</record>
```

Python `create()` ghép năm, mã ngành và số thứ tự:

```python
@api.model_create_multi
def create(self, vals_list):
    for vals in vals_list:
        if vals.get('student_code', 'New') == 'New':
            seq_num = self.env['ir.sequence'].next_by_code('univ.sms.student') or '0000'
            year = str(fields.Date.today().year)[2:]
            program = self.env['univ.sms.program'].browse(vals.get('program_id'))
            prog_code = (program.code or 'SV')[:5].upper() if program else 'SV'
            vals['student_code'] = f"{year}{prog_code}{seq_num}"
    return super().create(vals_list)
```

Giải thuật: khi tạo hồ sơ, nếu `student_code` còn là `New`, hệ thống lấy sequence, lấy hai số cuối của năm hiện tại, lấy mã ngành và ghép thành MSSV. Sau khi tạo, hàm `write()` không cho sửa MSSV để bảo toàn định danh.

### 4.6.3 Giải thuật đăng ký môn

Đăng ký môn có nhiều constraint để bảo đảm dữ liệu hợp lệ. Các điều kiện gồm sinh viên phải đang học, đợt đăng ký phải mở, lớp môn học đúng học kỳ, không trùng môn, đủ tiên quyết, không vượt tín chỉ và còn chỗ.

```python
@api.constrains('period_id', 'offering_id', 'state')
def _check_period_and_offering(self):
    now = fields.Datetime.now()
    for rec in self:
        if rec.state == 'cancelled' or not rec.period_id or not rec.offering_id:
            continue
        if rec.period_id.state != 'open':
            raise ValidationError(_('Đợt đăng ký chưa mở hoặc đã đóng.'))
        if rec.period_id.date_start and now < rec.period_id.date_start:
            raise ValidationError(_('Đợt đăng ký chưa tới thời gian bắt đầu.'))
        if rec.period_id.date_end and now > rec.period_id.date_end:
            raise ValidationError(_('Đợt đăng ký đã hết hạn.'))
        if rec.offering_id.term_id != rec.period_id.term_id:
            raise ValidationError(_('Lớp môn học phải thuộc đúng học kỳ của đợt đăng ký.'))
```

Kiểm tra môn tiên quyết:

```python
@api.constrains('offering_id', 'student_id')
def _check_prerequisite(self):
    for rec in self:
        prereqs = rec.offering_id.subject_id.prerequisite_ids
        if prereqs:
            passed = self.env['univ.sms.exam.result'].search([
                ('student_id', '=', rec.student_id.id),
                ('subject_id', 'in', prereqs.ids),
                ('is_passed', '=', True),
            ]).mapped('subject_id')
            missing = prereqs - passed
            if missing:
                raise ValidationError(
                    _('Chưa hoàn thành môn tiên quyết: %s') %
                    ', '.join(missing.mapped('name')))
```

Nhận xét: logic đăng ký môn được đặt ở model nên dù bản ghi được tạo từ backend hay portal, các ràng buộc vẫn được áp dụng nhất quán.

### 4.6.4 Giải thuật điểm danh, điểm và học phí

Điểm danh dùng button method để tải sinh viên từ enrollment vào phiếu:

```python
def action_load_students(self):
    self.ensure_one()
    if self.state == 'confirmed':
        raise ValidationError('Không thể sửa phiếu đã xác nhận!')
    enrollments = self.env['univ.sms.enrollment'].search([
        ('class_id', '=', self.class_id.id),
        ('state', '=', 'registered'),
    ])
```

Học phí được tính từ tổng số tín chỉ đã đăng ký trong học kỳ:

```python
@api.depends('student_id', 'term_id')
def _compute_total_credits(self):
    Enrollment = self.env['univ.sms.enrollment']
    for record in self:
        if record.student_id and record.term_id:
            enrollments = Enrollment.search([
                ('student_id', '=', record.student_id.id),
                ('term_id', '=', record.term_id.id),
                ('state', '=', 'registered'),
            ])
            record.total_credits = sum(enr.subject_id.credit for enr in enrollments)
        else:
            record.total_credits = 0
```

Sau đó tổng tiền học phí được tính:

```python
record.total_amount = record.fee_per_credit * record.total_credits
```

Điểm và GPA được tính trong module `univ_sms_exam`. Kết quả thi xác định `is_passed`; bảng điểm tổng hợp điểm học kỳ và tích lũy. Đây là nhóm logic có thể tiếp tục tối ưu khi dữ liệu lớn bằng stored computed field hoặc batch computation.

## 4.7 Báo cáo, dashboard, dữ liệu demo, kiểm thử và hiệu năng

Hệ thống không chỉ có CRUD dữ liệu mà còn có báo cáo PDF, dashboard graph/pivot và dữ liệu demo để trình bày nghiệp vụ hoàn chỉnh.

### 4.7.1 QWeb report và dashboard

Module `univ_sms_report` khai báo các report QWeb:

| File | Report | Model |
|---|---|---|
| `reports/transcript_report.xml` | Bảng điểm | `univ.sms.transcript` |
| `reports/invoice_report.xml` | Hóa đơn học phí | `univ.sms.fee.invoice` |
| `reports/conduct_score_report.xml` | Phiếu điểm rèn luyện | `univ.sms.conduct.score` |
| `reports/certificate_report.xml` | Giấy chứng nhận | `univ.sms.certificate.request` |
| `reports/registration_slip_report.xml` | Phiếu đăng ký môn | `univ.sms.registration` |
| `reports/attendance_sheet_report.xml` | Phiếu điểm danh | `univ.sms.attendance.sheet` |

Dashboard sử dụng graph/pivot/list view:

| Dashboard | Model | View mode |
|---|---|---|
| Dashboard Sinh viên | `univ.sms.student` | `graph,pivot,list` |
| Dashboard Điểm danh | `univ.sms.attendance.sheet` | `graph,pivot,list` |
| Dashboard Điểm thi | `univ.sms.exam.result` | `graph,pivot,list` |
| Dashboard Học phí | `univ.sms.fee.invoice` | `graph,pivot,list` |
| Dashboard Đăng ký môn | `univ.sms.registration` | `graph,pivot,list` |
| Dashboard Rèn luyện | `univ.sms.conduct.score` | `graph,pivot,list` |

### 4.7.2 Dữ liệu demo và tài khoản kiểm thử

Source có các script:

- `addons/seed_university_realistic.py`
- `addons/audit_university_data.py`
- `addons/audit_samples.sql`
- `addons/create_mock_data.py`
- `addons/create_mock_data_v2.py`
- `addons/create_mock_data_v3.py`

Script chính là `seed_university_realistic.py`, tạo dữ liệu realistic gồm khoa, bộ môn, ngành, môn, sinh viên, giảng viên, lớp, thời khóa biểu, điểm danh, điểm thi, học phí, đăng ký môn, giấy chứng nhận, rèn luyện, khảo sát, góp ý, thông báo và tài khoản theo role. Tài khoản demo tiêu biểu gồm `admin.sms`, `dt.nguyenthilan`, `tc.phamquanghuy`, `ctsv.levanhoa`, `gv.tranminhduc`, `sv.nguyenvanan`.

### 4.7.3 Kịch bản kiểm thử nghiệp vụ

| Kịch bản | Dữ liệu vào | Kết quả mong muốn |
|---|---|---|
| Sinh viên đăng ký môn hợp lệ | Sinh viên đang học, đợt mở, còn chỗ | Tạo `univ.sms.registration` trạng thái `registered` |
| Đăng ký khi đợt đóng | `period_id.state != open` | Báo lỗi validation |
| Đăng ký trùng môn trong kỳ | Cùng sinh viên, cùng subject, cùng term | Báo lỗi trùng môn |
| Thiếu môn tiên quyết | Chưa có `exam.result.is_passed` cho prerequisite | Báo lỗi chưa hoàn thành tiên quyết |
| Vượt tín chỉ tối đa | Tổng tín chỉ vượt `period.max_credit` | Báo lỗi vượt tín chỉ |
| Portal xem dữ liệu cá nhân | User portal có `partner_id` gắn sinh viên | Chỉ thấy dữ liệu của sinh viên đó |
| In bảng điểm | Có transcript và transcript line | Mở QWeb report bảng điểm |
| Tính học phí | Có enrollment trong kỳ | `total_amount = fee_per_credit * total_credits` |

### 4.7.4 Nhận xét hiệu năng

Với dữ liệu demo, các computed field và dashboard hiện hoạt động phù hợp. Khi dữ liệu lớn, một số điểm cần tối ưu:

- Một số computed field dùng `search()` trong vòng lặp, ví dụ attendance stats, GPA tích lũy, học phí.
- Portal dùng `sudo().search()` có domain theo sinh viên, nên cần bảo đảm các field như `student_id` được index tốt khi dữ liệu lớn.
- Dashboard graph/pivot dựa trên model gốc; khi dữ liệu tăng mạnh có thể cân nhắc model báo cáo riêng hoặc materialized view.
- Các tác vụ batch như tạo học phí hàng loạt, chốt đăng ký, import điểm nên phát triển thêm wizard hoặc cron trong giai đoạn sau.

## 4.8 Link demo, đánh giá hoàn thiện và kết luận chương

### 4.8.1 Link demo ứng dụng

Hệ thống đang chạy bằng Docker/Odoo local. Các link demo chính:

| Mục demo | URL | Ghi chú |
|---|---|---|
| Backend Odoo | `http://localhost:8069/web` | Đăng nhập quản trị để mở các menu backend |
| Landing page | `http://localhost:8069/university` | Trang công khai giới thiệu và điều hướng |
| Portal học vụ sinh viên | `http://localhost:8069/my/academic` | Sinh viên đăng nhập để xem thông tin cá nhân |
| Form đăng ký sinh viên | `http://localhost:8069/student/register` | Public route để tạo tài khoản/hồ sơ sinh viên |
| Portal đăng ký môn | `http://localhost:8069/my/academic/registration` | Sinh viên đăng ký/hủy môn học |
| Dashboard báo cáo | `http://localhost:8069/web` | Vào menu Dashboards trong backend |

### 4.8.2 Kịch bản demo gợi ý

Khi trình bày trước hội đồng, có thể demo theo thứ tự:

1. Đăng nhập backend bằng `admin.sms`.
2. Mở menu Quản lý sinh viên, xem danh sách sinh viên và form sinh viên.
3. Mở dữ liệu nền: khoa, ngành, môn học, học kỳ.
4. Mở lớp học phần và thời khóa biểu.
5. Đăng nhập portal bằng `sv.nguyenvanan`.
6. Vào `/my/academic/registration`, đăng ký hoặc xem môn đã đăng ký.
7. Xem bảng điểm, điểm danh, học phí trên portal.
8. Quay lại backend, mở dashboard và in QWeb report.

### 4.8.3 Kết luận chương

Chương 4 đã trình bày quá trình xây dựng module quản lý sinh viên trên Odoo theo hướng custom addon. Hệ thống được xây mới về nghiệp vụ nhưng kế thừa hạ tầng chuẩn của Odoo như `res.partner`, `mail.thread`, `CustomerPortal`, QWeb report, action, menu, view, access rights và record rules. Về dữ liệu, hệ thống tổ chức model theo namespace `univ.sms.*`, có quan hệ rõ ràng giữa dữ liệu nền, sinh viên, lớp học, điểm danh, điểm thi, học phí và đăng ký môn. Về giao diện, hệ thống có cả backend và portal, kèm dashboard và báo cáo in ấn.

Các logic quan trọng như sinh mã sinh viên, kiểm tra đăng ký môn, kiểm tra môn tiên quyết, tính học phí và tải danh sách điểm danh được đặt ở tầng model, phù hợp nguyên tắc phát triển Odoo. Bên cạnh các chức năng đã hoàn thiện, một số thành phần như wizard, cron, REST API riêng và JavaScript custom chưa được triển khai trong source hiện tại, nên được ghi nhận là không áp dụng hoặc hướng phát triển tiếp theo.
"""


def extract_screenshot_table(text: str) -> str:
    marker = "## 4.43 Danh mục screenshot giao diện"
    if marker not in text:
        marker = "# 4.40 Danh mục screenshot giao diện"
    if marker not in text:
        return "_Không tìm thấy bảng screenshot trong bản hiện tại._"
    start = text.index(marker)
    section = text[start:].strip()
    lines = section.splitlines()
    # Remove the old heading but keep note/table.
    if lines and "Danh mục screenshot" in lines[0]:
        lines = lines[1:]
    return "\n".join(lines).strip()


def main() -> None:
    text = REPORT.read_text(encoding="utf-8")
    start_marker = "# CHƯƠNG 4. XÂY DỰNG MODULE QUẢN LÝ SINH VIÊN TRÊN NỀN TẢNG ODOO"
    end_marker = "# CHƯƠNG 5. ĐÁNH GIÁ HỆ THỐNG VÀ HƯỚNG PHÁT TRIỂN"
    start = text.index(start_marker)
    end = text.index(end_marker)
    screenshot_table = extract_screenshot_table(text[start:end])
    chapter = CH4_TEMPLATE.replace("{{SCREENSHOT_TABLE}}", screenshot_table)
    new_text = text[:start] + chapter + "\n\n\\pagebreak\n\n" + text[end:]
    REPORT.write_text(new_text, encoding="utf-8")
    print(f"rewrote grouped chapter 4 in {REPORT}")


if __name__ == "__main__":
    main()
