from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    student_id = fields.Many2one(
        'univ.sms.student',
        string='Sinh viên',
        compute='_compute_student_id',
        store=False,
    )
    is_student = fields.Boolean(
        string='Là sinh viên',
        compute='_compute_is_student',
        store=True,
    )

    def _compute_student_id(self):
        """Tìm sinh viên liên kết với partner này (không lưu trữ)"""
        Student = self.env['univ.sms.student']
        for partner in self:
            student = Student.search([('partner_id', '=', partner.id)], limit=1)
            partner.student_id = student.id if student else False

    def _compute_is_student(self):
        """Xác định partner có phải sinh viên không (lưu trữ)"""
        Student = self.env['univ.sms.student']
        for partner in self:
            partner.is_student = bool(
                Student.search([('partner_id', '=', partner.id)], limit=1)
            )
