from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class UnivSmsNotification(models.Model):
    _name = 'univ.sms.notification'
    _inherit = ['mail.thread']
    _description = 'Thông báo'
    _order = 'is_pinned desc, publish_date desc'

    title = fields.Char(required=True, tracking=True)
    content = fields.Html(required=True)
    publish_date = fields.Datetime(default=fields.Datetime.now)
    expire_date = fields.Datetime()
    target_audience = fields.Selection([
        ('all', 'Toàn trường'),
        ('program', 'Theo ngành'),
        ('class', 'Theo lớp'),
    ], default='all')
    program_ids = fields.Many2many('univ.sms.program')
    class_ids = fields.Many2many('univ.sms.class')
    is_pinned = fields.Boolean(string='Ghim lên đầu')
    attachment_ids = fields.Many2many('ir.attachment')
    state = fields.Selection([
        ('draft', 'Soạn'),
        ('published', 'Đã đăng'),
        ('archived', 'Lưu trữ'),
    ], default='draft')

    @api.constrains('publish_date', 'expire_date')
    def _check_dates(self):
        for rec in self:
            if rec.publish_date and rec.expire_date and rec.expire_date <= rec.publish_date:
                raise ValidationError(_('Ngày hết hạn thông báo phải sau ngày đăng.'))

    def _check_states(self, allowed, action_label):
        labels = dict(self._fields['state'].selection)
        for rec in self:
            if rec.state not in allowed:
                raise UserError(_('Không thể %(action)s thông báo ở trạng thái "%(state)s".',
                                  action=action_label, state=labels.get(rec.state, rec.state)))

    def action_publish(self):
        self._check_states(('draft', 'archived'), _('đăng'))
        self.write({'state': 'published', 'publish_date': fields.Datetime.now()})

    def action_archive(self):
        self._check_states(('published',), _('lưu trữ'))
        self.write({'state': 'archived'})

    def action_draft(self):
        self._check_states(('published', 'archived'), _('mở lại'))
        self.write({'state': 'draft'})