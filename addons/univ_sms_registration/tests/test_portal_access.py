import json
import re

from odoo.exceptions import AccessError
from odoo.tests import HttpCase, tagged

from .common import RegistrationDataMixin


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_registration')
class TestRegistrationPortalAccess(RegistrationDataMixin, HttpCase):
    """Sinh viên A không được xem / hủy đăng ký của sinh viên B."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_registration_data()
        portal_group = cls.env.ref('base.group_portal')
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        cls.user_a = Users.create({
            'name': 'Portal F1 A', 'login': 'portal_f1_a', 'password': 'portal_f1_a_pwd',
            'partner_id': cls.s1.partner_id.id, 'groups_id': [(6, 0, [portal_group.id])]})
        cls.user_b = Users.create({
            'name': 'Portal F1 B', 'login': 'portal_f1_b', 'password': 'portal_f1_b_pwd',
            'partner_id': cls.s2.partner_id.id, 'groups_id': [(6, 0, [portal_group.id])]})
        Reg = cls.env['univ.sms.registration']
        cls.reg_a = Reg.browse(Reg.register_student(cls.s1, cls.off_a, cls.period)['registration_id'])
        cls.reg_b = Reg.browse(Reg.register_student(cls.s2, cls.off_c, cls.period)['registration_id'])
        # B chiếm chỗ duy nhất của off_e, A vào danh sách chờ.
        Reg.register_student(cls.s2, cls.off_e, cls.period)
        cls.wait_a = cls.env['univ.sms.registration.waitlist'].browse(
            Reg.register_student(cls.s1, cls.off_e, cls.period)['waitlist_id'])
        cls.wait_s3 = cls.env['univ.sms.registration.waitlist'].browse(
            Reg.register_student(cls.s3, cls.off_e, cls.period)['waitlist_id'])

    # ─── ORM ───────────────────────────────────────────────────────────────
    def test_orm_portal_cannot_read_other_student_records(self):
        Reg = self.env['univ.sms.registration'].with_user(self.user_a)
        visible = Reg.search([])
        self.assertIn(self.reg_a, visible)
        self.assertNotIn(self.reg_b, visible)
        with self.assertRaises(AccessError):
            self.reg_b.with_user(self.user_a).read(['state'])

        Waitlist = self.env['univ.sms.registration.waitlist'].with_user(self.user_a)
        self.assertEqual(Waitlist.search([]), self.wait_a)
        with self.assertRaises(AccessError):
            self.wait_s3.with_user(self.user_a).read(['position'])
        with self.assertRaises(AccessError):
            self.wait_a.with_user(self.user_a).write({'state': 'cancelled'})

    # ─── Controller ────────────────────────────────────────────────────────
    def _require_portal(self):
        if not self.env['ir.module.module'].search_count([
                ('name', '=', 'univ_sms_portal'), ('state', '=', 'installed')]):
            self.skipTest('univ_sms_portal chưa được cài')

    def _csrf_from_page(self):
        response = self.url_open('/my/academic/registration')
        self.assertEqual(response.status_code, 200)
        match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
        self.assertTrue(match, 'Không tìm thấy csrf_token trên trang đăng ký')
        return response, match.group(1)

    def _json_add(self, offering_id):
        response = self.url_open(
            '/my/academic/registration/add',
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 1,
                             'params': {'offering_id': offering_id}}),
            headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200)
        return response.json().get('result')

    def test_portal_page_shows_waitlist_position(self):
        self._require_portal()
        self.authenticate('portal_f1_a', 'portal_f1_a_pwd')
        response, _token = self._csrf_from_page()
        self.assertIn('Bạn đang ở vị trí chờ số', response.text)
        self.assertIn(self.sub_a.name, response.text)

    def test_portal_cannot_cancel_other_student_registration(self):
        self._require_portal()
        self.authenticate('portal_f1_a', 'portal_f1_a_pwd')
        _response, token = self._csrf_from_page()
        self.url_open('/my/academic/registration/cancel/%s' % self.reg_b.id,
                      data={'csrf_token': token})
        self.reg_b.invalidate_recordset()
        self.assertEqual(self.reg_b.state, 'registered')

        # Hủy đăng ký của chính mình thì được.
        self.url_open('/my/academic/registration/cancel/%s' % self.reg_a.id,
                      data={'csrf_token': token})
        self.reg_a.invalidate_recordset()
        self.assertEqual(self.reg_a.state, 'cancelled')

    def test_portal_add_validates_input_and_hides_errors(self):
        self._require_portal()
        self.authenticate('portal_f1_a', 'portal_f1_a_pwd')
        for bad in ('abc', None, -1, True, 999999999):
            result = self._json_add(bad)
            self.assertEqual(result['status'], 'rejected', bad)
            self.assertTrue(result['message'])
        # Lớp ngoài học kỳ của đợt đang mở.
        result = self._json_add(self.off_old.id)
        self.assertEqual(result['status'], 'rejected')
        self.assertIn('đợt đăng ký', result['message'])
        # Bị từ chối (trùng lịch với off_a đã đăng ký): thông báo tiếng Việt, không lộ traceback.
        result = self._json_add(self.off_d.id)
        self.assertEqual(result['status'], 'rejected')
        self.assertIn('Trùng lịch', result['message'])
        self.assertNotIn('Traceback', result['message'])
        result = self._json_add(self.off_a2.id)
        self.assertEqual(result['status'], 'rejected')  # trùng môn với off_a
        result = self._json_add(self.off_c.id)
        self.assertEqual(result['status'], 'registered', result['message'])
        result = self._json_add(self.off_c.id)
        self.assertEqual(result['status'], 'already')
        # Đang chờ off_e: trả về vị trí.
        result = self._json_add(self.off_e.id)
        self.assertEqual(result['status'], 'already')
        self.assertEqual(result['position'], 1)
