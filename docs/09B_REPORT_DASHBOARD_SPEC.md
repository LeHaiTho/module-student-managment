A. Dashboard theo Role (dùng view kanban/graph/pivot chuẩn Odoo — KHÔNG cần JS custom)
DashboardRoleModel nguồnLoại viewTổng quan toàn trườngAdminuniv.sms.studentgraph (bar: SV theo state), pivot (theo program x state)Tỷ lệ điểm danh theo lớpLecturer/Officeruniv.sms.attendance.linegraph (line: % theo tuần)Điểm trung bình theo lớp/khoaOfficer/Deanuniv.sms.exam.resultpivot (avg score by class/subject)Công nợ học phíFinanceuniv.sms.fee.invoice (account.move)graph (bar: outstanding by term)Đăng ký môn học theo thời gian thựcOfficeruniv.sms.registrationgraph (bar: registered count by offering)Phân loại rèn luyệnDeanuniv.sms.conduct.scorepivot (classification x program)
B. Ví dụ view Graph (univ_sms_report/views/student_dashboard_views.xml)
xml<odoo>
    <record id="view_student_graph" model="ir.ui.view">
        <field name="name">univ.sms.student.graph</field>
        <field name="model">univ.sms.student</field>
        <field name="arch" type="xml">
            <graph string="Sinh viên theo trạng thái" type="bar">
                <field name="state" type="row"/>
                <field name="program_id" type="col"/>
            </graph>
        </field>
    </record>

    <record id="view_student_pivot" model="ir.ui.view">
        <field name="name">univ.sms.student.pivot</field>
        <field name="model">univ.sms.student</field>
        <field name="arch" type="xml">
            <pivot string="Phân bổ sinh viên">
                <field name="program_id" type="row"/>
                <field name="state" type="col"/>
            </pivot>
        </field>
    </record>

    <record id="action_student_dashboard" model="ir.actions.act_window">
        <field name="name">Dashboard Sinh viên</field>
        <field name="res_model">univ.sms.student</field>
        <field name="view_mode">graph,pivot,list</field>
    </record>
</odoo>
C. QWeb PDF Report mới cần bổ sung
- certificate_report.xml      → Giấy xác nhận SV / Phiếu xin tạm vắng (Phase 7)
- conduct_score_report.xml    → Phiếu điểm rèn luyện cá nhân (Phase 7)
- registration_slip_report.xml → Phiếu đăng ký môn học đã xác nhận (Phase 6)
- attendance_sheet_report.xml  → Bảng điểm danh lớp theo tuần (Phase 2, bổ sung)
- transcript_report.xml        → Bảng điểm tổng hợp (đã có Phase 3)
- invoice_report.xml           → Hóa đơn điện tử (đã có Phase 3)
D. Dashboard Sinh viên trên Portal (không dùng Odoo backend view)
QWeb portal đơn giản — render số liệu tổng hợp (KHÔNG dùng chart.js phức tạp ở bản đầu, có thể nâng cấp Phase 2):
xml<template id="portal_academic_home_v2" inherit_id="univ_sms_portal.portal_academic_home">
    <xpath expr="//div[hasclass('row')]" position="before">
        <div class="row mt-3 mb-3">
            <div class="col-md-3"><div class="card text-center p-2">
                <h5>GPA hiện tại</h5><h3 t-esc="student.gpa"/></div></div>
            <div class="col-md-3"><div class="card text-center p-2">
                <h5>Số TC đã đạt</h5><h3 t-esc="student.passed_credit"/></div></div>
            <div class="col-md-3"><div class="card text-center p-2">
                <h5>Điểm rèn luyện</h5><h3 t-esc="student.latest_conduct_score"/></div></div>
            <div class="col-md-3"><div class="card text-center p-2">
                <h5>Công nợ học phí</h5><h3 t-esc="student.fee_balance"/></div></div>
        </div>
    </xpath>
</template>

⚠️ Các field gpa, passed_credit, latest_conduct_score, fee_balance là computed fields cần bổ sung vào univ.sms.student qua Class Inheritance từ các module Phase 3/7 tương ứng (mỗi module tự thêm field của mình, tránh module Phase 1 phình to).

