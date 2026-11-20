from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_feedback')
class TestFeedback(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        faculty = env['univ.sms.faculty'].create({'name': 'Khoa GY', 'code': 'KGY'})
        dept = env['univ.sms.department'].create({'name': 'BM GY', 'code': 'BMGY', 'faculty_id': faculty.id})
        program = env['univ.sms.program'].create({'name': 'Ngành GY', 'code': 'NGY', 'department_id': dept.id})
        cls.student = env['univ.sms.student'].create({'name': 'SV GY', 'program_id': program.id})
        cls.student2 = env['univ.sms.student'].create({'name': 'SV GY 2', 'program_id': program.id})

    def _fb(self, subject='Wifi yếu', student=None):
        return self.env['univ.sms.feedback'].create({
            'student_id': (student or self.student).id, 'category': 'facility',
            'subject': subject, 'description': 'Nội dung'})

    def test_duplicate_within_one_minute(self):
        fb = self._fb()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self._fb()
        self._fb('Tiêu đề khác')
        self._fb(student=self.student2)
        # Sau 1 phút thì được gửi lại cùng tiêu đề
        self.env.cr.execute(
            "UPDATE univ_sms_feedback SET create_date = create_date - interval '2 minutes' "
            "WHERE student_id = %s", (fb.student_id.id,))
        self.env.invalidate_all()
        self._fb()

    def test_workflow_guards(self):
        fb = self._fb()
        fb.action_in_progress()
        with self.assertRaises(UserError):
            fb.action_in_progress()
        fb.action_resolved()
        with self.assertRaises(UserError):
            fb.action_resolved()
        fb.action_close()
        with self.assertRaises(UserError):
            fb.action_close()
        with self.assertRaises(UserError):
            fb.action_in_progress()
