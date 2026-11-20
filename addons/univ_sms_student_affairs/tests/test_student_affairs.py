from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_student_affairs')
class TestStudentAffairs(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        faculty = env['univ.sms.faculty'].create({'name': 'Khoa CTSV', 'code': 'KCTSV'})
        dept = env['univ.sms.department'].create({'name': 'BM CTSV', 'code': 'BMCTSV', 'faculty_id': faculty.id})
        program = env['univ.sms.program'].create({'name': 'Ngành CTSV', 'code': 'NCTSV', 'department_id': dept.id})
        cls.student = env['univ.sms.student'].create({'name': 'SV CTSV', 'program_id': program.id})

    def test_military_workflow(self):
        mil = self.env['univ.sms.military.service'].create({
            'student_id': self.student.id, 'registration_status': 'deferred'})
        with self.assertRaises(UserError):
            mil.action_approve()
        with self.assertRaises(UserError):
            mil.action_reject()
        with self.assertRaises(UserError):
            mil.action_draft()
        mil.action_submit()
        with self.assertRaises(UserError):
            mil.action_submit()
        mil.action_approve()
        with self.assertRaises(UserError):
            mil.action_reject()
        mil.action_draft()
        self.assertEqual(mil.state, 'draft')

    def test_health_insurance_dates_and_workflow(self):
        HI = self.env['univ.sms.health.insurance']
        with self.assertRaises(ValidationError), self.cr.savepoint():
            HI.create({'student_id': self.student.id, 'insurance_code': 'X1',
                       'date_start': '2030-01-01', 'date_end': '2030-01-01'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            HI.create({'student_id': self.student.id, 'insurance_code': 'X2',
                       'date_start': '2030-06-01', 'date_end': '2030-01-01'})
        hi = HI.create({'student_id': self.student.id, 'insurance_code': 'X3',
                        'date_start': '2030-01-01', 'date_end': '2030-12-31'})
        with self.assertRaises(UserError):
            hi.action_draft()
        hi.action_confirm()
        with self.assertRaises(UserError):
            hi.action_confirm()

    def test_residence_workflow(self):
        res = self.env['univ.sms.residence.info'].create({
            'student_id': self.student.id, 'residence_type': 'rent', 'address': 'Số 1'})
        with self.assertRaises(UserError):
            res.action_draft()
        res.action_confirm()
        with self.assertRaises(UserError):
            res.action_confirm()
        res.action_draft()
        self.assertEqual(res.state, 'draft')
