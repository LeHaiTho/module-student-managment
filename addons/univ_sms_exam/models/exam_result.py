from odoo import models, fields, api
from odoo.exceptions import ValidationError


class UnivSmsExamResult(models.Model):
    _name = 'univ.sms.exam.result'
    _description = 'Kết quả thi'
    _order = 'exam_id, student_id'

    exam_id = fields.Many2one(
        'univ.sms.exam',
        string='Kỳ thi',
        required=True,
        ondelete='cascade',
    )
    student_id = fields.Many2one(
        'univ.sms.student',
        string='Sinh viên',
        required=True,
    )
    # Related fields để portal template và prerequisite check dùng được
    subject_id = fields.Many2one(
        'univ.sms.subject',
        string='Môn học',
        related='exam_id.subject_id',
        store=True,
    )
    class_id = fields.Many2one(
        'univ.sms.class',
        string='Lớp',
        related='exam_id.class_id',
        store=True,
    )
    term_id = fields.Many2one(
        'univ.sms.term',
        string='Học kỳ',
        related='exam_id.class_id.term_id',
        store=True,
    )
    score = fields.Float(string='Điểm', digits=(4, 2))
    max_score = fields.Float(
        string='Điểm tối đa',
        related='exam_id.max_score',
        store=True,
    )
    percentage = fields.Float(
        string='Tỷ lệ %',
        compute='_compute_percentage',
        store=True,
    )
    is_passed = fields.Boolean(
        string='Đạt',
        compute='_compute_is_passed',
        store=True,
    )
    note = fields.Char(string='Ghi chú')

    _sql_constraints = [
        (
            'result_uniq',
            'unique(exam_id, student_id)',
            'Sinh viên đã có kết quả cho kỳ thi này!',
        ),
    ]

    @api.depends('score', 'max_score')
    def _compute_percentage(self):
        for record in self:
            if record.max_score:
                record.percentage = round(record.score / record.max_score * 100, 2)
            else:
                record.percentage = 0.0

    @api.depends('score', 'max_score')
    def _compute_is_passed(self):
        for record in self:
            if record.max_score:
                # Đạt khi >= 50% điểm tối đa (thang 10 thì >= 5.0)
                record.is_passed = record.score >= (record.max_score * 0.5)
            else:
                record.is_passed = False

    @api.constrains('score')
    def _check_score_range(self):
        for record in self:
            if record.score < 0:
                raise ValidationError('Điểm không được âm!')
            if record.max_score and record.score > record.max_score:
                raise ValidationError(
                    f'Điểm ({record.score}) không được vượt quá điểm tối đa ({record.max_score})!'
                )
