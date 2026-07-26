from odoo import models, fields


class UnivSmsSubject(models.Model):
    _name = 'univ.sms.subject'
    _description = 'Môn học'
    _order = 'name'

    name = fields.Char(string='Tên môn học', required=True, translate=True)
    code = fields.Char(string='Mã môn học', required=True)
    credit = fields.Float(string='Số tín chỉ', required=True)
    program_ids = fields.Many2many(
        'univ.sms.program',
        string='Thuộc ngành',
    )
    is_active = fields.Boolean(string='Còn áp dụng', default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã môn học đã tồn tại!'),
    ]
