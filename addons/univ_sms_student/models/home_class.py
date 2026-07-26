from odoo import models, fields, api


class UnivSmsHomeClass(models.Model):
    _name = 'univ.sms.home.class'
    _description = 'Lớp hành chính'
    _order = 'name'

    name = fields.Char(string='Tên lớp', required=True)
    code = fields.Char(string='Mã lớp', required=True)
    program_id = fields.Many2one(
        'univ.sms.program',
        string='Ngành',
        required=True,
    )
    academic_year_id = fields.Many2one(
        'univ.sms.academic.year',
        string='Niên khóa',
        required=True,
    )
    advisor_id = fields.Many2one(
        'res.partner',
        string='Cố vấn học tập',
        domain=[('is_company', '=', False)],
    )
    student_ids = fields.One2many(
        'univ.sms.student',
        'home_class_id',
        string='Sinh viên',
    )
    student_count = fields.Integer(
        string='Số sinh viên',
        compute='_compute_student_count',
        store=True,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã lớp hành chính đã tồn tại!'),
    ]

    @api.depends('student_ids')
    def _compute_student_count(self):
        for record in self:
            record.student_count = len(record.student_ids)

    def action_view_students(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Sinh viên lớp {self.name}',
            'res_model': 'univ.sms.student',
            'view_mode': 'tree,form',
            'domain': [('home_class_id', '=', self.id)],
            'context': {'default_home_class_id': self.id},
        }

    def name_get(self):
        return [(r.id, f"{r.code} - {r.name}") for r in self]
