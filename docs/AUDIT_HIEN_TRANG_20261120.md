# Audit hiện trạng source University SMS (20/11/2026)

Nguồn sự thật: đọc source trong `addons/` và chạy thật trên Docker
(Odoo 17.0, PostgreSQL 15). Mọi nhận định đều có vị trí trong code hoặc log
đi kèm.

## 1. Module và dependency

```
base, mail
└─ univ_sms_base
   └─ univ_sms_student
      ├─ univ_sms_class
      │  └─ univ_sms_attendance
      │     ├─ univ_sms_exam ──────────────┐
      │     └─ univ_sms_fee (+account)     │
      │                                    ├─ univ_sms_registration (base, student, class, exam)
      ├─ univ_sms_notification (class)     │
      ├─ univ_sms_conduct (class)          │
      ├─ univ_sms_feedback                 │
      ├─ univ_sms_student_affairs          │
      ├─ univ_sms_certificate              │
      └─ univ_sms_survey                   │
univ_sms_portal  ← portal, student, exam, attendance, fee, registration, class,
                   certificate, student_affairs, conduct, survey, feedback
univ_sms_report  ← student, exam, fee, account, attendance, registration,
                   conduct, certificate, student_affairs
univ_sms_early_warning (MỚI, F3) ← student, exam, attendance, fee, registration
```

## 2. Kết quả chạy baseline

| Kiểm tra | Kết quả |
|---|---|
| Cài mới 15 module trên DB sạch | Đạt (exit 0). Chỉ có cảnh báo icon `fa` thiếu title và docstring RST |
| `-u all` trên bản sao DB hiện tại (14 SV, 24 đăng ký, 94 enrollment) | Đạt (exit 0) |
| Automated test có sẵn | 0 test |
| Test leader bổ sung (base, student) | 9/9 đạt (`test-results/sms_t_leader.log`) |

## 3. Bảng phân loại

### 3.1 Đã có và hoạt động (đã kiểm bằng cài đặt và đọc code; test ghi ở cột cuối)
| Hạng mục | Bằng chứng | Test |
|---|---|---|
| Mã duy nhất khoa, bộ môn, ngành, môn | `_sql_constraints` trong `univ_sms_base/models/*` | `test_base_constraints` |
| Ngày năm học, học kỳ | `academic_period.py` `_check_dates` | có |
| MSSV tự sinh, không sửa được | `student.py` `create`/`write`, ir.sequence (an toàn đồng thời) | có |
| Không tạo partner trùng khi tạo SV | `student.py` `create` | có |
| Giờ bắt đầu < giờ kết thúc TKB | `timetable.py` `_check_time_range` | F1 |
| Dòng điểm danh không trùng | `attendance.py` `line_uniq` | F2 |
| Kết quả thi không trùng, khoảng điểm | `exam_result.py` | cần thêm |
| Bảng điểm không trùng | `transcript.py` `transcript_uniq`, `subject_uniq` | cần thêm |
| Record rule portal cho enrollment, điểm danh, học phí, đăng ký, chứng nhận, CTSV, rèn luyện, khảo sát, góp ý | các `security_rules.xml` | Agent F |

### 3.2 Đã có nhưng chưa hoàn chỉnh
| Hạng mục | Vấn đề | Vị trí | Xử lý |
|---|---|---|---|
| Workflow trạng thái SV | Nút chỉ ẩn ở view, server không chặn (tốt nghiệp từ nháp…) | `student.py` | **Đã sửa** (`_check_state_transition`) + test |
| Đăng ký môn | Không trùng lịch, không danh sách chờ, không đồng bộ enrollment; `draft` chiếm chỗ; portal trả nguyên văn exception | `registration.py`, `portal.py` | F1 |
| Học phí | `total_credits` chỉ phụ thuộc student/term nên không tự tính lại; tạo hóa đơn trùng được; thiếu hạn thanh toán | `fee.py` | F1 (`due_date` leader đã thêm) |
| Account move | Tạo `account.move.line` không có account hoặc journal sandbox | `fee.py` `action_create_account_move` | Giai đoạn 4 |
| Điểm danh | Sửa được dòng sau khi xác nhận (chỉ chặn ở view) | `attendance.py` | F2 |
| Điều kiện dự thi | Không liên kết chuyên cần; nạp toàn bộ SV | `exam.py` | F2 |
| Cảnh báo học vụ SV | Ngưỡng `term_gpa < 1.0` trong khi GPA lưu thang 10 | `student.py` | Giữ nguyên; F3 dùng ngưỡng 5.0/10 theo SPEC |
| GPA tích lũy | Chỉ tính lại bảng điểm đang sửa, các kỳ khác không cập nhật | `transcript.py` | Giai đoạn 4 |
| `res.partner.is_student` | Compute stored nhưng không có `@api.depends` nên không bao giờ tính lại | `res_partner.py` | Giai đoạn 4 |
| Rèn luyện 3 cấp | Không giới hạn điểm theo `max_score` tiêu chí | `conduct_score.py` | Giai đoạn 4 |
| Khảo sát | Không có unique (SV, đợt); portal nộp được vào đợt đã đóng | `survey_response.py`, `portal.py` | Giai đoạn 4 |
| Portal POST dịch vụ | `int()` trên input không kiểm tra (lỗi 500), không kiểm tra loại giấy hoặc bộ phận còn hiệu lực, giá trị selection NVQS không kiểm tra, gửi lặp | `portal.py` | Giai đoạn 4 |
| Deploy | `deploy/odoo.conf` commit `admin_passwd = admin123`; health check `/web/login` | `deploy/` | **Đã sửa** (đọc từ env, `/web/health`) |

### 3.3 Có lỗi bảo mật
| Mức | Lỗi | Vị trí | Xử lý |
|---|---|---|---|
| Cao | Portal có ACL đọc `univ.sms.exam.result`, `univ.sms.transcript`, `univ.sms.transcript.line` nhưng **không có record rule**, nên SV A đọc được điểm SV B qua JSON-RPC (`/web/dataset/call_kw`) | `univ_sms_exam/security/ir.model.access.csv` | Agent F (giai đoạn 4) |
| Trung bình | Portal đọc được mọi `univ.sms.notification`, kể cả bản nháp | `univ_sms_notification` ACL | Giai đoạn 4 |
| Trung bình | Rule "Lecturer: own class" áp cho mọi nhóm kế thừa giảng viên (cố vấn, tài chính, CTSV, trưởng khoa), nên phòng tài chính chỉ thấy enrollment lớp mình dạy và học phí tính thiếu nếu không chạy bằng sudo | `univ_sms_attendance/security/security_rules.xml` | Giai đoạn 4 |

### 3.4 Chưa có
F1 danh sách chờ và trùng lịch; F2 phiên QR; F3 model cảnh báo, cron, dashboard cố vấn; F4 thông báo theo sự kiện; seed dữ liệu chuẩn chạy lặp được; tài liệu backup và restore.

### 3.5 Cần migration hoặc phương án nâng cấp
* `univ.sms.registration`: trạng thái `draft` không còn chiếm chỗ; backfill `enrollment_id` cho đăng ký đang hoạt động (F1).
* `univ.sms.enrollment`: các field điều kiện dự thi (F2), mặc định `exam_eligible=True`.
* `univ.sms.fee.due_date`: field mới, để trống với dữ liệu cũ (không phát sinh cảnh báo nợ cho tới khi được đặt hạn).

### 3.6 Cần automated test
Toàn bộ danh sách test bắt buộc trong yêu cầu. Trạng thái cập nhật ở
`docs/BAO_CAO_KIEM_THU.md` (lập sau khi gộp F1 đến F3).

## 4. Phân công và lý do điều chỉnh
| Agent | Phạm vi | Lý do |
|---|---|---|
| F1 (gộp A+B) | registration, class, enrollment, fee, route và template đăng ký trên portal | Đồng bộ enrollment, sĩ số và học phí là một giao dịch với đăng ký; tách hai agent sẽ cùng sửa `registration.py` |
| F2 (gộp C+D) | attendance, exam, controller và template QR mới | Điều kiện dự thi dùng trực tiếp dữ liệu điểm danh; `univ_sms_attendance` không thể chia cho hai agent |
| F3 (E) | module mới `univ_sms_early_warning` | Không đụng file nào của F1/F2 |
| F (bảo mật) | ACL, rule, `portal.py`, test truy cập chéo | Chạy sau khi gộp F1/F2, vì cùng sửa `portal.py` |
| G (tích hợp) | seed, demo, kiểm thử tích hợp, deploy | Chạy sau cùng |
