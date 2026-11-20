from odoo import _, fields, models
from odoo.exceptions import UserError


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

    _sql_constraints = [
        ('student_survey_uniq', 'unique(student_id, survey_instance_id)',
         'Mỗi sinh viên chỉ được gửi một phản hồi cho một đợt khảo sát!'),
    ]

    _LOCKED_FIELDS = {'answer_data', 'student_id', 'survey_instance_id', 'response_date'}

    def write(self, vals):
        if (self._LOCKED_FIELDS & set(vals) and not self.env.su
                and not self.env.user.has_group('univ_sms_base.group_univ_admin')
                and any(rec.state == 'submitted' for rec in self)):
            raise UserError(_('Phản hồi khảo sát đã gửi thì không thể thay đổi.'))
        return super().write(vals)

    def action_submit(self):
        for rec in self:
            if rec.state == 'submitted':
                raise UserError(_('Phản hồi này đã được gửi trước đó.'))
            if not rec.survey_instance_id._is_accepting_responses():
                raise UserError(_('Đợt khảo sát "%s" không còn nhận phản hồi.')
                                % rec.survey_instance_id.name)
            if not (rec.answer_data or '').strip():
                raise UserError(_('Vui lòng nhập nội dung phản hồi trước khi gửi.'))
        self.write({'state': 'submitted', 'response_date': fields.Datetime.now()})
