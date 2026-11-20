from datetime import date

from odoo.tests import tagged

from odoo.addons.univ_sms_attendance.tests.common import AttendanceCase


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_exam')
class TestExamEligibility(AttendanceCase):

    def setUp(self):
        super().setUp()
        a, b = self.student_a, self.student_b
        # A vắng 3/5 = 60% (> 20%), B vắng 1/5 = 20% (không vượt ngưỡng)
        self._confirmed_sheet({a: 'absent', b: 'absent'}, date(2040, 9, 10))
        self._confirmed_sheet({a: 'absent', b: 'late'}, date(2040, 9, 17))
        self._confirmed_sheet({a: 'absent', b: 'excused'}, date(2040, 9, 24))
        self._confirmed_sheet({a: 'present'}, date(2040, 10, 1))
        self._confirmed_sheet({a: 'late'}, date(2040, 10, 8))
        # Phiếu nháp B vắng: không tính
        draft = self._make_sheet(date=date(2040, 10, 15))
        draft.action_load_students()
        draft.line_ids.write({'state': 'absent'})

    def test_default_eligible(self):
        self.assertTrue(self.enr_a.exam_eligible)
        self.assertFalse(self.enr_a.eligibility_checked_at)

    def test_at10_over_threshold_ineligible_with_reason(self):
        self.course_class.action_compute_exam_eligibility()
        self.assertFalse(self.enr_a.exam_eligible)
        self.assertEqual(self.enr_a.exam_ineligible_reason, 'Vắng 3/5 buổi (60.0%) vượt ngưỡng 20%')
        self.assertTrue(self.enr_a.eligibility_checked_at)
        # đúng bằng ngưỡng (20%) vẫn đủ điều kiện; phiếu nháp không tính
        self.assertTrue(self.enr_b.exam_eligible)
        self.assertFalse(self.enr_b.exam_ineligible_reason)
        self.assertTrue(self.enr_b.eligibility_checked_at)
        self.assertEqual(self.course_class.exam_ineligible_count, 1)

    def test_threshold_from_config_and_recover(self):
        self.course_class.action_compute_exam_eligibility()
        self.assertFalse(self.enr_a.exam_eligible)
        self.env['ir.config_parameter'].sudo().set_param('univ_sms.max_absence_rate', '60')
        self.course_class.action_compute_exam_eligibility()
        self.assertTrue(self.enr_a.exam_eligible)
        self.assertFalse(self.enr_a.exam_ineligible_reason)
        self.env['ir.config_parameter'].sudo().set_param('univ_sms.max_absence_rate', '10')
        self.course_class.action_compute_exam_eligibility()
        self.assertFalse(self.enr_b.exam_eligible)
        self.assertEqual(self.enr_b.exam_ineligible_reason, 'Vắng 1/5 buổi (20.0%) vượt ngưỡng 10%')

    def test_lecturer_can_compute(self):
        action = self.course_class.with_user(self.lecturer_user).action_compute_exam_eligibility()
        self.assertEqual(action['tag'], 'display_notification')
        self.assertFalse(self.enr_a.exam_eligible)

    def test_exam_load_students_only_eligible_idempotent(self):
        exam = self.env['univ.sms.exam'].create({
            'name': 'Cuối kỳ F2', 'class_id': self.course_class.id, 'exam_type': 'final'})
        exam.action_load_students()
        self.assertEqual(exam.result_ids.mapped('student_id'), self.student_b)
        self.assertFalse(self.enr_a.exam_eligible)  # đã tự tính lại
        exam.action_load_students()
        self.assertEqual(len(exam.result_ids), 1)
        self.assertEqual(exam.ineligible_enrollment_ids, self.enr_a)
        # nút trên form kỳ thi
        action = exam.action_compute_exam_eligibility()
        self.assertEqual(action['type'], 'ir.actions.client')
