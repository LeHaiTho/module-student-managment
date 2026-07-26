# Tài liệu nghiệp vụ và hướng dẫn sử dụng hệ thống University SMS

Phiên bản tài liệu: 1.0  
Cập nhật: 08/07/2026  
Phạm vi: Các module Odoo `univ_sms_*` trong hệ thống quản lý sinh viên đại học.

## 1. Mục đích tài liệu

Tài liệu này mô tả đầy đủ nghiệp vụ, chức năng, luồng xử lý, phân quyền và cách sử dụng hệ thống University SMS. Nội dung được viết cho 4 nhóm người dùng chính:

- Quản trị viên hệ thống SMS.
- Cán bộ Phòng Đào tạo.
- Giảng viên, cố vấn học tập, trưởng khoa.
- Phòng Tài chính, Phòng Công tác Sinh viên.
- Sinh viên sử dụng cổng portal.

Tài liệu có thể dùng làm:

- Tài liệu nghiệp vụ khi thuyết trình hoặc bảo vệ đồ án.
- User guide cho người dùng cuối.
- Checklist kiểm thử chức năng.
- Tài liệu bàn giao vận hành hệ thống.

## 2. Tổng quan hệ thống

University SMS là hệ thống quản lý sinh viên xây dựng trên Odoo 17. Hệ thống quản lý dữ liệu đào tạo theo mô hình trường đại học, gồm hồ sơ sinh viên, khoa, bộ môn, ngành, môn học, lớp học phần, thời khóa biểu, điểm danh, điểm thi, học phí, đăng ký môn học, giấy xác nhận, công tác sinh viên, rèn luyện, khảo sát, góp ý, thông báo và dashboard.

Hệ thống có 2 khu vực sử dụng chính:

- Backend Odoo: dành cho admin, phòng ban, giảng viên, cán bộ.
- Student Portal: dành cho sinh viên tra cứu và thực hiện nghiệp vụ cá nhân.

## 3. Link truy cập hệ thống

| Khu vực | Link | Người dùng |
|---|---|---|
| Trang giới thiệu/landing | `http://localhost:8069/university` | Công khai hoặc user đã đăng nhập |
| Backend Odoo | `http://localhost:8069/web` | Admin, phòng ban, giảng viên, cố vấn, trưởng khoa |
| Trang học vụ sinh viên | `http://localhost:8069/my/academic` | Sinh viên portal |
| Đăng ký môn học | `http://localhost:8069/my/academic/registration` | Sinh viên portal |
| Thời khóa biểu | `http://localhost:8069/my/academic/timetable` | Sinh viên portal |
| Bảng điểm | `http://localhost:8069/my/academic/transcript` | Sinh viên portal |
| Điểm danh | `http://localhost:8069/my/academic/attendance` | Sinh viên portal |
| Học phí | `http://localhost:8069/my/academic/fees` | Sinh viên portal |
| Giấy chứng nhận | `http://localhost:8069/my/academic/certificates` | Sinh viên portal |
| Công tác sinh viên | `http://localhost:8069/my/academic/student-affairs` | Sinh viên portal |
| Điểm rèn luyện | `http://localhost:8069/my/academic/conduct` | Sinh viên portal |
| Khảo sát | `http://localhost:8069/my/academic/surveys` | Sinh viên portal |
| Góp ý | `http://localhost:8069/my/academic/feedback` | Sinh viên portal |

## 4. Tài khoản mẫu sau khi seed dữ liệu

Mật khẩu mặc định của các tài khoản mẫu là `123456`.

| Role | Tài khoản mẫu | Mục đích |
|---|---|---|
| Quản trị viên SMS | `admin.sms` | Quản trị toàn bộ hệ thống |
| Phòng Đào tạo | `dt.nguyenthilan` | Quản lý học vụ, lớp, môn, đăng ký, điểm |
| Phòng Tài chính | `tc.phamquanghuy` | Quản lý học phí, hóa đơn |
| Phòng Công tác SV | `ctsv.levanhoa` | Quản lý BHYT, cư trú, NVQS, giấy tờ, khảo sát |
| Giảng viên | `gv.tranminhduc` | Quản lý lớp, điểm danh, điểm thi được phân công |
| Sinh viên | `sv.nguyenvanan` | Truy cập portal cá nhân |
| Sinh viên | `sv.tranthibichngoc` | Truy cập portal cá nhân |

Tài khoản demo cũ `sinhvien` và `giangvien` đã được vô hiệu hóa để tránh demo sai nghiệp vụ.

## 5. Danh sách module trong hệ thống

| Module kỹ thuật | Tên nghiệp vụ | Chức năng chính |
|---|---|---|
| `univ_sms_base` | Dữ liệu nền | Khoa, bộ môn, ngành, môn học, năm học, học kỳ, nhóm quyền |
| `univ_sms_student` | Quản lý sinh viên | Hồ sơ sinh viên, lớp hành chính, tra cứu sinh viên, lịch sử học phần |
| `univ_sms_class` | Lớp và thời khóa biểu | Lớp học phần, giảng viên phụ trách, phòng học, lịch học |
| `univ_sms_attendance` | Điểm danh | Phiếu điểm danh, chi tiết có mặt, vắng, đi trễ, có phép |
| `univ_sms_exam` | Thi và điểm | Kỳ thi, kết quả thi, bảng điểm, GPA, xếp loại |
| `univ_sms_fee` | Học phí | Khoản học phí, hóa đơn, trạng thái thanh toán |
| `univ_sms_registration` | Đăng ký môn học | Đợt đăng ký, lớp mở đăng ký, đăng ký, hủy đăng ký, kiểm tra tiên quyết |
| `univ_sms_certificate` | Giấy chứng nhận | Loại giấy, yêu cầu cấp giấy, duyệt, hoàn thành, từ chối |
| `univ_sms_student_affairs` | Công tác sinh viên | BHYT, cư trú, nghĩa vụ quân sự |
| `univ_sms_conduct` | Điểm rèn luyện | Tiêu chí, tự chấm, cố vấn duyệt, khoa duyệt |
| `univ_sms_survey` | Khảo sát | Loại khảo sát, đợt khảo sát, phản hồi sinh viên |
| `univ_sms_feedback` | Góp ý | Sinh viên gửi góp ý, phòng ban tiếp nhận và phản hồi |
| `univ_sms_notification` | Thông báo | Tạo và công bố thông báo cho sinh viên |
| `univ_sms_portal` | Portal sinh viên | Giao diện web cho sinh viên thao tác |
| `univ_sms_report` | Báo cáo và dashboard | Dashboard, biểu mẫu in PDF |

## 6. Phân quyền và vai trò người dùng

### 6.1. Các role chính

| Role | Nhóm kỹ thuật | Mô tả |
|---|---|---|
| Sinh viên | `base.group_portal` | Chỉ xem và thao tác dữ liệu của chính mình qua portal |
| Giảng viên | `group_univ_lecturer` | Xem dữ liệu học vụ, lớp, điểm danh, điểm thi liên quan |
| Cán bộ Phòng Đào tạo | `group_univ_academic_officer` | Quản lý dữ liệu đào tạo, sinh viên, lớp, môn, điểm, đăng ký |
| Phòng Tài chính | `group_univ_finance_office` | Quản lý học phí, hóa đơn, thông báo tài chính |
| Phòng Công tác SV | `group_univ_student_affairs_office` | Quản lý BHYT, cư trú, NVQS, giấy chứng nhận, khảo sát, góp ý |
| Cố vấn học tập | `group_univ_advisor` | Theo dõi sinh viên, rèn luyện, hỗ trợ xét duyệt |
| Trưởng khoa | `group_univ_dean` | Duyệt rèn luyện cấp khoa, theo dõi dữ liệu khoa |
| Quản trị viên SMS | `group_univ_admin` | Có toàn quyền và kế thừa các nhóm nghiệp vụ |

### 6.2. Nguyên tắc phân quyền

- Admin có toàn quyền tạo, sửa, xóa dữ liệu nghiệp vụ.
- Phòng Đào tạo có quyền tạo, sửa phần lớn dữ liệu học vụ nhưng không xóa dữ liệu quan trọng.
- Giảng viên chủ yếu đọc dữ liệu nền, thao tác điểm danh và điểm thi.
- Phòng Tài chính được thao tác học phí, hóa đơn và thông báo liên quan.
- Phòng Công tác SV được thao tác BHYT, cư trú, NVQS, giấy chứng nhận, khảo sát.
- Sinh viên chỉ thao tác dữ liệu của chính sinh viên đang đăng nhập, thông qua record rule theo `partner_id`.

### 6.3. Ma trận chức năng theo role

| Chức năng | Admin | Phòng Đào tạo | Giảng viên | Tài chính | CTSV | CVHT | Trưởng khoa | Sinh viên |
|---|---|---|---|---|---|---|---|---|
| Khoa, bộ môn, ngành, môn học | CRUD | Tạo/Sửa/Xem | Xem | Xem gián tiếp | Xem gián tiếp | Xem | Xem | Không |
| Hồ sơ sinh viên | CRUD | Tạo/Sửa/Xem | Xem | Xem gián tiếp | Xem | Xem | Xem | Xem cá nhân |
| Lớp hành chính | CRUD | Tạo/Sửa/Xem | Xem | Không chính | Xem | Xem | Xem | Xem cá nhân |
| Lớp học phần, TKB | CRUD | Tạo/Sửa/Xem | Xem/Sửa TKB nếu được cấp | Không chính | Không chính | Xem | Xem | Xem TKB cá nhân |
| Điểm danh | CRUD | Tạo/Sửa/Xem | Tạo/Sửa/Xem | Không | Không | Xem | Xem | Xem cá nhân |
| Kỳ thi, điểm | CRUD | Tạo/Sửa/Xem | Tạo/Sửa/Xem | Không | Không | Xem | Xem | Xem cá nhân |
| Học phí | CRUD | Tạo/Sửa/Xem | Xem | Tạo/Sửa/Xem | Không | Không | Không | Xem cá nhân |
| Đăng ký môn | CRUD | Tạo/Sửa/Xem | Xem | Không | Không | Xem | Xem | Đăng ký/Hủy cá nhân |
| Giấy chứng nhận | CRUD | Xem gián tiếp | Xem | Xem nếu liên quan phí | Tạo/Sửa/Xem | Không | Không | Gửi yêu cầu/Xem cá nhân |
| BHYT, cư trú, NVQS | CRUD | Không chính | Không | Không | Tạo/Sửa/Xem | Xem | Xem | Xem/Gửi NVQS cá nhân |
| Rèn luyện | CRUD | Xem | Xem | Không | Tạo/Sửa/Xem | Duyệt CVHT | Duyệt khoa | Xem cá nhân |
| Khảo sát | CRUD | Xem | Xem | Không | Tạo/Sửa/Xem | Xem | Xem | Trả lời khảo sát |
| Góp ý | CRUD | Xử lý/Xem | Không chính | Xử lý/Xem | Xử lý/Xem | Không chính | Không chính | Gửi góp ý/Xem cá nhân |
| Thông báo | CRUD | Tạo/Sửa/Xem | Xem | Tạo/Sửa/Xem | Tạo/Sửa/Xem | Xem | Xem | Xem thông báo |

Ghi chú: CRUD nghĩa là tạo, đọc, sửa, xóa. Các quyền thực tế còn phụ thuộc ACL, record rule và nhóm mà tài khoản được gán.

## 7. Cấu trúc menu backend

Sau khi đăng nhập backend tại `http://localhost:8069/web`, người dùng mở ứng dụng `University SMS`.

### 7.1. Dữ liệu nền

Menu: `University SMS / Dữ liệu nền`

- Khoa.
- Bộ môn.
- Ngành đào tạo.
- Môn học.
- Năm học.
- Học kỳ.

Mục đích: tạo bộ dữ liệu chuẩn trước khi tạo sinh viên, lớp học phần, đăng ký môn và báo cáo.

### 7.2. Quản lý sinh viên

Menu: `University SMS / Sinh viên`

- Hồ sơ sinh viên.
- Tra cứu sinh viên.
- Lớp hành chính.
- Lịch sử học phần.

Mục đích: quản lý toàn bộ vòng đời sinh viên từ nhập học, đang học, bảo lưu, tốt nghiệp đến thôi học.

### 7.3. Lớp học và thời khóa biểu

Menu: `University SMS / Lớp học`

- Lớp học phần.
- Thời khóa biểu.

Mục đích: quản lý lớp môn học, giảng viên phụ trách, lịch học, phòng học, tòa nhà.

### 7.4. Điểm danh

Menu: `University SMS / Điểm danh`

- Phiếu điểm danh.
- Chi tiết điểm danh.

Mục đích: ghi nhận trạng thái tham dự buổi học của sinh viên.

### 7.5. Thi và điểm

Menu: `University SMS / Điểm thi`

- Kỳ thi.
- Kết quả thi.
- Bảng điểm.

Mục đích: tạo kỳ thi, nhập điểm, tổng hợp điểm cuối kỳ, GPA, xếp loại.

### 7.6. Học phí

Menu: `University SMS / Học phí`

- Khoản học phí.
- Hóa đơn học phí.

Mục đích: tính học phí theo số tín chỉ, lập hóa đơn, xác nhận thanh toán.

### 7.7. Đăng ký môn

Menu: `University SMS / Đăng ký môn`

- Đợt đăng ký.
- Lớp môn học.
- Đăng ký môn học.
- Nguyện vọng.

Mục đích: mở đợt đăng ký, cấu hình lớp được đăng ký, ghi nhận sinh viên đăng ký hoặc hủy môn.

### 7.8. Giấy chứng nhận

Menu: `University SMS / Giấy chứng nhận`

- Loại giấy chứng nhận.
- Yêu cầu giấy chứng nhận.

Mục đích: sinh viên gửi yêu cầu, phòng CTSV duyệt và hoàn tất cấp giấy.

### 7.9. Công tác sinh viên

Menu: `University SMS / Công tác SV`

- Bảo hiểm y tế.
- Cư trú/Ngoại trú.
- Nghĩa vụ quân sự.

Mục đích: quản lý thông tin ngoài học vụ của sinh viên.

### 7.10. Rèn luyện

Menu: `University SMS / Rèn luyện`

- Tiêu chí rèn luyện.
- Điểm rèn luyện.

Mục đích: sinh viên tự chấm, cố vấn học tập duyệt, trưởng khoa duyệt.

### 7.11. Khảo sát

Menu: `University SMS / Khảo sát`

- Loại khảo sát.
- Đợt khảo sát.
- Phản hồi khảo sát.

Mục đích: tạo khảo sát và thu thập phản hồi của sinh viên.

### 7.12. Góp ý

Menu: `University SMS / Góp ý`

- Phản hồi và góp ý.

Mục đích: tiếp nhận và xử lý phản ánh của sinh viên.

### 7.13. Thông báo

Menu: `University SMS / Thông báo`

- Danh sách thông báo.

Mục đích: tạo thông báo, ghim thông báo, công bố cho portal.

### 7.14. Dashboard và báo cáo

Menu: `University SMS / Dashboards`

- SV Dashboard.
- Điểm danh Dashboard.
- Điểm thi Dashboard.
- Học phí Dashboard.
- Đăng ký môn Dashboard.
- Rèn luyện Dashboard.

Biểu mẫu báo cáo PDF hiện có:

- Phiếu điểm danh.
- Giấy chứng nhận.
- Điểm rèn luyện.
- Hóa đơn học phí.
- Phiếu đăng ký môn.
- Bảng điểm.

## 8. Quy trình nghiệp vụ tổng thể

Quy trình vận hành chuẩn nên đi theo thứ tự sau:

1. Admin hoặc Phòng Đào tạo tạo dữ liệu nền.
2. Phòng Đào tạo tạo hồ sơ sinh viên và lớp hành chính.
3. Phòng Đào tạo tạo lớp học phần và thời khóa biểu.
4. Phòng Đào tạo mở đợt đăng ký môn.
5. Sinh viên đăng ký môn trên portal.
6. Giảng viên điểm danh theo lớp học phần.
7. Giảng viên hoặc Phòng Đào tạo tạo kỳ thi và nhập điểm.
8. Hệ thống tổng hợp bảng điểm, GPA.
9. Phòng Tài chính tạo học phí và hóa đơn.
10. Sinh viên theo dõi học phí, điểm, điểm danh, thời khóa biểu trên portal.
11. Sinh viên gửi yêu cầu giấy chứng nhận, NVQS, khảo sát, góp ý.
12. Phòng CTSV xử lý các yêu cầu.
13. CVHT và khoa xét điểm rèn luyện.
14. Admin và phòng ban theo dõi dashboard, xuất báo cáo.

## 9. Quy trình dữ liệu nền

### 9.1. Quản lý khoa

Role thực hiện: Admin, Phòng Đào tạo.  
Menu: `University SMS / Dữ liệu nền / Khoa`.

Thông tin cần nhập:

- Mã khoa.
- Tên khoa.
- Trưởng khoa.
- Trạng thái hoạt động.

Quy trình:

1. Vào menu Khoa.
2. Bấm Tạo.
3. Nhập mã khoa, ví dụ `CNTT`.
4. Nhập tên khoa, ví dụ `Khoa Công nghệ thông tin`.
5. Chọn trưởng khoa nếu có.
6. Lưu.

Lưu ý:

- Mã khoa là duy nhất.
- Không nên xóa khoa nếu đã phát sinh bộ môn/ngành; nên ngưng hoạt động nếu cần.

### 9.2. Quản lý bộ môn

Role thực hiện: Admin, Phòng Đào tạo.  
Menu: `University SMS / Dữ liệu nền / Bộ môn`.

Thông tin cần nhập:

- Mã bộ môn.
- Tên bộ môn.
- Khoa quản lý.

Quy trình:

1. Vào Bộ môn.
2. Bấm Tạo.
3. Nhập mã, tên.
4. Chọn khoa chủ quản.
5. Lưu.

### 9.3. Quản lý ngành đào tạo

Role thực hiện: Admin, Phòng Đào tạo.  
Menu: `University SMS / Dữ liệu nền / Ngành đào tạo`.

Thông tin cần nhập:

- Mã ngành.
- Tên ngành.
- Bộ môn quản lý.
- Tổng tín chỉ.
- Thời gian đào tạo.

Quy trình:

1. Vào Ngành đào tạo.
2. Tạo ngành mới.
3. Nhập mã ngành theo quy định, ví dụ `7480103`.
4. Nhập tên ngành, ví dụ `Kỹ thuật phần mềm`.
5. Chọn bộ môn.
6. Nhập tổng tín chỉ và thời gian đào tạo.
7. Lưu.

### 9.4. Quản lý môn học

Role thực hiện: Admin, Phòng Đào tạo.  
Menu: `University SMS / Dữ liệu nền / Môn học`.

Thông tin cần nhập:

- Mã môn học.
- Tên môn học.
- Số tín chỉ.
- Ngành áp dụng.
- Môn tiên quyết nếu có.
- Trạng thái còn áp dụng.

Quy trình:

1. Vào Môn học.
2. Bấm Tạo.
3. Nhập mã môn, ví dụ `IT202`.
4. Nhập tên môn, ví dụ `Lập trình Web`.
5. Nhập tín chỉ.
6. Chọn các ngành được học môn này.
7. Chọn môn tiên quyết nếu môn yêu cầu đã học trước.
8. Lưu.

Ràng buộc:

- Mã môn học là duy nhất.
- Đăng ký môn sẽ kiểm tra môn tiên quyết dựa trên kết quả thi đạt của sinh viên.

### 9.5. Quản lý năm học và học kỳ

Role thực hiện: Admin, Phòng Đào tạo.  
Menu:

- `University SMS / Dữ liệu nền / Năm học`.
- `University SMS / Dữ liệu nền / Học kỳ`.

Quy trình:

1. Tạo năm học, ví dụ `2026-2027`.
2. Nhập ngày bắt đầu và ngày kết thúc năm học.
3. Tạo học kỳ thuộc năm học đó, ví dụ `HK1 2026-2027`.
4. Nhập ngày bắt đầu và ngày kết thúc học kỳ.

Học kỳ được dùng bởi:

- Lớp học phần.
- Đợt đăng ký.
- Điểm thi.
- Bảng điểm.
- Học phí.
- Điểm rèn luyện.

## 10. Quy trình quản lý sinh viên

### 10.1. Tạo hồ sơ sinh viên

Role thực hiện: Admin, Phòng Đào tạo.  
Menu: `University SMS / Sinh viên / Hồ sơ sinh viên`.

Thông tin chính:

- Họ tên.
- Ngày sinh.
- Giới tính.
- CCCD/CMND.
- Email cá nhân.
- Địa chỉ thường trú, tạm trú.
- Ngành học.
- Lớp hành chính.
- Niên khóa nhập học.
- Cố vấn học tập.
- Trạng thái học vụ.

Quy trình:

1. Vào Hồ sơ sinh viên.
2. Bấm Tạo.
3. Nhập thông tin cá nhân.
4. Chọn ngành học.
5. Chọn lớp hành chính.
6. Chọn năm học nhập học.
7. Chọn cố vấn học tập.
8. Lưu.

Ràng buộc:

- MSSV được sinh tự động.
- Không sửa MSSV sau khi đã tạo hồ sơ.
- CCCD/CMND là duy nhất.
- Chỉ sinh viên trạng thái `Đang học` mới được đăng ký môn.

### 10.2. Trạng thái hồ sơ sinh viên

| Trạng thái | Ý nghĩa |
|---|---|
| Hồ sơ mới | Sinh viên mới tạo, chưa xác nhận đang học |
| Đang học | Sinh viên đang học bình thường |
| Bảo lưu | Sinh viên tạm nghỉ/bảo lưu |
| Đã tốt nghiệp | Sinh viên hoàn tất chương trình |
| Bị buộc thôi học | Sinh viên bị xử lý học vụ/kỷ luật |
| Thôi học tự nguyện | Sinh viên tự nguyện thôi học |

### 10.3. Tra cứu sinh viên

Role thực hiện: Admin, Phòng Đào tạo, Giảng viên xem dữ liệu được phân quyền.  
Menu: `University SMS / Sinh viên / Tra cứu sinh viên`.

Mục đích:

- Tìm nhanh sinh viên theo MSSV, tên, ngành, lớp.
- Xem thông tin học vụ, lớp hành chính, liên hệ.
- Không dùng màn này làm nơi nhập liệu chính nếu người dùng chỉ có quyền xem.

### 10.4. Quản lý lớp hành chính

Role thực hiện: Admin, Phòng Đào tạo.  
Menu: `University SMS / Sinh viên / Lớp hành chính`.

Thông tin:

- Mã lớp.
- Tên lớp.
- Ngành.
- Năm học.
- Cố vấn học tập.
- Danh sách sinh viên.

Quy trình:

1. Vào Lớp hành chính.
2. Tạo lớp theo ngành và khóa.
3. Chọn cố vấn học tập.
4. Gán sinh viên vào lớp qua hồ sơ sinh viên.

Ví dụ dữ liệu chuẩn:

- `DH25-7480103-01`: Kỹ thuật phần mềm.
- `DH25-7480201-01`: Công nghệ thông tin.
- `DH25-7340101-01`: Quản trị kinh doanh.

## 11. Quy trình lớp học phần và thời khóa biểu

### 11.1. Tạo lớp học phần

Role thực hiện: Admin, Phòng Đào tạo.  
Menu: `University SMS / Lớp học / Lớp học phần`.

Thông tin:

- Mã lớp học phần.
- Tên lớp.
- Môn học.
- Giảng viên.
- Học kỳ.
- Số sinh viên tối đa.
- Trạng thái mở/đóng.

Quy trình:

1. Vào Lớp học phần.
2. Bấm Tạo.
3. Chọn môn học.
4. Chọn giảng viên.
5. Chọn học kỳ.
6. Nhập sĩ số tối đa.
7. Đặt trạng thái `Mở` nếu lớp còn hoạt động.
8. Lưu.

### 11.2. Tạo thời khóa biểu

Role thực hiện: Admin, Phòng Đào tạo, Giảng viên nếu được cấp quyền.  
Menu: `University SMS / Lớp học / Thời khóa biểu`.

Thông tin:

- Lớp học phần.
- Thứ trong tuần.
- Giờ bắt đầu.
- Giờ kết thúc.
- Phòng học.
- Tòa nhà.

Quy trình:

1. Vào Thời khóa biểu.
2. Bấm Tạo.
3. Chọn lớp học phần.
4. Chọn thứ học.
5. Nhập giờ bắt đầu và giờ kết thúc.
6. Nhập phòng học và tòa nhà.
7. Lưu.

Lưu ý:

- Giờ kết thúc phải sau giờ bắt đầu.
- Sinh viên chỉ thấy thời khóa biểu của các lớp đang đăng ký.

## 12. Quy trình đăng ký môn học

### 12.1. Chuẩn bị đợt đăng ký

Role thực hiện: Admin, Phòng Đào tạo.  
Menu: `University SMS / Đăng ký môn / Đợt đăng ký`.

Thông tin:

- Tên đợt đăng ký.
- Học kỳ áp dụng.
- Ngày giờ bắt đầu.
- Ngày giờ kết thúc.
- Loại đăng ký: chính thức hoặc nguyện vọng.
- Tín chỉ tối thiểu.
- Tín chỉ tối đa.
- Trạng thái: chưa mở, đang mở, đã đóng.

Quy trình:

1. Vào Đợt đăng ký.
2. Tạo đợt mới.
3. Chọn học kỳ.
4. Nhập thời gian bắt đầu, kết thúc.
5. Chọn loại đăng ký.
6. Nhập giới hạn tín chỉ.
7. Bấm Mở khi đến thời gian đăng ký.

### 12.2. Mở lớp môn học cho đăng ký

Role thực hiện: Admin, Phòng Đào tạo.  
Menu: `University SMS / Đăng ký môn / Lớp môn học`.

Thông tin:

- Môn học.
- Học kỳ.
- Giảng viên.
- Lớp tín chỉ.
- Số chỗ tối đa.
- Số đã đăng ký.
- Số chỗ còn lại.
- Môn tiên quyết.

Quy trình:

1. Vào Lớp môn học.
2. Tạo bản ghi mới.
3. Chọn môn học.
4. Chọn học kỳ trùng với đợt đăng ký.
5. Chọn lớp tín chỉ tương ứng.
6. Nhập số chỗ tối đa.
7. Đánh dấu active.
8. Lưu.

### 12.3. Sinh viên đăng ký môn trên portal

Role thực hiện: Sinh viên.  
Link: `http://localhost:8069/my/academic/registration`.

Quy trình:

1. Sinh viên đăng nhập portal.
2. Vào Trang học vụ.
3. Chọn Đăng ký môn học.
4. Xem đợt đăng ký đang mở.
5. Xem danh sách lớp môn học khả dụng.
6. Chọn môn cần đăng ký.
7. Bấm Đăng ký.
8. Hệ thống kiểm tra điều kiện.
9. Nếu hợp lệ, môn xuất hiện trong danh sách đã đăng ký.

### 12.4. Sinh viên hủy môn

Role thực hiện: Sinh viên.  
Link: `http://localhost:8069/my/academic/registration`.

Quy trình:

1. Vào Đăng ký môn học.
2. Xem danh sách môn đã đăng ký.
3. Bấm Hủy ở môn cần hủy.
4. Hệ thống đổi trạng thái đăng ký sang `Đã hủy`.

### 12.5. Ràng buộc đăng ký môn

Hệ thống kiểm tra:

- Sinh viên phải ở trạng thái `Đang học`.
- Đợt đăng ký phải ở trạng thái `Đang mở`.
- Thời gian hiện tại phải nằm trong khoảng bắt đầu và kết thúc.
- Lớp môn học phải thuộc đúng học kỳ của đợt đăng ký.
- Không được đăng ký trùng cùng môn trong cùng học kỳ.
- Phải hoàn thành môn tiên quyết nếu môn có yêu cầu.
- Không vượt quá số tín chỉ tối đa.
- Không vượt quá số chỗ tối đa của lớp môn học.
- Khi xác nhận có thể kiểm tra tín chỉ tối thiểu.

### 12.6. Phòng Đào tạo quản lý đăng ký backend

Role thực hiện: Admin, Phòng Đào tạo.  
Menu: `University SMS / Đăng ký môn / Đăng ký môn học`.

Quy trình:

1. Vào Đăng ký môn học.
2. Lọc theo học kỳ, đợt đăng ký, sinh viên, trạng thái.
3. Kiểm tra danh sách đăng ký.
4. Tạo hộ đăng ký nếu có nghiệp vụ đặc biệt.
5. Hủy đăng ký nếu có yêu cầu hợp lệ.
6. Xác nhận đăng ký khi kết thúc đợt.

Trạng thái đăng ký:

- Nháp.
- Đã đăng ký.
- Đã xác nhận.
- Đã hủy.

## 13. Quy trình điểm danh

### 13.1. Tạo phiếu điểm danh

Role thực hiện: Admin, Phòng Đào tạo, Giảng viên.  
Menu: `University SMS / Điểm danh`.

Thông tin:

- Lớp học phần.
- Ngày điểm danh.
- Giảng viên.
- Danh sách sinh viên.
- Trạng thái phiếu.

Quy trình:

1. Vào Điểm danh.
2. Bấm Tạo.
3. Chọn lớp học phần.
4. Chọn ngày điểm danh.
5. Bấm Tải danh sách sinh viên.
6. Hệ thống tạo dòng điểm danh theo sinh viên của lớp.
7. Giảng viên cập nhật trạng thái từng sinh viên.
8. Bấm Xác nhận.

Trạng thái điểm danh:

- Có mặt.
- Vắng mặt.
- Đi trễ.
- Có phép.

### 13.2. Sinh viên xem điểm danh

Role thực hiện: Sinh viên.  
Link: `http://localhost:8069/my/academic/attendance`.

Sinh viên chỉ thấy các dòng điểm danh của chính mình.

## 14. Quy trình thi, nhập điểm và bảng điểm

### 14.1. Tạo kỳ thi

Role thực hiện: Admin, Phòng Đào tạo, Giảng viên.  
Menu: `University SMS / Điểm thi / Kỳ thi`.

Thông tin:

- Tên kỳ thi.
- Lớp học phần.
- Loại kỳ thi.
- Ngày thi.
- Điểm tối đa.
- Trạng thái.

Loại kỳ thi:

- Giữa kỳ.
- Cuối kỳ.
- Kiểm tra nhanh.
- Đồ án/Bài tập lớn.
- Khác.

Quy trình:

1. Vào Kỳ thi.
2. Bấm Tạo.
3. Chọn lớp học phần.
4. Chọn loại kỳ thi.
5. Nhập ngày thi.
6. Nhập điểm tối đa, thường là 10.
7. Lưu.
8. Bấm Tải danh sách sinh viên.
9. Nhập điểm cho từng sinh viên.
10. Chuyển trạng thái Đang chấm.
11. Hoàn thành kỳ thi.

### 14.2. Kết quả thi

Role thực hiện: Admin, Phòng Đào tạo, Giảng viên.  
Menu: `University SMS / Điểm thi / Kết quả thi`.

Hệ thống tự tính:

- Tỷ lệ phần trăm.
- Đạt/Không đạt, với điều kiện đạt là điểm từ 50% điểm tối đa.
- Môn đã đạt phục vụ kiểm tra môn tiên quyết khi đăng ký.

### 14.3. Bảng điểm

Role thực hiện: Admin, Phòng Đào tạo.  
Menu: `University SMS / Điểm thi / Bảng điểm`.

Quy trình:

1. Tạo bảng điểm cho sinh viên và học kỳ.
2. Bấm tạo dòng từ lịch sử học phần.
3. Bấm đồng bộ điểm.
4. Hệ thống tính điểm tổng kết.
5. Hệ thống tính GPA học kỳ, GPA tích lũy và xếp loại.

Công thức hiện tại:

- Nếu có giữa kỳ và cuối kỳ: điểm tổng kết = giữa kỳ x 40% + cuối kỳ x 60%.
- Nếu chỉ có một loại điểm: dùng điểm hiện có.

Xếp loại chữ:

- A: 8.5 đến 10.
- B: 7.0 đến 8.4.
- C: 5.5 đến 6.9.
- D: 4.0 đến 5.4.
- F: dưới 4.0.

### 14.4. Sinh viên xem điểm

Role thực hiện: Sinh viên.  
Link: `http://localhost:8069/my/academic/transcript`.

Sinh viên chỉ xem kết quả thi của chính mình.

## 15. Quy trình học phí

### 15.1. Tạo khoản học phí

Role thực hiện: Admin, Phòng Tài chính, Phòng Đào tạo.  
Menu: `University SMS / Học phí / Khoản học phí`.

Thông tin:

- Sinh viên.
- Học kỳ.
- Đơn giá mỗi tín chỉ.
- Tổng số tín chỉ.
- Tổng học phí.
- Đã thanh toán.
- Còn lại.
- Trạng thái.

Quy trình:

1. Vào Khoản học phí.
2. Bấm Tạo.
3. Chọn sinh viên.
4. Chọn học kỳ.
5. Nhập đơn giá mỗi tín chỉ.
6. Lưu.
7. Hệ thống tính tổng tín chỉ từ học phần đã đăng ký.
8. Hệ thống tính tổng học phí.

### 15.2. Tạo hóa đơn học phí

Role thực hiện: Admin, Phòng Tài chính.  
Menu: `University SMS / Học phí / Hóa đơn học phí`.

Quy trình:

1. Mở khoản học phí.
2. Bấm Tạo hóa đơn.
3. Kiểm tra thông tin sinh viên, học kỳ, tổng tiền.
4. Thêm dòng hóa đơn nếu cần.
5. Xác nhận hóa đơn.
6. Khi sinh viên thanh toán, chuyển trạng thái Đã thanh toán.

Trạng thái hóa đơn:

- Dự thảo.
- Đã xác nhận.
- Đã thanh toán.
- Đã hủy.

### 15.3. Sinh viên xem học phí

Role thực hiện: Sinh viên.  
Link: `http://localhost:8069/my/academic/fees`.

Sinh viên thấy:

- Học phí theo kỳ.
- Tổng tiền.
- Đã thanh toán.
- Còn lại.
- Hóa đơn liên quan.

## 16. Quy trình giấy chứng nhận

### 16.1. Cấu hình loại giấy

Role thực hiện: Admin, Phòng Công tác SV.  
Menu: `University SMS / Giấy chứng nhận / Loại giấy chứng nhận`.

Thông tin:

- Mã loại giấy.
- Tên loại giấy.
- Mô tả.
- Có yêu cầu phí hay không.
- Mức phí.
- Trạng thái active.

Ví dụ:

- Giấy xác nhận sinh viên.
- Giấy xác nhận vay vốn.
- Giấy xác nhận tạm hoãn nghĩa vụ quân sự.

### 16.2. Sinh viên gửi yêu cầu

Role thực hiện: Sinh viên.  
Link: `http://localhost:8069/my/academic/certificates`.

Quy trình:

1. Vào Giấy chứng nhận.
2. Chọn loại giấy.
3. Nhập lý do yêu cầu.
4. Gửi yêu cầu.
5. Theo dõi trạng thái xử lý.

### 16.3. Phòng CTSV xử lý

Role thực hiện: Admin, Phòng Công tác SV.  
Menu: `University SMS / Giấy chứng nhận / Yêu cầu giấy chứng nhận`.

Quy trình:

1. Mở danh sách yêu cầu.
2. Kiểm tra thông tin sinh viên.
3. Kiểm tra loại giấy và lý do.
4. Nếu hợp lệ, bấm Duyệt.
5. Nếu có phí, kiểm tra trạng thái thanh toán.
6. Sau khi cấp giấy, bấm Hoàn thành.
7. Nếu không hợp lệ, bấm Từ chối.

Trạng thái:

- Chờ duyệt.
- Đã duyệt.
- Hoàn thành.
- Từ chối.

## 17. Quy trình công tác sinh viên

### 17.1. Bảo hiểm y tế

Role thực hiện: Admin, Phòng Công tác SV.  
Menu: `University SMS / Công tác SV / Bảo hiểm y tế`.

Thông tin:

- Sinh viên.
- Mã BHYT.
- Ngày bắt đầu.
- Ngày kết thúc.
- Trạng thái thanh toán.
- Trạng thái xác nhận.

Sinh viên xem tại `http://localhost:8069/my/academic/student-affairs`.

### 17.2. Cư trú/Ngoại trú

Role thực hiện: Admin, Phòng Công tác SV.  
Menu: `University SMS / Công tác SV / Cư trú/Ngoại trú`.

Thông tin:

- Sinh viên.
- Loại cư trú.
- Địa chỉ.
- Chủ nhà hoặc đơn vị quản lý.
- Số điện thoại liên hệ.
- Ngày hiệu lực.
- Trạng thái.

### 17.3. Nghĩa vụ quân sự

Role thực hiện:

- Sinh viên gửi khai báo qua portal.
- Phòng CTSV xử lý backend.

Portal: `http://localhost:8069/my/academic/student-affairs`.  
Backend: `University SMS / Công tác SV / Nghĩa vụ quân sự`.

Quy trình sinh viên:

1. Vào Công tác sinh viên.
2. Chọn trạng thái NVQS.
3. Gửi khai báo.
4. Hệ thống tạo bản ghi trạng thái Đã nộp.

Quy trình phòng CTSV:

1. Mở bản ghi NVQS.
2. Kiểm tra trạng thái khai báo.
3. Kiểm tra hồ sơ kèm nếu có.
4. Duyệt hoặc từ chối.
5. Nếu cần chỉnh sửa, đưa về nháp.

Trạng thái:

- Chờ duyệt.
- Đã nộp.
- Đã duyệt.
- Bị từ chối.

## 18. Quy trình điểm rèn luyện

### 18.1. Cấu hình tiêu chí

Role thực hiện: Admin, Phòng Công tác SV.  
Menu: `University SMS / Rèn luyện / Tiêu chí rèn luyện`.

Thông tin:

- Tên tiêu chí.
- Nhóm tiêu chí.
- Điểm tối đa.
- Trạng thái active.

Nhóm tiêu chí:

- Ý thức học tập.
- Ý thức chấp hành nội quy.
- Hoạt động đoàn thể, xã hội.
- Quan hệ với cộng đồng.
- Vai trò trong lớp/đoàn thể.

### 18.2. Tạo phiếu điểm rèn luyện

Role thực hiện: Admin, Phòng CTSV, CVHT.  
Menu: `University SMS / Rèn luyện / Điểm rèn luyện`.

Thông tin:

- Sinh viên.
- Học kỳ đánh giá.
- Dòng tiêu chí.
- Điểm tự chấm.
- Điểm CVHT chấm.
- Điểm cuối.
- Xếp loại.
- Trạng thái.

### 18.3. Workflow rèn luyện

1. Sinh viên hoặc phòng ban tạo phiếu rèn luyện.
2. Sinh viên tự chấm điểm theo tiêu chí.
3. Sinh viên gửi phiếu.
4. Cố vấn học tập xem và duyệt.
5. Trưởng khoa duyệt cấp khoa.
6. Hệ thống tính tổng điểm cuối và xếp loại.
7. Sinh viên xem kết quả trên portal.

Trạng thái:

- SV đang chấm.
- Đã gửi.
- CVHT đã duyệt.
- Khoa đã duyệt.
- Bị trả về.

Xếp loại:

- Xuất sắc: từ 90.
- Tốt: từ 80.
- Khá: từ 65.
- Trung bình: từ 50.
- Yếu: từ 35.
- Kém: dưới 35.

Portal sinh viên: `http://localhost:8069/my/academic/conduct`.

## 19. Quy trình khảo sát

### 19.1. Tạo loại khảo sát

Role thực hiện: Admin, Phòng CTSV.  
Menu: `University SMS / Khảo sát / Loại khảo sát`.

Thông tin:

- Mã loại.
- Tên loại.
- Mô tả.

### 19.2. Tạo đợt khảo sát

Role thực hiện: Admin, Phòng CTSV.  
Menu: `University SMS / Khảo sát / Đợt khảo sát`.

Thông tin:

- Tên khảo sát.
- Loại khảo sát.
- Ngày bắt đầu.
- Ngày kết thúc.
- Trạng thái.

Trạng thái thường dùng:

- Nháp.
- Đang mở.
- Đã đóng.

### 19.3. Sinh viên trả lời khảo sát

Role thực hiện: Sinh viên.  
Link: `http://localhost:8069/my/academic/surveys`.

Quy trình:

1. Vào Khảo sát.
2. Xem danh sách khảo sát đang mở.
3. Nhập nội dung phản hồi.
4. Gửi khảo sát.
5. Hệ thống ghi nhận phản hồi.

### 19.4. Phòng CTSV xem phản hồi

Menu: `University SMS / Khảo sát / Phản hồi khảo sát`.

Quy trình:

1. Lọc theo đợt khảo sát.
2. Xem danh sách sinh viên phản hồi.
3. Tổng hợp ý kiến.
4. Xuất báo cáo nếu cần.

## 20. Quy trình góp ý, phản hồi

### 20.1. Sinh viên gửi góp ý

Role thực hiện: Sinh viên.  
Link: `http://localhost:8069/my/academic/feedback`.

Thông tin cần nhập:

- Loại góp ý.
- Tiêu đề.
- Nội dung.
- Bộ phận nhận.

Quy trình:

1. Vào Góp ý.
2. Chọn loại góp ý.
3. Nhập tiêu đề.
4. Nhập mô tả chi tiết.
5. Chọn bộ phận liên quan nếu có.
6. Gửi.
7. Theo dõi phản hồi và trạng thái xử lý.

Loại góp ý:

- Học vụ.
- Cơ sở vật chất.
- Dịch vụ.
- Khác.

### 20.2. Phòng ban xử lý góp ý

Role thực hiện: Admin, Phòng Đào tạo, Phòng CTSV, Phòng Tài chính.  
Menu: `University SMS / Góp ý / Phản hồi và góp ý`.

Quy trình:

1. Vào danh sách góp ý.
2. Lọc theo trạng thái, loại góp ý hoặc bộ phận.
3. Mở góp ý.
4. Cập nhật trạng thái Đang xử lý.
5. Nhập nội dung phản hồi.
6. Chuyển Hoàn thành/Đã xử lý khi xong.

## 21. Quy trình thông báo

Role thực hiện: Admin, Phòng Đào tạo, Phòng CTSV, Phòng Tài chính.  
Menu: `University SMS / Thông báo / Danh sách thông báo`.

Thông tin:

- Tiêu đề.
- Nội dung.
- Đối tượng nhận.
- Ngành/lớp nếu thông báo có phạm vi cụ thể.
- File đính kèm nếu có.
- Có ghim hay không.
- Trạng thái.

Quy trình:

1. Vào Thông báo.
2. Bấm Tạo.
3. Nhập tiêu đề.
4. Nhập nội dung.
5. Chọn đối tượng nhận.
6. Đánh dấu ghim nếu là thông báo quan trọng.
7. Công bố.

Sinh viên xem thông báo ở landing `/university` hoặc các khu vực portal tùy giao diện.

## 22. User guide dành cho sinh viên

### 22.1. Đăng nhập

1. Mở `http://localhost:8069/web/login`.
2. Nhập tài khoản sinh viên, ví dụ `sv.nguyenvanan`.
3. Nhập mật khẩu `123456`.
4. Sau khi đăng nhập, mở `http://localhost:8069/my/academic`.

### 22.2. Trang học vụ

Link: `http://localhost:8069/my/academic`.

Sinh viên thấy:

- Thông tin cá nhân.
- MSSV.
- Ngành.
- Email trường.
- Các nút chức năng học vụ.

### 22.3. Đăng ký môn

Link: `http://localhost:8069/my/academic/registration`.

Thao tác:

1. Xem đợt đăng ký đang mở.
2. Xem lớp môn học.
3. Kiểm tra tín chỉ, giảng viên, số chỗ.
4. Bấm đăng ký.
5. Nếu cần hủy, bấm hủy trong danh sách đã đăng ký.

Thông báo lỗi thường gặp:

- Chưa có đợt đăng ký đang mở.
- Đợt đăng ký chưa tới thời gian bắt đầu.
- Đợt đăng ký đã hết hạn.
- Môn đã đăng ký rồi.
- Chưa hoàn thành môn tiên quyết.
- Lớp đã đủ chỗ.
- Vượt quá số tín chỉ tối đa.

### 22.4. Xem thời khóa biểu

Link: `http://localhost:8069/my/academic/timetable`.

Sinh viên xem:

- Thứ học.
- Giờ bắt đầu, kết thúc.
- Môn/lớp học phần.
- Phòng học.
- Tòa nhà.

### 22.5. Xem bảng điểm

Link: `http://localhost:8069/my/academic/transcript`.

Sinh viên xem:

- Môn học.
- Học kỳ.
- Loại kỳ thi.
- Điểm.
- Đạt/Không đạt.

### 22.6. Xem điểm danh

Link: `http://localhost:8069/my/academic/attendance`.

Sinh viên xem từng buổi:

- Tên lớp.
- Ngày điểm danh.
- Trạng thái: có mặt, vắng, đi trễ, có phép.

### 22.7. Xem học phí

Link: `http://localhost:8069/my/academic/fees`.

Sinh viên xem:

- Học kỳ.
- Tổng tín chỉ.
- Tổng học phí.
- Đã thanh toán.
- Còn lại.
- Hóa đơn liên quan.

### 22.8. Yêu cầu giấy chứng nhận

Link: `http://localhost:8069/my/academic/certificates`.

Thao tác:

1. Chọn loại giấy.
2. Nhập lý do.
3. Gửi yêu cầu.
4. Theo dõi trạng thái.

### 22.9. Công tác sinh viên

Link: `http://localhost:8069/my/academic/student-affairs`.

Sinh viên xem:

- BHYT.
- Cư trú.
- Nghĩa vụ quân sự.

Sinh viên có thể gửi khai báo NVQS nếu giao diện đang mở form khai báo.

### 22.10. Xem điểm rèn luyện

Link: `http://localhost:8069/my/academic/conduct`.

Sinh viên xem:

- Học kỳ đánh giá.
- Điểm tự chấm.
- Điểm CVHT.
- Điểm cuối.
- Xếp loại.
- Trạng thái duyệt.

### 22.11. Trả lời khảo sát

Link: `http://localhost:8069/my/academic/surveys`.

Thao tác:

1. Chọn khảo sát đang mở.
2. Nhập phản hồi.
3. Gửi.

### 22.12. Gửi góp ý

Link: `http://localhost:8069/my/academic/feedback`.

Thao tác:

1. Chọn loại góp ý.
2. Nhập tiêu đề.
3. Nhập nội dung.
4. Chọn bộ phận nhận.
5. Gửi.
6. Theo dõi phản hồi.

## 23. User guide dành cho Phòng Đào tạo

### 23.1. Đăng nhập backend

1. Mở `http://localhost:8069/web`.
2. Đăng nhập tài khoản Phòng Đào tạo, ví dụ `dt.nguyenthilan`.
3. Mở app `University SMS`.

### 23.2. Công việc chính

- Tạo và cập nhật dữ liệu nền.
- Tạo hồ sơ sinh viên.
- Tạo lớp hành chính.
- Tạo lớp học phần.
- Tạo thời khóa biểu.
- Tạo đợt đăng ký môn.
- Mở lớp môn học.
- Theo dõi đăng ký môn.
- Quản lý kỳ thi, kết quả thi, bảng điểm.
- Theo dõi điểm danh.

### 23.3. Checklist vận hành học kỳ mới

1. Tạo năm học nếu chưa có.
2. Tạo học kỳ.
3. Kiểm tra danh sách ngành, môn học.
4. Cập nhật môn tiên quyết.
5. Tạo lớp học phần.
6. Phân công giảng viên.
7. Tạo thời khóa biểu.
8. Tạo lớp môn học để đăng ký.
9. Tạo đợt đăng ký.
10. Mở đợt đăng ký.
11. Theo dõi số chỗ và số tín chỉ.
12. Đóng đợt đăng ký.
13. Chốt danh sách lớp.

## 24. User guide dành cho giảng viên

### 24.1. Công việc chính

- Xem lớp học phần được phân công.
- Xem thời khóa biểu.
- Tạo phiếu điểm danh.
- Cập nhật trạng thái điểm danh.
- Tạo kỳ thi.
- Nhập điểm.
- Hoàn thành kỳ thi.

### 24.2. Quy trình điểm danh nhanh

1. Vào `University SMS / Điểm danh`.
2. Tạo phiếu điểm danh.
3. Chọn lớp.
4. Chọn ngày.
5. Tải danh sách sinh viên.
6. Cập nhật trạng thái.
7. Xác nhận.

### 24.3. Quy trình nhập điểm nhanh

1. Vào `University SMS / Điểm thi / Kỳ thi`.
2. Tạo kỳ thi.
3. Chọn lớp và loại kỳ thi.
4. Tải danh sách sinh viên.
5. Nhập điểm.
6. Chuyển Đang chấm.
7. Hoàn thành.

## 25. User guide dành cho Phòng Tài chính

### 25.1. Công việc chính

- Tạo khoản học phí.
- Kiểm tra số tín chỉ.
- Tạo hóa đơn.
- Xác nhận hóa đơn.
- Cập nhật thanh toán.
- Gửi thông báo học phí.

### 25.2. Quy trình thu học phí

1. Vào `University SMS / Học phí / Khoản học phí`.
2. Tạo khoản phí theo sinh viên và kỳ.
3. Kiểm tra tổng tín chỉ.
4. Tạo hóa đơn.
5. Xác nhận hóa đơn.
6. Khi sinh viên thanh toán, chuyển trạng thái `Đã thanh toán`.
7. Kiểm tra số còn lại.

## 26. User guide dành cho Phòng Công tác Sinh viên

### 26.1. Công việc chính

- Quản lý bảo hiểm y tế.
- Quản lý cư trú.
- Quản lý nghĩa vụ quân sự.
- Xử lý yêu cầu giấy chứng nhận.
- Tạo và theo dõi khảo sát.
- Xử lý góp ý.
- Tạo thông báo liên quan công tác sinh viên.

### 26.2. Checklist xử lý giấy chứng nhận

1. Vào `University SMS / Giấy chứng nhận / Yêu cầu giấy chứng nhận`.
2. Lọc yêu cầu trạng thái `Chờ duyệt`.
3. Kiểm tra sinh viên và loại giấy.
4. Duyệt.
5. Nếu có phí, kiểm tra thanh toán.
6. Cấp giấy.
7. Chuyển Hoàn thành.

### 26.3. Checklist xử lý NVQS

1. Vào `University SMS / Công tác SV / Nghĩa vụ quân sự`.
2. Lọc bản ghi Đã nộp.
3. Kiểm tra trạng thái đăng ký.
4. Kiểm tra hồ sơ.
5. Duyệt hoặc từ chối.

## 27. User guide dành cho CVHT và trưởng khoa

### 27.1. Cố vấn học tập

Công việc chính:

- Theo dõi sinh viên lớp phụ trách.
- Xem điểm danh, kết quả học tập nếu được cấp quyền.
- Chấm hoặc duyệt điểm rèn luyện cấp CVHT.

Quy trình duyệt rèn luyện:

1. Vào `University SMS / Rèn luyện / Điểm rèn luyện`.
2. Lọc phiếu trạng thái `Đã gửi`.
3. Kiểm tra điểm tự chấm.
4. Nhập điểm CVHT nếu cần.
5. Bấm CVHT duyệt.

### 27.2. Trưởng khoa

Công việc chính:

- Theo dõi dữ liệu khoa.
- Duyệt điểm rèn luyện cấp khoa.

Quy trình:

1. Vào `University SMS / Rèn luyện / Điểm rèn luyện`.
2. Lọc phiếu `CVHT đã duyệt`.
3. Kiểm tra điểm cuối.
4. Bấm Khoa duyệt.

## 28. Dashboard và báo cáo

### 28.1. Dashboard

Role sử dụng: Admin, phòng ban được cấp quyền.

Menu: `University SMS / Dashboards`.

Các dashboard:

- SV Dashboard: tổng quan sinh viên.
- Điểm danh Dashboard: tình hình chuyên cần.
- Điểm thi Dashboard: kết quả học tập.
- Học phí Dashboard: công nợ và thanh toán.
- Đăng ký môn Dashboard: số lượng đăng ký, lớp mở.
- Rèn luyện Dashboard: kết quả rèn luyện.

### 28.2. Báo cáo PDF

Các mẫu báo cáo có thể in:

- Phiếu điểm danh.
- Bảng điểm.
- Phiếu đăng ký môn.
- Hóa đơn học phí.
- Giấy chứng nhận.
- Điểm rèn luyện.

Quy trình chung:

1. Mở bản ghi cần in.
2. Chọn menu In hoặc Print.
3. Chọn mẫu báo cáo.
4. Tải file PDF.

## 29. Dữ liệu mẫu và kiểm tra chất lượng data

### 29.1. Seed dữ liệu mẫu

File seed chính:

`addons/seed_university_realistic.py`

Lệnh chạy khuyến nghị:

```bash
cmd /c 'docker compose exec -T odoo bash -lc "odoo shell -d univ_sms_db < /mnt/extra-addons/seed_university_realistic.py"'
```

Lý do dùng cách này:

- Odoo đọc trực tiếp file UTF-8 trong container.
- Không pipe nội dung tiếng Việt qua PowerShell.
- Tránh lỗi encoding như `Nguy??n`, `Khoa CÃ´ng...`.

Không khuyến nghị:

```powershell
Get-Content addons\seed_university_realistic.py | docker compose exec -T odoo odoo shell -d univ_sms_db
```

Cách trên có thể làm vỡ tiếng Việt khi terminal không dùng đúng encoding.

### 29.2. Audit dữ liệu

File audit:

`addons/audit_university_data.py`

Lệnh chạy:

```bash
cmd /c 'docker compose exec -T odoo bash -lc "odoo shell -d univ_sms_db < /mnt/extra-addons/audit_university_data.py"'
```

Kết quả đạt yêu cầu:

```text
[audit] OK: no broken text markers found
```

File SQL xem mẫu:

`addons/audit_samples.sql`

Lệnh chạy:

```bash
cmd /c "type addons\audit_samples.sql | docker compose exec -T db psql -U odoo -d univ_sms_db"
```

### 29.3. Kết quả seed dữ liệu hiện tại

Sau khi reset và seed sạch, dữ liệu mẫu gồm:

- 7 khoa/phòng.
- 7 bộ môn.
- 7 ngành.
- 19 môn học.
- 7 lớp hành chính.
- 18 lớp học phần.
- 18 thời khóa biểu.
- 54 phiếu điểm danh.
- 14 sinh viên có tài khoản riêng.
- 94 lịch sử học phần.
- 23 đăng ký môn.
- 188 kết quả thi.
- 42 khoản học phí.
- 14 yêu cầu giấy chứng nhận.
- 14 phiếu rèn luyện.
- 10 phản hồi khảo sát.
- 8 góp ý.
- 4 thông báo.

## 30. Checklist kiểm thử chức năng

### 30.1. Kiểm thử sinh viên

- Đăng nhập `sv.nguyenvanan`.
- Vào `/my/academic`.
- Kiểm tra hiển thị MSSV, ngành, email trường.
- Vào đăng ký môn.
- Đăng ký một môn còn chỗ.
- Hủy môn vừa đăng ký.
- Xem thời khóa biểu.
- Xem điểm danh.
- Xem bảng điểm.
- Xem học phí.
- Gửi yêu cầu giấy chứng nhận.
- Gửi khai báo NVQS.
- Trả lời khảo sát.
- Gửi góp ý.

### 30.2. Kiểm thử Phòng Đào tạo

- Đăng nhập `dt.nguyenthilan`.
- Tạo môn học mới.
- Tạo lớp học phần.
- Tạo thời khóa biểu.
- Tạo đợt đăng ký.
- Mở đợt đăng ký.
- Kiểm tra danh sách đăng ký.
- Tạo kỳ thi.
- Nhập điểm.
- Tạo bảng điểm.

### 30.3. Kiểm thử giảng viên

- Đăng nhập giảng viên.
- Xem lớp học phần.
- Tạo phiếu điểm danh.
- Tải danh sách sinh viên.
- Cập nhật vắng/có mặt.
- Xác nhận phiếu.
- Tạo kỳ thi.
- Nhập điểm.
- Hoàn thành kỳ thi.

### 30.4. Kiểm thử Phòng Tài chính

- Đăng nhập `tc.phamquanghuy`.
- Tạo khoản học phí.
- Tạo hóa đơn.
- Xác nhận hóa đơn.
- Chuyển trạng thái đã thanh toán.
- Kiểm tra sinh viên thấy học phí trên portal.

### 30.5. Kiểm thử Phòng CTSV

- Đăng nhập `ctsv.levanhoa`.
- Duyệt yêu cầu giấy chứng nhận.
- Tạo/cập nhật BHYT.
- Duyệt khai báo NVQS.
- Tạo khảo sát.
- Xem phản hồi khảo sát.
- Xử lý góp ý.

### 30.6. Kiểm thử dữ liệu

- Chạy audit encoding.
- Kiểm tra không có `?`, `Ã`, `�` trong dữ liệu nghiệp vụ.
- Kiểm tra khoa hiển thị tiếng Việt chuẩn.
- Kiểm tra lớp hành chính không còn lớp lỗi hoặc lớp 0 sinh viên do seed cũ.
- Kiểm tra thời khóa biểu hiển thị tên môn chuẩn.
- Kiểm tra điểm danh có dòng sinh viên và số liệu có mặt/vắng mặt.

## 31. Lỗi thường gặp và cách xử lý

### 31.1. Sinh viên không thấy trang học vụ

Nguyên nhân có thể:

- User không có partner liên kết với hồ sơ sinh viên.
- Hồ sơ sinh viên chưa được tạo.
- Truy cập sai link.

Cách xử lý:

1. Vào backend kiểm tra user.
2. Kiểm tra partner của user.
3. Kiểm tra hồ sơ sinh viên có `partner_id` đúng không.
4. Mở lại `http://localhost:8069/my/academic`.

### 31.2. Sinh viên không thấy nút chức năng portal

Nguyên nhân có thể:

- Module portal chưa update.
- Template portal chưa được load.
- User chưa đăng nhập đúng tài khoản sinh viên.

Cách xử lý:

1. Update module `univ_sms_portal`.
2. Restart Odoo.
3. Đăng nhập bằng tài khoản `sv.*`.

### 31.3. Đăng ký môn báo lỗi tiên quyết

Nguyên nhân:

- Môn học có cấu hình môn tiên quyết.
- Sinh viên chưa có kết quả thi đạt ở môn tiên quyết.

Cách xử lý:

1. Kiểm tra môn tiên quyết trong Môn học.
2. Kiểm tra kết quả thi của sinh viên.
3. Nếu sinh viên đã học nhưng thiếu điểm, nhập bổ sung kết quả thi.
4. Thử đăng ký lại.

### 31.4. Dữ liệu hiển thị lỗi dấu tiếng Việt

Nguyên nhân:

- Nạp seed qua PowerShell pipe không đúng encoding.

Cách xử lý:

1. Chạy lại seed bằng lệnh `cmd` khuyến nghị.
2. Chạy audit.
3. Restart Odoo.

### 31.5. Điểm danh không có sinh viên

Nguyên nhân:

- Lớp chưa có enrollment.
- Enrollment không đúng trạng thái.
- Chưa bấm Tải danh sách sinh viên.

Cách xử lý:

1. Kiểm tra lớp học phần.
2. Kiểm tra lịch sử học phần của sinh viên.
3. Bấm Tải danh sách sinh viên.
4. Nếu là dữ liệu seed, chạy lại seed bản mới.

### 31.6. Học phí bằng 0

Nguyên nhân:

- Sinh viên chưa có học phần trạng thái đăng ký trong kỳ.
- Chưa nhập đơn giá tín chỉ.

Cách xử lý:

1. Kiểm tra enrollment của sinh viên trong kỳ.
2. Kiểm tra đơn giá tín chỉ.
3. Lưu lại khoản học phí để hệ thống tính lại.

## 32. Khuyến nghị vận hành

- Không dùng tài khoản demo chung như `sinhvien/sinhvien` hoặc `giangvien/giangvien`.
- Mỗi sinh viên, giảng viên, phòng ban nên có tài khoản riêng.
- Không sửa trực tiếp MSSV sau khi tạo.
- Không xóa dữ liệu học vụ đã phát sinh; nên dùng trạng thái hủy/đóng/ngưng hoạt động.
- Trước demo nên chạy audit encoding.
- Sau khi update module nên restart Odoo.
- Khi seed dữ liệu có tiếng Việt, dùng lệnh trong container hoặc `cmd`, tránh pipe PowerShell.
- Phân quyền theo role nghiệp vụ, không cấp quyền admin cho tất cả tài khoản.

## 33. Phụ lục link nhanh theo role

### Sinh viên

- Trang học vụ: `http://localhost:8069/my/academic`
- Đăng ký môn: `http://localhost:8069/my/academic/registration`
- Thời khóa biểu: `http://localhost:8069/my/academic/timetable`
- Bảng điểm: `http://localhost:8069/my/academic/transcript`
- Điểm danh: `http://localhost:8069/my/academic/attendance`
- Học phí: `http://localhost:8069/my/academic/fees`
- Giấy chứng nhận: `http://localhost:8069/my/academic/certificates`
- Công tác SV: `http://localhost:8069/my/academic/student-affairs`
- Rèn luyện: `http://localhost:8069/my/academic/conduct`
- Khảo sát: `http://localhost:8069/my/academic/surveys`
- Góp ý: `http://localhost:8069/my/academic/feedback`

### Admin và phòng ban

- Backend: `http://localhost:8069/web`
- App: `University SMS`
- Dữ liệu nền: `University SMS / Dữ liệu nền`
- Sinh viên: `University SMS / Sinh viên`
- Lớp học: `University SMS / Lớp học`
- Điểm danh: `University SMS / Điểm danh`
- Điểm thi: `University SMS / Điểm thi`
- Học phí: `University SMS / Học phí`
- Đăng ký môn: `University SMS / Đăng ký môn`
- Giấy chứng nhận: `University SMS / Giấy chứng nhận`
- Công tác SV: `University SMS / Công tác SV`
- Rèn luyện: `University SMS / Rèn luyện`
- Khảo sát: `University SMS / Khảo sát`
- Góp ý: `University SMS / Góp ý`
- Thông báo: `University SMS / Thông báo`
- Dashboard: `University SMS / Dashboards`

## 34. Kết luận

University SMS hiện bao phủ các nghiệp vụ lõi của hệ thống quản lý sinh viên đại học:

- Quản lý dữ liệu đào tạo.
- Quản lý hồ sơ sinh viên.
- Quản lý lớp, thời khóa biểu, điểm danh.
- Quản lý điểm thi, bảng điểm.
- Quản lý đăng ký môn học.
- Quản lý học phí.
- Quản lý công tác sinh viên.
- Quản lý giấy chứng nhận.
- Quản lý rèn luyện.
- Quản lý khảo sát, góp ý, thông báo.
- Portal sinh viên để tự phục vụ.
- Dashboard và báo cáo.

Hệ thống nên được demo bằng tài khoản thật theo role, dữ liệu mẫu đã seed sạch, tránh dùng tài khoản chung hoặc dữ liệu lỗi encoding.
