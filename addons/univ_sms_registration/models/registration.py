from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UnivSmsRegistration(models.Model):
    _name = 'univ.sms.registration'
    _description = 'Đăng ký môn học'
    _order = 'registration_date desc'

    student_id = fields.Many2one(
        'univ.sms.student',
        string='Sinh viên',
        required=True,
        ondelete='cascade',
        domain=[('state', '=', 'studying')],
    )
    offering_id = fields.Many2one(
        'univ.sms.course.offering',
        string='Lớp môn học',
        required=True,
    )
    period_id = fields.Many2one(
        'univ.sms.registration.period',
        string='Đợt đăng ký',
        required=True,
    )
    period_term_id = fields.Many2one(
        'univ.sms.term',
        related='period_id.term_id',
        string='Học kỳ của đợt đăng ký',
        readonly=True,
    )
    subject_id = fields.Many2one(
        'univ.sms.subject',
        related='offering_id.subject_id',
        string='Môn học',
        store=True,
        readonly=True,
    )
    term_id = fields.Many2one(
        'univ.sms.term',
        related='offering_id.term_id',
        string='Học kỳ',
        store=True,
        readonly=True,
    )
    subject_credit = fields.Float(
        related='subject_id.credit',
        string='Số tín chỉ',
        readonly=True,
    )
    registration_date = fields.Datetime(
        string='Ngày đăng ký',
        default=fields.Datetime.now,
    )
    registered_credit = fields.Float(
        string='Tổng tín chỉ đã đăng ký',
        compute='_compute_registered_credit',
    )
    available_seats = fields.Integer(
        related='offering_id.available_seats',
        string='Còn chỗ',
        readonly=True,
    )
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('registered', 'Đã đăng ký'),
        ('confirmed', 'Đã xác nhận'),
        ('cancelled', 'Đã hủy'),
    ], default='registered', string='Trạng thái')

    _sql_constraints = [
        ('reg_uniq', 'unique(student_id, offering_id)', 'Đã đăng ký lớp môn học này!')
    ]

    @api.depends('student_id', 'period_id', 'state')
    def _compute_registered_credit(self):
        for rec in self:
            rec.registered_credit = rec._get_registered_credit()

    def _get_registered_credit(self):
        self.ensure_one()
        if not self.student_id or not self.period_id:
            return 0.0
        registrations = self.search([
            ('student_id', '=', self.student_id.id),
            ('period_id', '=', self.period_id.id),
            ('state', 'in', ('draft', 'registered', 'confirmed')),
        ])
        return sum(registrations.mapped('subject_credit'))

    @api.onchange('period_id')
    def _onchange_period_id(self):
        self.offering_id = False

    @api.constrains('student_id')
    def _check_student_status(self):
        for rec in self:
            if rec.student_id and rec.student_id.state != 'studying':
                raise ValidationError(_('Chỉ sinh viên đang học mới được đăng ký môn.'))

    @api.constrains('period_id', 'offering_id', 'state')
    def _check_period_and_offering(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.state == 'cancelled' or not rec.period_id or not rec.offering_id:
                continue
            if rec.period_id.state != 'open':
                raise ValidationError(_('Đợt đăng ký chưa mở hoặc đã đóng.'))
            if rec.period_id.date_start and now < rec.period_id.date_start:
                raise ValidationError(_('Đợt đăng ký chưa tới thời gian bắt đầu.'))
            if rec.period_id.date_end and now > rec.period_id.date_end:
                raise ValidationError(_('Đợt đăng ký đã hết hạn.'))
            if rec.offering_id.term_id != rec.period_id.term_id:
                raise ValidationError(_('Lớp môn học phải thuộc đúng học kỳ của đợt đăng ký.'))

    @api.constrains('offering_id', 'student_id', 'state')
    def _check_duplicate_subject_in_term(self):
        for rec in self:
            if rec.state == 'cancelled' or not rec.student_id or not rec.offering_id:
                continue
            duplicate = self.search_count([
                ('id', '!=', rec.id),
                ('student_id', '=', rec.student_id.id),
                ('offering_id.subject_id', '=', rec.offering_id.subject_id.id),
                ('offering_id.term_id', '=', rec.offering_id.term_id.id),
                ('state', 'in', ('draft', 'registered', 'confirmed')),
            ])
            if duplicate:
                raise ValidationError(_('Sinh viên đã đăng ký môn này trong học kỳ hiện tại.'))

    @api.constrains('offering_id', 'student_id')
    def _check_prerequisite(self):
        for rec in self:
            prereqs = rec.offering_id.subject_id.prerequisite_ids
            if prereqs:
                passed = self.env['univ.sms.exam.result'].search([
                    ('student_id', '=', rec.student_id.id),
                    ('subject_id', 'in', prereqs.ids),
                    ('is_passed', '=', True),
                ]).mapped('subject_id')
                missing = prereqs - passed
                if missing:
                    raise ValidationError(
                        _('Chưa hoàn thành môn tiên quyết: %s') %
                        ', '.join(missing.mapped('name')))

    @api.constrains('student_id', 'period_id', 'offering_id', 'state')
    def _check_max_credit_limit(self):
        for rec in self:
            period = rec.period_id
            if not period or rec.state == 'cancelled' or not period.max_credit:
                continue
            total_credit = rec._get_registered_credit()
            if total_credit > period.max_credit:
                raise ValidationError(
                    _('Vượt quá số tín chỉ tối đa (%s). Hiện tại: %s tín chỉ.') %
                    (period.max_credit, total_credit))

    @api.constrains('offering_id', 'state')
    def _check_seats(self):
        for rec in self:
            offering = rec.offering_id
            if not offering or rec.state == 'cancelled' or not offering.max_seats:
                continue
            active_count = self.search_count([
                ('offering_id', '=', offering.id),
                ('state', 'in', ('draft', 'registered', 'confirmed')),
            ])
            if active_count > offering.max_seats:
                raise ValidationError(_('Lớp môn học đã đủ số lượng sinh viên.'))

    def action_register(self):
        self.write({'state': 'registered'})

    def action_confirm(self):
        for rec in self:
            total_credit = rec._get_registered_credit()
            if rec.period_id.min_credit and total_credit < rec.period_id.min_credit:
                raise ValidationError(
                    _('Chưa đạt số tín chỉ tối thiểu (%s). Hiện tại: %s tín chỉ.') %
                    (rec.period_id.min_credit, total_credit))
        self.write({'state': 'confirmed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})
