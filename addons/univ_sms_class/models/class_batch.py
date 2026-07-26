from odoo import models, fields, api


class UnivSmsClass(models.Model):
    _name = 'univ.sms.class'
    _description = 'Lớp học'
    _order = 'term_id, name'

    name = fields.Char(string='Tên lớp', required=True)
    code = fields.Char(string='Mã lớp', required=True)
    subject_id = fields.Many2one(
        'univ.sms.subject',
        string='Môn học',
        required=True,
    )
    lecturer_id = fields.Many2one(
        'res.partner',
        string='Giảng viên',
        domain="[('is_company', '=', False)]",
    )
    term_id = fields.Many2one(
        'univ.sms.term',
        string='Học kỳ',
        required=True,
    )
    max_students = fields.Integer(string='Sĩ số tối đa', default=50)
    state = fields.Selection([
        ('draft', 'Dự kiến'),
        ('open', 'Đang mở'),
        ('closed', 'Đã kết thúc'),
    ], string='Trạng thái', default='draft')

    enrollment_ids = fields.One2many(
        'univ.sms.enrollment',
        'class_id',
        string='Đăng ký học',
    )
    enrollment_count = fields.Integer(
        string='Số sinh viên',
        compute='_compute_enrollment_count',
    )
    timetable_ids = fields.One2many(
        'univ.sms.timetable',
        'class_id',
        string='Thời khóa biểu',
    )

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã lớp đã tồn tại!'),
    ]

    @api.depends('enrollment_ids')
    def _compute_enrollment_count(self):
        for record in self:
            record.enrollment_count = len(record.enrollment_ids)

    def action_view_enrollments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Sinh viên lớp {self.name}',
            'res_model': 'univ.sms.enrollment',
            'view_mode': 'tree,form',
            'domain': [('class_id', '=', self.id)],
            'context': {'default_class_id': self.id},
        }

    def action_open(self):
        for record in self:
            record.state = 'open'

    def action_close(self):
        for record in self:
            record.state = 'closed'

    def action_reset_draft(self):
        for record in self:
            record.state = 'draft'
