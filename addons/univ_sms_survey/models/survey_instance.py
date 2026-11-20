from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class UnivSmsSurveyInstance(models.Model):
    _name = 'univ.sms.survey.instance'
    _description = 'Đợt khảo sát'
    _order = 'create_date desc'

    name = fields.Char(required=True)
    survey_type_id = fields.Many2one('univ.sms.survey.type', required=True)
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    state = fields.Selection([
        ('draft', 'Soạn thảo'),
        ('open', 'Đang mở'),
        ('closed', 'Đã đóng'),
    ], default='draft')
    response_ids = fields.One2many('univ.sms.survey.response', 'survey_instance_id')
    response_count = fields.Integer(compute='_compute_response_count', store=True)

    @api.depends('response_ids')
    def _compute_response_count(self):
        for rec in self:
            rec.response_count = len(rec.response_ids)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_start > rec.date_end:
                raise ValidationError(_('Ngày bắt đầu khảo sát phải trước hoặc bằng ngày kết thúc.'))

    def _is_accepting_responses(self, today=None):
        """Đợt đang mở và hôm nay nằm trong [date_start, date_end]."""
        self.ensure_one()
        today = today or fields.Date.context_today(self)
        return (self.state == 'open'
                and self.date_start and self.date_end
                and self.date_start <= today <= self.date_end)

    def action_open(self):
        for rec in self:
            if rec.state == 'open':
                raise UserError(_('Đợt khảo sát "%s" đang mở.') % rec.name)
        self.write({'state': 'open'})

    def action_close(self):
        for rec in self:
            if rec.state != 'open':
                raise UserError(_('Chỉ đóng được đợt khảo sát đang mở.'))
        self.write({'state': 'closed'})

    def action_draft(self):
        for rec in self:
            if rec.state == 'draft':
                raise UserError(_('Đợt khảo sát "%s" đã ở trạng thái soạn thảo.') % rec.name)
        self.write({'state': 'draft'})
