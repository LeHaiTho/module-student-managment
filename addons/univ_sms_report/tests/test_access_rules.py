"""Record rule nội bộ: enrollment, kỳ thi, kết quả thi, bảng điểm theo từng nhóm quyền."""
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

from .common import ReportDataMixin


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_report')
class TestInternalRecordRules(ReportDataMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_report_data()
        cls.all_enr = cls.enr1 | cls.enr2 | cls.enr3
        cls.all_res = cls.res1 | cls.res2 | cls.res3

    def _visible(self, user, records):
        return records.with_user(user).search([('id', 'in', records.ids)])

    # ─── Enrollment ─────────────────────────────────────────────────────────
    def test_enrollment_lecturer_own_class(self):
        self.assertEqual(self._visible(self.lecturer_a, self.all_enr), self.enr1)
        self.assertEqual(self._visible(self.lecturer_b, self.all_enr), self.enr2 | self.enr3)
        with self.assertRaises(AccessError):
            self.enr2.with_user(self.lecturer_a).read(['state'])

    def test_enrollment_advisor_advised_students(self):
        # SV1 qua lớp sinh hoạt, SV2 qua cố vấn trực tiếp; SV3 không
        self.assertEqual(self._visible(self.advisor, self.all_enr), self.enr1 | self.enr2)
        self.assertFalse(self._visible(self.advisor_other, self.all_enr))
        with self.assertRaises(AccessError):
            self.enr3.with_user(self.advisor).read(['state'])

    def test_enrollment_offices_and_dean_read_all(self):
        for user in (self.finance, self.affairs, self.dean, self.officer, self.sms_admin):
            self.assertEqual(self._visible(user, self.all_enr), self.all_enr, user.login)

    def test_enrollment_finance_cannot_write(self):
        with self.assertRaises(AccessError):
            self.enr1.with_user(self.finance).write({'state': 'cancelled'})

    def test_fee_credits_visible_to_finance(self):
        """Học phí tính đủ tín chỉ khi Phòng Tài chính tạo khoản phí (không dùng sudo)."""
        fee = self.env['univ.sms.fee'].with_user(self.finance).create({
            'student_id': self.st1.id, 'term_id': self.term.id})
        self.assertEqual(fee.total_credits, 3)

    # ─── Kỳ thi / kết quả thi ───────────────────────────────────────────────
    def test_exam_result_lecturer_own_class_only(self):
        self.assertEqual(self._visible(self.lecturer_a, self.all_res), self.res1)
        self.res1.with_user(self.lecturer_a).write({'score': 9})
        self.assertEqual(self.res1.score, 9)
        with self.assertRaises(AccessError):
            self.res2.with_user(self.lecturer_a).write({'score': 10})
        with self.assertRaises(AccessError):
            self.env['univ.sms.exam.result'].with_user(self.lecturer_a).create({
                'exam_id': self.exam_b.id, 'student_id': self.st1.id, 'score': 5})
        exams = self.exam_a | self.exam_b
        self.assertEqual(self._visible(self.lecturer_a, exams), self.exam_a)
        with self.assertRaises(AccessError):
            self.exam_b.with_user(self.lecturer_a).write({'name': 'Đổi tên'})

    def test_exam_result_advisor_and_dean(self):
        self.assertEqual(self._visible(self.advisor, self.all_res), self.res1 | self.res2)
        with self.assertRaises(AccessError):
            self.res1.with_user(self.advisor).write({'score': 1})
        self.assertEqual(self._visible(self.dean, self.all_res), self.all_res)
        with self.assertRaises(AccessError):
            self.res3.with_user(self.dean).write({'score': 1})

    def test_exam_result_officer_admin_full(self):
        for user in (self.officer, self.sms_admin):
            self.assertEqual(self._visible(user, self.all_res), self.all_res, user.login)
            self.res3.with_user(user).write({'score': 5})

    def test_transcripts(self):
        trs = self.tr1 | self.tr3
        self.assertEqual(self._visible(self.lecturer_a, trs), self.tr1)
        self.assertEqual(self._visible(self.lecturer_b, trs), self.tr3)
        self.assertEqual(self._visible(self.advisor, trs), self.tr1)
        lines = trs.mapped('line_ids')
        self.assertEqual(self._visible(self.advisor, lines), self.tr1.line_ids)
        for user in (self.dean, self.affairs, self.officer, self.sms_admin):
            self.assertEqual(self._visible(user, trs), trs, user.login)
            self.assertEqual(self._visible(user, lines), lines, user.login)
