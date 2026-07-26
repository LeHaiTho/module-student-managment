from odoo import models, fields, api


class UnivSmsHealthInsurance(models.Model):
    _name = 'univ.sms.health.insurance'
    _description = 'Bảo hiểm y tế sinh viên'
    _order = 'student_id'

    student_id = fields.Many2one('univ.sms.student', required=True)
    insurance_code = fields.Char(string='Mã thẻ BHYT', required=True)
    issue_place_id = fields.Many2one('res.country.state', string='Nơi đăng ký KCB')
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    payment_state = fields.Selection([
        ('unpaid', 'Chưa đóng'),
        ('paid', 'Đã đóng'),
    ], default='unpaid')
    state = fields.Selection([
        ('draft', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
    ], default='draft')

    @api.depends('date_end')
    def _compute_is_expired(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_expired = bool(rec.date_end) and rec.date_end < today

    is_expired = fields.Boolean(compute='_compute_is_expired', store=True)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_draft(self):
        self.write({'state': 'draft'})