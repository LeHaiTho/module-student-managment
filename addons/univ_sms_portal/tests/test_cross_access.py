"""AT14: sinh viên A không đọc được dữ liệu của sinh viên B (ACL + record rule)."""
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_portal')
class TestPortalCrossAccess(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        faculty = env['univ.sms.faculty'].create({'name': 'Khoa XA', 'code': 'KXA'})
        dept = env['univ.sms.department'].create({'name': 'BM XA', 'code': 'BMXA', 'faculty_id': faculty.id})
        program = env['univ.sms.program'].create({'name': 'Ngành XA', 'code': 'NXA', 'department_id': dept.id})
        year = env['univ.sms.academic.year'].create({
            'name': 'XA', 'date_start': '2031-09-01', 'date_end': '2032-08-31'})
        term = env['univ.sms.term'].create({
            'name': 'HK XA', 'academic_year_id': year.id, 'date_start': '2031-09-01', 'date_end': '2032-01-15'})
        subject = env['univ.sms.subject'].create({'name': 'Môn XA', 'code': 'MXA', 'credit': 3})
        cls_ = env['univ.sms.class'].create({
            'name': 'Lớp XA', 'code': 'LXA', 'subject_id': subject.id, 'term_id': term.id})
        portal = env.ref('base.group_portal')

        def make(login):
            user = env['res.users'].create({
                'name': login, 'login': login, 'password': login + '_pw!',
                'groups_id': [(6, 0, [portal.id])]})
            student = env['univ.sms.student'].create({
                'partner_id': user.partner_id.id, 'program_id': program.id})
            student.action_confirm()
            enr = env['univ.sms.enrollment'].create({
                'student_id': student.id, 'subject_id': subject.id, 'term_id': term.id,
                'class_id': cls_.id})
            return user, student, enr

        cls.user_a, cls.student_a, cls.enr_a = make('xa_student_a')
        cls.user_b, cls.student_b, cls.enr_b = make('xa_student_b')

        exam = env['univ.sms.exam'].create({
            'name': 'Cuối kỳ XA', 'class_id': cls_.id, 'exam_type': 'final', 'max_score': 10})
        Result = env['univ.sms.exam.result']
        cls.res_a = Result.create({'exam_id': exam.id, 'student_id': cls.student_a.id, 'score': 8})
        cls.res_b = Result.create({'exam_id': exam.id, 'student_id': cls.student_b.id, 'score': 3})
        Transcript = env['univ.sms.transcript']
        cls.tr_b = Transcript.create({'student_id': cls.student_b.id, 'term_id': term.id,
                                      'line_ids': [(0, 0, {'subject_id': subject.id, 'final_score': 3})]})
        Transcript.create({'student_id': cls.student_a.id, 'term_id': term.id,
                           'line_ids': [(0, 0, {'subject_id': subject.id, 'final_score': 8})]})
        cls.fee_b = env['univ.sms.fee'].create({'student_id': cls.student_b.id, 'term_id': term.id})
        sheet = env['univ.sms.attendance.sheet'].create({'class_id': cls_.id, 'attendance_date': '2031-10-01'})
        sheet.action_load_students()
        cls.att_b = sheet.line_ids.filtered(lambda l: l.student_id == cls.student_b)
        cls.cert_type = env['univ.sms.certificate.type'].create({'name': 'Giấy XN', 'code': 'GXA'})
        cls.cert_b = env['univ.sms.certificate.request'].create({
            'student_id': cls.student_b.id, 'certificate_type_id': cls.cert_type.id})
        cls.fb_b = env['univ.sms.feedback'].create({
            'student_id': cls.student_b.id, 'category': 'other', 'subject': 'B', 'description': 'B'})
        Notif = env['univ.sms.notification']
        cls.notif_draft = Notif.create({'title': 'Nháp', 'content': '<p>x</p>'})
        cls.notif_pub = Notif.create({'title': 'Đã đăng', 'content': '<p>y</p>'})
        cls.notif_pub.action_publish()

    def _assert_only_own(self, model, own, other, field='student_id'):
        Model = self.env[model].with_user(self.user_a)
        found = Model.search([(field, 'in', (self.student_a | self.student_b).ids)])
        self.assertTrue(set(found.ids) >= set(own.ids), model)
        self.assertNotIn(other.id, found.ids, '%s: thấy dữ liệu của SV khác' % model)
        with self.assertRaises(AccessError):
            Model.browse(other.id).read([field])

    def test_at14_exam_results(self):
        self._assert_only_own('univ.sms.exam.result', self.res_a, self.res_b)

    def test_at14_transcripts(self):
        tr_a = self.env['univ.sms.transcript'].search([('student_id', '=', self.student_a.id)])
        self._assert_only_own('univ.sms.transcript', tr_a, self.tr_b)
        with self.assertRaises(AccessError):
            self.tr_b.line_ids.with_user(self.user_a).read(['final_score'])

    def test_at14_enrollment_fee_attendance(self):
        self._assert_only_own('univ.sms.enrollment', self.enr_a, self.enr_b)
        with self.assertRaises(AccessError):
            self.fee_b.with_user(self.user_a).read(['total_amount'])
        with self.assertRaises(AccessError):
            self.att_b.with_user(self.user_a).read(['state'])

    def test_at14_services(self):
        with self.assertRaises(AccessError):
            self.cert_b.with_user(self.user_a).read(['state'])
        with self.assertRaises(AccessError):
            self.fb_b.with_user(self.user_a).read(['subject'])

    def test_portal_cannot_read_student_master_or_write_grades(self):
        with self.assertRaises(AccessError):
            self.student_b.with_user(self.user_a).read(['id_number'])
        with self.assertRaises(AccessError):
            self.res_a.with_user(self.user_a).write({'score': 10})

    def test_notifications_only_published(self):
        visible = self.env['univ.sms.notification'].with_user(self.user_a).search(
            [('id', 'in', (self.notif_draft | self.notif_pub).ids)])
        self.assertEqual(visible, self.notif_pub)
