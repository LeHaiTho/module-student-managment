from odoo import models, fields


class UnivSmsExam(models.Model):
    _name = 'univ.sms.exam'
    _description = 'Kỳ thi / Bài kiểm tra'
    _order = 'date desc'

    name = fields.Char(string='Tên kỳ thi', required=True)
    class_id = fields.Many2one(
        'univ.sms.class',
        string='Lớp',
        required=True,
    )
    term_id = fields.Many2one(
        'univ.sms.term',
        string='Học kỳ',
        related='class_id.term_id',
        store=True,
    )
    subject_id = fields.Many2one(
        'univ.sms.subject',
        string='Môn học',
        related='class_id.subject_id',
        store=True,
    )
    exam_type = fields.Selection([
        ('midterm', 'Giữa kỳ'),
        ('final', 'Cuối kỳ'),
        ('quiz', 'Kiểm tra nhanh'),
        ('project', 'Đồ án / Bài tập lớn'),
        ('other', 'Khác'),
    ], string='Loại kỳ thi', default='midterm', required=True)
    date = fields.Date(string='Ngày thi')
    max_score = fields.Float(string='Điểm tối đa', default=10.0)
    result_ids = fields.One2many(
        'univ.sms.exam.result',
        'exam_id',
        string='Kết quả',
    )
    state = fields.Selection([
        ('draft', 'Dự kiến'),
        ('in_progress', 'Đang chấm'),
        ('done', 'Đã hoàn thành'),
    ], string='Trạng thái', default='draft')

    def action_start_grading(self):
        for record in self:
            record.state = 'in_progress'

    def action_done(self):
        for record in self:
            record.state = 'done'

    def action_reset(self):
        for record in self:
            record.state = 'draft'

    def action_load_students(self):
        """Tạo kết quả rỗng cho tất cả sinh viên trong lớp"""
        self.ensure_one()
        existing = self.result_ids.mapped('student_id').ids
        enrollments = self.env['univ.sms.enrollment'].search([
            ('class_id', '=', self.class_id.id),
            ('state', '=', 'registered'),
        ])
        lines = []
        for enr in enrollments:
            if enr.student_id.id not in existing:
                lines.append({
                    'exam_id': self.id,
                    'student_id': enr.student_id.id,
                    'score': 0.0,
                })
        if lines:
            self.env['univ.sms.exam.result'].create(lines)
