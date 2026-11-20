from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_early_warning')
class TestEarlyWarning(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, no_reset_password=True, mail_create_nosubscribe=True))
        ref = cls.env.ref
        g_user = ref('base.group_user')
        cls.g_advisor = ref('univ_sms_base.group_univ_advisor')
        Users = cls.env['res.users']

        def mk_user(login, groups):
            return Users.create({
                'name': login.upper(), 'login': login, 'email': '%s@test.local' % login,
                'groups_id': [(6, 0, [g.id for g in groups])],
            })

        cls.advisor_a = mk_user('ew_advisor_a', [g_user, cls.g_advisor])
        cls.advisor_b = mk_user('ew_advisor_b', [g_user, cls.g_advisor])
        cls.lecturer = mk_user('ew_lecturer', [g_user, ref('univ_sms_base.group_univ_lecturer')])
        cls.officer = mk_user('ew_officer', [g_user, ref('univ_sms_base.group_univ_academic_officer')])
        cls.affairs = mk_user('ew_affairs', [g_user, ref('univ_sms_base.group_univ_student_affairs_office')])
        cls.sms_admin = mk_user('ew_admin', [g_user, ref('univ_sms_base.group_univ_admin')])

        faculty = cls.env['univ.sms.faculty'].create({'name': 'Khoa EW', 'code': 'EW_K'})
        dept = cls.env['univ.sms.department'].create({
            'name': 'BM EW', 'code': 'EW_BM', 'faculty_id': faculty.id})
        cls.program = cls.env['univ.sms.program'].create({
            'name': 'Ngành EW', 'code': 'EWP', 'department_id': dept.id})
        cls.year = cls.env['univ.sms.academic.year'].create({
            'name': 'EW 2040-2041', 'date_start': '2040-09-01', 'date_end': '2041-08-31'})
        Term = cls.env['univ.sms.term']
        cls.term1 = Term.create({'name': 'EW HK1', 'academic_year_id': cls.year.id,
                                 'date_start': '2040-09-01', 'date_end': '2041-01-15'})
        cls.term2 = Term.create({'name': 'EW HK2', 'academic_year_id': cls.year.id,
                                 'date_start': '2041-02-01', 'date_end': '2041-06-30'})
        HomeClass = cls.env['univ.sms.home.class']
        cls.hc_a = HomeClass.create({'name': 'Lớp EW A', 'code': 'EW_A', 'program_id': cls.program.id,
                                     'academic_year_id': cls.year.id,
                                     'advisor_id': cls.advisor_a.partner_id.id})
        cls.hc_b = HomeClass.create({'name': 'Lớp EW B', 'code': 'EW_B', 'program_id': cls.program.id,
                                     'academic_year_id': cls.year.id,
                                     'advisor_id': cls.advisor_b.partner_id.id})
        Subject = cls.env['univ.sms.subject']
        cls.subjects = Subject.browse([
            Subject.create({'name': 'Môn EW %s' % i, 'code': 'EW_MH%s' % i, 'credit': 3}).id
            for i in range(1, 5)
        ])
        cls.Warning = cls.env['univ.sms.warning']

    # ─── helpers ───────────────────────────────────────────────────────────
    def _student(self, name, home_class=None, confirm=True):
        hc = home_class or self.hc_a
        st = self.env['univ.sms.student'].create({
            'name': name, 'program_id': self.program.id, 'home_class_id': hc.id})
        if confirm:
            st.action_confirm()
        return st

    def _transcript(self, student, term, scores):
        return self.env['univ.sms.transcript'].create({
            'student_id': student.id,
            'term_id': term.id,
            'line_ids': [(0, 0, {'subject_id': self.subjects[i].id, 'final_score': s})
                         for i, s in enumerate(scores)],
        })

    def _warnings(self, student, wtype=None, open_only=True):
        domain = [('student_id', '=', student.id)]
        if wtype:
            domain.append(('warning_type', '=', wtype))
        if open_only:
            domain.append(('state', '!=', 'closed'))
        return self.Warning.search(domain)

    def _low_gpa_student(self, name='SV GPA thấp', home_class=None):
        st = self._student(name, home_class)
        self._transcript(st, self.term2, [4.5, 5.0])  # GPA 4.75, 1 môn trượt
        return st

    # ─── AT11 / AT12 ───────────────────────────────────────────────────────
    def test_at11_at12_gpa_warning_no_duplicate(self):
        st = self._low_gpa_student()
        res = self.Warning.run_evaluation(st)
        self.assertEqual((res['created'], res['updated'], res['checked']), (1, 0, 1))
        w = self._warnings(st)
        self.assertEqual(len(w), 1)
        self.assertEqual(w.warning_type, 'gpa')
        self.assertAlmostEqual(w.evidence_value, 4.75, places=2)
        self.assertEqual(w.severity, 'high')
        self.assertEqual(w.state, 'new')
        self.assertEqual(w.term_id, self.term2)
        self.assertEqual(w.advisor_partner_id, self.advisor_a.partner_id)
        self.assertEqual(w.home_class_id, self.hc_a)
        self.assertEqual(w.program_id, self.program)
        self.assertTrue(w.detected_at)
        # Giao cho cố vấn: activity To-Do cho user cố vấn
        self.assertIn(self.advisor_a, w.activity_ids.mapped('user_id'))

        res2 = self.Warning.run_evaluation(st)
        self.assertEqual((res2['created'], res2['updated']), (0, 1))
        self.assertEqual(len(self._warnings(st)), 1, 'Chạy lại không được sinh cảnh báo trùng')
        self.assertEqual(len(w.activity_ids), 1, 'Chạy lại không được giao thêm activity')

    def test_gpa_uses_latest_term(self):
        st = self._student('SV cải thiện')
        self._transcript(st, self.term1, [2.0, 3.0])
        self._transcript(st, self.term2, [8.0, 9.0])
        self.Warning.run_evaluation(st)
        self.assertFalse(self._warnings(st, 'gpa'))
        self.assertFalse(self._warnings(st, 'failed_subjects'))

    def test_advisor_fallback_student_advisor_first(self):
        st = self._student('SV có cố vấn riêng', self.hc_a)
        st.advisor_id = self.advisor_b.partner_id
        self._transcript(st, self.term2, [3.0, 3.0, 3.0])
        self.Warning.run_evaluation(st)
        w = self._warnings(st, 'gpa')
        self.assertEqual(w.advisor_partner_id, self.advisor_b.partner_id)

    def test_failed_subjects_rule(self):
        st = self._student('SV nợ môn')
        self._transcript(st, self.term2, [4.0, 4.0, 9.0, 9.0])  # GPA 6.5, 2 môn trượt
        res = self.Warning.run_evaluation(st)
        self.assertEqual(res['created'], 1)
        self.assertFalse(self._warnings(st, 'gpa'))
        w = self._warnings(st, 'failed_subjects')
        self.assertEqual(w.evidence_value, 2)
        self.assertEqual(w.severity, 'high')
        self.assertIn(self.subjects[0].name, w.evidence_text)

    def test_threshold_from_config_parameter(self):
        self.env['ir.config_parameter'].sudo().set_param('univ_sms.warning_gpa_threshold', '4.0')
        st = self._low_gpa_student()
        self.Warning.run_evaluation(st)
        self.assertFalse(self._warnings(st, 'gpa'), 'GPA 4.75 không dưới ngưỡng 4.0')

    def test_attendance_rule(self):
        st = self._student('SV vắng nhiều')
        other = self._student('SV chăm')
        cls_ = self.env['univ.sms.class'].create({
            'name': 'Lớp TC EW', 'code': 'EW_TC1', 'subject_id': self.subjects[0].id,
            'term_id': self.term2.id})
        Enr = self.env['univ.sms.enrollment']
        for s in (st, other):
            Enr.create({'student_id': s.id, 'subject_id': self.subjects[0].id,
                        'term_id': self.term2.id, 'class_id': cls_.id, 'state': 'registered'})
        Sheet = self.env['univ.sms.attendance.sheet']
        for day in ('2041-02-10', '2041-02-17', '2041-02-24'):
            sheet = Sheet.create({
                'class_id': cls_.id, 'attendance_date': day,
                'line_ids': [(0, 0, {'student_id': st.id, 'state': 'absent'}),
                             (0, 0, {'student_id': other.id, 'state': 'present'})],
            })
            sheet.action_confirm()
        self.Warning.run_evaluation(st | other)
        w = self._warnings(st, 'attendance')
        self.assertEqual(len(w), 1)
        self.assertAlmostEqual(w.evidence_value, 100.0, places=1)
        self.assertEqual(w.severity, 'high')
        self.assertIn('Lớp TC EW', w.evidence_text)
        self.assertFalse(self._warnings(other, 'attendance'))

    def test_debt_rule(self):
        st = self._student('SV nợ phí')
        ok = self._student('SV chưa tới hạn')
        Enr = self.env['univ.sms.enrollment']
        Fee = self.env['univ.sms.fee']
        today = fields.Date.context_today(self.Warning)
        fees = Fee
        for s, due in ((st, today - timedelta(days=10)), (ok, today + timedelta(days=10))):
            Enr.create({'student_id': s.id, 'subject_id': self.subjects[1].id,
                        'term_id': self.term2.id, 'state': 'registered'})
            fees |= Fee.create({'student_id': s.id, 'term_id': self.term2.id, 'due_date': due})
        self.assertTrue(all(f.remaining_amount > 0 for f in fees), 'Học phí phải > 0 để kiểm tra nợ')
        self.Warning.run_evaluation(st | ok)
        w = self._warnings(st, 'debt')
        self.assertEqual(len(w), 1)
        self.assertEqual(w.severity, 'medium')
        self.assertAlmostEqual(w.evidence_value, fees[0].remaining_amount, places=0)
        self.assertFalse(self._warnings(ok, 'debt'), 'Chưa quá hạn thì không cảnh báo')

    def test_credit_rule(self):
        st_low = self._student('SV đăng ký ít')
        st_none = self._student('SV chưa đăng ký')
        now = fields.Datetime.now()
        period = self.env['univ.sms.registration.period'].create({
            'name': 'Đợt EW', 'term_id': self.term2.id, 'reg_type': 'regular',
            'date_start': now - timedelta(days=1), 'date_end': now + timedelta(days=10),
            'min_credit': 10, 'state': 'open'})
        offering = self.env['univ.sms.course.offering'].create({
            'subject_id': self.subjects[2].id, 'term_id': self.term2.id, 'max_seats': 10})
        self.env['univ.sms.registration'].create({
            'student_id': st_low.id, 'offering_id': offering.id, 'period_id': period.id,
            'state': 'registered'})
        # Đợt còn mở: sinh viên vẫn còn thời gian đăng ký nên chưa cảnh báo
        self.Warning.run_evaluation(st_low | st_none)
        self.assertFalse(self._warnings(st_low, 'credit'))
        self.assertFalse(self._warnings(st_none, 'credit'))
        period.action_close()
        self.Warning.run_evaluation(st_low | st_none)
        w_low = self._warnings(st_low, 'credit')
        self.assertEqual(len(w_low), 1)
        self.assertEqual(w_low.evidence_value, 3)
        self.assertEqual(w_low.severity, 'medium')
        self.assertEqual(w_low.term_id, self.term2)
        self.assertEqual(self._warnings(st_none, 'credit').evidence_value, 0)
        # min_credit = 0 → không xét
        period.min_credit = 0
        st3 = self._student('SV khác')
        self.Warning.run_evaluation(st3)
        self.assertFalse(self._warnings(st3, 'credit'))

    def test_non_studying_ignored(self):
        draft = self._student('SV hồ sơ mới', confirm=False)
        leave = self._student('SV bảo lưu')
        leave.action_on_leave()
        for st in (draft, leave):
            self._transcript(st, self.term2, [1.0, 1.0])
        res = self.Warning.run_evaluation(draft | leave)
        self.assertEqual((res['checked'], res['created']), (0, 0))
        self.assertFalse(self._warnings(draft, open_only=False))
        self.assertFalse(self._warnings(leave, open_only=False))

    # ─── Vòng đời cảnh báo ─────────────────────────────────────────────────
    def test_close_requires_consultation_or_note(self):
        st = self._low_gpa_student()
        self.Warning.run_evaluation(st)
        w = self._warnings(st, 'gpa')
        with self.assertRaises(UserError):
            w.action_close()
        w.action_start()
        self.assertEqual(w.state, 'in_progress')
        w.close_note = 'Sinh viên đã cải thiện'
        w.with_user(self.advisor_a).action_close()
        self.assertEqual(w.state, 'closed')
        self.assertTrue(w.closed_at)
        self.assertEqual(w.closed_by_id, self.advisor_a)
        w.action_reopen()
        self.assertEqual(w.state, 'in_progress')
        self.assertFalse(w.closed_at)
        self.assertFalse(w.closed_by_id)

    def test_closed_then_rerun_creates_new_warning(self):
        """Hành vi chốt: cảnh báo đã đóng được giữ lại làm lịch sử; nếu điều kiện vẫn còn,
        lần đánh giá sau sinh một cảnh báo MỚI. Không tự đóng khi điều kiện hết."""
        st = self._low_gpa_student()
        self.Warning.run_evaluation(st)
        old = self._warnings(st, 'gpa')
        old.write({'close_note': 'Đã tư vấn trực tiếp'})
        old.action_close()
        res = self.Warning.run_evaluation(st)
        self.assertEqual(res['created'], 1)
        new = self._warnings(st, 'gpa')
        self.assertEqual(len(new), 1)
        self.assertNotEqual(new, old)
        self.assertEqual(old.state, 'closed')
        # Không mở lại được khi đã có cảnh báo cùng loại đang mở
        with self.assertRaises(UserError):
            old.action_reopen()
        # Điều kiện hết → không tự đóng
        self.env['univ.sms.transcript'].search([('student_id', '=', st.id)]).line_ids.write(
            {'final_score': 9.0})
        res = self.Warning.run_evaluation(st)
        self.assertEqual((res['created'], res['updated']), (0, 0))
        self.assertEqual(new.state, 'new')

    def test_duplicate_open_warning_rejected(self):
        st = self._student('SV trùng')
        self.Warning.create({'student_id': st.id, 'warning_type': 'debt'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.Warning.create({'student_id': st.id, 'warning_type': 'debt'})
        # Bỏ qua constraint Python vẫn bị chặn bởi partial unique index
        from psycopg2 import IntegrityError
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError), self.cr.savepoint():
            self.cr.execute("""
                INSERT INTO univ_sms_warning (student_id, warning_type, severity, state)
                VALUES (%s, 'debt', 'medium', 'in_progress')""", (st.id,))

    def test_consultation_logging(self):
        st = self._low_gpa_student()
        self.Warning.run_evaluation(st)
        w = self._warnings(st, 'gpa')
        c = self.env['univ.sms.warning.consultation'].with_user(self.advisor_a).create({
            'warning_id': w.id, 'note': 'Gặp sinh viên, lập kế hoạch học lại', 'outcome': 'plan_agreed'})
        self.assertEqual(c.user_id, self.advisor_a)
        self.assertEqual(w.state, 'in_progress', 'Ghi nhận tư vấn chuyển cảnh báo sang Đang xử lý')
        self.assertEqual(w.consultation_count, 1)
        self.assertTrue(any('lập kế hoạch học lại' in (m.body or '') for m in w.message_ids))
        # Đã có tư vấn → đóng được không cần ghi chú
        w.with_user(self.advisor_a).action_close()
        self.assertEqual(w.state, 'closed')
        # Cố vấn B không được ghi tư vấn cho cảnh báo của cố vấn A
        with self.assertRaises(AccessError):
            self.env['univ.sms.warning.consultation'].with_user(self.advisor_b).create({
                'warning_id': w.id, 'note': 'x'})

    # ─── AT13: phân quyền ──────────────────────────────────────────────────
    def test_at13_advisor_sees_only_own(self):
        st_a = self._low_gpa_student('SV lớp A', self.hc_a)
        st_b = self._low_gpa_student('SV lớp B', self.hc_b)
        self.Warning.run_evaluation(st_a | st_b)
        w_a = self._warnings(st_a)
        w_b = self._warnings(st_b)
        self.assertTrue(w_a and w_b)

        seen_a = self.Warning.with_user(self.advisor_a).search([('student_id', 'in', (st_a | st_b).ids)])
        self.assertEqual(seen_a, w_a)
        seen_b = self.Warning.with_user(self.advisor_b).search([('student_id', 'in', (st_a | st_b).ids)])
        self.assertEqual(seen_b, w_b)
        self.assertFalse(seen_b & w_a)
        with self.assertRaises(AccessError):
            w_a.with_user(self.advisor_b).read(['state'])
        with self.assertRaises(AccessError):
            w_a.with_user(self.advisor_b).write({'close_note': 'x'})
        # Cố vấn A được ghi trên cảnh báo của mình
        w_a.with_user(self.advisor_a).write({'close_note': 'ok'})
        # Cố vấn không tự đổi người phụ trách hay bằng chứng
        with self.assertRaises(UserError):
            w_a.with_user(self.advisor_a).write({'advisor_partner_id': self.advisor_b.partner_id.id})
        with self.assertRaises(UserError):
            w_a.with_user(self.advisor_a).write({'evidence_value': 9.9})
        # Cố vấn không được tự tạo cảnh báo
        with self.assertRaises(AccessError):
            self.Warning.with_user(self.advisor_a).create({'student_id': st_a.id, 'warning_type': 'debt'})

        # Admin SMS (kế thừa cả Cố vấn) và Phòng ĐT / CTSV thấy tất cả
        for user in (self.sms_admin, self.officer, self.affairs):
            seen = self.Warning.with_user(user).search([('student_id', 'in', (st_a | st_b).ids)])
            self.assertEqual(seen, w_a | w_b, user.login)
        self.assertTrue(self.sms_admin.has_group('univ_sms_base.group_univ_advisor'))

    def test_portal_student_sees_only_own(self):
        st1 = self._low_gpa_student('SV portal 1')
        st2 = self._low_gpa_student('SV portal 2')
        self.Warning.run_evaluation(st1 | st2)
        portal = self.env['res.users'].create({
            'name': 'SV portal 1', 'login': 'ew_portal1', 'partner_id': st1.partner_id.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])]})
        seen = self.Warning.with_user(portal).search([])
        self.assertEqual(seen, self._warnings(st1))
        self.assertEqual(seen.read(['warning_type'])[0]['warning_type'], 'gpa')
        with self.assertRaises(AccessError):
            self._warnings(st2).with_user(portal).read(['warning_type'])
        with self.assertRaises(AccessError):
            seen.with_user(portal).write({'close_note': 'x'})

    def test_plain_lecturer_has_no_access(self):
        st = self._low_gpa_student()
        self.Warning.run_evaluation(st)
        w = self._warnings(st)
        with self.assertRaises(AccessError):
            w.with_user(self.lecturer).read(['state'])
        with self.assertRaises(AccessError):
            self.Warning.with_user(self.lecturer).search([])

    def test_student_form_counter(self):
        st = self._low_gpa_student()
        self.Warning.run_evaluation(st)
        self.assertEqual(st.with_user(self.advisor_a).warning_open_count, 1)
        self.assertEqual(st.with_user(self.advisor_b).warning_open_count, 0)
        action = st.action_view_warnings()
        self.assertEqual(action['domain'], [('student_id', '=', st.id)])

    # ─── Wizard & cron ─────────────────────────────────────────────────────
    def test_wizard_scope_and_counts(self):
        st_a = self._low_gpa_student('SV wizard A', self.hc_a)
        st_b = self._low_gpa_student('SV wizard B', self.hc_b)
        wiz = self.env['univ.sms.warning.evaluation.wizard'].with_user(self.officer).create({
            'home_class_ids': [(6, 0, [self.hc_a.id])]})
        action = wiz.action_run()
        self.assertEqual(action['res_model'], 'univ.sms.warning.evaluation.wizard')
        self.assertEqual(wiz.state, 'done')
        self.assertGreaterEqual(wiz.checked_count, 1)
        self.assertGreaterEqual(wiz.created_count, 1)
        self.assertTrue(self._warnings(st_a, 'gpa'))
        self.assertFalse(self._warnings(st_b), 'Ngoài phạm vi lớp đã chọn')
        wiz2 = self.env['univ.sms.warning.evaluation.wizard'].with_user(self.officer).create({
            'home_class_ids': [(6, 0, [self.hc_a.id])]})
        wiz2.action_run()
        self.assertEqual(wiz2.created_count, 0)
        self.assertGreaterEqual(wiz2.updated_count, 1)

    def test_cron_runs(self):
        st = self._low_gpa_student()
        cron = self.env.ref('univ_sms_early_warning.ir_cron_univ_sms_warning_evaluation')
        self.assertTrue(cron.active)
        res = self.Warning._cron_run_evaluation()
        self.assertIsInstance(res, dict)
        self.assertGreaterEqual(res['checked'], 1)
        self.assertTrue(self._warnings(st, 'gpa'))
