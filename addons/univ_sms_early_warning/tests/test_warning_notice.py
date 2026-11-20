"""F4: cảnh báo sớm → thông báo cá nhân cho sinh viên + chatter nhắc cố vấn."""
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_early_warning')
class TestWarningNotice(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, no_reset_password=True))
        env = cls.env
        cls.advisor = env['res.users'].create({
            'name': 'CV F4', 'login': 'f4_ew_advisor', 'email': 'f4_ew_advisor@test.local',
            'groups_id': [(6, 0, [env.ref('base.group_user').id,
                                  env.ref('univ_sms_base.group_univ_advisor').id])]})
        faculty = env['univ.sms.faculty'].create({'name': 'Khoa F4EW', 'code': 'F4EW_K'})
        dept = env['univ.sms.department'].create({
            'name': 'BM F4EW', 'code': 'F4EW_BM', 'faculty_id': faculty.id})
        program = env['univ.sms.program'].create({
            'name': 'Ngành F4EW', 'code': 'F4EWP', 'department_id': dept.id})
        year = env['univ.sms.academic.year'].create({
            'name': 'F4EW 2042', 'date_start': '2042-09-01', 'date_end': '2043-08-31'})
        cls.term = env['univ.sms.term'].create({
            'name': 'F4EW HK1', 'academic_year_id': year.id,
            'date_start': '2042-09-01', 'date_end': '2043-01-15'})
        hc = env['univ.sms.home.class'].create({
            'name': 'Lớp F4EW', 'code': 'F4EW_A', 'program_id': program.id,
            'academic_year_id': year.id, 'advisor_id': cls.advisor.partner_id.id})
        cls.subjects = env['univ.sms.subject'].create([
            {'name': 'Môn F4EW %s' % i, 'code': 'F4EW_MH%s' % i, 'credit': 3} for i in range(2)])
        cls.student = env['univ.sms.student'].create({
            'name': 'SV F4 cảnh báo', 'program_id': program.id, 'home_class_id': hc.id})
        cls.student.action_confirm()
        env['univ.sms.transcript'].create({
            'student_id': cls.student.id, 'term_id': cls.term.id,
            'line_ids': [(0, 0, {'subject_id': s.id, 'final_score': 4.0}) for s in cls.subjects]})
        cls.Warning = env['univ.sms.warning']
        cls.Notice = env['univ.sms.student.notice']

    def _notices(self):
        return self.Notice.search([('student_id', '=', self.student.id),
                                   ('event_type', '=', 'early_warning')])

    def test_new_warning_creates_one_notice_per_warning(self):
        res = self.Warning.run_evaluation(self.student)
        warnings = self.Warning.search([('student_id', '=', self.student.id)])
        self.assertEqual(res['created'], len(warnings))
        self.assertTrue(warnings)
        notices = self._notices()
        self.assertEqual(len(notices), len(warnings))
        self.assertEqual(set(notices.mapped('res_id')), set(warnings.ids))
        self.assertTrue(all(n.res_model == 'univ.sms.warning' for n in notices))
        gpa = warnings.filtered(lambda w: w.warning_type == 'gpa')
        gpa_notice = notices.filtered(lambda n: n.res_id == gpa.id)
        self.assertIn('GPA thấp', gpa_notice.title)
        self.assertIn('cố vấn', gpa_notice.body)
        # Chạy lại: cập nhật bằng chứng, không thêm thông báo (kể cả khi đã đọc)
        notices.action_mark_read()
        res2 = self.Warning.run_evaluation(self.student)
        self.assertEqual(res2['created'], 0)
        self.assertEqual(len(self._notices()), len(warnings))

    def test_chatter_mentions_advisor(self):
        self.Warning.run_evaluation(self.student)
        warning = self.Warning.search([('student_id', '=', self.student.id)], limit=1)
        notes = warning.message_ids.filtered(lambda m: self.advisor.partner_id in m.partner_ids)
        self.assertEqual(len(notes), 1)
        self.assertIn(self.advisor.partner_id.name, notes.body)
        self.assertEqual(notes.subtype_id, self.env.ref('mail.mt_note'))
        self.assertEqual(len(warning.activity_ids), 1)

    def test_notice_failure_does_not_block_warning(self):
        with mute_logger('odoo.addons.univ_sms_student.models.student_notice'), \
                patch.object(type(self.Notice), 'create', side_effect=RuntimeError('boom')):
            res = self.Warning.run_evaluation(self.student)
        self.assertGreater(res['created'], 0)
        self.assertEqual(res['errors'], 0)
        self.assertFalse(self._notices())
