from odoo import models, fields


class UnivSmsElectiveWish(models.Model):
    _name = 'univ.sms.elective.wish'
    _description = 'Đăng ký môn nguyện vọng'
    _order = 'priority'

    student_id = fields.Many2one('univ.sms.student', required=True)
    offering_id = fields.Many2one('univ.sms.course.offering', required=True,
        domain=[('subject_id.subject_type', '=', 'elective')])
    priority = fields.Integer(string='Độ ưu tiên', default=1)
    state = fields.Selection([
        ('pending', 'Chờ xử lý'),
        ('approved', 'Được chọn'),
        ('rejected', 'Không đủ slot'),
    ], default='pending')