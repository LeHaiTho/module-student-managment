Kiến trúc

Kế thừa CustomerPortal (controller addons/portal/controllers/portal.py) — chuẩn Odoo cho mọi portal module (eCommerce, Helpdesk...).
Route mới: /my/academic (Dashboard sinh viên), /my/academic/transcript, /my/academic/attendance, /my/academic/timetable, /my/academic/fees.

Controller mẫu (univ_sms_portal/controllers/portal.py)
pythonfrom odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request, route

class UnivSmsPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        student = request.env['univ.sms.student'].sudo().search(
            [('partner_id', '=', partner.id)], limit=1)
        if 'enrollment_count' in counters:
            values['enrollment_count'] = student.enrollment_ids and \
                len(student.enrollment_ids) or 0
        values['sms_student'] = student
        return values

    @route(['/my/academic'], type='http', auth='user', website=True)
    def portal_academic_home(self, **kw):
        partner = request.env.user.partner_id
        student = request.env['univ.sms.student'].sudo().search(
            [('partner_id', '=', partner.id)], limit=1)
        return request.render('univ_sms_portal.portal_academic_home', {
            'student': student,
            'page_name': 'academic_home',
        })

    @route(['/my/academic/transcript'], type='http', auth='user', website=True)
    def portal_transcript(self, **kw):
        student = request.env['univ.sms.student'].sudo().search(
            [('partner_id', '=', request.env.user.partner_id.id)], limit=1)
        results = request.env['univ.sms.exam.result'].sudo().search(
            [('student_id', '=', student.id)])
        return request.render('univ_sms_portal.portal_transcript', {
            'student': student,
            'results': results,
        })

⚠️ Lưu ý bảo mật: dùng .sudo() để bypass quyền model, nhưng bắt buộc filter theo partner_id = request.env.user.partner_id.id ngay trong domain search() — không phụ thuộc record rule khi đã sudo. Đây là điểm dễ bị bỏ sót nhất khi AI Agent generate controller.

QWeb Template gốc (portal_templates.xml)
xml<template id="portal_academic_home" name="Academic Home">
    <t t-call="portal.portal_layout">
        <t t-set="breadcrumbs_searchbar" t-value="True"/>
        <div class="o_portal_my_doc_table">
            <h3>Xin chào, <t t-esc="student.name"/></h3>
            <p>MSSV: <t t-esc="student.student_code"/></p>
            <p>Ngành: <t t-esc="student.program_id.name"/></p>
            <div class="row mt-4">
                <a href="/my/academic/transcript" class="btn btn-primary col-md-3 mx-2">Bảng điểm</a>
                <a href="/my/academic/attendance" class="btn btn-secondary col-md-3 mx-2">Điểm danh</a>
                <a href="/my/academic/fees" class="btn btn-secondary col-md-3 mx-2">Học phí</a>
            </div>
        </div>
    </t>
</template>
Thêm menu Portal vào trang /my (kế thừa portal.portal_my_home)
xml<template id="portal_my_home_academic" inherit_id="portal.portal_my_home">
    <xpath expr="//div[hasclass('o_portal_docs')]" position="inside">
        <t t-call="portal.portal_docs_entry">
            <t t-set="title">Học tập</t>
            <t t-set="url" t-value="'/my/academic'"/>
            <t t-set="icon" t-value="'/univ_sms_portal/static/src/img/academic_icon.png'"/>
        </t>
    </xpath>
</template>