from odoo import models, fields


class UnivSmsFaculty(models.Model):
    _name = 'univ.sms.faculty'
    _description = 'Khoa'
    _order = 'name'

    name = fields.Char(string='Tên khoa', required=True, translate=True)
    code = fields.Char(string='Mã khoa', required=True)
    dean_id = fields.Many2one('res.partner', string='Trưởng khoa')
    department_ids = fields.One2many('univ.sms.department', 'faculty_id', string='Bộ môn')
    active = fields.Boolean(string='Hoạt động', default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã khoa đã tồn tại!'),
    ]
