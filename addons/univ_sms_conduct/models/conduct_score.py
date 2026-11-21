from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class UnivSmsConductScore(models.Model):
    _name = 'univ.sms.conduct.score'
    _description = 'Điểm rèn luyện sinh viên'
    _order = 'student_id'

    name = fields.Char(string='Phiếu rèn luyện', compute='_compute_name', store=True)
    student_id = fields.Many2one('univ.sms.student', string='Sinh viên', required=True)
    period_id = fields.Many2one('univ.sms.term', required=True, string='Học kỳ đánh giá')
    line_ids = fields.One2many('univ.sms.conduct.score.line', 'conduct_score_id')
    self_total = fields.Integer(compute='_compute_totals', store=True, string='Tự chấm')
    advisor_total = fields.Integer(compute='_compute_totals', store=True, string='CVHT duyệt')
    final_total = fields.Integer(compute='_compute_totals', store=True, string='Khoa duyệt')
    classification = fields.Selection([
        ('excellent', 'Xuất sắc'), ('good', 'Tốt'), ('fair', 'Khá'),
        ('average', 'Trung bình'), ('weak', 'Yếu'), ('poor', 'Kém'),
    ], string='Xếp loại', compute='_compute_classification', store=True)
    state = fields.Selection([
        ('draft', 'SV đang chấm'),
        ('submitted', 'Đã gửi'),
        ('advisor_approved', 'CVHT đã duyệt'),
        ('dean_approved', 'Khoa đã duyệt'),
        ('rejected', 'Bị trả về'),
    ], default='draft')

    _sql_constraints = [
        ('student_period_uniq', 'unique(student_id, period_id)',
         'Mỗi sinh viên chỉ có một phiếu điểm rèn luyện cho một học kỳ!'),
    ]

    # ─── Workflow (kiểm tra phía server, không chỉ ẩn nút ở view) ──────────
    def _state_label(self, state):
        return dict(self._fields['state'].selection).get(state, state)

    def _check_states(self, allowed, action_label):
        for rec in self:
            if rec.state not in allowed:
                raise UserError(_(
                    'Không thể %(action)s phiếu rèn luyện của %(student)s ở trạng thái "%(state)s".',
                    action=action_label, student=rec.student_id.name or '',
                    state=self._state_label(rec.state)))

    def _check_group(self, xmlids, message):
        if self.env.su:
            return
        user = self.env.user
        if not any(user.has_group(x) for x in xmlids):
            raise AccessError(message)

    def action_submit(self):
        self._check_states(('draft', 'rejected'), _('gửi'))
        self.write({'state': 'submitted'})

    def action_advisor_approve(self):
        self._check_group(('univ_sms_base.group_univ_advisor',),
                          _('Chỉ cố vấn học tập mới được duyệt cấp CVHT.'))
        self._check_states(('submitted',), _('duyệt cấp CVHT'))
        # Tiêu chí cố vấn chưa chấm (0) thì lấy điểm sinh viên tự chấm
        for line in self.mapped('line_ids').filtered(lambda l: not l.advisor_score):
            line.advisor_score = line.self_score
        self.write({'state': 'advisor_approved'})

    def action_dean_approve(self):
        self._check_group(('univ_sms_base.group_univ_dean',),
                          _('Chỉ trưởng khoa mới được duyệt cấp khoa.'))
        self._check_states(('advisor_approved',), _('duyệt cấp khoa'))
        # Tiêu chí khoa chưa chấm (0) thì lấy điểm cố vấn đã duyệt, tránh xếp loại sai thành "Kém"
        for line in self.mapped('line_ids').filtered(lambda l: not l.final_score):
            line.final_score = line.advisor_score
        self.write({'state': 'dean_approved'})

    def action_reject(self):
        self._check_group(('univ_sms_base.group_univ_advisor', 'univ_sms_base.group_univ_dean'),
                          _('Chỉ cố vấn học tập hoặc trưởng khoa mới được trả về phiếu rèn luyện.'))
        self._check_states(('submitted', 'advisor_approved'), _('trả về'))
        self.write({'state': 'rejected'})

    def action_draft(self):
        self._check_states(('rejected',), _('đưa về nháp'))
        self.write({'state': 'draft'})

    @api.depends('line_ids.self_score', 'line_ids.advisor_score', 'line_ids.final_score')
    def _compute_totals(self):
        for rec in self:
            rec.self_total = sum(rec.line_ids.mapped('self_score'))
            rec.advisor_total = sum(rec.line_ids.mapped('advisor_score'))
            rec.final_total = sum(rec.line_ids.mapped('final_score'))

    @api.depends('student_id.name', 'student_id.student_code', 'period_id.name')
    def _compute_name(self):
        for rec in self:
            parts = [p for p in (rec.student_id.student_code, rec.student_id.name, rec.period_id.name) if p]
            rec.name = 'Rèn luyện – ' + ' – '.join(parts) if parts else 'Phiếu rèn luyện'

    @api.depends('final_total', 'state')
    def _compute_classification(self):
        for rec in self:
            # Chỉ xếp loại khi khoa đã duyệt; trước đó điểm cuối chưa chốt
            if rec.state != 'dean_approved':
                rec.classification = False
                continue
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

    conduct_score_id = fields.Many2one('univ.sms.conduct.score', string='Phiếu rèn luyện', ondelete='cascade')
    criteria_id = fields.Many2one('univ.sms.conduct.criteria', string='Tiêu chí', required=True)
    self_score = fields.Integer(string='SV tự chấm')
    advisor_score = fields.Integer(string='CVHT chấm')
    final_score = fields.Integer(string='Điểm cuối')

    @api.constrains('self_score', 'advisor_score', 'final_score', 'criteria_id')
    def _check_score_range(self):
        for line in self:
            max_score = line.criteria_id.max_score or 0
            for fname in ('self_score', 'advisor_score', 'final_score'):
                value = line[fname] or 0
                if value < 0 or value > max_score:
                    raise ValidationError(_(
                        'Điểm "%(label)s" của tiêu chí "%(criteria)s" phải trong khoảng 0 đến %(max)s.',
                        label=line._fields[fname].string, criteria=line.criteria_id.name,
                        max=max_score))
