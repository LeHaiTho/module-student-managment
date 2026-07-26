from odoo import models, fields


class UnivSmsDepartment(models.Model):
    _name = 'univ.sms.department'
    _description = 'Bộ môn'
    _order = 'name'

    name = fields.Char(string='Tên bộ môn', required=True, translate=True)
    code = fields.Char(string='Mã bộ môn', required=True)
    faculty_id = fields.Many2one(
        'univ.sms.faculty',
        string='Khoa',
        required=True,
        ondelete='cascade',
    )
    program_ids = fields.One2many('univ.sms.program', 'department_id', string='Ngành đào tạo')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã bộ môn đã tồn tại!'),
    ]
