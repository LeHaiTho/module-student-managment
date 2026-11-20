from odoo.tests import HttpCase, tagged

from .common import PORTAL_PASSWORD, AttendanceFixtureMixin


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_attendance')
class TestAttendanceQrHttp(AttendanceFixtureMixin, HttpCase):
    """Smoke test route /attendance/qr/<token> (nằm trong univ_sms_portal)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_attendance_data()

    def setUp(self):
        super().setUp()
        portal = self.env['ir.module.module'].search([('name', '=', 'univ_sms_portal')])
        if portal.state != 'installed':
            self.skipTest('univ_sms_portal chưa cài')
        self.sheet = self._make_sheet()

    def _line(self, student):
        return self.env['univ.sms.attendance.line'].search([
            ('sheet_id', '=', self.sheet.id), ('student_id', '=', student.id)])

    def test_route_checkin_enrolled_then_rescan(self):
        _session, token = self._make_session(self.sheet)
        self.authenticate('f2_sv_a', PORTAL_PASSWORD)
        resp = self.url_open('/attendance/qr/%s' % token)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('data-result="ok_present"', resp.text)
        self.assertIn('Điểm danh thành công', resp.text)
        line = self._line(self.student_a)
        self.assertEqual(len(line), 1)
        self.assertEqual(line.checkin_source, 'qr')
        self.assertTrue(line.checkin_time)

        resp = self.url_open('/attendance/qr/%s' % token)
        self.assertIn('data-result="already"', resp.text)
        self.assertEqual(len(self._line(self.student_a)), 1)

        # trang lịch sử điểm danh hiển thị giờ check-in và điều kiện dự thi
        resp = self.url_open('/my/academic/attendance')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Giờ check-in', resp.text)
        self.assertIn('Điều kiện dự thi', resp.text)

    def test_route_out_of_class_and_anonymous(self):
        _session, token = self._make_session(self.sheet)
        # chưa đăng nhập: chuyển sang trang login, không ghi gì
        resp = self.url_open('/attendance/qr/%s' % token, allow_redirects=False)
        self.assertIn(resp.status_code, (302, 303))
        self.assertIn('/web/login', resp.headers.get('Location', ''))

        self.authenticate('f2_sv_out', PORTAL_PASSWORD)
        resp = self.url_open('/attendance/qr/%s' % token)
        self.assertIn('data-result="not_enrolled"', resp.text)
        resp = self.url_open('/attendance/qr/khong-hop-le')
        self.assertIn('data-result="invalid"', resp.text)
        self.assertFalse(self.sheet.line_ids)
