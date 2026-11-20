"""F4: thông báo cá nhân theo sự kiện đăng ký môn / danh sách chờ + trang portal."""
import re
from unittest.mock import patch

from odoo.tests import HttpCase, tagged
from odoo.tools import mute_logger

from .common import RegistrationCase, RegistrationDataMixin


class NoticeHelpers:

    def _notices(self, student, event_type=None):
        domain = [('student_id', '=', student.id)]
        if event_type:
            domain.append(('event_type', '=', event_type))
        return self.env['univ.sms.student.notice'].search(domain)


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_registration')
class TestRegistrationNotices(NoticeHelpers, RegistrationCase):

    def test_registered_notice_once_and_already_no_new(self):
        res = self._register(self.s1, self.off_a)
        self.assertEqual(res['status'], 'registered')
        notice = self._notices(self.s1)
        self.assertEqual(len(notice), 1)
        self.assertEqual(notice.event_type, 'reg_success')
        self.assertEqual((notice.res_model, notice.res_id),
                         ('univ.sms.registration', res['registration_id']))
        self.assertIn(self.sub_a.name, notice.title)
        notice.action_mark_read()
        self.assertEqual(self._register(self.s1, self.off_a)['status'], 'already')
        self.assertEqual(len(self._notices(self.s1)), 1, "'already' không được sinh thông báo")

    def test_rejected_notice_with_reason_dedup(self):
        res = self._register(self.s1, self.off_b)  # thiếu tiên quyết
        self.assertEqual(res['status'], 'rejected')
        notice = self._notices(self.s1)
        self.assertEqual(len(notice), 1)
        self.assertEqual(notice.event_type, 'reg_rejected')
        self.assertIn('tiên quyết', notice.body)
        self.assertEqual((notice.res_model, notice.res_id),
                         ('univ.sms.course.offering', self.off_b.id))
        # Thử lại khi chưa đọc: cập nhật, không thêm thông báo
        self._register(self.s1, self.off_b)
        self.assertEqual(len(self._notices(self.s1)), 1)

    def test_waitlisted_promoted_and_cancel_notices(self):
        reg1 = self.Registration.browse(self._register(self.s1, self.off_e)['registration_id'])
        res2 = self._register(self.s2, self.off_e)
        self.assertEqual(res2['status'], 'waitlisted')
        waiting = self._notices(self.s2, 'waitlisted')
        self.assertEqual(len(waiting), 1)
        self.assertIn('vị trí chờ số 1', waiting.body)
        self.assertEqual((waiting.res_model, waiting.res_id),
                         ('univ.sms.registration.waitlist', res2['waitlist_id']))
        # Đăng ký lại khi đang chờ → 'already', không thêm
        self.assertEqual(self._register(self.s2, self.off_e)['status'], 'already')
        self.assertEqual(len(self._notices(self.s2)), 1)

        # Phòng đào tạo hủy đăng ký của s1 → s1 nhận thông báo hủy, s2 được nhận.
        reg1.action_cancel()
        cancelled = self._notices(self.s1, 'other')
        self.assertEqual(len(cancelled), 1)
        self.assertIn('hủy', cancelled.title.lower())
        promoted = self._notices(self.s2, 'waitlist_promoted')
        self.assertEqual(len(promoted), 1)
        self.assertEqual(promoted.res_id, res2['waitlist_id'])
        self.assertEqual(len(self._notices(self.s2)), 2)

    def test_self_cancel_no_cancel_notice(self):
        portal = self.env.ref('base.group_portal')
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'SV tự hủy', 'login': 'f4_self_cancel', 'partner_id': self.s1.partner_id.id,
            'groups_id': [(6, 0, [portal.id])]})
        reg = self.Registration.browse(self._register(self.s1, self.off_a)['registration_id'])
        reg.with_user(user).sudo().action_cancel()  # như controller portal
        self.assertEqual(reg.state, 'cancelled')
        self.assertFalse(self._notices(self.s1, 'other'))

    def test_waitlist_rejected_notice(self):
        reg1 = self.Registration.browse(self._register(self.s1, self.off_e)['registration_id'])
        w2 = self.Waitlist.browse(self._register(self.s2, self.off_e)['waitlist_id'])
        w3 = self.Waitlist.browse(self._register(self.s3, self.off_e)['waitlist_id'])
        self.s2.action_on_leave()
        reg1.action_cancel()
        self.assertEqual(w2.state, 'rejected')
        rejected = self._notices(self.s2, 'waitlist_rejected')
        self.assertEqual(len(rejected), 1)
        self.assertIn('đang học', rejected.body)
        self.assertEqual(w3.state, 'promoted')
        self.assertEqual(len(self._notices(self.s3, 'waitlist_promoted')), 1)
        self.assertFalse(self._notices(self.s3, 'waitlist_rejected'))

    def test_notice_failure_does_not_break_registration(self):
        Notice = type(self.env['univ.sms.student.notice'])
        with mute_logger('odoo.addons.univ_sms_student.models.student_notice'), \
                patch.object(Notice, 'create', side_effect=RuntimeError('boom')):
            res = self._register(self.s1, self.off_a)
            reg1 = self.Registration.browse(self._register(self.s1, self.off_e)['registration_id'])
            res2 = self._register(self.s2, self.off_e)
            reg1.action_cancel()
        self.assertEqual(res['status'], 'registered')
        self.assertTrue(self._occupying(self.off_a, self.s1))
        self.assertEqual(res2['status'], 'waitlisted')
        self.assertTrue(self._occupying(self.off_e, self.s2), 'Vẫn nhận người chờ dù thông báo lỗi')
        self.assertFalse(self._notices(self.s1) | self._notices(self.s2))


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_registration')
class TestNoticePortal(NoticeHelpers, RegistrationDataMixin, HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_registration_data()
        portal_group = cls.env.ref('base.group_portal')
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        cls.user_a = Users.create({
            'name': 'Portal F4 A', 'login': 'portal_f4_a', 'password': 'portal_f4_a_pwd',
            'partner_id': cls.s1.partner_id.id, 'groups_id': [(6, 0, [portal_group.id])]})
        cls.user_b = Users.create({
            'name': 'Portal F4 B', 'login': 'portal_f4_b', 'password': 'portal_f4_b_pwd',
            'partner_id': cls.s2.partner_id.id, 'groups_id': [(6, 0, [portal_group.id])]})
        Notice = cls.env['univ.sms.student.notice']
        cls.na1 = Notice._notify(cls.s1, 'other', 'Thông báo A1 <script>', 'Nội dung A1')
        cls.na2 = Notice._notify(cls.s1, 'reg_success', 'Thông báo A2', 'Nội dung A2', cls.off_a)
        cls.nb = Notice._notify(cls.s2, 'other', 'Thông báo riêng của B', 'Bí mật B')

    def _require_portal(self):
        if not self.env['ir.module.module'].search_count([
                ('name', '=', 'univ_sms_portal'), ('state', '=', 'installed')]):
            self.skipTest('univ_sms_portal chưa được cài')

    def _page(self, url='/my/academic/notices'):
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        return response

    def _csrf(self, html):
        match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        self.assertTrue(match, 'Không tìm thấy csrf_token')
        return match.group(1)

    def test_notices_page_lists_only_own(self):
        self._require_portal()
        self.authenticate('portal_f4_a', 'portal_f4_a_pwd')
        html = self._page().text
        self.assertIn('Thông báo A2', html)
        self.assertIn('Thông báo A1 &lt;script&gt;', html)
        self.assertNotIn('Thông báo riêng của B', html)
        self.assertIn('2 chưa đọc', html)
        home = self._page('/my/academic').text
        self.assertIn('/my/academic/notices', home)
        self.assertIn('Thông báo (2)', home)

    def test_mark_read_own_only(self):
        self._require_portal()
        self.authenticate('portal_f4_a', 'portal_f4_a_pwd')
        token = self._csrf(self._page().text)
        # Notice của B: không đổi
        response = self.url_open('/my/academic/notices/%s/read' % self.nb.id,
                                 data={'csrf_token': token})
        self.assertEqual(response.status_code, 200)
        self.assertIn('marked=denied', response.url)
        self.nb.invalidate_recordset()
        self.assertFalse(self.nb.is_read)
        # Không có CSRF: bị chặn
        response = self.url_open('/my/academic/notices/%s/read' % self.na1.id, data={})
        self.na1.invalidate_recordset()
        self.assertFalse(self.na1.is_read)
        # Của chính mình: được
        self.url_open('/my/academic/notices/%s/read' % self.na1.id, data={'csrf_token': token})
        self.na1.invalidate_recordset()
        self.assertTrue(self.na1.is_read)
        self.assertFalse(self.na2.is_read)
        # Đọc tất cả: chỉ thông báo của A
        self.url_open('/my/academic/notices/read-all', data={'csrf_token': token})
        (self.na2 | self.nb).invalidate_recordset()
        self.assertTrue(self.na2.is_read)
        self.assertFalse(self.nb.is_read)
        self.assertIn('Thông báo (0)', self._page('/my/academic').text)

    def test_non_student_user_page(self):
        self._require_portal()
        portal_group = self.env.ref('base.group_portal')
        self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Portal no student', 'login': 'portal_f4_x', 'password': 'portal_f4_x_pwd',
            'groups_id': [(6, 0, [portal_group.id])]})
        self.authenticate('portal_f4_x', 'portal_f4_x_pwd')
        html = self._page().text
        self.assertIn('chưa được liên kết', html)
        self.assertNotIn('Thông báo riêng của B', html)
        self.assertNotIn('Thông báo (', self._page('/my/academic').text)
