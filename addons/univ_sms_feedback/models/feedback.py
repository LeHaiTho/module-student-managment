from odoo import models, fields


class UnivSmsFeedback(models.Model):
    _name = 'univ.sms.feedback'
    _description = 'Phản hồi/Góp ý của sinh viên'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    student_id = fields.Many2one('univ.sms.student', required=True,
        default=lambda s: s._default_student())
    category = fields.Selection([
        ('academic', 'Học vụ'),
        ('facility', 'Cơ sở vật chất'),
        ('service', 'Dịch vụ hành chính'),
        ('other', 'Khác'),
    ], required=True)
    subject = fields.Char(required=True)
    description = fields.Text(required=True)
    department_id = fields.Many2one('univ.sms.department', string='Gửi đến bộ phận')
    state = fields.Selection([
        ('new', 'Mới'),
        ('in_progress', 'Đang xử lý'),
        ('resolved', 'Đã xử lý'),
        ('closed', 'Đã đóng'),
    ], default='new', tracking=True)
    response = fields.Text(string='Phản hồi từ phòng ban')

    def _default_student(self):
        return self.env['univ.sms.student'].search(
            [('partner_id', '=', self.env.user.partner_id.id)], limit=1)

    def action_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_resolved(self):
        self.write({'state': 'resolved'})

    def action_close(self):
        self.write({'state': 'closed'})