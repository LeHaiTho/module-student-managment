from odoo import models, fields, api


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

    def action_open(self):
        self.write({'state': 'open'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_draft(self):
        self.write({'state': 'draft'})