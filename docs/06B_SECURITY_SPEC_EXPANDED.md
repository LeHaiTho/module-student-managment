Bổ sung Security Groups (univ_sms_base/security/security_groups_v2.xml)
xml<odoo>
    <!-- Phòng Tài chính -->
    <record id="group_univ_finance_office" model="res.groups">
        <field name="name">Phòng Tài chính - Kế toán</field>
        <field name="category_id" ref="module_category_university"/>
        <field name="implied_ids" eval="[(4, ref('group_univ_lecturer'))]"/>
    </record>

    <!-- Phòng Công tác Sinh viên -->
    <record id="group_univ_student_affairs_office" model="res.groups">
        <field name="name">Phòng Công tác Sinh viên</field>
        <field name="category_id" ref="module_category_university"/>
        <field name="implied_ids" eval="[(4, ref('group_univ_lecturer'))]"/>
    </record>

    <!-- Trưởng Khoa -->
    <record id="group_univ_dean" model="res.groups">
        <field name="name">Trưởng Khoa</field>
        <field name="category_id" ref="module_category_university"/>
        <field name="implied_ids" eval="[(4, ref('group_univ_lecturer'))]"/>
    </record>

    <!-- Cố vấn học tập -->
    <record id="group_univ_advisor" model="res.groups">
        <field name="name">Cố vấn học tập</field>
        <field name="category_id" ref="module_category_university"/>
        <field name="implied_ids" eval="[(4, ref('group_univ_lecturer'))]"/>
    </record>
</odoo>
Record Rules — Workflow đánh giá rèn luyện (3 cấp)
xml<odoo>
    <!-- SV chỉ thấy/sửa bản ghi của chính mình khi state=draft -->
    <record id="rule_conduct_student_own" model="ir.rule">
        <field name="name">Conduct: student own record (draft only via UI button)</field>
        <field name="model_id" ref="model_univ_sms_conduct_score"/>
        <field name="domain_force">[('student_id.partner_id', '=', user.partner_id.id)]</field>
        <field name="groups" eval="[(4, ref('base.group_portal'))]"/>
    </record>

    <!-- CVHT chỉ thấy bản ghi của SV thuộc lớp mình cố vấn -->
    <record id="rule_conduct_advisor" model="ir.rule">
        <field name="name">Conduct: advisor sees own class students</field>
        <field name="model_id" ref="model_univ_sms_conduct_score"/>
        <field name="domain_force">[('student_id.class_id.advisor_id.user_id', '=', user.id)]</field>
        <field name="groups" eval="[(4, ref('group_univ_advisor'))]"/>
    </record>

    <!-- Trưởng khoa thấy toàn bộ SV trong khoa -->
    <record id="rule_conduct_dean" model="ir.rule">
        <field name="name">Conduct: dean sees faculty students</field>
        <field name="model_id" ref="model_univ_sms_conduct_score"/>
        <field name="domain_force">[('student_id.program_id.department_id.faculty_id.dean_id.user_id', '=', user.id)]</field>
        <field name="groups" eval="[(4, ref('group_univ_dean'))]"/>
    </record>
</odoo>
Access Rights bổ sung (ir.model.access.csv snippet)
csvid,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_registration_portal,registration.portal,model_univ_sms_registration,base.group_portal,1,1,1,1
access_registration_officer,registration.officer,model_univ_sms_registration,univ_sms_base.group_univ_academic_office,1,1,1,1
access_conduct_score_portal,conduct.portal,model_univ_sms_conduct_score,base.group_portal,1,1,1,0
access_conduct_score_advisor,conduct.advisor,model_univ_sms_conduct_score,univ_sms_base.group_univ_advisor,1,1,0,0
access_conduct_score_dean,conduct.dean,model_univ_sms_conduct_score,univ_sms_base.group_univ_dean,1,1,0,0
access_certificate_request_portal,cert.portal,model_univ_sms_certificate_request,base.group_portal,1,1,1,0
access_certificate_request_affairs,cert.affairs,model_univ_sms_certificate_request,univ_sms_base.group_univ_student_affairs_office,1,1,0,1
access_feedback_portal,feedback.portal,model_univ_sms_feedback,base.group_portal,1,1,1,0
access_feedback_office,feedback.office,model_univ_sms_feedback,univ_sms_base.group_univ_academic_office,1,1,0,0