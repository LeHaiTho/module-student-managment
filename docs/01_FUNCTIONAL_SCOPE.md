A. DANH SÁCH PHÂN HỆ CHỨC NĂNG (Modules)
univ_sms_base          → Models nền: Faculty, Department, Program, Subject, AcademicYear, Term
univ_sms_student        → Quản lý hồ sơ sinh viên, Enrollment
univ_sms_class          → Lớp học, Thời khóa biểu (Timetable)
univ_sms_attendance      → Điểm danh
univ_sms_exam           → Kỳ thi, Điểm số, Bảng điểm (Transcript)
univ_sms_fee            → Học phí, Hóa đơn
univ_sms_portal          → Cổng tra cứu sinh viên (Website/Portal frontend)
univ_sms_report          → Báo cáo PDF (QWeb), Dashboard
B. CHỨC NĂNG THEO ĐỐI TƯỢNG NGƯỜI DÙNG
1. Phòng đào tạo / Admin (Backend Odoo)

CRUD: Sinh viên, Giảng viên, Khoa/Bộ môn, Ngành, Môn học, Lớp, Năm học/Học kỳ
Quản lý tuyển sinh (Admission) → Enrollment
Sắp thời khóa biểu, phân lớp
Cấu hình kỳ thi, nhập điểm
Quản lý học phí, xuất hóa đơn
Báo cáo: danh sách lớp, bảng điểm, tỷ lệ điểm danh, công nợ học phí

2. Giảng viên (Backend Odoo - quyền hạn chế)

Xem danh sách lớp mình dạy
Điểm danh sinh viên trong lớp
Nhập điểm thành phần/cuối kỳ cho môn mình dạy
Xem hồ sơ sinh viên (read-only, chỉ sinh viên thuộc lớp mình)

3. Sinh viên (Portal - Frontend tra cứu)

Đăng nhập bằng email/portal account
Xem thông tin cá nhân, mã số sinh viên
Xem thời khóa biểu cá nhân
Xem điểm danh của bản thân (theo môn)
Xem bảng điểm (Transcript) + tải PDF
Xem tình trạng học phí (đã đóng/còn nợ) + tải hóa đơn PDF
Xem thông báo từ phòng đào tạo

## ✅ CONFIRMED ANSWERS

| # | Question | Answer |
|---|----------|--------|
| Q1 | Org structure | Trường → Khoa → Bộ môn → Ngành (4 levels) |
| Q2 | MSSV format | Auto-increment sequential (sinh tự động, tăng dần) |
| Q3 | Grading system | Scale 10. GPA semester: e.g. 9.30 (Xuất sắc), semester credits: 15, cumulative GPA: 8.03, cumulative credits: 150 |
| Q4 | Fee calculation | Per credit (tính theo tín chỉ) |
| Q5 | Portal registration | Admin creates account, sends activation link |
| Q6 | Online payment | Placeholder/sample data only, don't over-engineer |
| Q7 | i18n | Vietnamese only |
| Q8 | Lecturer model | Not a focus area, feature under development — minimal impl |