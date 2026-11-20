from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

PENDING_STATES = ('draft', 'approved')


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

    @api.model_create_multi
    def create(self, vals_list):
        Type = self.env['univ.sms.certificate.type'].with_context(active_test=False)
        for vals in vals_list:
            ctype = Type.browse(vals.get('certificate_type_id') or 0).exists()
            if ctype and not ctype.active:
                raise ValidationError(_('Loại giấy "%s" hiện không còn nhận yêu cầu.') % ctype.name)
        return super().create(vals_list)

    @api.constrains('student_id', 'certificate_type_id', 'state')
    def _check_no_duplicate_pending(self):
        for rec in self:
            if rec.state not in PENDING_STATES:
                continue
            dup = self.search_count([
                ('id', '!=', rec.id),
                ('student_id', '=', rec.student_id.id),
                ('certificate_type_id', '=', rec.certificate_type_id.id),
                ('state', 'in', PENDING_STATES),
            ])
            if dup:
                raise ValidationError(_(
                    'Bạn đã có yêu cầu "%s" đang xử lý. Vui lòng chờ kết quả trước khi gửi yêu cầu mới.'
                ) % rec.certificate_type_id.name)

    def _check_states(self, allowed, action_label):
        labels = dict(self._fields['state'].selection)
        for rec in self:
            if rec.state not in allowed:
                raise UserError(_('Không thể %(action)s yêu cầu ở trạng thái "%(state)s".',
                                  action=action_label, state=labels.get(rec.state, rec.state)))

    def action_approve(self):
        self._check_states(('draft',), _('duyệt'))
        self.write({'state': 'approved'})

    def action_complete(self):
        self._check_states(('approved',), _('hoàn thành'))
        self.write({'state': 'completed'})

    def action_reject(self):
        self._check_states(('draft', 'approved'), _('từ chối'))
        self.write({'state': 'rejected'})

    def action_draft(self):
        self._check_states(('rejected',), _('đặt lại nháp'))
        self.write({'state': 'draft'})
