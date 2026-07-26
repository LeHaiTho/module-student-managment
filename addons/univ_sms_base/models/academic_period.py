from odoo import models, fields, api
from odoo.exceptions import ValidationError


class UnivSmsAcademicYear(models.Model):
    _name = 'univ.sms.academic.year'
    _description = 'Năm học'
    _order = 'date_start desc'

    name = fields.Char(string='Năm học', required=True, help='Ví dụ: 2025-2026')
    date_start = fields.Date(string='Ngày bắt đầu', required=True)
    date_end = fields.Date(string='Ngày kết thúc', required=True)
    term_ids = fields.One2many('univ.sms.term', 'academic_year_id', string='Học kỳ')

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for record in self:
            if record.date_start and record.date_end and record.date_start >= record.date_end:
                raise ValidationError('Ngày kết thúc phải sau ngày bắt đầu!')


class UnivSmsTerm(models.Model):
    _name = 'univ.sms.term'
    _description = 'Học kỳ'
    _order = 'academic_year_id, date_start'

    name = fields.Char(string='Học kỳ', required=True, help='Ví dụ: Học kỳ 1')
    academic_year_id = fields.Many2one(
        'univ.sms.academic.year',
        string='Năm học',
        required=True,
    )
    date_start = fields.Date(string='Ngày bắt đầu', required=True)
    date_end = fields.Date(string='Ngày kết thúc', required=True)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for record in self:
            if record.date_start and record.date_end and record.date_start >= record.date_end:
                raise ValidationError('Ngày kết thúc phải sau ngày bắt đầu!')
