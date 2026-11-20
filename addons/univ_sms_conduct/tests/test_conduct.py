from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_conduct')
class TestConductScore(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        faculty = env['univ.sms.faculty'].create({'name': 'Khoa RL', 'code': 'KRL'})
        dept = env['univ.sms.department'].create({'name': 'BM RL', 'code': 'BMRL', 'faculty_id': faculty.id})
        program = env['univ.sms.program'].create({'name': 'Ngành RL', 'code': 'NRL', 'department_id': dept.id})
        year = env['univ.sms.academic.year'].create({
            'name': 'RL', 'date_start': '2035-09-01', 'date_end': '2036-08-31'})
        cls.term = env['univ.sms.term'].create({
            'name': 'HK RL', 'academic_year_id': year.id, 'date_start': '2035-09-01', 'date_end': '2036-01-15'})
        cls.term2 = env['univ.sms.term'].create({
            'name': 'HK RL 2', 'academic_year_id': year.id, 'date_start': '2036-02-01', 'date_end': '2036-06-15'})
        cls.student = env['univ.sms.student'].create({'name': 'SV RL', 'program_id': program.id})
        cls.criteria = env['univ.sms.conduct.criteria'].create({
            'name': 'Tiêu chí RL', 'group_name': 'discipline', 'max_score': 20})
        g = 'base.group_user,univ_sms_base.group_univ_'
        cls.advisor = new_test_user(env, login='rl_advisor', groups=g + 'advisor')
        cls.dean = new_test_user(env, login='rl_dean', groups=g + 'dean')
        cls.affairs = new_test_user(env, login='rl_affairs', groups=g + 'student_affairs_office')

    def _score(self, term=None):
        return self.env['univ.sms.conduct.score'].create({
            'student_id': self.student.id, 'period_id': (term or self.term).id,
            'line_ids': [(0, 0, {'criteria_id': self.criteria.id,
                                 'self_score': 15, 'advisor_score': 14, 'final_score': 14})]})

    def test_line_score_range(self):
        score = self._score()
        self.assertEqual(score.final_total, 14)
        line = score.line_ids
        for fname in ('self_score', 'advisor_score', 'final_score'):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                line.write({fname: 21})
            with self.assertRaises(ValidationError), self.cr.savepoint():
                line.write({fname: -1})
        line.write({'self_score': 20, 'advisor_score': 0, 'final_score': 20})

    def test_unique_student_period(self):
        self._score()
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError), self.cr.savepoint():
            self._score()
        self._score(self.term2)

    def test_workflow_guards(self):
        score = self._score()
        with self.assertRaises(UserError):
            score.action_advisor_approve()
        with self.assertRaises(UserError):
            score.action_dean_approve()
        with self.assertRaises(UserError):
            score.action_draft()
        score.action_submit()
        with self.assertRaises(UserError):
            score.action_submit()
        with self.assertRaises(UserError):
            score.action_dean_approve()
        score.action_advisor_approve()
        score.action_dean_approve()
        self.assertEqual(score.state, 'dean_approved')
        with self.assertRaises(UserError):
            score.action_reject()

    def test_reject_and_resubmit(self):
        score = self._score()
        score.action_submit()
        score.action_reject()
        score.action_submit()  # gửi lại trực tiếp từ trạng thái bị trả về
        self.assertEqual(score.state, 'submitted')

    def test_role_enforcement(self):
        score = self._score()
        score.action_submit()
        # Trưởng khoa không phải cố vấn: không được duyệt cấp CVHT
        with self.assertRaises(AccessError):
            score.with_user(self.dean).action_advisor_approve()
        # CTSV không được duyệt
        with self.assertRaises(AccessError):
            score.with_user(self.affairs).action_advisor_approve()
        score.with_user(self.advisor).action_advisor_approve()
        self.assertEqual(score.state, 'advisor_approved')
        # Cố vấn không được duyệt cấp khoa
        with self.assertRaises(AccessError):
            score.with_user(self.advisor).action_dean_approve()
        score.with_user(self.dean).action_dean_approve()
        self.assertEqual(score.state, 'dean_approved')
