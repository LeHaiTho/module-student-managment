from odoo import models, fields


class UnivSmsEnrollment(models.Model):
    _name = 'univ.sms.enrollment'
    _description = 'Đăng ký học môn'
    _order = 'student_id, term_id'

    student_id = fields.Many2one(
        'univ.sms.student',
        string='Sinh viên',
        required=True,
        ondelete='cascade',
    )
    subject_id = fields.Many2one(
        'univ.sms.subject',
        string='Môn học',
        required=True,
    )
    term_id = fields.Many2one(
        'univ.sms.term',
        string='Học kỳ',
        required=True,
    )
    # class_id will be added when univ_sms_class module is installed (Phase 2)
    # class_id = fields.Many2one('univ.sms.class', string='Lớp')
    state = fields.Selection([
        ('registered', 'Đã đăng ký'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ], string='Trạng thái', default='registered')

    _sql_constraints = [
        (
            'enroll_uniq',
            'unique(student_id, subject_id, term_id)',
            'Sinh viên đã đăng ký môn này trong học kỳ này!',
        ),
    ]

    def action_complete(self):
        for record in self:
            record.state = 'completed'

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'

    def action_reset(self):
        for record in self:
            record.state = 'registered'
