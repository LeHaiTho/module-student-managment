from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.univ_sms_attendance.models.attendance_session import (
    UnivSmsAttendanceSession, hash_token)

from .common import AttendanceCase


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_attendance')
class TestAttendanceQr(AttendanceCase):

    def setUp(self):
        super().setUp()
        self.sheet = self._make_sheet()
        self.Session = self.env['univ.sms.attendance.session']
        self.Line = self.env['univ.sms.attendance.line']

    def _lines(self, student, sheet=None):
        return self.Line.search([('sheet_id', '=', (sheet or self.sheet).id),
                                 ('student_id', '=', student.id)])

    # ─── Mở phiên từ phiếu ────────────────────────────────────────────────
    def test_start_session_from_sheet(self):
        self.env['ir.config_parameter'].sudo().set_param('web.base.url', 'http://sms.test')
        self.sheet.with_user(self.lecturer_user).action_start_qr_session()
        session = self.sheet.active_session_id
        self.assertTrue(session)
        self.assertEqual(session.state, 'active')
        self.assertEqual(session.late_after_minutes, 5)
        self.assertLessEqual(session.expire_time, session.start_time + timedelta(minutes=10))
        # nạp sẵn sinh viên khi mở phiên
        self.assertEqual(set(self.sheet.line_ids.mapped('student_id').ids),
                         {self.student_a.id, self.student_b.id})
        # Chưa quét thì mặc định vắng, quét QR hợp lệ mới thành có mặt
        self.assertEqual(set(self.sheet.line_ids.mapped('state')), {'absent'})
        url = session.qr_url
        res = self.Session._checkin(self.user_a, url.rsplit('/', 1)[1])
        self.assertEqual(res['result'], 'ok_present')
        self.assertEqual(res['line'].state, 'present')
        self.assertTrue(url.startswith('http://sms.test/attendance/qr/'))
        self.assertIn('/report/barcode/?barcode_type=QR&value=http%3A%2F%2Fsms.test%2Fattendance%2Fqr%2F',
                      self.sheet.qr_image_src)
        self.assertIn('width=300&height=300', self.sheet.qr_image_src)
        # chỉ lưu mã băm, không lưu token thô
        token = url.rsplit('/', 1)[1]
        self.assertGreaterEqual(len(token), 40)
        self.assertEqual(session.token_hash, hash_token(token))
        self.assertNotEqual(session.token_hash, token)
        # mở lại: phiên cũ đóng, chỉ một phiên active
        self.sheet.action_start_qr_session()
        self.assertEqual(session.state, 'closed')
        self.assertEqual(self.Session.search_count([('sheet_id', '=', self.sheet.id), ('state', '=', 'active')]), 1)
        # Đóng phiên: xóa qr_url → token thô không còn trong DB
        self.sheet.action_close_qr_session()
        self.assertFalse(self.sheet.active_session_id)
        self.env.flush_all()
        self.env.cr.execute("SELECT count(*) FROM univ_sms_attendance_session WHERE "
                            "coalesce(qr_url, '') LIKE %s OR token_hash = %s", ('%' + token + '%', token))
        self.assertEqual(self.env.cr.fetchone()[0], 0)
        result = self.Session._checkin(self.user_a, token)
        self.assertEqual(result['result'], 'expired' if fields.Datetime.now() > session.expire_time else 'closed')

    def test_start_session_empty_class(self):
        empty_class = self.env['univ.sms.class'].create({
            'name': 'Lớp rỗng', 'code': 'F2_EMPTY', 'subject_id': self.subject.id,
            'term_id': self.term.id})
        sheet = self._make_sheet(empty_class)
        sheet.action_load_students()  # không lỗi, không tạo dòng
        self.assertFalse(sheet.line_ids)
        with self.assertRaises(UserError):
            sheet.action_start_qr_session()

    def test_lecturer_cannot_open_session_on_other_class(self):
        sheet = self._make_sheet(self.other_class)
        with self.assertRaises(AccessError):
            self.Session.with_user(self.lecturer_user)._create_for_sheet(sheet)
        # giảng viên lớp kia thì được
        session, _token = self.Session.with_user(self.other_lecturer_user)._create_for_sheet(sheet)
        self.assertEqual(session.state, 'active')

    def test_portal_cannot_read_session(self):
        session, _token = self._make_session(self.sheet)
        with self.assertRaises(AccessError):
            session.with_user(self.user_a).read(['state'])

    # ─── Ràng buộc ────────────────────────────────────────────────────────
    def test_expire_over_ten_minutes_rejected(self):
        with self.assertRaises(ValidationError):
            self._make_session(self.sheet, duration_min=11)
        with self.assertRaises(ValidationError):
            self._make_session(self.sheet, duration_min=0)

    def test_only_one_active_session_per_sheet(self):
        self._make_session(self.sheet)
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception), self.env.cr.savepoint():
            self._make_session(self.sheet)
            self.env.flush_all()

    # ─── Check-in ─────────────────────────────────────────────────────────
    def test_at06_valid_token_enrolled_student(self):
        session, token = self._make_session(self.sheet)
        result = self.Session._checkin(self.user_a, token)
        self.assertEqual(result['result'], 'ok_present')
        line = self._lines(self.student_a)
        self.assertEqual(len(line), 1)
        self.assertEqual(line.state, 'present')
        self.assertEqual(line.checkin_source, 'qr')
        self.assertTrue(line.checkin_time)
        self.assertEqual(line.session_id, session)
        self.assertEqual(session.checkin_count, 1)

    def test_checkin_updates_preloaded_manual_line(self):
        self.sheet.action_load_students()
        self._lines(self.student_a).state = 'absent'
        _session, token = self._make_session(self.sheet)
        self.assertEqual(self.Session._checkin(self.user_a, token)['result'], 'ok_present')
        line = self._lines(self.student_a)
        self.assertEqual(len(line), 1)
        self.assertEqual((line.state, line.checkin_source), ('present', 'qr'))

    def test_at07_out_of_class_account_rejected(self):
        _session, token = self._make_session(self.sheet)
        count_before = self.Line.search_count([])
        result = self.Session._checkin(self.user_out, token)
        self.assertEqual(result['result'], 'not_enrolled')
        self.assertEqual(self.Line.search_count([]), count_before)
        self.assertFalse(self._lines(self.student_out))

    def test_not_student_and_cancelled_enrollment(self):
        _session, token = self._make_session(self.sheet)
        self.assertEqual(self.Session._checkin(self.user_portal_nostudent, token)['result'], 'not_student')
        self.assertEqual(self.Session._checkin(self.lecturer_user, token)['result'], 'not_student')
        self.enr_b.state = 'cancelled'
        self.assertEqual(self.Session._checkin(self.user_b, token)['result'], 'not_enrolled')
        self.assertFalse(self.sheet.line_ids)

    def test_at08_expired_token_rejected(self):
        _session, token = self._make_session(self.sheet, start_offset_min=15, duration_min=10)
        result = self.Session._checkin(self.user_a, token)
        self.assertEqual(result['result'], 'expired')
        self.assertFalse(self._lines(self.student_a))
        # cron đóng phiên hết hạn
        self.assertEqual(self.Session._cron_close_expired(), 1)
        self.assertEqual(_session.state, 'closed')
        self.assertFalse(_session.qr_url)
        self.assertEqual(self.Session._checkin(self.user_a, token)['result'], 'expired')

    def test_closed_and_invalid(self):
        session, token = self._make_session(self.sheet)
        self.assertEqual(self.Session._checkin(self.user_a, 'khong-ton-tai')['result'], 'invalid')
        self.assertEqual(self.Session._checkin(self.user_a, '')['result'], 'invalid')
        self.assertEqual(self.Session._checkin(self.user_a, 'x' * 500)['result'], 'invalid')
        session.action_close()
        self.assertEqual(self.Session._checkin(self.user_a, token)['result'], 'closed')
        self.assertFalse(self.sheet.line_ids)

    def test_confirmed_sheet_rejects_checkin(self):
        self.sheet.action_load_students()
        _session, token = self._make_session(self.sheet)
        # phiên vẫn active ở DB nhưng phiếu đã chốt (ghi thẳng state để mô phỏng)
        self.sheet.write({'state': 'confirmed'})
        self.assertEqual(self.Session._checkin(self.user_a, token)['result'], 'closed')
        self.assertEqual(self._lines(self.student_a).checkin_source, 'manual')

    def test_confirm_closes_active_session(self):
        self.sheet.action_start_qr_session()
        session = self.sheet.active_session_id
        self.sheet.action_confirm()
        self.assertEqual(session.state, 'closed')
        self.assertFalse(session.qr_url)

    def test_at09_rescan_no_duplicate(self):
        _session, token = self._make_session(self.sheet)
        self.assertEqual(self.Session._checkin(self.user_a, token)['result'], 'ok_present')
        first_time = self._lines(self.student_a).checkin_time
        result = self.Session._checkin(self.user_a, token)
        self.assertEqual(result['result'], 'already')
        line = self._lines(self.student_a)
        self.assertEqual(len(line), 1)
        self.assertEqual(line.checkin_time, first_time)

    def test_concurrent_insert_returns_already(self):
        """Hai lần quét đồng thời: lần sau gặp unique(sheet_id, student_id) → 'already'."""
        _session, token = self._make_session(self.sheet)
        self.assertEqual(self.Session._checkin(self.user_a, token)['result'], 'ok_present')
        empty = self.Line.browse()
        with patch.object(UnivSmsAttendanceSession, '_find_line', lambda *a, **k: empty):
            result = self.Session._checkin(self.user_a, token)
        self.assertEqual(result['result'], 'already')
        self.assertEqual(len(self._lines(self.student_a)), 1)

    def test_late_classification(self):
        # bắt đầu 7 phút trước, trễ sau 5 phút, hết hạn start + 10
        _session, token = self._make_session(self.sheet, start_offset_min=7, late_after=5)
        result = self.Session._checkin(self.user_a, token)
        self.assertEqual(result['result'], 'ok_late')
        self.assertEqual(self._lines(self.student_a).state, 'late')
        # late_after lớn hơn thời gian đã trôi → có mặt
        sheet2 = self._make_sheet(date=fields.Date.today() - timedelta(days=1))
        _s2, token2 = self._make_session(sheet2, start_offset_min=7, late_after=8)
        self.assertEqual(self.Session._checkin(self.user_a, token2)['result'], 'ok_present')
