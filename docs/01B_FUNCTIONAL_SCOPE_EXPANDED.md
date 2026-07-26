A. PHÂN TÍCH CHỨC NĂNG TỪ HỆ THỐNG THAM CHIẾU (23 mục menu)
ID Menu gốcTên hiển thịPhân hệ Odoo tương ứngPhaseWEB_XEMTHONGBAOThông báo từ ban quản trịuniv_sms_notification6WEB_CTDTXem chương trình đào tạouniv_sms_curriculum1 (mở rộng program)WEB_XEMMONTIENQUYETMôn học tiên quyếtuniv_sms_curriculum1 (mở rộng subject)WEB_DKMHĐăng ký môn họcuniv_sms_registration6WEB_DKMNVĐăng ký môn nguyện vọnguniv_sms_registration6WEB_HOCPHIXem học phíuniv_sms_fee3WEB_XEMBHYTBảo hiểm y tếuniv_sms_student_affairs7WEB_HDDTHóa đơn điện tửuniv_sms_fee3WEB_TKB_1TUAN / WEB_TKB_HKThời khóa biểu (tuần/kỳ)univ_sms_class2WEB_ELEARNINGE-learninguniv_sms_elearning (link website_slides)8 (optional)WEB_SVXEMDIEMDANHXem điểm danhuniv_sms_attendance2WEB_LICHTHILịch thiuniv_sms_exam3WEB_DIEMXem điểmuniv_sms_exam3WEB_SVDANHGIARENLUYENĐánh giá rèn luyệnuniv_sms_conduct7WEB_KSDGKhảo sát đánh giáuniv_sms_survey (kế thừa survey)7WEB_DKGCN / WEB_XEMGCNDANGKYGiấy chứng nhậnuniv_sms_certificate7WEB_NHAPTTNGOAITRUThông tin ngoại trúuniv_sms_student_affairs7WEB_THONG_TIN_SV / WEB_TT_DIA_CHI_MOICập nhật hồ sơ/địa chỉuniv_sms_student1(bổ sung yêu cầu mới)NVQS (Nghĩa vụ quân sự)univ_sms_student_affairs7(bổ sung yêu cầu mới)Form ý kiến/phản hồiuniv_sms_feedback6(bổ sung yêu cầu mới)Xin phiếu (xác nhận SV, tạm vắng...)univ_sms_certificate7(bổ sung yêu cầu mới)Báo cáo/Dashboard (Admin + GV + SV)univ_sms_report9(bổ sung yêu cầu mới)Phân quyền theo Phòng/Banuniv_sms_base (mở rộng groups)5
B. NHÓM NGƯỜI DÙNG (RBAC) — CHUẨN HÓA THEO PHÒNG BAN ĐẠI HỌC THỰC TẾ
1. Super Admin (CNTT)           → group_univ_admin
2. Phòng Đào tạo (PĐT)          → group_univ_academic_office
3. Phòng Tài chính - Kế toán    → group_univ_finance_office
4. Phòng Công tác Sinh viên     → group_univ_student_affairs_office
5. Trưởng Khoa / Trưởng Bộ môn  → group_univ_dean
6. Giảng viên                   → group_univ_lecturer
7. Cố vấn học tập (Cố vấn HT)    → group_univ_advisor  (kế thừa lecturer + quyền duyệt NV)
8. Sinh viên (Portal)           → base.group_portal + tag univ_student
C. OPEN QUESTIONS BỔ SUNG (Phase 6-10)

⚠️ Bắt buộc trả lời trước khi Agent generate Phase 6-10. Câu hỏi Phase 1-5 cũ vẫn còn hiệu lực nếu chưa trả lời.


Đăng ký môn học (DKMH/DKMNV): có giới hạn số tín chỉ tối thiểu/tối đa mỗi kỳ không? Có kiểm tra môn tiên quyết tự động (block nếu chưa học/chưa đạt môn trước) không?
Khảo sát đánh giá (KSDG): dùng module survey gốc của Odoo (kế thừa) hay xây model riêng để custom UI theo style trường?
Giấy chứng nhận/Xin phiếu: cần ký số (digital signature) hay chỉ xuất PDF + xác nhận thủ công của PĐT (workflow duyệt draft→approved→issued)?
Đánh giá rèn luyện: thang điểm theo Thông tư 16/2024 (100 điểm, 5 nội dung đánh giá) hay quy chế riêng của trường? Ai chấm: SV tự chấm → Lớp trưởng/CVHT duyệt → Khoa duyệt (workflow 3 cấp)?
Cố vấn học tập (CVHT): 1 CVHT phụ trách 1 lớp hay theo nhóm sinh viên tự chọn? CVHT có quyền duyệt đăng ký môn của SV không?
Dashboard/Báo cáo: cần loại biểu đồ cụ thể nào? (VD: tỷ lệ SV theo trạng thái học, biểu đồ điểm trung bình theo lớp/khoa, biểu đồ công nợ học phí theo thời gian, biểu đồ điểm danh...)
E-learning: có cần tích hợp thật (Odoo website_slides/eLearning module Community) hay chỉ là link ra LMS ngoài (Moodle...)?
NVQS (Nghĩa vụ quân sự): chỉ là form khai báo thông tin lưu trữ, hay có workflow gửi báo cáo định kỳ lên hệ thống quân sự địa phương (export file theo mẫu)?