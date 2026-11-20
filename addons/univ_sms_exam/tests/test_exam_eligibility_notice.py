"""F4: thông báo cá nhân khi sinh viên chuyển sang không đủ điều kiện dự thi."""
from datetime import date

from odoo.tests import tagged

from odoo.addons.univ_sms_attendance.tests.common import AttendanceCase


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_exam')
class TestExamIneligibleNotice(AttendanceCase):

    def setUp(self):
        super().setUp()
        a, b = self.student_a, self.student_b
        # A vắng 2/3 (66.7%) → không đủ điều kiện; B đủ điều kiện.
        self._confirmed_sheet({a: 'absent', b: 'present'}, date(2040, 9, 10))
        self._confirmed_sheet({a: 'absent', b: 'present'}, date(2040, 9, 17))
        self._confirmed_sheet({a: 'present', b: 'present'}, date(2040, 9, 24))
        self.Notice = self.env['univ.sms.student.notice']

    def _notices(self, student):
        return self.Notice.search([('student_id', '=', student.id),
                                   ('event_type', '=', 'exam_ineligible')])

    def test_ineligible_creates_one_notice_no_spam(self):
        self.course_class.action_compute_exam_eligibility()
        notice = self._notices(self.student_a)
        self.assertEqual(len(notice), 1)
        self.assertEqual((notice.res_model, notice.res_id), ('univ.sms.enrollment', self.enr_a.id))
        self.assertIn(self.subject.name, notice.title)
        self.assertIn('Vắng 2/3 buổi', notice.body)
        self.assertFalse(self._notices(self.student_b))
        # Tính lại khi không đổi trạng thái: không thêm, kể cả sau khi đã đọc
        notice.action_mark_read()
        self.course_class.action_compute_exam_eligibility()
        self.course_class.action_compute_exam_eligibility()
        self.assertEqual(len(self._notices(self.student_a)), 1)

    def test_back_to_eligible_then_ineligible_notifies_again(self):
        self.course_class.action_compute_exam_eligibility()
        self._notices(self.student_a).action_mark_read()
        Param = self.env['ir.config_parameter'].sudo()
        Param.set_param('univ_sms.max_absence_rate', '80')
        self.course_class.action_compute_exam_eligibility()
        self.assertTrue(self.enr_a.exam_eligible)
        self.assertEqual(len(self._notices(self.student_a)), 1)
        Param.set_param('univ_sms.max_absence_rate', '20')
        self.course_class.action_compute_exam_eligibility()
        self.assertFalse(self.enr_a.exam_eligible)
        self.assertEqual(len(self._notices(self.student_a)), 2)

    def test_lecturer_trigger_creates_notice(self):
        # Giảng viên không có quyền tạo thông báo: _notify dùng sudo bên trong.
        self.course_class.with_user(self.lecturer_user).action_compute_exam_eligibility()
        self.assertEqual(len(self._notices(self.student_a)), 1)
