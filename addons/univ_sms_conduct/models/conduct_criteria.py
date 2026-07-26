from odoo import models, fields


class UnivSmsConductCriteria(models.Model):
    _name = 'univ.sms.conduct.criteria'
    _description = 'Tiêu chí đánh giá rèn luyện'
    _order = 'group_name, name'

    name = fields.Char(required=True)
    group_name = fields.Selection([
        ('study_attitude', 'Ý thức học tập'),
        ('discipline', 'Ý thức chấp hành nội quy'),
        ('activity', 'Hoạt động đoàn thể, xã hội'),
        ('citizen', 'Quan hệ với cộng đồng'),
        ('class_role', 'Vai trò trong lớp/đoàn thể'),
    ], required=True)
    max_score = fields.Integer(required=True)
    active = fields.Boolean(default=True)