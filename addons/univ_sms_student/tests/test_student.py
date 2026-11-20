from psycopg2 import IntegrityError

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_student')
class TestStudent(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        faculty = cls.env['univ.sms.faculty'].create({'name': 'Khoa ST', 'code': 'KST'})
        dept = cls.env['univ.sms.department'].create({
            'name': 'BM ST', 'code': 'BMST', 'faculty_id': faculty.id})
        cls.program = cls.env['univ.sms.program'].create({
            'name': 'CNTT ST', 'code': 'CNST', 'department_id': dept.id, 'total_credits': 120})
        cls.Student = cls.env['univ.sms.student']

    def _student(self, name='SV Test', **kw):
        vals = {'name': name, 'program_id': self.program.id}
        vals.update(kw)
        return self.Student.create(vals)

    def test_student_code_generated_unique(self):
        students = self.Student.create([
            {'name': 'SV %s' % i, 'program_id': self.program.id} for i in range(5)])
        codes = students.mapped('student_code')
        self.assertEqual(len(set(codes)), 5)
        for code in codes:
            self.assertNotEqual(code, 'New')
            self.assertIn('CNST', code)
        self.assertTrue(students[0].school_email.endswith('@student.edu.vn'))

    def test_student_code_cannot_be_changed(self):
        student = self._student()
        with self.assertRaises(UserError):
            student.write({'student_code': 'HACKED'})

    def test_duplicate_code_and_id_number_rejected(self):
        a = self._student(id_number='079000000001')
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError), self.cr.savepoint():
            self._student(name='Khác', id_number='079000000001')
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError), self.cr.savepoint():
            self._student(name='Khác 2', student_code=a.student_code)

    def test_one_partner_per_student(self):
        before = self.env['res.partner'].search_count([])
        student = self._student(email='sv@example.test')
        self.assertEqual(self.env['res.partner'].search_count([]), before + 1)
        self.assertEqual(student.partner_id.email, 'sv@example.test')
        # Tạo sinh viên với partner có sẵn không sinh thêm partner
        partner = self.env['res.partner'].create({'name': 'Có sẵn'})
        before = self.env['res.partner'].search_count([])
        self._student(partner_id=partner.id)
        self.assertEqual(self.env['res.partner'].search_count([]), before)

    def test_state_workflow(self):
        student = self._student()
        self.assertEqual(student.state, 'draft')
        with self.assertRaises(UserError):
            student.action_on_leave()
        with self.assertRaises(UserError):
            student.action_graduate()
        student.action_confirm()
        self.assertEqual(student.state, 'studying')
        student.action_on_leave()
        self.assertEqual(student.state, 'on_leave')
        student.action_confirm()
        self.assertEqual(student.state, 'studying')
        student.action_drop()
        self.assertEqual(student.state, 'dropped')
        with self.assertRaises(UserError):
            student.action_confirm()
        with self.assertRaises(UserError):
            student.action_dismiss()

    def test_only_draft_student_without_history_can_be_deleted(self):
        student = self._student()
        student.action_confirm()
        with self.assertRaises(UserError):
            student.unlink()
        draft = self._student(name='Nháp')
        draft.unlink()
        self.assertFalse(draft.exists())
