from odoo import api, models, fields


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

    ineligible_enrollment_ids = fields.Many2many(
        'univ.sms.enrollment',
        string='Sinh viên không đủ điều kiện dự thi',
        compute='_compute_ineligible_enrollment_ids',
    )

    @api.depends('class_id')
    def _compute_ineligible_enrollment_ids(self):
        Enrollment = self.env['univ.sms.enrollment']
        for record in self:
            record.ineligible_enrollment_ids = Enrollment.search([
                ('class_id', '=', record.class_id.id),
                ('state', '=', 'registered'),
                ('exam_eligible', '=', False),
            ]) if record.class_id else Enrollment

    def action_compute_exam_eligibility(self):
        self.ensure_one()
        return self.class_id.action_compute_exam_eligibility()

    def action_load_students(self):
        """Tính lại điều kiện dự thi rồi tạo kết quả rỗng cho sinh viên đủ điều kiện.

        Lặp lại an toàn: sinh viên đã có kết quả thì bỏ qua.
        """
        self.ensure_one()
        enrollments = self.class_id._recompute_exam_eligibility()
        existing = set(self.result_ids.mapped('student_id').ids)
        lines = []
        for enr in enrollments.filtered('exam_eligible'):
            if enr.student_id.id not in existing:
                existing.add(enr.student_id.id)
                lines.append({
                    'exam_id': self.id,
                    'student_id': enr.student_id.id,
                    'score': 0.0,
                })
        if lines:
            self.env['univ.sms.exam.result'].create(lines)
        return True
