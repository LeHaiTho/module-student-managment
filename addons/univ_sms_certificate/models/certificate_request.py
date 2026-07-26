from odoo import models, fields, api


class UnivSmsCertificateRequest(models.Model):
    _name = 'univ.sms.certificate.request'
    _description = 'Yêu cầu giấy chứng nhận'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    student_id = fields.Many2one('univ.sms.student', required=True)
    certificate_type_id = fields.Many2one('univ.sms.certificate.type', required=True)
    request_date = fields.Date(default=fields.Date.today)
    reason = fields.Text(string='Lý do yêu cầu')
    state = fields.Selection([
        ('draft', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('completed', 'Hoàn thành'),
        ('rejected', 'Từ chối'),
    ], default='draft', tracking=True)
    fee_amount = fields.Float(related='certificate_type_id.fee_amount', string='Phí')
    fee_payment_state = fields.Selection([
        ('unpaid', 'Chưa đóng'),
        ('paid', 'Đã đóng'),
    ], default='unpaid')
    output_file = fields.Binary(string='File giấy chứng nhận')
    output_filename = fields.Char(string='Tên file')

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_draft(self):
        self.write({'state': 'draft'})