from odoo import models, fields


class UnivSmsSurveyResponse(models.Model):
    _name = 'univ.sms.survey.response'
    _description = 'Phản hồi khảo sát'
    _order = 'create_date desc'

    student_id = fields.Many2one('univ.sms.student', required=True)
    survey_instance_id = fields.Many2one('univ.sms.survey.instance', required=True)
    response_date = fields.Datetime(default=fields.Datetime.now)
    answer_data = fields.Text(string='Nội dung phản hồi')
    state = fields.Selection([
        ('draft', 'Chờ gửi'),
        ('submitted', 'Đã gửi'),
    ], default='draft')

    def action_submit(self):
        self.write({'state': 'submitted'})