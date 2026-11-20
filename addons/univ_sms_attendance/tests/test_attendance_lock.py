from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import AttendanceCase


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_attendance')
class TestAttendanceLock(AttendanceCase):

    def test_load_students_idempotent(self):
        sheet = self._make_sheet()
        sheet.action_load_students()
        sheet.action_load_students()
        self.assertEqual(len(sheet.line_ids), 2)
        # sinh viên đăng ký sau được nạp bổ sung, không trùng
        late_student = self._make_student('SV F2 vào sau')
        self._enroll(late_student, self.course_class)
        sheet.action_load_students()
        self.assertEqual(len(sheet.line_ids), 3)
        self.assertTrue(all(line.checkin_source == 'manual' for line in sheet.line_ids))

    def test_confirmed_sheet_lines_locked(self):
        sheet = self._make_sheet()
        sheet.action_load_students()
        sheet.action_confirm()
        line = sheet.line_ids[0]
        with self.assertRaises(UserError):
            line.write({'state': 'absent'})
        with self.assertRaises(UserError):
            line.unlink()
        with self.assertRaises(UserError):
            self.env['univ.sms.attendance.line'].create({
                'sheet_id': sheet.id, 'student_id': self.student_out.id})
        with self.assertRaises(UserError):
            sheet.write({'line_ids': [(1, line.id, {'state': 'absent'})]})
        with self.assertRaises(UserError):
            sheet.action_load_students()
        # lecturer cannot reset; admin/officer can, then edit
        with self.assertRaises(UserError):
            sheet.with_user(self.lecturer_user).action_reset_draft()
        sheet.action_reset_draft()
        line.write({'state': 'absent'})
        self.assertEqual(line.state, 'absent')

    def test_absence_rate_counts_confirmed_sheets_only(self):
        a, b = self.student_a, self.student_b
        self._confirmed_sheet({a: 'absent', b: 'excused'}, date(2040, 9, 10))
        self._confirmed_sheet({a: 'late', b: 'present'}, date(2040, 9, 17))
        self._confirmed_sheet({a: 'present'}, date(2040, 9, 24))
        self._confirmed_sheet({a: 'present'}, date(2040, 10, 1))
        # phiếu nháp có vắng: không được tính
        draft = self._make_sheet(date=date(2040, 10, 8))
        draft.action_load_students()
        draft.line_ids.write({'state': 'absent'})

        self.enr_a.invalidate_recordset()
        self.assertEqual(self.enr_a.total_sessions, 4)
        self.assertEqual(self.enr_a.absence_count, 1)
        self.assertAlmostEqual(self.enr_a.absence_rate, 25.0)
        self.assertTrue(self.enr_a.has_attendance_warning)  # 25 > 20
        # excused không tính vắng
        self.assertEqual(self.enr_b.absence_count, 0)
        self.assertFalse(self.enr_b.has_attendance_warning)
        # ngưỡng cấu hình
        self.env['ir.config_parameter'].sudo().set_param('univ_sms.max_absence_rate', '30')
        self.enr_a.invalidate_recordset()
        self.assertFalse(self.enr_a.has_attendance_warning)

    def test_default_threshold_param(self):
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_param('univ_sms.max_absence_rate'), '20')
