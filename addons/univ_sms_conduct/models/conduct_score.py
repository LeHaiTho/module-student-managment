from odoo import models, fields, api


class UnivSmsConductScore(models.Model):
    _name = 'univ.sms.conduct.score'
    _description = 'Điểm rèn luyện sinh viên'
    _order = 'student_id'

    student_id = fields.Many2one('univ.sms.student', required=True)
    period_id = fields.Many2one('univ.sms.term', required=True, string='Học kỳ đánh giá')
    line_ids = fields.One2many('univ.sms.conduct.score.line', 'conduct_score_id')
    self_total = fields.Integer(compute='_compute_totals', store=True, string='Tự chấm')
    advisor_total = fields.Integer(compute='_compute_totals', store=True, string='CVHT duyệt')
    final_total = fields.Integer(compute='_compute_totals', store=True, string='Khoa duyệt')
    classification = fields.Selection([
        ('excellent', 'Xuất sắc'), ('good', 'Tốt'), ('fair', 'Khá'),
        ('average', 'Trung bình'), ('weak', 'Yếu'), ('poor', 'Kém'),
    ], compute='_compute_classification', store=True)
    state = fields.Selection([
        ('draft', 'SV đang chấm'),
        ('submitted', 'Đã gửi'),
        ('advisor_approved', 'CVHT đã duyệt'),
        ('dean_approved', 'Khoa đã duyệt'),
        ('rejected', 'Bị trả về'),
    ], default='draft')

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_advisor_approve(self):
        self.write({'state': 'advisor_approved'})

    def action_dean_approve(self):
        self.write({'state': 'dean_approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.depends('line_ids.self_score', 'line_ids.advisor_score', 'line_ids.final_score')
    def _compute_totals(self):
        for rec in self:
            rec.self_total = sum(rec.line_ids.mapped('self_score'))
            rec.advisor_total = sum(rec.line_ids.mapped('advisor_score'))
            rec.final_total = sum(rec.line_ids.mapped('final_score'))

    @api.depends('final_total')
    def _compute_classification(self):
        for rec in self:
            score = rec.final_total
            if score >= 90:
                rec.classification = 'excellent'
            elif score >= 80:
                rec.classification = 'good'
            elif score >= 65:
                rec.classification = 'fair'
            elif score >= 50:
                rec.classification = 'average'
            elif score >= 35:
                rec.classification = 'weak'
            else:
                rec.classification = 'poor'


class UnivSmsConductScoreLine(models.Model):
    _name = 'univ.sms.conduct.score.line'
    _description = 'Chi tiết điểm theo tiêu chí'

    conduct_score_id = fields.Many2one('univ.sms.conduct.score', ondelete='cascade')
    criteria_id = fields.Many2one('univ.sms.conduct.criteria', required=True)
    self_score = fields.Integer(string='SV tự chấm')
    advisor_score = fields.Integer(string='CVHT chấm')
    final_score = fields.Integer(string='Điểm cuối')