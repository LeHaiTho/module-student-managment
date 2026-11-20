import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Trạng thái chiếm chỗ trong lớp môn học (schema lock 2.1). 'draft' KHÔNG chiếm chỗ.
OCCUPYING_STATES = ('registered', 'confirmed')


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
    enrollment_id = fields.Many2one(
        'univ.sms.enrollment',
        string='Ghi danh học phần',
        readonly=True,
        copy=False,
        ondelete='set null',
    )
    result_message = fields.Char(
        string='Kết quả xử lý',
        help='Lý do hoặc kết quả xử lý gần nhất.',
        copy=False,
    )

    _sql_constraints = [
        ('reg_uniq', 'unique(student_id, offering_id)', 'Đã đăng ký lớp môn học này!')
    ]

    # ─── Compute ───────────────────────────────────────────────────────────
    @api.depends('student_id', 'period_id', 'state')
    def _compute_registered_credit(self):
        for rec in self:
            rec.registered_credit = rec._get_registered_credit()

    def _get_registered_credit(self):
        """Tổng tín chỉ các đăng ký đang chiếm chỗ trong cùng đợt (gồm chính bản ghi nếu chiếm chỗ)."""
        self.ensure_one()
        if not self.student_id or not self.period_id:
            return 0.0
        registrations = self.search([
            ('student_id', '=', self.student_id.id),
            ('period_id', '=', self.period_id.id),
            ('state', 'in', OCCUPYING_STATES),
        ])
        return sum(registrations.mapped('subject_credit'))

    @api.onchange('period_id')
    def _onchange_period_id(self):
        self.offering_id = False

    # ─── Bộ kiểm tra dùng chung (service + constraint + nhận người chờ) ────
    @api.model
    def _occupying_domain(self, student, exclude_offering=None):
        domain = [
            ('student_id', '=', student.id),
            ('state', 'in', OCCUPYING_STATES),
        ]
        if exclude_offering:
            domain.append(('offering_id', '!=', exclude_offering.id))
        return domain

    @api.model
    def _find_timetable_conflicts(self, student, offering):
        """Trả về list (slot_mới, slot_đã_có, đăng_ký_đã_có) bị trùng lịch.

        Xét lịch của offering.class_id với lịch các lớp mà sinh viên đang chiếm chỗ
        trong cùng học kỳ. Offering không có lớp hoặc không có lịch thì không xét.
        """
        new_slots = offering.class_id.timetable_ids
        if not new_slots:
            return []
        others = self.search(self._occupying_domain(student, exclude_offering=offering) + [
            ('offering_id.term_id', '=', offering.term_id.id),
        ])
        conflicts = []
        for other in others:
            for other_slot in other.offering_id.class_id.timetable_ids:
                for slot in new_slots:
                    if slot._overlaps(other_slot):
                        conflicts.append((slot, other_slot, other))
        return conflicts

    @api.model
    def _get_block_reason(self, student, offering, period):
        """Kiểm tra mọi điều kiện trừ số chỗ, theo thứ tự trong schema lock 2.1.

        Trả về (mã, thông báo tiếng Việt) hoặc None nếu hợp lệ.
        Không tính chính lớp `offering` khi xét trùng môn, tín chỉ, trùng lịch.
        """
        # 1. Sinh viên đang học
        if not student or student.state != 'studying':
            return ('student', _('Chỉ sinh viên đang học mới được đăng ký môn.'))
        # 2. Đợt mở và đúng thời gian
        now = fields.Datetime.now()
        if not period or period.state != 'open':
            return ('period', _('Đợt đăng ký chưa mở hoặc đã đóng.'))
        if period.date_start and now < period.date_start:
            return ('period', _('Đợt đăng ký chưa tới thời gian bắt đầu.'))
        if period.date_end and now > period.date_end:
            return ('period', _('Đợt đăng ký đã hết hạn.'))
        # 3. Lớp thuộc học kỳ của đợt
        if not offering or not offering.active or offering.term_id != period.term_id:
            return ('term', _('Lớp môn học không thuộc học kỳ của đợt đăng ký.'))
        # 4. Trùng môn trong học kỳ
        duplicate = self.search(self._occupying_domain(student, exclude_offering=offering) + [
            ('offering_id.subject_id', '=', offering.subject_id.id),
            ('offering_id.term_id', '=', offering.term_id.id),
        ], limit=1)
        if duplicate:
            return ('duplicate', _('Bạn đã đăng ký môn %s ở lớp khác trong học kỳ này.')
                    % offering.subject_id.name)
        # 5. Môn tiên quyết
        prereqs = offering.subject_id.prerequisite_ids
        if prereqs:
            passed = self.env['univ.sms.exam.result'].sudo().search([
                ('student_id', '=', student.id),
                ('subject_id', 'in', prereqs.ids),
                ('is_passed', '=', True),
            ]).mapped('subject_id')
            missing = prereqs - passed
            if missing:
                return ('prerequisite', _('Chưa hoàn thành môn tiên quyết: %s.')
                        % ', '.join(missing.mapped('name')))
        # 6. Giới hạn tín chỉ tối đa
        if period.max_credit:
            current = sum(self.search(
                self._occupying_domain(student, exclude_offering=offering)
                + [('period_id', '=', period.id)]
            ).mapped('subject_credit'))
            total = current + (offering.subject_id.credit or 0.0)
            if total > period.max_credit:
                return ('max_credit', _(
                    'Vượt quá số tín chỉ tối đa (%(max)s). Đã đăng ký %(cur)s tín chỉ, '
                    'thêm môn này sẽ là %(total)s tín chỉ.',
                    max=period.max_credit, cur=f'{current:g}', total=f'{total:g}'))
        # 7. Trùng lịch
        conflicts = self._find_timetable_conflicts(student, offering)
        if conflicts:
            slot, other_slot, other = conflicts[0]
            return ('timetable', _(
                'Trùng lịch với môn %(subject)s (%(slot)s).',
                subject=other.offering_id.subject_id.name, slot=other_slot._slot_label()))
        return None

    # ─── Service đăng ký (schema 2.1) ──────────────────────────────────────
    @api.model
    def _lock_offering(self, offering):
        """Khóa dòng offering để hai người đăng ký cùng lúc không vượt sĩ số."""
        self.env.cr.execute(
            'SELECT id FROM univ_sms_course_offering WHERE id = %s FOR UPDATE', (offering.id,))
        offering.invalidate_recordset(['registered_count', 'waitlist_count',
                                       'available_seats', 'is_full'])

    @api.model
    def _activate_registration(self, student, offering, period, message):
        """Tạo mới hoặc kích hoạt lại đăng ký (bản ghi đã hủy/nháp) sang 'registered'."""
        existing = self.with_context(active_test=False).search([
            ('student_id', '=', student.id),
            ('offering_id', '=', offering.id),
        ], limit=1)
        vals = {
            'state': 'registered',
            'period_id': period.id,
            'registration_date': fields.Datetime.now(),
            'result_message': message,
        }
        if existing:
            existing.write(vals)
            return existing
        vals.update({'student_id': student.id, 'offering_id': offering.id})
        return self.create(vals)

    @api.model
    def register_student(self, student, offering, period):
        """Đăng ký một sinh viên vào lớp môn học.

        Trả về dict(status, message, registration_id, waitlist_id, position) với
        status ∈ {'registered', 'waitlisted', 'rejected', 'already'}.
        Bị từ chối thì không tạo bản ghi chiếm chỗ.
        """
        Waitlist = self.env['univ.sms.registration.waitlist']
        result = {'status': 'rejected', 'message': '', 'registration_id': False,
                  'waitlist_id': False, 'position': 0}
        if not student or not offering:
            result['message'] = _('Thông tin đăng ký không hợp lệ.')
            return result
        student.ensure_one()
        offering.ensure_one()

        existing = self.search([
            ('student_id', '=', student.id),
            ('offering_id', '=', offering.id),
        ], limit=1)
        if existing and existing.state in OCCUPYING_STATES:
            result.update(status='already', registration_id=existing.id,
                          message=_('Bạn đã đăng ký lớp %s.') % offering.name)
            return result
        waiting = Waitlist.search([
            ('student_id', '=', student.id),
            ('offering_id', '=', offering.id),
            ('state', '=', 'waiting'),
        ], limit=1)
        if waiting:
            result.update(status='already', waitlist_id=waiting.id, position=waiting.position,
                          message=_('Bạn đang ở vị trí chờ số %s của lớp %s.')
                          % (waiting.position, offering.name))
            return result

        reason = self._get_block_reason(student, offering, period)
        if reason:
            result['message'] = reason[1]
            if existing:
                existing.sudo().write({'result_message': reason[1]})
            return result

        self._lock_offering(offering)
        if offering.max_seats and offering.registered_count >= offering.max_seats:
            entry = Waitlist.create({
                'student_id': student.id,
                'offering_id': offering.id,
                'period_id': period.id,
            })
            result.update(status='waitlisted', waitlist_id=entry.id, position=entry.position,
                          message=_('Lớp đã đủ chỗ. Bạn đang ở vị trí chờ số %s.') % entry.position)
            return result

        message = _('Đăng ký thành công lớp %s.') % offering.name
        reg = self._activate_registration(student, offering, period, message)
        result.update(status='registered', registration_id=reg.id, message=message)
        return result

    # ─── Đồng bộ enrollment (schema 2.5) ───────────────────────────────────
    def _sync_enrollment(self):
        """Đồng bộ univ.sms.enrollment theo trạng thái đăng ký. Chạy lại nhiều lần an toàn."""
        Enrollment = self.env['univ.sms.enrollment'].sudo()
        for reg in self.sudo():
            offering = reg.offering_id
            if reg.state in OCCUPYING_STATES:
                enrollment = reg.enrollment_id
                if not enrollment or (enrollment.student_id, enrollment.subject_id, enrollment.term_id) != (
                        reg.student_id, offering.subject_id, offering.term_id):
                    enrollment = Enrollment.search([
                        ('student_id', '=', reg.student_id.id),
                        ('subject_id', '=', offering.subject_id.id),
                        ('term_id', '=', offering.term_id.id),
                    ], limit=1)
                if enrollment:
                    vals = {}
                    if enrollment.state == 'cancelled':
                        vals['state'] = 'registered'
                    if offering.class_id and enrollment.class_id != offering.class_id:
                        vals['class_id'] = offering.class_id.id
                    if vals:
                        enrollment.write(vals)
                else:
                    enrollment = Enrollment.create({
                        'student_id': reg.student_id.id,
                        'subject_id': offering.subject_id.id,
                        'term_id': offering.term_id.id,
                        'class_id': offering.class_id.id or False,
                        'state': 'registered',
                    })
                if reg.enrollment_id != enrollment:
                    super(UnivSmsRegistration, reg).write({'enrollment_id': enrollment.id})
            elif reg.enrollment_id and reg.enrollment_id.state == 'registered':
                # Hủy (hoặc đưa về nháp): enrollment chuyển 'cancelled', không xóa.
                reg.enrollment_id.write({'state': 'cancelled'})

    # ─── ORM overrides ─────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_enrollment()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals or 'offering_id' in vals or 'student_id' in vals:
            self._sync_enrollment()
        return res

    def unlink(self):
        offerings = self.filtered(lambda r: r.state in OCCUPYING_STATES).mapped('offering_id')
        enrollments = self.mapped('enrollment_id').filtered(lambda e: e.state == 'registered')
        res = super().unlink()
        if enrollments:
            enrollments.sudo().write({'state': 'cancelled'})
        if offerings:
            offerings._promote_waitlist()
        return res

    # ─── Ràng buộc an toàn (back-office create/write) ──────────────────────
    @api.constrains('student_id')
    def _check_student_status(self):
        for rec in self:
            if rec.state in OCCUPYING_STATES and rec.student_id and rec.student_id.state != 'studying':
                raise ValidationError(_('Chỉ sinh viên đang học mới được đăng ký môn.'))

    @api.constrains('period_id', 'offering_id', 'state')
    def _check_period_and_offering(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.state not in OCCUPYING_STATES or not rec.period_id or not rec.offering_id:
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
            if rec.state not in OCCUPYING_STATES or not rec.student_id or not rec.offering_id:
                continue
            duplicate = self.search_count([
                ('id', '!=', rec.id),
                ('student_id', '=', rec.student_id.id),
                ('offering_id.subject_id', '=', rec.offering_id.subject_id.id),
                ('offering_id.term_id', '=', rec.offering_id.term_id.id),
                ('state', 'in', OCCUPYING_STATES),
            ])
            if duplicate:
                raise ValidationError(_('Sinh viên đã đăng ký môn này trong học kỳ hiện tại.'))

    @api.constrains('offering_id', 'student_id', 'state')
    def _check_prerequisite(self):
        for rec in self:
            if rec.state not in OCCUPYING_STATES:
                continue
            prereqs = rec.offering_id.subject_id.prerequisite_ids
            if prereqs:
                passed = self.env['univ.sms.exam.result'].sudo().search([
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
            if not period or rec.state not in OCCUPYING_STATES or not period.max_credit:
                continue
            total_credit = rec._get_registered_credit()
            if total_credit > period.max_credit:
                raise ValidationError(
                    _('Vượt quá số tín chỉ tối đa (%s). Hiện tại: %s tín chỉ.') %
                    (period.max_credit, total_credit))

    @api.constrains('student_id', 'offering_id', 'state')
    def _check_timetable_conflict(self):
        for rec in self:
            if rec.state not in OCCUPYING_STATES or not rec.student_id or not rec.offering_id:
                continue
            conflicts = self._find_timetable_conflicts(rec.student_id, rec.offering_id)
            if conflicts:
                slot, other_slot, other = conflicts[0]
                raise ValidationError(_(
                    'Trùng lịch với môn %(subject)s (%(slot)s).',
                    subject=other.offering_id.subject_id.name, slot=other_slot._slot_label()))

    @api.constrains('offering_id', 'state')
    def _check_seats(self):
        for rec in self:
            offering = rec.offering_id
            if not offering or rec.state not in OCCUPYING_STATES or not offering.max_seats:
                continue
            active_count = self.search_count([
                ('offering_id', '=', offering.id),
                ('state', 'in', OCCUPYING_STATES),
            ])
            if active_count > offering.max_seats:
                raise ValidationError(_('Lớp môn học đã đủ số lượng sinh viên.'))

    # ─── Actions ───────────────────────────────────────────────────────────
    def action_register(self):
        self.write({'state': 'registered'})

    def action_confirm(self):
        for rec in self:
            total_credit = rec._get_registered_credit()
            if rec.state not in OCCUPYING_STATES:
                total_credit += rec.subject_credit or 0.0
            if rec.period_id.min_credit and total_credit < rec.period_id.min_credit:
                raise ValidationError(
                    _('Chưa đạt số tín chỉ tối thiểu (%s). Hiện tại: %s tín chỉ.') %
                    (rec.period_id.min_credit, total_credit))
        self.write({'state': 'confirmed'})

    def action_cancel(self):
        """Hủy đăng ký: enrollment → cancelled, học phí tính lại (qua hook enrollment),
        sau đó tự động nhận người đầu danh sách chờ."""
        freed = self.filtered(lambda r: r.state in OCCUPYING_STATES).mapped('offering_id')
        self.write({'state': 'cancelled', 'result_message': _('Đã hủy đăng ký.')})
        if freed:
            freed._promote_waitlist()
        return True

    def action_draft(self):
        self.write({'state': 'draft'})
