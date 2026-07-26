from odoo import models, fields, api


class UnivSmsRegistrationPeriod(models.Model):
    _name = 'univ.sms.registration.period'
    _description = 'Đợt đăng ký môn học'
    _order = 'date_start desc'

    name = fields.Char(required=True)
    term_id = fields.Many2one('univ.sms.term', required=True)
    date_start = fields.Datetime(required=True)
    date_end = fields.Datetime(required=True)
    reg_type = fields.Selection([
        ('regular', 'Đăng ký chính thức (DKMH)'),
        ('elective', 'Đăng ký nguyện vọng (DKMNV)'),
    ], required=True, default='regular')
    min_credit = fields.Integer(string='Tín chỉ tối thiểu')
    max_credit = fields.Integer(string='Tín chỉ tối đa')
    description = fields.Text(string='Ghi chú')
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Chưa mở'),
        ('open', 'Đang mở'),
        ('closed', 'Đã đóng'),
    ], default='draft')

    def action_open(self):
        self.write({'state': 'open'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_draft(self):
        self.write({'state': 'draft'})