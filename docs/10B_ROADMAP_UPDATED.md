PhaseModuleOutput chínhPhụ thuộc1-5(như cũ)Master data, Student, Class, Attendance, Exam, Fee, Portal cơ bản, Report cơ bản—6univ_sms_registration, univ_sms_notification, univ_sms_feedbackDKMH/DKMNV, Thông báo, Form góp ýPhase 1-3, OPEN_Q1/Q27univ_sms_student_affairs, univ_sms_conduct, univ_sms_certificate, univ_sms_surveyBHYT, Ngoại trú, NVQS, Điểm rèn luyện (3 cấp), Xin phiếu, Khảo sátPhase 1, OPEN_Q3/Q4/Q5/Q88univ_sms_elearning (optional)E-learning (kế thừa website_slides hoặc link ngoài)OPEN_Q79univ_sms_report (mở rộng lớn)Dashboard Admin/Officer/Dean/Lecturer + Portal widget SV, toàn bộ PDF reportTất cả phase trên10HardeningPerformance tuning, audit log (mail.thread toàn bộ model trọng yếu), data migration scriptsSau khi đủ Phase 1-9
Thứ tự khai báo depends tổng thể (manifest chain)
univ_sms_base
  └── univ_sms_student
        ├── univ_sms_class
        │     └── univ_sms_attendance
        ├── univ_sms_exam
        ├── univ_sms_fee
        ├── univ_sms_registration (depends: univ_sms_class, univ_sms_exam)
        ├── univ_sms_notification
        ├── univ_sms_feedback
        ├── univ_sms_student_affairs
        ├── univ_sms_conduct
        ├── univ_sms_certificate
        └── univ_sms_survey
              └── univ_sms_portal (depends: tất cả module trên có route)
                    └── univ_sms_report (depends: tất cả)

➡️ Bước tiếp theo: Trả lời 8 câu hỏi mới trong 01B_FUNCTIONAL_SCOPE_EXPANDED.md mục C (OPEN_Q1-Q8 Phase 6-10), kết hợp với 8 câu hỏi cũ chưa trả lời ở 01_FUNCTIONAL_SCOPE.md. Sau khi có đủ thông tin, Agent generate theo thứ tự: Phase 6 → Phase 7 → Phase 9, mỗi Phase tuân quy trình tại 09_AGENT_WORKFLOW.md.