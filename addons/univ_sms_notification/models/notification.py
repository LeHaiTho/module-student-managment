from odoo import models, fields


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

    def action_publish(self):
        self.write({'state': 'published', 'publish_date': fields.Datetime.now()})

    def action_archive(self):
        self.write({'state': 'archived'})

    def action_draft(self):
        self.write({'state': 'draft'})