from markupsafe import Markup, escape

from odoo import _, api, fields, models

OUTCOMES = [
    ('contacted', 'Đã liên hệ'),
    ('plan_agreed', 'Đã thống nhất kế hoạch'),
    ('referred', 'Chuyển đơn vị hỗ trợ'),
    ('resolved', 'Đã giải quyết'),
]


class UnivSmsWarningConsultation(models.Model):
    _name = 'univ.sms.warning.consultation'
    _description = 'Nhật ký tư vấn cảnh báo sớm'
    _order = 'date desc, id desc'

    warning_id = fields.Many2one(
        'univ.sms.warning', string='Cảnh báo', required=True, ondelete='cascade', index=True)
    student_id = fields.Many2one(
        related='warning_id.student_id', store=True, string='Sinh viên')
    user_id = fields.Many2one(
        'res.users', string='Người tư vấn', required=True, default=lambda self: self.env.user)
    date = fields.Datetime(string='Thời gian', required=True, default=fields.Datetime.now)
    note = fields.Text(string='Nội dung tư vấn', required=True)
    outcome = fields.Selection(OUTCOMES, string='Kết quả', required=True, default='contacted')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        labels = dict(OUTCOMES)
        for rec in records:
            warning = rec.warning_id
            if warning.state == 'new':
                warning.state = 'in_progress'
            warning.message_post(
                body=Markup('<b>%s</b> (%s)<br/>%s') % (
                    _('Ghi nhận tư vấn'), labels.get(rec.outcome, ''),
                    Markup('<br/>').join(escape(x) for x in (rec.note or '').splitlines())),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        return records
