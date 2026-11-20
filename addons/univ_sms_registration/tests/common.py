from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase


class RegistrationDataMixin:
    """Tạo dữ liệu đăng ký môn độc lập cho test (không dùng dữ liệu demo)."""

    @classmethod
    def _setup_registration_data(cls):
        env = cls.env
        today = fields.Date.today()
        now = fields.Datetime.now()
        faculty = env['univ.sms.faculty'].create({'name': 'Khoa F1', 'code': 'KF1T'})
        dept = env['univ.sms.department'].create({
            'name': 'BM F1', 'code': 'BMF1T', 'faculty_id': faculty.id})
        cls.program = env['univ.sms.program'].create({
            'name': 'Ngành F1', 'code': 'NF1T', 'department_id': dept.id})
        year = env['univ.sms.academic.year'].create({
            'name': 'F1-YEAR', 'date_start': today - timedelta(days=200),
            'date_end': today + timedelta(days=200)})
        cls.term = env['univ.sms.term'].create({
            'name': 'HK F1', 'academic_year_id': year.id,
            'date_start': today - timedelta(days=30), 'date_end': today + timedelta(days=120)})
        cls.old_term = env['univ.sms.term'].create({
            'name': 'HK F1 cũ', 'academic_year_id': year.id,
            'date_start': today - timedelta(days=190), 'date_end': today - timedelta(days=40)})

        Subject = env['univ.sms.subject']
        cls.sub_a = Subject.create({'name': 'Toán F1', 'code': 'F1A', 'credit': 3})
        cls.sub_b = Subject.create({'name': 'Lập trình F1', 'code': 'F1B', 'credit': 3,
                                    'prerequisite_ids': [(6, 0, [cls.sub_a.id])]})
        cls.sub_c = Subject.create({'name': 'Vật lý F1', 'code': 'F1C', 'credit': 4})
        cls.sub_d = Subject.create({'name': 'Hóa F1', 'code': 'F1D', 'credit': 3})
        cls.sub_e = Subject.create({'name': 'Anh văn F1', 'code': 'F1E', 'credit': 2})

        # (subject, mã lớp, thứ, giờ bắt đầu, giờ kết thúc)
        def make_class(subject, code, day, start, end, term=None):
            klass = env['univ.sms.class'].create({
                'name': code, 'code': code, 'subject_id': subject.id,
                'term_id': (term or cls.term).id})
            env['univ.sms.timetable'].create({
                'class_id': klass.id, 'day_of_week': day,
                'start_time': start, 'end_time': end, 'room': 'A1'})
            return klass

        cls.cls_a = make_class(cls.sub_a, 'F1-A', '0', 7.0, 9.0)       # Thứ Hai 7-9
        cls.cls_a2 = make_class(cls.sub_a, 'F1-A2', '4', 7.0, 9.0)     # Thứ Sáu
        cls.cls_b = make_class(cls.sub_b, 'F1-B', '3', 7.0, 9.0)       # Thứ Năm
        cls.cls_c = make_class(cls.sub_c, 'F1-C', '1', 7.0, 9.0)       # Thứ Ba
        cls.cls_d = make_class(cls.sub_d, 'F1-D', '0', 8.0, 10.0)      # Thứ Hai 8-10: trùng A
        cls.cls_e = make_class(cls.sub_e, 'F1-E', '2', 7.0, 9.0)       # Thứ Tư
        cls.cls_old_a = make_class(cls.sub_a, 'F1-OLD-A', '0', 7.0, 9.0, term=cls.old_term)

        Offering = env['univ.sms.course.offering']

        def make_offering(klass, seats=30, term=None):
            return Offering.create({
                'subject_id': klass.subject_id.id, 'term_id': (term or cls.term).id,
                'class_id': klass.id, 'max_seats': seats})

        cls.off_a = make_offering(cls.cls_a)
        cls.off_a2 = make_offering(cls.cls_a2)
        cls.off_b = make_offering(cls.cls_b)
        cls.off_c = make_offering(cls.cls_c)
        cls.off_d = make_offering(cls.cls_d)
        cls.off_e = make_offering(cls.cls_e, seats=1)
        cls.off_old = make_offering(cls.cls_old_a, term=cls.old_term)

        cls.period = env['univ.sms.registration.period'].create({
            'name': 'Đợt F1', 'term_id': cls.term.id, 'reg_type': 'regular',
            'date_start': now - timedelta(days=1), 'date_end': now + timedelta(days=7),
            'max_credit': 12, 'min_credit': 0})
        cls.period.action_open()

        Student = env['univ.sms.student']
        cls.s1, cls.s2, cls.s3, cls.s4 = Student.create([
            {'name': 'SV F1 %s' % i, 'program_id': cls.program.id} for i in range(1, 5)])
        (cls.s1 | cls.s2 | cls.s3 | cls.s4).action_confirm()
        cls.Registration = env['univ.sms.registration']
        cls.Waitlist = env['univ.sms.registration.waitlist']
        cls.Enrollment = env['univ.sms.enrollment']

    @classmethod
    def _pass_subject(cls, student, klass, score=7.0):
        exam = cls.env['univ.sms.exam'].create({
            'name': 'Thi %s' % klass.code, 'class_id': klass.id, 'max_score': 10.0})
        return cls.env['univ.sms.exam.result'].create({
            'exam_id': exam.id, 'student_id': student.id, 'score': score})

    def _register(self, student, offering, period=None):
        return self.Registration.register_student(student, offering, period or self.period)

    def _enrollment(self, student, subject):
        return self.Enrollment.search([
            ('student_id', '=', student.id), ('subject_id', '=', subject.id),
            ('term_id', '=', self.term.id)])

    def _occupying(self, offering, student=None):
        domain = [('offering_id', '=', offering.id), ('state', 'in', ('registered', 'confirmed'))]
        if student:
            domain.append(('student_id', '=', student.id))
        return self.Registration.search(domain)


class RegistrationCase(RegistrationDataMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_registration_data()
