from odoo import models, fields, api
from odoo.exceptions import ValidationError


class UnivSmsTimetable(models.Model):
    _name = 'univ.sms.timetable'
    _description = 'Thời khóa biểu'
    _order = 'class_id, day_of_week, start_time'

    class_id = fields.Many2one(
        'univ.sms.class',
        string='Lớp',
        required=True,
        ondelete='cascade',
    )
    day_of_week = fields.Selection([
        ('0', 'Thứ Hai'),
        ('1', 'Thứ Ba'),
        ('2', 'Thứ Tư'),
        ('3', 'Thứ Năm'),
        ('4', 'Thứ Sáu'),
        ('5', 'Thứ Bảy'),
        ('6', 'Chủ nhật'),
    ], string='Thứ', required=True)
    start_time = fields.Float(string='Giờ bắt đầu', required=True)
    end_time = fields.Float(string='Giờ kết thúc', required=True)
    room = fields.Char(string='Phòng học')
    building = fields.Char(string='Tòa nhà')

    @api.constrains('start_time', 'end_time')
    def _check_time_range(self):
        for record in self:
            if record.start_time and record.end_time and record.start_time >= record.end_time:
                raise ValidationError('Giờ kết thúc phải sau giờ bắt đầu!')

    def _format_time(self, time_value):
        """Convert float time (e.g. 8.5) to string (e.g. '08:30')"""
        hours = int(time_value)
        minutes = int((time_value - hours) * 60)
        return f'{hours:02d}:{minutes:02d}'
