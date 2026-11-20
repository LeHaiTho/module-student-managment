from odoo.tests import new_test_user

GROUP = 'base.group_user,univ_sms_base.group_univ_'


class ReportDataMixin:
    """Hai lớp, hai giảng viên, một cố vấn, SV có dữ liệu và SV không có dữ liệu."""

    @classmethod
    def _setup_report_data(cls):
        env = cls.env
        faculty = env['univ.sms.faculty'].create({'name': 'Khoa BC', 'code': 'KBC'})
        dept = env['univ.sms.department'].create({'name': 'BM BC', 'code': 'BMBC', 'faculty_id': faculty.id})
        cls.program = env['univ.sms.program'].create({'name': 'Ngành BC', 'code': 'NBC', 'department_id': dept.id})
        cls.year = env['univ.sms.academic.year'].create({
            'name': 'BC 2039', 'date_start': '2039-09-01', 'date_end': '2040-08-31'})
        cls.term = env['univ.sms.term'].create({
            'name': 'HK BC', 'academic_year_id': cls.year.id,
            'date_start': '2039-09-01', 'date_end': '2040-01-15'})
        Subject = env['univ.sms.subject']
        cls.subject_a = Subject.create({'name': 'Môn BC A', 'code': 'BC_A', 'credit': 3})
        cls.subject_b = Subject.create({'name': 'Môn BC B', 'code': 'BC_B', 'credit': 2})

        cls.lecturer_a = new_test_user(env, login='bc_lect_a', groups=GROUP + 'lecturer', name='GV BC A')
        cls.lecturer_b = new_test_user(env, login='bc_lect_b', groups=GROUP + 'lecturer', name='GV BC B')
        cls.advisor = new_test_user(env, login='bc_advisor', groups=GROUP + 'advisor', name='CVHT BC')
        cls.advisor_other = new_test_user(env, login='bc_advisor2', groups=GROUP + 'advisor', name='CVHT BC 2')
        cls.finance = new_test_user(env, login='bc_finance', groups=GROUP + 'finance_office', name='TC BC')
        cls.affairs = new_test_user(env, login='bc_affairs', groups=GROUP + 'student_affairs_office', name='CTSV BC')
        cls.dean = new_test_user(env, login='bc_dean', groups=GROUP + 'dean', name='TK BC')
        cls.officer = new_test_user(env, login='bc_officer', groups=GROUP + 'academic_officer', name='PĐT BC')
        cls.sms_admin = new_test_user(env, login='bc_admin', groups=GROUP + 'admin', name='Admin BC')

        Class = env['univ.sms.class']
        cls.class_a = Class.create({'name': 'Lớp BC A', 'code': 'LBC_A', 'subject_id': cls.subject_a.id,
                                    'term_id': cls.term.id, 'lecturer_id': cls.lecturer_a.partner_id.id})
        cls.class_b = Class.create({'name': 'Lớp BC B', 'code': 'LBC_B', 'subject_id': cls.subject_b.id,
                                    'term_id': cls.term.id, 'lecturer_id': cls.lecturer_b.partner_id.id})
        cls.home_class = env['univ.sms.home.class'].create({
            'name': 'SH BC', 'code': 'SHBC', 'program_id': cls.program.id,
            'academic_year_id': cls.year.id, 'advisor_id': cls.advisor.partner_id.id})

        Student = env['univ.sms.student']
        # SV1: thuộc lớp sinh hoạt do cố vấn phụ trách, học lớp A
        cls.st1 = Student.create({'name': 'SV BC 1', 'program_id': cls.program.id,
                                  'home_class_id': cls.home_class.id})
        # SV2: cố vấn trực tiếp là advisor, học lớp B
        cls.st2 = Student.create({'name': 'SV BC 2', 'program_id': cls.program.id,
                                  'advisor_id': cls.advisor.partner_id.id})
        # SV3: không thuộc cố vấn nào, học lớp B
        cls.st3 = Student.create({'name': 'SV BC 3', 'program_id': cls.program.id})
        # SV rỗng: không có dữ liệu học tập
        cls.st_empty = Student.create({'name': 'SV BC rỗng', 'program_id': cls.program.id})
        for st in (cls.st1, cls.st2, cls.st3, cls.st_empty):
            st.action_confirm()

        Enr = env['univ.sms.enrollment']
        cls.enr1 = Enr.create({'student_id': cls.st1.id, 'subject_id': cls.subject_a.id,
                               'term_id': cls.term.id, 'class_id': cls.class_a.id})
        cls.enr2 = Enr.create({'student_id': cls.st2.id, 'subject_id': cls.subject_b.id,
                               'term_id': cls.term.id, 'class_id': cls.class_b.id})
        cls.enr3 = Enr.create({'student_id': cls.st3.id, 'subject_id': cls.subject_b.id,
                               'term_id': cls.term.id, 'class_id': cls.class_b.id})

        Exam = env['univ.sms.exam']
        cls.exam_a = Exam.create({'name': 'CK BC A', 'class_id': cls.class_a.id, 'exam_type': 'final',
                                  'max_score': 10})
        cls.exam_b = Exam.create({'name': 'CK BC B', 'class_id': cls.class_b.id, 'exam_type': 'final',
                                  'max_score': 10})
        Result = env['univ.sms.exam.result']
        cls.res1 = Result.create({'exam_id': cls.exam_a.id, 'student_id': cls.st1.id, 'score': 8})
        cls.res2 = Result.create({'exam_id': cls.exam_b.id, 'student_id': cls.st2.id, 'score': 6})
        cls.res3 = Result.create({'exam_id': cls.exam_b.id, 'student_id': cls.st3.id, 'score': 4})
        Transcript = env['univ.sms.transcript']
        cls.tr1 = Transcript.create({'student_id': cls.st1.id, 'term_id': cls.term.id,
                                     'line_ids': [(0, 0, {'subject_id': cls.subject_a.id, 'final_score': 8})]})
        cls.tr3 = Transcript.create({'student_id': cls.st3.id, 'term_id': cls.term.id,
                                     'line_ids': [(0, 0, {'subject_id': cls.subject_b.id, 'final_score': 4})]})
