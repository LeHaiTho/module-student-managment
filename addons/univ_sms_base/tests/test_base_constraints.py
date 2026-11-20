from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_base')
class TestBaseConstraints(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.faculty = cls.env['univ.sms.faculty'].create({'name': 'Khoa Test', 'code': 'KT_T'})
        cls.department = cls.env['univ.sms.department'].create({
            'name': 'Bộ môn Test', 'code': 'BM_T', 'faculty_id': cls.faculty.id})
        cls.program = cls.env['univ.sms.program'].create({
            'name': 'Ngành Test', 'code': 'NG_T', 'department_id': cls.department.id})

    def _assert_duplicate_rejected(self, model, vals):
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError), self.cr.savepoint():
            self.env[model].create(vals)

    def test_unique_codes(self):
        self._assert_duplicate_rejected('univ.sms.faculty', {'name': 'Khoa 2', 'code': 'KT_T'})
        self._assert_duplicate_rejected('univ.sms.department', {
            'name': 'BM 2', 'code': 'BM_T', 'faculty_id': self.faculty.id})
        self._assert_duplicate_rejected('univ.sms.program', {
            'name': 'Ngành 2', 'code': 'NG_T', 'department_id': self.department.id})
        self.env['univ.sms.subject'].create({'name': 'Môn A', 'code': 'MH_T', 'credit': 3})
        self._assert_duplicate_rejected('univ.sms.subject', {'name': 'Môn B', 'code': 'MH_T', 'credit': 2})

    def test_relations(self):
        self.assertIn(self.department, self.faculty.department_ids)
        self.assertIn(self.program, self.department.program_ids)

    def test_academic_year_and_term_dates(self):
        with self.assertRaises(ValidationError):
            self.env['univ.sms.academic.year'].create({
                'name': 'X', 'date_start': '2026-09-01', 'date_end': '2026-08-01'})
        year = self.env['univ.sms.academic.year'].create({
            'name': '2030-2031', 'date_start': '2030-09-01', 'date_end': '2031-08-31'})
        with self.assertRaises(ValidationError):
            self.env['univ.sms.term'].create({
                'name': 'HK1', 'academic_year_id': year.id,
                'date_start': '2030-12-01', 'date_end': '2030-12-01'})
