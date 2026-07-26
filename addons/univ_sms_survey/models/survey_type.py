from odoo import models, fields


class UnivSmsSurveyType(models.Model):
    _name = 'univ.sms.survey.type'
    _description = 'Loại khảo sát'

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã loại khảo sát phải là duy nhất!'),
    ]