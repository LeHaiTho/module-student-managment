Bước thực thi (mỗi Phase lặp lại quy trình này)

Input: Agent đọc đúng 1 file spec (VD: 05_MODEL_SPEC_PHASE1.md) — không tự gộp/giả định module khác chưa code.
Checklist trước khi sinh code:

Field nào đánh dấu ⚠️ OPEN → dừng, hỏi lại Owner, KHÔNG generate giá trị mặc định bừa.
Kiểm tra depends trong manifest có đủ module cần thiết chưa.
Kiểm tra naming convention đúng univ.sms.* / univ_sms_*.


Output bắt buộc theo thứ tự: __manifest__.py → models/*.py → security/*.csv,*.xml → views/*.xml → data/*.xml (nếu có) → controllers/*.py (nếu Portal).
Sau khi sinh code: liệt kê danh sách file đã tạo/sửa + lệnh -i/-u tương ứng để test.
Không xóa/sửa field đã định nghĩa ở Phase trước trừ khi Owner yêu cầu rõ ràng (migration script riêng nếu cần đổi schema).
Khi phát hiện mâu thuẫn giữa spec và best-practice Odoo (VD: field trùng tên reserved của ORM như name, state, active) → Agent báo cáo, đề xuất tên thay thế, chờ xác nhận trước khi đổi spec.

Định dạng câu hỏi khi chưa rõ thông tin (template chuẩn)
❓ CẦN XÁC NHẬN — [Tên module/field liên quan]
- Vấn đề: <mô tả ngắn>
- Lựa chọn đề xuất:
  A. <option 1 + hệ quả kỹ thuật>
  B. <option 2 + hệ quả kỹ thuật>
- Ảnh hưởng nếu không xác nhận: <ví dụ: không thể tạo _sql_constraints cho MSSV>