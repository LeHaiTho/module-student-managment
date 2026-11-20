import logging
from collections import defaultdict


from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

WARNING_TYPES = [
    ('gpa', 'GPA thấp'),
    ('failed_subjects', 'Nợ nhiều môn'),
    ('attendance', 'Vắng học vượt ngưỡng'),
    ('debt', 'Nợ học phí quá hạn'),
    ('credit', 'Thiếu tín chỉ đăng ký'),
]

SEVERITY_BY_TYPE = {
    'gpa': 'high',
    'failed_subjects': 'high',
    'attendance': 'high',
    'debt': 'medium',
    'credit': 'medium',
}

# Khóa tham số cấu hình và giá trị mặc định
PARAM_GPA = 'univ_sms.warning_gpa_threshold'
PARAM_FAILED = 'univ_sms.warning_failed_subjects'
PARAM_ABSENCE = 'univ_sms.max_absence_rate'  # dùng chung với F2, không khai báo record ở module này
DEFAULT_GPA = 5.0
DEFAULT_FAILED = 2
DEFAULT_ABSENCE = 20.0
PASS_SCORE = 5.0


class UnivSmsWarning(models.Model):
    _name = 'univ.sms.warning'
    _description = 'Cảnh báo sớm sinh viên'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'state_sequence, severity_sequence, detected_at desc, id desc'

    name = fields.Char(string='Tiêu đề', compute='_compute_name', store=True)
    student_id = fields.Many2one(
        'univ.sms.student', string='Sinh viên', required=True, index=True,
        ondelete='cascade', tracking=True)
    student_code = fields.Char(related='student_id.student_code', string='MSSV')
    warning_type = fields.Selection(
        WARNING_TYPES, string='Loại cảnh báo', required=True, index=True)
    severity = fields.Selection([
        ('high', 'Cao'),
        ('medium', 'Trung bình'),
        ('low', 'Thấp'),
    ], string='Mức độ', required=True, default='medium', tracking=True)
    severity_sequence = fields.Integer(compute='_compute_sequences', store=True)
    state = fields.Selection([
        ('new', 'Mới'),
        ('in_progress', 'Đang xử lý'),
        ('closed', 'Đã đóng'),
    ], string='Trạng thái', default='new', required=True, tracking=True, index=True)
    state_sequence = fields.Integer(compute='_compute_sequences', store=True)
    term_id = fields.Many2one('univ.sms.term', string='Học kỳ')
    evidence_value = fields.Float(
        string='Giá trị bằng chứng', digits=(16, 2),
        help='GPA / % vắng / số tiền nợ / số tín chỉ / số môn trượt tại lần đánh giá gần nhất.')
    evidence_text = fields.Text(string='Bằng chứng')
    home_class_id = fields.Many2one(
        related='student_id.home_class_id', store=True, string='Lớp hành chính')
    program_id = fields.Many2one(
        related='student_id.program_id', store=True, string='Ngành')
    advisor_partner_id = fields.Many2one(
        'res.partner', string='Cố vấn phụ trách', compute='_compute_advisor_partner_id',
        store=True, readonly=False, tracking=True, index=True)
    detected_at = fields.Datetime(string='Phát hiện lúc', default=fields.Datetime.now, readonly=True)
    last_checked_at = fields.Datetime(string='Đánh giá gần nhất', readonly=True)
    closed_at = fields.Datetime(string='Đóng lúc', readonly=True, copy=False)
    closed_by_id = fields.Many2one('res.users', string='Người đóng', readonly=True, copy=False)
    close_note = fields.Text(string='Ghi chú khi đóng', copy=False)
    consultation_ids = fields.One2many(
        'univ.sms.warning.consultation', 'warning_id', string='Nhật ký tư vấn')
    consultation_count = fields.Integer(compute='_compute_consultation_count', string='Số lần tư vấn')

    # ─── Compute ───────────────────────────────────────────────────────────
    @api.depends('student_id.student_code', 'student_id.name', 'warning_type')
    def _compute_name(self):
        labels = dict(WARNING_TYPES)
        for rec in self:
            student = rec.student_id
            rec.name = '%s - %s' % (
                student.student_code or student.name or '', labels.get(rec.warning_type, ''))

    @api.depends('severity', 'state')
    def _compute_sequences(self):
        sev = {'high': 1, 'medium': 2, 'low': 3}
        st = {'new': 1, 'in_progress': 2, 'closed': 3}
        for rec in self:
            rec.severity_sequence = sev.get(rec.severity, 9)
            rec.state_sequence = st.get(rec.state, 9)

    @api.depends('student_id')
    def _compute_advisor_partner_id(self):
        # Gán tại thời điểm tạo: cố vấn của sinh viên, nếu trống thì cố vấn lớp hành chính.
        for rec in self:
            student = rec.student_id.sudo()
            rec.advisor_partner_id = student.advisor_id or student.home_class_id.advisor_id

    def _compute_consultation_count(self):
        for rec in self:
            rec.consultation_count = len(rec.consultation_ids)

    # ─── Ràng buộc chống trùng ─────────────────────────────────────────────
    def init(self):
        self.env.cr.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS univ_sms_warning_open_uniq
            ON univ_sms_warning (student_id, warning_type)
            WHERE state != 'closed'
        """)

    @api.model
    def _check_open_duplicates_before_create(self, vals_list):
        """Báo lỗi tiếng Việt trước khi partial unique index chặn ở mức SQL."""
        seen = set()
        for vals in vals_list:
            if vals.get('state', 'new') == 'closed' or not vals.get('student_id'):
                continue
            key = (vals['student_id'], vals.get('warning_type'))
            exists = key in seen or self.sudo().search_count([
                ('student_id', '=', key[0]),
                ('warning_type', '=', key[1]),
                ('state', '!=', 'closed'),
            ])
            if exists:
                student = self.env['univ.sms.student'].sudo().browse(key[0])
                raise ValidationError(_(
                    'Sinh viên %s đã có một cảnh báo "%s" đang mở. '
                    'Hãy cập nhật cảnh báo đó thay vì tạo mới.'
                ) % (student.display_name, dict(WARNING_TYPES).get(key[1])))
            seen.add(key)

    @api.constrains('student_id', 'warning_type', 'state')
    def _check_unique_open(self):
        for rec in self:
            if rec.state == 'closed':
                continue
            dup = self.sudo().search_count([
                ('id', '!=', rec.id),
                ('student_id', '=', rec.student_id.id),
                ('warning_type', '=', rec.warning_type),
                ('state', '!=', 'closed'),
            ])
            if dup:
                raise ValidationError(_(
                    'Sinh viên %s đã có một cảnh báo "%s" đang mở. '
                    'Hãy cập nhật cảnh báo đó thay vì tạo mới.'
                ) % (rec.student_id.display_name, dict(WARNING_TYPES).get(rec.warning_type)))

    # ─── CRUD ──────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('warning_type') and not vals.get('severity'):
                vals['severity'] = SEVERITY_BY_TYPE.get(vals['warning_type'], 'medium')
            vals.setdefault('last_checked_at', fields.Datetime.now())
        self._check_open_duplicates_before_create(vals_list)
        records = super().create(vals_list)
        records._notify_advisor()
        return records

    _STAFF_ONLY_FIELDS = ('student_id', 'advisor_partner_id', 'warning_type',
                          'evidence_value', 'evidence_text', 'detected_at')

    def _is_warning_staff(self):
        user = self.env.user
        return self.env.su or any(user.has_group(g) for g in (
            'univ_sms_base.group_univ_academic_officer',
            'univ_sms_base.group_univ_student_affairs_office',
            'univ_sms_base.group_univ_admin',
        ))

    def write(self, vals):
        if set(vals) & set(self._STAFF_ONLY_FIELDS) and not self._is_warning_staff():
            raise UserError(_('Cố vấn không được thay đổi sinh viên, cố vấn phụ trách '
                              'hoặc bằng chứng của cảnh báo.'))
        old_advisors = {rec.id: rec.advisor_partner_id for rec in self} if 'advisor_partner_id' in vals else {}
        res = super().write(vals)
        if old_advisors:
            changed = self.filtered(lambda r: r.advisor_partner_id and r.advisor_partner_id != old_advisors.get(r.id))
            changed._notify_advisor()
        return res

    def _notify_advisor(self):
        """Giao cảnh báo cho cố vấn: tạo activity (To-Do) cho user của cố vấn.

        Nếu cố vấn chưa có tài khoản nội bộ thì chỉ ghi chatter.
        """
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        for rec in self:
            partner = rec.advisor_partner_id
            if not partner or rec.state == 'closed':
                continue
            users = partner.sudo().with_context(active_test=True).user_ids.filtered(lambda u: not u.share)
            if not users or not activity_type:
                continue
            user = users[0]
            try:
                with self.env.cr.savepoint():
                    rec.sudo().activity_schedule(
                        activity_type_id=activity_type.id,
                        user_id=user.id,
                        summary=_('Cảnh báo sớm: %s') % rec.name,
                        note=rec.evidence_text or '',
                    )
            except Exception as exc:  # không để lỗi giao việc chặn việc tạo cảnh báo
                _logger.warning('Không giao được activity cảnh báo %s cho user %s: %s', rec.id, user.id, exc)

    # ─── Actions ───────────────────────────────────────────────────────────
    def action_start(self):
        for rec in self:
            if rec.state != 'new':
                raise UserError(_('Chỉ cảnh báo ở trạng thái Mới mới có thể bắt đầu xử lý.'))
        self.write({'state': 'in_progress'})
        return True

    def action_close(self):
        """Đóng cảnh báo. Điều kiện: có ít nhất một lần tư vấn HOẶC có ghi chú khi đóng."""
        for rec in self:
            if rec.state == 'closed':
                continue
            if not rec.consultation_ids and not (rec.close_note or '').strip():
                raise UserError(_(
                    'Cần ghi nhận ít nhất một lần tư vấn hoặc nhập "Ghi chú khi đóng" '
                    'trước khi đóng cảnh báo %s.') % rec.name)
            rec.write({
                'state': 'closed',
                'closed_at': fields.Datetime.now(),
                'closed_by_id': self.env.user.id,
            })
            rec.activity_ids.sudo().action_feedback(feedback=_('Cảnh báo đã đóng.'))
        return True

    def action_reopen(self):
        for rec in self:
            if rec.state != 'closed':
                continue
            other_open = self.sudo().search_count([
                ('id', '!=', rec.id),
                ('student_id', '=', rec.student_id.id),
                ('warning_type', '=', rec.warning_type),
                ('state', '!=', 'closed'),
            ])
            if other_open:
                raise UserError(_(
                    'Không thể mở lại: sinh viên đã có một cảnh báo cùng loại đang mở. '
                    'Hãy xử lý trên cảnh báo đang mở.'))
            rec.write({'state': 'in_progress', 'closed_at': False, 'closed_by_id': False})
        return True

    def action_open_consultation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ghi nhận tư vấn'),
            'res_model': 'univ.sms.warning.consultation',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_warning_id': self.id},
        }

    # ─── Bộ máy đánh giá ───────────────────────────────────────────────────
    @api.model
    def _get_param_float(self, key, default):
        value = self.env['ir.config_parameter'].sudo().get_param(key)
        try:
            return float(value) if value not in (None, False, '') else float(default)
        except (TypeError, ValueError):
            _logger.warning('Tham số %s không hợp lệ (%r), dùng mặc định %s', key, value, default)
            return float(default)

    @api.model
    def _get_thresholds(self):
        return {
            'gpa': self._get_param_float(PARAM_GPA, DEFAULT_GPA),
            'failed': int(self._get_param_float(PARAM_FAILED, DEFAULT_FAILED)),
            'absence': self._get_param_float(PARAM_ABSENCE, DEFAULT_ABSENCE),
        }

    @api.model
    def _collect_triggers(self, students):
        """Trả về dict {student_id: [ {warning_type, evidence_value, evidence_text, term_id}, ...]}.

        Dữ liệu được nạp theo lô cho toàn bộ sinh viên để giảm số truy vấn.
        """
        th = self._get_thresholds()
        triggers = defaultdict(list)
        ids = students.ids
        if not ids:
            return triggers

        # 1+2. GPA và số môn trượt trong bảng điểm gần nhất (theo ngày bắt đầu học kỳ)
        transcripts = self.env['univ.sms.transcript'].sudo().search([('student_id', 'in', ids)])
        latest = {}
        for tr in transcripts:
            if not tr.line_ids:
                continue  # bảng điểm rỗng chưa có dữ liệu, bỏ qua
            key = (tr.term_id.date_start or fields.Date.from_string('1900-01-01'), tr.id)
            cur = latest.get(tr.student_id.id)
            if not cur or key > cur[0]:
                latest[tr.student_id.id] = (key, tr)
        for sid, (_key, tr) in latest.items():
            if tr.term_gpa < th['gpa']:
                triggers[sid].append({
                    'warning_type': 'gpa',
                    'evidence_value': tr.term_gpa,
                    'evidence_text': _('GPA học kỳ %s: %.2f (ngưỡng < %.2f, thang 10).') % (
                        tr.term_id.display_name, tr.term_gpa, th['gpa']),
                    'term_id': tr.term_id.id,
                })
            failed = tr.line_ids.filtered(lambda l: l.final_score < PASS_SCORE)
            if th['failed'] > 0 and len(failed) >= th['failed']:
                triggers[sid].append({
                    'warning_type': 'failed_subjects',
                    'evidence_value': len(failed),
                    'evidence_text': _('Học kỳ %s có %s môn dưới %.1f điểm (ngưỡng ≥ %s):\n%s') % (
                        tr.term_id.display_name, len(failed), PASS_SCORE, th['failed'],
                        '\n'.join('- %s: %.2f' % (l.subject_id.display_name, l.final_score) for l in failed)),
                    'term_id': tr.term_id.id,
                })

        # 3. Chuyên cần: enrollment đang học có tỷ lệ vắng vượt ngưỡng
        enrollments = self.env['univ.sms.enrollment'].sudo().search([
            ('student_id', 'in', ids),
            ('state', '=', 'registered'),
            ('class_id', '!=', False),
        ])
        over = defaultdict(list)
        for enr in enrollments:
            rate = enr.absence_rate
            if rate > th['absence']:
                over[enr.student_id.id].append((rate, enr))
        for sid, items in over.items():
            items.sort(key=lambda x: -x[0])
            max_rate, top = items[0]
            triggers[sid].append({
                'warning_type': 'attendance',
                'evidence_value': max_rate,
                'evidence_text': _('Tỷ lệ vắng vượt ngưỡng %.0f%%:\n%s') % (
                    th['absence'],
                    '\n'.join('- %s (%s): vắng %.1f%%' % (
                        e.class_id.display_name, e.subject_id.display_name, r) for r, e in items)),
                'term_id': top.term_id.id,
            })

        # 4. Công nợ học phí quá hạn
        today = fields.Date.context_today(self)
        fees = self.env['univ.sms.fee'].sudo().search([
            ('student_id', 'in', ids),
            ('remaining_amount', '>', 0),
            ('due_date', '!=', False),
            ('due_date', '<', today),
        ], order='due_date')
        debt = defaultdict(lambda: self.env['univ.sms.fee'])
        for fee in fees:
            debt[fee.student_id.id] |= fee
        for sid, sfees in debt.items():
            total = sum(sfees.mapped('remaining_amount'))
            triggers[sid].append({
                'warning_type': 'debt',
                'evidence_value': total,
                'evidence_text': _('Nợ học phí quá hạn, tổng %s:\n%s') % (
                    '{:,.0f}'.format(total),
                    '\n'.join('- %s: còn %s, hạn %s' % (
                        f.term_id.display_name, '{:,.0f}'.format(f.remaining_amount),
                        f.due_date.strftime('%d/%m/%Y')) for f in sfees)),
                'term_id': sfees[0].term_id.id,
            })

        # 5. Tín chỉ đăng ký dưới mức tối thiểu của đợt đăng ký chính thức gần nhất
        # đã ĐÓNG. Đợt đang mở thì sinh viên vẫn còn thời gian đăng ký, chưa xét.
        period = self.env['univ.sms.registration.period'].sudo().search([
            ('reg_type', '=', 'regular'),
            ('state', '=', 'closed'),
        ], order='date_start desc, id desc', limit=1)
        if period and period.min_credit > 0:
            regs = self.env['univ.sms.registration'].sudo().search([
                ('period_id', '=', period.id),
                ('student_id', 'in', ids),
                ('state', 'in', ('registered', 'confirmed')),
            ])
            credits = defaultdict(float)
            for reg in regs:
                credits[reg.student_id.id] += reg.offering_id.subject_id.credit or 0.0
            for sid in ids:
                total = credits.get(sid, 0.0)
                if total < period.min_credit:
                    triggers[sid].append({
                        'warning_type': 'credit',
                        'evidence_value': total,
                        'evidence_text': _('Đợt %s: đã đăng ký %s tín chỉ, tối thiểu %s tín chỉ.') % (
                            period.display_name, '%g' % total, period.min_credit),
                        'term_id': period.term_id.id,
                    })
        return triggers

    @api.model
    def run_evaluation(self, students=None):
        """Đánh giá cảnh báo sớm.

        - Chỉ xét sinh viên trạng thái ``studying``.
        - Có cảnh báo đang mở cùng (sinh viên, loại) → cập nhật bằng chứng (``updated``);
          chưa có → tạo mới (``created``).
        - KHÔNG tự đóng cảnh báo khi điều kiện hết: cố vấn quyết định đóng sau khi tư vấn.
        - Cảnh báo đã đóng được giữ nguyên; nếu điều kiện vẫn còn thì sinh cảnh báo mới.

        :return: dict(created=n, updated=n, checked=n, errors=n)
        """
        Student = self.env['univ.sms.student'].sudo()
        domain = [('state', '=', 'studying')]
        if students is not None:
            domain.append(('id', 'in', students.ids))
        students = Student.search(domain)
        result = {'created': 0, 'updated': 0, 'checked': len(students), 'errors': 0}
        if not students:
            return result

        triggers = self._collect_triggers(students)
        Warning = self.sudo()
        open_warnings = Warning.search([
            ('student_id', 'in', list(triggers.keys())),
            ('state', '!=', 'closed'),
        ])
        open_map = {(w.student_id.id, w.warning_type): w for w in open_warnings}
        now = fields.Datetime.now()

        for sid, items in triggers.items():
            try:
                with self.env.cr.savepoint():
                    created = updated = 0
                    for item in items:
                        existing = open_map.get((sid, item['warning_type']))
                        vals = {
                            'evidence_value': item['evidence_value'],
                            'evidence_text': item['evidence_text'],
                            'term_id': item.get('term_id') or False,
                            'last_checked_at': now,
                        }
                        if existing:
                            existing.write(vals)
                            updated += 1
                        else:
                            vals.update({
                                'student_id': sid,
                                'warning_type': item['warning_type'],
                                'detected_at': now,
                            })
                            Warning.create(vals)
                            created += 1
                    result['created'] += created
                    result['updated'] += updated
            except Exception:
                result['errors'] += 1
                _logger.exception('Lỗi khi đánh giá cảnh báo sớm cho sinh viên id=%s', sid)
        return result

    @api.model
    def _cron_run_evaluation(self):
        _logger.info('Bắt đầu đánh giá cảnh báo sớm (cron)')
        try:
            res = self.run_evaluation()
        except Exception:
            _logger.exception('Đánh giá cảnh báo sớm (cron) thất bại')
            return False
        _logger.info(
            'Đánh giá cảnh báo sớm xong: checked=%(checked)s created=%(created)s '
            'updated=%(updated)s errors=%(errors)s', res)
        return res
