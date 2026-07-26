from odoo import models, fields, api


class UnivSmsTranscript(models.Model):
    _name = 'univ.sms.transcript'
    _description = 'Bảng điểm tổng hợp'
    _order = 'student_id, term_id'

    student_id = fields.Many2one(
        'univ.sms.student',
        string='Sinh viên',
        required=True,
    )
    term_id = fields.Many2one(
        'univ.sms.term',
        string='Học kỳ',
        required=True,
    )
    program_id = fields.Many2one(
        'univ.sms.program',
        string='Ngành học',
        related='student_id.program_id',
        store=True,
    )
    line_ids = fields.One2many(
        'univ.sms.transcript.line',
        'transcript_id',
        string='Chi tiết điểm',
    )
    term_gpa = fields.Float(
        string='GPA học kỳ',
        compute='_compute_gpa',
        store=True,
    )
    cumulative_gpa = fields.Float(
        string='GPA tích lũy',
        compute='_compute_cumulative_gpa',
        store=True,
    )
    classification = fields.Selection(
        string='Xếp loại',
        selection=[
            ('excellent', 'Xuất sắc (9.0-10.0)'),
            ('very_good', 'Giỏi (8.0-8.9)'),
            ('good', 'Khá (7.0-7.9)'),
            ('average_good', 'Trung bình khá (6.5-6.9)'),
            ('average', 'Trung bình (5.5-6.4)'),
            ('below_average', 'Yếu (4.0-5.4)'),
            ('fail', 'Kém (dưới 4.0)'),
        ],
        compute='_compute_gpa',
        store=True,
    )

    _sql_constraints = [
        (
            'transcript_uniq',
            'unique(student_id, term_id)',
            'Đã có bảng điểm cho sinh viên và học kỳ này!',
        ),
    ]

    @api.depends('line_ids.grade_point', 'line_ids.credit')
    def _compute_gpa(self):
        for record in self:
            if record.line_ids:
                total_credits = sum(record.line_ids.mapped('credit'))
                if total_credits:
                    weighted = sum(
                        line.grade_point * line.credit for line in record.line_ids
                    )
                    record.term_gpa = round(weighted / total_credits, 2)
                else:
                    record.term_gpa = 0.0
            else:
                record.term_gpa = 0.0
            record.classification = self._get_classification(record.term_gpa)

    @api.depends('student_id', 'term_id', 'term_gpa')
    def _compute_cumulative_gpa(self):
        for record in self:
            if record.student_id:
                all_transcripts = self.search([
                    ('student_id', '=', record.student_id.id),
                ])
                if all_transcripts:
                    total_credits = sum(
                        sum(t.line_ids.mapped('credit')) for t in all_transcripts
                    )
                    if total_credits:
                        weighted = sum(
                            sum(line.grade_point * line.credit for line in t.line_ids)
                            for t in all_transcripts
                        )
                        record.cumulative_gpa = round(weighted / total_credits, 2)
                    else:
                        record.cumulative_gpa = 0.0
                else:
                    record.cumulative_gpa = 0.0
            else:
                record.cumulative_gpa = 0.0

    @api.model
    def _get_classification(self, gpa):
        if gpa >= 9.0:
            return 'excellent'
        elif gpa >= 8.0:
            return 'very_good'
        elif gpa >= 7.0:
            return 'good'
        elif gpa >= 6.5:
            return 'average_good'
        elif gpa >= 5.5:
            return 'average'
        elif gpa >= 4.0:
            return 'below_average'
        else:
            return 'fail'

    def action_generate_from_enrollments(self):
        """Tạo dòng bảng điểm từ môn học đã đăng ký trong học kỳ, rồi tự động tính điểm."""
        for transcript in self:
            enrolled_subjects = self.env['univ.sms.enrollment'].search([
                ('student_id', '=', transcript.student_id.id),
                ('term_id', '=', transcript.term_id.id),
                ('state', '!=', 'cancelled'),
            ]).mapped('subject_id')
            existing_subjects = transcript.line_ids.mapped('subject_id')
            for subject in (enrolled_subjects - existing_subjects):
                self.env['univ.sms.transcript.line'].create({
                    'transcript_id': transcript.id,
                    'subject_id': subject.id,
                    'final_score': 0.0,
                })
        self.action_sync_scores()

    def action_sync_scores(self):
        """Tính điểm tổng kết tự động từ kết quả thi (giữa kỳ 40% + cuối kỳ 60%)."""
        for transcript in self:
            for line in transcript.line_ids:
                midterm = self.env['univ.sms.exam.result'].search([
                    ('student_id', '=', transcript.student_id.id),
                    ('subject_id', '=', line.subject_id.id),
                    ('term_id', '=', transcript.term_id.id),
                    ('exam_id.exam_type', '=', 'midterm'),
                    ('exam_id.state', '=', 'done'),
                ], limit=1)
                final = self.env['univ.sms.exam.result'].search([
                    ('student_id', '=', transcript.student_id.id),
                    ('subject_id', '=', line.subject_id.id),
                    ('term_id', '=', transcript.term_id.id),
                    ('exam_id.exam_type', '=', 'final'),
                    ('exam_id.state', '=', 'done'),
                ], limit=1)
                if midterm and final:
                    line.final_score = round(midterm.score * 0.4 + final.score * 0.6, 2)
                elif final:
                    line.final_score = final.score
                elif midterm:
                    line.final_score = midterm.score


class UnivSmsTranscriptLine(models.Model):
    _name = 'univ.sms.transcript.line'
    _description = 'Chi tiết bảng điểm'

    transcript_id = fields.Many2one(
        'univ.sms.transcript',
        string='Bảng điểm',
        required=True,
        ondelete='cascade',
    )
    subject_id = fields.Many2one(
        'univ.sms.subject',
        string='Môn học',
        required=True,
    )
    credit = fields.Float(
        string='Số tín chỉ',
        related='subject_id.credit',
        store=True,
    )
    final_score = fields.Float(string='Điểm tổng kết', digits=(4, 2))
    grade_point = fields.Float(
        string='Điểm quy đổi (thang 10)',
        compute='_compute_grade_point',
        store=True,
    )
    grade_letter = fields.Selection(
        string='Xếp loại chữ',
        selection=[
            ('A', 'A (8.5-10.0)'),
            ('B', 'B (7.0-8.4)'),
            ('C', 'C (5.5-6.9)'),
            ('D', 'D (4.0-5.4)'),
            ('F', 'F (dưới 4.0)'),
        ],
        compute='_compute_grade_point',
        store=True,
    )

    _sql_constraints = [
        (
            'subject_uniq',
            'unique(transcript_id, subject_id)',
            'Môn học đã có trong bảng điểm!',
        ),
    ]

    @api.depends('final_score')
    def _compute_grade_point(self):
        for record in self:
            record.grade_point = record.final_score
            if record.final_score >= 8.5:
                record.grade_letter = 'A'
            elif record.final_score >= 7.0:
                record.grade_letter = 'B'
            elif record.final_score >= 5.5:
                record.grade_letter = 'C'
            elif record.final_score >= 4.0:
                record.grade_letter = 'D'
            else:
                record.grade_letter = 'F'
