from odoo import models, fields


class UnivSmsProgram(models.Model):
    _name = 'univ.sms.program'
    _description = 'Ngành đào tạo'
    _order = 'name'

    name = fields.Char(string='Tên ngành', required=True)
    code = fields.Char(string='Mã ngành', required=True)
    department_id = fields.Many2one(
        'univ.sms.department',
        string='Bộ môn',
        required=True,
    )
    total_credits = fields.Integer(string='Tổng số tín chỉ')
    duration_years = fields.Integer(string='Thời gian đào tạo (năm)', default=4)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã ngành đã tồn tại!'),
    ]
