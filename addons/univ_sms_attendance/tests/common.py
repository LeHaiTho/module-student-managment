import secrets
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, new_test_user

from odoo.addons.univ_sms_attendance.models.attendance_session import hash_token

PORTAL_PASSWORD = 'QrCheckin#2026-test'


class AttendanceFixtureMixin:
    """Dữ liệu dùng chung: khoa → ngành → môn → học kỳ → lớp → sinh viên + đăng ký."""

    @classmethod
    def _setup_attendance_data(cls):
        env = cls.env
        cls.faculty = env['univ.sms.faculty'].create({'name': 'Khoa F2', 'code': 'F2_KH'})
        cls.department = env['univ.sms.department'].create({
            'name': 'Bộ môn F2', 'code': 'F2_BM', 'faculty_id': cls.faculty.id})
        cls.program = env['univ.sms.program'].create({
            'name': 'Ngành F2', 'code': 'F2NG', 'department_id': cls.department.id})
        cls.subject = env['univ.sms.subject'].create({'name': 'Môn F2', 'code': 'F2_MH', 'credit': 3})
        cls.subject_other = env['univ.sms.subject'].create({'name': 'Môn F2 khác', 'code': 'F2_MH2', 'credit': 2})
        cls.year = env['univ.sms.academic.year'].create({
            'name': 'F2 2040-2041', 'date_start': '2040-09-01', 'date_end': '2041-08-31'})
        cls.term = env['univ.sms.term'].create({
            'name': 'HK1 F2', 'academic_year_id': cls.year.id,
            'date_start': '2040-09-01', 'date_end': '2041-01-15'})
        cls.lecturer_user = new_test_user(
            env, login='f2_lecturer', groups='base.group_user,univ_sms_base.group_univ_lecturer',
            name='GV F2')
        cls.other_lecturer_user = new_test_user(
            env, login='f2_lecturer2', groups='base.group_user,univ_sms_base.group_univ_lecturer',
            name='GV F2 khác')
        cls.course_class = env['univ.sms.class'].create({
            'name': 'Lớp F2', 'code': 'F2_L1', 'subject_id': cls.subject.id,
            'term_id': cls.term.id, 'lecturer_id': cls.lecturer_user.partner_id.id})
        cls.other_class = env['univ.sms.class'].create({
            'name': 'Lớp F2 khác', 'code': 'F2_L2', 'subject_id': cls.subject_other.id,
            'term_id': cls.term.id, 'lecturer_id': cls.other_lecturer_user.partner_id.id})

        cls.student_a = cls._make_student('SV F2 A')
        cls.student_b = cls._make_student('SV F2 B')
        cls.student_out = cls._make_student('SV F2 ngoài lớp')
        cls.enr_a = cls._enroll(cls.student_a, cls.course_class)
        cls.enr_b = cls._enroll(cls.student_b, cls.course_class)
        cls._enroll(cls.student_out, cls.other_class)

        cls.user_a = cls._make_portal_user(cls.student_a, 'f2_sv_a')
        cls.user_b = cls._make_portal_user(cls.student_b, 'f2_sv_b')
        cls.user_out = cls._make_portal_user(cls.student_out, 'f2_sv_out')
        cls.user_portal_nostudent = new_test_user(
            env, login='f2_portal_x', groups='base.group_portal', password=PORTAL_PASSWORD)

    @classmethod
    def _make_student(cls, name):
        student = cls.env['univ.sms.student'].create({'name': name, 'program_id': cls.program.id})
        student.action_confirm()
        return student

    @classmethod
    def _enroll(cls, student, course_class, state='registered'):
        return cls.env['univ.sms.enrollment'].create({
            'student_id': student.id,
            'subject_id': course_class.subject_id.id,
            'term_id': course_class.term_id.id,
            'class_id': course_class.id,
            'state': state,
        })

    @classmethod
    def _make_portal_user(cls, student, login):
        return cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': student.name,
            'login': login,
            'password': PORTAL_PASSWORD,
            'partner_id': student.partner_id.id,
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def _make_sheet(self, course_class=None, date=None):
        return self.env['univ.sms.attendance.sheet'].create({
            'class_id': (course_class or self.course_class).id,
            'attendance_date': date or fields.Date.today(),
        })

    def _make_session(self, sheet, start_offset_min=0, duration_min=10, late_after=5, state='active'):
        """Tạo phiên với token đã biết. start = now - start_offset_min phút."""
        token = secrets.token_urlsafe(32)
        start = fields.Datetime.now() - timedelta(minutes=start_offset_min)
        session = self.env['univ.sms.attendance.session'].create({
            'sheet_id': sheet.id,
            'token_hash': hash_token(token),
            'start_time': start,
            'expire_time': start + timedelta(minutes=duration_min),
            'late_after_minutes': late_after,
            'state': state,
            'qr_url': 'http://localhost/attendance/qr/%s' % token,
        })
        return session, token

    def _confirmed_sheet(self, states, date):
        """Phiếu đã xác nhận; states = {student: 'absent'|'present'|...}."""
        sheet = self._make_sheet(date=date)
        sheet.action_load_students()
        for line in sheet.line_ids:
            if line.student_id in states:
                line.state = states[line.student_id]
        sheet.action_confirm()
        return sheet


class AttendanceCase(AttendanceFixtureMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_attendance_data()
