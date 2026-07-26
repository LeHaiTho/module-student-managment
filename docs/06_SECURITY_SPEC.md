Security Groups (univ_sms_base/security/security_groups.xml)
xml<odoo>
    <record id="module_category_university" model="ir.module.category">
        <field name="name">University SMS</field>
    </record>

    <record id="group_univ_lecturer" model="res.groups">
        <field name="name">Giảng viên</field>
        <field name="category_id" ref="module_category_university"/>
    </record>

    <record id="group_univ_academic_officer" model="res.groups">
        <field name="name">Cán bộ Phòng đào tạo</field>
        <field name="category_id" ref="module_category_university"/>
        <field name="implied_ids" eval="[(4, ref('group_univ_lecturer'))]"/>
    </record>

    <record id="group_univ_admin" model="res.groups">
        <field name="name">Quản trị viên SMS</field>
        <field name="category_id" ref="module_category_university"/>
        <field name="implied_ids" eval="[(4, ref('group_univ_academic_officer'))]"/>
    </record>
</odoo>
Access Rights (ir.model.access.csv — mẫu cho univ_sms_student)
csvid,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_univ_sms_student_admin,student.admin,model_univ_sms_student,univ_sms_base.group_univ_admin,1,1,1,1
access_univ_sms_student_officer,student.officer,model_univ_sms_student,univ_sms_base.group_univ_academic_officer,1,1,1,0
access_univ_sms_student_lecturer,student.lecturer,model_univ_sms_student,univ_sms_base.group_univ_lecturer,1,0,0,0
access_univ_sms_enrollment_portal,enrollment.portal,model_univ_sms_enrollment,base.group_portal,1,0,0,0
Record Rule — Giảng viên chỉ xem sinh viên lớp mình dạy (univ_sms_attendance/security/security_rules.xml)
xml<record id="rule_student_lecturer_own_class" model="ir.rule">
    <field name="name">Lecturer: only own class students</field>
    <field name="model_id" ref="model_univ_sms_enrollment"/>
    <field name="domain_force">[('class_id.lecturer_id.user_id', '=', user.id)]</field>
    <field name="groups" eval="[(4, ref('univ_sms_base.group_univ_lecturer'))]"/>
</record>
Record Rule — Sinh viên chỉ xem dữ liệu của bản thân (Portal)
xml<record id="rule_enrollment_portal_own" model="ir.rule">
    <field name="name">Portal: student sees only own enrollment</field>
    <field name="model_id" ref="model_univ_sms_enrollment"/>
    <field name="domain_force">[('student_id.partner_id', '=', user.partner_id.id)]</field>
    <field name="groups" eval="[(4, ref('base.group_portal'))]"/>
</record>