from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

DUPLICATE_WINDOW_SECONDS = 60


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

    @api.model_create_multi
    def create(self, vals_list):
        since = fields.Datetime.now() - timedelta(seconds=DUPLICATE_WINDOW_SECONDS)
        for vals in vals_list:
            subject = (vals.get('subject') or '').strip()
            student_id = vals.get('student_id')
            if subject and student_id and self.sudo().search_count([
                ('student_id', '=', student_id),
                ('subject', '=', subject),
                ('create_date', '>=', since),
            ]):
                raise ValidationError(_(
                    'Bạn vừa gửi góp ý với cùng tiêu đề. Vui lòng chờ ít nhất 1 phút trước khi gửi lại.'))
        return super().create(vals_list)

    def _check_states(self, allowed, action_label):
        labels = dict(self._fields['state'].selection)
        for rec in self:
            if rec.state not in allowed:
                raise UserError(_('Không thể %(action)s góp ý ở trạng thái "%(state)s".',
                                  action=action_label, state=labels.get(rec.state, rec.state)))

    def action_in_progress(self):
        self._check_states(('new',), _('tiếp nhận'))
        self.write({'state': 'in_progress'})

    def action_resolved(self):
        self._check_states(('new', 'in_progress'), _('đánh dấu đã xử lý'))
        self.write({'state': 'resolved'})

    def action_close(self):
        self._check_states(('new', 'in_progress', 'resolved'), _('đóng'))
        self.write({'state': 'closed'})
