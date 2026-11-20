"""F4: thông báo cá nhân sinh viên (model, chống trùng, phân quyền)."""
from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_student')
class TestStudentNotice(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env(context=dict(cls.env.context, no_reset_password=True))
        cls.env = env
        faculty = env['univ.sms.faculty'].create({'name': 'Khoa TB', 'code': 'KTB4'})
        dept = env['univ.sms.department'].create({
            'name': 'BM TB', 'code': 'BMTB4', 'faculty_id': faculty.id})
        program = env['univ.sms.program'].create({
            'name': 'Ngành TB', 'code': 'NTB4', 'department_id': dept.id})
        portal = env.ref('base.group_portal')
        Users = env['res.users']

        def make(login):
            user = Users.create({'name': login, 'login': login, 'password': login + '_pw!',
                                 'groups_id': [(6, 0, [portal.id])]})
            student = env['univ.sms.student'].create({
                'partner_id': user.partner_id.id, 'program_id': program.id})
            return user, student

        cls.user_a, cls.student_a = make('f4_notice_a')
        cls.user_b, cls.student_b = make('f4_notice_b')
        cls.lecturer = Users.create({
            'name': 'GV TB', 'login': 'f4_notice_lecturer',
            'groups_id': [(6, 0, [env.ref('base.group_user').id,
                                  env.ref('univ_sms_base.group_univ_lecturer').id])]})
        cls.officer = Users.create({
            'name': 'PDT TB', 'login': 'f4_notice_officer',
            'groups_id': [(6, 0, [env.ref('base.group_user').id,
                                  env.ref('univ_sms_base.group_univ_academic_officer').id])]})
        cls.Notice = env['univ.sms.student.notice']

    def _count(self, student, **kw):
        domain = [('student_id', '=', student.id)] + [(k, '=', v) for k, v in kw.items()]
        return self.Notice.search_count(domain)

    # ─── _notify ──────────────────────────────────────────────────────────
    def test_notify_creates_and_dedups_unread(self):
        n1 = self.Notice._notify(self.student_a, 'other', 'Tiêu đề 1', 'Nội dung 1', self.student_b)
        self.assertTrue(n1)
        self.assertEqual((n1.res_model, n1.res_id), ('univ.sms.student', self.student_b.id))
        n2 = self.Notice._notify(self.student_a, 'other', 'Tiêu đề 2', 'Nội dung 2', self.student_b)
        self.assertEqual(n1, n2, 'Thông báo chưa đọc cùng khóa phải được cập nhật, không tạo mới')
        self.assertEqual(n1.body, 'Nội dung 2')
        self.assertEqual(self._count(self.student_a), 1)
        # Khác bản ghi liên quan → thông báo khác
        self.Notice._notify(self.student_a, 'other', 'X', 'Y', self.student_a)
        self.assertEqual(self._count(self.student_a), 2)
        # Đã đọc → sự kiện mới tạo thông báo mới
        n1.action_mark_read()
        n3 = self.Notice._notify(self.student_a, 'other', 'Tiêu đề 3', 'Z', self.student_b)
        self.assertNotEqual(n3, n1)
        self.assertEqual(self._count(self.student_a), 3)

    def test_notify_without_record_dedups(self):
        a = self.Notice._notify(self.student_a, 'other', 'Không gắn bản ghi')
        b = self.Notice._notify(self.student_a, 'other', 'Không gắn bản ghi (lần 2)')
        self.assertEqual(a, b)
        self.assertEqual(self._count(self.student_a), 1)

    def test_notify_never_raises(self):
        self.assertFalse(self.Notice._notify(self.Notice.env['univ.sms.student'], 'other', 'x'))
        with mute_logger('odoo.addons.univ_sms_student.models.student_notice'):
            res = self.Notice._notify(self.student_a, 'not_a_valid_event', 'x')
            self.assertFalse(res)
            with patch.object(type(self.Notice), 'create', side_effect=RuntimeError('boom')):
                self.assertFalse(self.Notice._notify(self.student_a, 'other', 'x'))
        self.assertEqual(self._count(self.student_a), 0)
        # Cursor vẫn dùng được sau lỗi
        self.assertTrue(self.Notice._notify(self.student_a, 'other', 'ok'))

    # ─── Phân quyền ───────────────────────────────────────────────────────
    def test_portal_sees_and_marks_only_own(self):
        na = self.Notice._notify(self.student_a, 'other', 'Của A')
        nb = self.Notice._notify(self.student_b, 'other', 'Của B')
        NoticeA = self.Notice.with_user(self.user_a)
        self.assertEqual(NoticeA.search([]), na)
        with self.assertRaises(AccessError):
            nb.with_user(self.user_a).read(['title'])
        with self.assertRaises(AccessError):
            nb.with_user(self.user_a).action_mark_read()
        self.assertFalse(nb.is_read)
        na.with_user(self.user_a).action_mark_read()
        self.assertTrue(na.is_read)
        self.assertTrue(na.read_at)
        self.assertEqual(self.Notice._portal_unread_count(self.user_a), 0)
        self.assertEqual(self.Notice._portal_unread_count(self.user_b), 1)

    def test_portal_cannot_write_content_create_or_unlink(self):
        na = self.Notice._notify(self.student_a, 'other', 'Của A', 'Nội dung gốc')
        with self.assertRaises(AccessError):
            na.with_user(self.user_a).write({'title': 'Sửa'})
        with self.assertRaises(AccessError):
            na.with_user(self.user_a).write({'body': 'Sửa', 'is_read': True})
        with self.assertRaises(AccessError):
            na.with_user(self.user_a).write({'student_id': self.student_b.id})
        with self.assertRaises(AccessError):
            self.Notice.with_user(self.user_a).create({
                'student_id': self.student_a.id, 'title': 'Tự tạo'})
        with self.assertRaises(AccessError):
            na.with_user(self.user_a).unlink()
        self.assertEqual((na.title, na.body, na.is_read), ('Của A', 'Nội dung gốc', False))

    def test_lecturer_read_only_officer_full(self):
        na = self.Notice._notify(self.student_a, 'other', 'Của A')
        self.assertEqual(na.with_user(self.lecturer).title, 'Của A')
        with self.assertRaises(AccessError):
            na.with_user(self.lecturer).write({'title': 'GV sửa'})
        manual = self.Notice.with_user(self.officer).create({
            'student_id': self.student_b.id, 'title': 'Thông báo thủ công', 'body': 'Nội dung'})
        manual.write({'title': 'Đã sửa'})
        self.assertEqual(manual.event_type, 'other')
        manual.unlink()

    def test_unread_count_for_non_student(self):
        self.assertEqual(self.Notice._portal_unread_count(self.officer), 0)
        self.assertEqual(self.Notice._portal_unread_count(self.env.ref('base.public_user')), 0)
