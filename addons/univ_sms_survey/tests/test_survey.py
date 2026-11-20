from datetime import timedelta

from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_survey')
class TestSurvey(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        faculty = env['univ.sms.faculty'].create({'name': 'Khoa KS', 'code': 'KKS'})
        dept = env['univ.sms.department'].create({'name': 'BM KS', 'code': 'BMKS', 'faculty_id': faculty.id})
        program = env['univ.sms.program'].create({'name': 'Ngành KS', 'code': 'NKS', 'department_id': dept.id})
        cls.student = env['univ.sms.student'].create({'name': 'SV KS', 'program_id': program.id})
        cls.stype = env['univ.sms.survey.type'].create({'name': 'Loại KS', 'code': 'KS_T'})
        today = fields.Date.today()
        cls.open_survey = env['univ.sms.survey.instance'].create({
            'name': 'Đợt mở', 'survey_type_id': cls.stype.id,
            'date_start': today - timedelta(days=1), 'date_end': today + timedelta(days=5),
            'state': 'open'})
        cls.expired_survey = env['univ.sms.survey.instance'].create({
            'name': 'Đợt hết hạn', 'survey_type_id': cls.stype.id,
            'date_start': today - timedelta(days=10), 'date_end': today - timedelta(days=1),
            'state': 'open'})
        cls.officer = new_test_user(
            env, login='ks_officer',
            groups='base.group_user,univ_sms_base.group_univ_student_affairs_office')

    def test_instance_dates(self):
        today = fields.Date.today()
        with self.assertRaises(ValidationError):
            self.env['univ.sms.survey.instance'].create({
                'name': 'Sai ngày', 'survey_type_id': self.stype.id,
                'date_start': today, 'date_end': today - timedelta(days=1)})
        # Một ngày (start == end) hợp lệ
        self.env['univ.sms.survey.instance'].create({
            'name': 'Một ngày', 'survey_type_id': self.stype.id,
            'date_start': today, 'date_end': today})

    def test_instance_workflow_guards(self):
        with self.assertRaises(UserError):
            self.open_survey.action_open()
        self.open_survey.action_close()
        with self.assertRaises(UserError):
            self.open_survey.action_close()

    def test_unique_response(self):
        Response = self.env['univ.sms.survey.response']
        Response.create({'student_id': self.student.id, 'survey_instance_id': self.open_survey.id,
                         'answer_data': 'A'})
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError), self.cr.savepoint():
            Response.create({'student_id': self.student.id, 'survey_instance_id': self.open_survey.id,
                             'answer_data': 'B'})

    def test_submit_requires_open_window(self):
        resp = self.env['univ.sms.survey.response'].create({
            'student_id': self.student.id, 'survey_instance_id': self.expired_survey.id,
            'answer_data': 'Muộn'})
        with self.assertRaises(UserError):
            resp.action_submit()
        self.assertEqual(resp.state, 'draft')

    def test_submit_empty_answer_refused(self):
        resp = self.env['univ.sms.survey.response'].create({
            'student_id': self.student.id, 'survey_instance_id': self.open_survey.id,
            'answer_data': '   '})
        with self.assertRaises(UserError):
            resp.action_submit()

    def test_submitted_response_is_locked(self):
        resp = self.env['univ.sms.survey.response'].create({
            'student_id': self.student.id, 'survey_instance_id': self.open_survey.id,
            'answer_data': 'Ý kiến'})
        resp.action_submit()
        self.assertEqual(resp.state, 'submitted')
        with self.assertRaises(UserError):
            resp.action_submit()
        with self.assertRaises(UserError):
            resp.with_user(self.officer).write({'answer_data': 'Sửa lại'})
        self.assertEqual(resp.answer_data, 'Ý kiến')
