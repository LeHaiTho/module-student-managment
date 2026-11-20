from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_fee')
class TestFeeEnrollmentSync(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        today = fields.Date.today()
        faculty = env['univ.sms.faculty'].create({'name': 'Khoa Fee', 'code': 'KFEET'})
        dept = env['univ.sms.department'].create({
            'name': 'BM Fee', 'code': 'BMFEET', 'faculty_id': faculty.id})
        program = env['univ.sms.program'].create({
            'name': 'Ngành Fee', 'code': 'NFEET', 'department_id': dept.id})
        year = env['univ.sms.academic.year'].create({
            'name': 'FEE-YEAR', 'date_start': today - timedelta(days=100),
            'date_end': today + timedelta(days=200)})
        cls.term = env['univ.sms.term'].create({
            'name': 'HK Fee', 'academic_year_id': year.id,
            'date_start': today - timedelta(days=10), 'date_end': today + timedelta(days=100)})
        Subject = env['univ.sms.subject']
        cls.sub1 = Subject.create({'name': 'Môn phí 1', 'code': 'FEE1', 'credit': 3})
        cls.sub2 = Subject.create({'name': 'Môn phí 2', 'code': 'FEE2', 'credit': 2})
        cls.sub3 = Subject.create({'name': 'Môn phí 3', 'code': 'FEE3', 'credit': 4})
        cls.student = env['univ.sms.student'].create({'name': 'SV Fee', 'program_id': program.id})
        cls.student.action_confirm()
        cls.Enrollment = env['univ.sms.enrollment']
        cls.fee = env['univ.sms.fee'].create({
            'student_id': cls.student.id, 'term_id': cls.term.id, 'fee_per_credit': 100000})

    def _enroll(self, subject, **vals):
        return self.Enrollment.create(dict({
            'student_id': self.student.id, 'subject_id': subject.id, 'term_id': self.term.id},
            **vals))

    def test_credits_follow_enrollment_changes(self):
        self.assertEqual(self.fee.total_credits, 0)
        e1 = self._enroll(self.sub1)
        e2 = self._enroll(self.sub2)
        self.assertEqual(self.fee.total_credits, 5)
        self.assertEqual(self.fee.total_amount, 500000)
        e2.action_cancel()
        self.assertEqual(self.fee.total_credits, 3)
        e2.action_reset()
        self.assertEqual(self.fee.total_credits, 5)
        e2.unlink()
        self.assertEqual(self.fee.total_credits, 3)
        e1.action_complete()  # môn đã hoàn thành vẫn tính học phí
        self.assertEqual(self.fee.total_credits, 3)
        self.assertEqual(self.fee.remaining_amount, 300000)

    def test_fee_created_after_enrollment_gets_credits(self):
        other_term = self.env['univ.sms.term'].create({
            'name': 'HK Fee 2', 'academic_year_id': self.term.academic_year_id.id,
            'date_start': self.term.date_start, 'date_end': self.term.date_end})
        self.Enrollment.create({'student_id': self.student.id, 'subject_id': self.sub3.id,
                                'term_id': other_term.id})
        fee2 = self.env['univ.sms.fee'].create({
            'student_id': self.student.id, 'term_id': other_term.id, 'fee_per_credit': 100000})
        self.assertEqual(fee2.total_credits, 4)
        self.assertEqual(self.fee.total_credits, 0)  # học kỳ khác không ảnh hưởng

    def test_create_invoice_no_duplicate(self):
        self._enroll(self.sub1)
        action1 = self.fee.action_create_invoice()
        action2 = self.fee.action_create_invoice()
        self.assertEqual(action1['res_id'], action2['res_id'])
        self.assertEqual(len(self.fee.invoice_ids), 1)
        self.assertEqual(self.fee.invoice_ids.amount_total, 300000)
        # Hóa đơn cũ bị hủy thì được lập hóa đơn mới.
        self.fee.invoice_ids.action_cancel()
        action3 = self.fee.action_create_invoice()
        self.assertNotEqual(action3['res_id'], action1['res_id'])
        self.assertEqual(len(self.fee.invoice_ids.filtered(lambda i: i.state != 'cancel')), 1)

    def test_invoiced_fee_amount_not_changed(self):
        self._enroll(self.sub1)
        self.fee.action_create_invoice()
        self.assertEqual(self.fee.state, 'invoiced')
        self._enroll(self.sub2)
        self.assertEqual(self.fee.total_credits, 3)
        self.assertEqual(self.fee.total_amount, 300000)
