"""Portal dịch vụ: kiểm tra input, chống gửi lặp, không lỗi 500, đăng ký hồ sơ public."""
import re
from datetime import timedelta

from odoo import fields
from odoo.tests import HttpCase, new_test_user, tagged

PASSWORD = 'PortalSv#2026-test'
CSRF_RE = re.compile(r'name="csrf_token"\s+value="([^"]+)"')


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_portal')
class TestPortalServices(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        faculty = env['univ.sms.faculty'].create({'name': 'Khoa DV', 'code': 'KDV'})
        cls.department = env['univ.sms.department'].create({
            'name': 'Phòng DV', 'code': 'PDV', 'faculty_id': faculty.id})
        cls.program = env['univ.sms.program'].create({
            'name': 'Ngành DV', 'code': 'NDV', 'department_id': cls.department.id})
        cls.year = env['univ.sms.academic.year'].create({
            'name': 'DV 2026', 'date_start': '2026-09-01', 'date_end': '2027-08-31'})
        portal = env.ref('base.group_portal')
        Users = env['res.users'].with_context(no_reset_password=True)

        def make(login):
            user = Users.create({'name': login, 'login': login, 'password': PASSWORD,
                                 'groups_id': [(6, 0, [portal.id])]})
            student = env['univ.sms.student'].create({
                'partner_id': user.partner_id.id, 'program_id': cls.program.id,
                'personal_email': '%s@example.com' % login})
            return user, student

        cls.user_a, cls.student_a = make('dv_student_a')
        cls.user_b, cls.student_b = make('dv_student_b')
        cls.portal_nostudent = Users.create({
            'name': 'dv_nostudent', 'login': 'dv_nostudent', 'password': PASSWORD,
            'groups_id': [(6, 0, [portal.id])]})
        cls.internal = new_test_user(env, login='dv_internal', password=PASSWORD,
                                     groups='base.group_user,univ_sms_base.group_univ_lecturer')

        Type = env['univ.sms.certificate.type']
        cls.ctype = Type.create({'name': 'Giấy xác nhận DV', 'code': 'DV_GXN'})
        cls.ctype_off = Type.create({'name': 'Ngừng DV', 'code': 'DV_OFF', 'active': False})

        today = fields.Date.today()
        stype = env['univ.sms.survey.type'].create({'name': 'KS DV', 'code': 'DV_KS'})
        Survey = env['univ.sms.survey.instance']
        cls.survey_open = Survey.create({
            'name': 'KS mở', 'survey_type_id': stype.id, 'state': 'open',
            'date_start': today - timedelta(days=1), 'date_end': today + timedelta(days=3)})
        cls.survey_closed = Survey.create({
            'name': 'KS đóng', 'survey_type_id': stype.id, 'state': 'closed',
            'date_start': today - timedelta(days=1), 'date_end': today + timedelta(days=3)})
        cls.survey_expired = Survey.create({
            'name': 'KS hết hạn', 'survey_type_id': stype.id, 'state': 'open',
            'date_start': today - timedelta(days=9), 'date_end': today - timedelta(days=1)})

    # ─── Helpers ───────────────────────────────────────────────────────────
    def _login(self, user):
        self.authenticate(user.login, PASSWORD)

    def _csrf(self, url):
        resp = self.url_open(url)
        self.assertEqual(resp.status_code, 200, url)
        match = CSRF_RE.search(resp.text)
        self.assertTrue(match, 'Trang %s thiếu csrf_token' % url)
        return match.group(1)

    def _post(self, page, action, data):
        # Token CSRF gắn với phiên: trang khảo sát đã trả lời hết không còn form,
        # nên khi cần thì lấy token từ trang góp ý (luôn có form).
        resp = self.url_open(page)
        self.assertEqual(resp.status_code, 200, page)
        match = CSRF_RE.search(resp.text)
        token = match.group(1) if match else self._csrf('/my/academic/feedback')
        payload = dict(data, csrf_token=token)
        resp = self.url_open(action, data=payload, allow_redirects=False)
        self.assertLess(resp.status_code, 500, '%s trả lỗi %s' % (action, resp.status_code))
        return resp

    def _assert_redirect(self, resp, code):
        self.assertIn(resp.status_code, (302, 303))
        self.assertIn('msg=%s' % code, resp.headers.get('Location', ''))

    # ─── Giấy chứng nhận ───────────────────────────────────────────────────
    def test_certificate_input_validation_and_duplicate(self):
        self._login(self.user_a)
        page, action = '/my/academic/certificates', '/my/academic/certificates/create'
        Req = self.env['univ.sms.certificate.request']
        for bad in ('abc', '-1', '0', '99999999999', '1.5', '', str(self.ctype_off.id)):
            resp = self._post(page, action, {'certificate_type_id': bad, 'reason': 'Lý do'})
            self._assert_redirect(resp, 'invalid_type')
        resp = self._post(page, action, {'certificate_type_id': self.ctype.id, 'reason': '   '})
        self._assert_redirect(resp, 'invalid_reason')
        resp = self._post(page, action, {'certificate_type_id': self.ctype.id, 'reason': 'x' * 1001})
        self._assert_redirect(resp, 'invalid_reason')
        self.assertFalse(Req.search_count([('student_id', '=', self.student_a.id)]))

        # student_id giả mạo bị bỏ qua: yêu cầu luôn thuộc SV đang đăng nhập
        resp = self._post(page, action, {'certificate_type_id': self.ctype.id, 'reason': 'Vay vốn',
                                         'student_id': self.student_b.id})
        self._assert_redirect(resp, 'created')
        resp = self._post(page, action, {'certificate_type_id': self.ctype.id, 'reason': 'Lần hai'})
        self._assert_redirect(resp, 'duplicate_cert')
        self.assertEqual(Req.search_count([('student_id', '=', self.student_a.id)]), 1)
        self.assertFalse(Req.search_count([('student_id', '=', self.student_b.id)]))

        resp = self.url_open(page + '?msg=duplicate_cert')
        self.assertIn('Bạn đã có yêu cầu đang xử lý', resp.text)
        # Mã lạ không được phản chiếu lên trang
        resp = self.url_open(page + '?msg=%3Cscript%3Ealert(1)%3C/script%3E')
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('<script>alert(1)</script>', resp.text)

    def test_service_without_student_profile(self):
        self._login(self.portal_nostudent)
        resp = self._post('/my/academic/certificates', '/my/academic/certificates/create',
                          {'certificate_type_id': self.ctype.id, 'reason': 'Lý do'})
        self._assert_redirect(resp, 'no_student')

    # ─── Nghĩa vụ quân sự ───────────────────────────────────────────────────
    def test_military_validation_and_duplicate(self):
        self._login(self.user_a)
        page, action = '/my/academic/student-affairs', '/my/academic/student-affairs/military/create'
        Mil = self.env['univ.sms.military.service']
        for bad in ('hacked', '', 'REGISTERED'):
            self._assert_redirect(self._post(page, action, {'registration_status': bad}), 'invalid_status')
        self.assertFalse(Mil.search_count([('student_id', '=', self.student_a.id)]))
        self._assert_redirect(self._post(page, action, {'registration_status': 'deferred'}), 'created')
        mil = Mil.search([('student_id', '=', self.student_a.id)])
        self.assertEqual(mil.state, 'submitted')
        self._assert_redirect(self._post(page, action, {'registration_status': 'registered'}),
                              'duplicate_military')
        self.assertEqual(Mil.search_count([('student_id', '=', self.student_a.id)]), 1)

    # ─── Khảo sát ───────────────────────────────────────────────────────────
    def test_survey_rules(self):
        self._login(self.user_a)
        page, action = '/my/academic/surveys', '/my/academic/surveys/submit'
        Resp = self.env['univ.sms.survey.response']
        html = self.url_open(page).text
        self.assertIn('KS mở', html)
        self.assertNotIn('KS hết hạn', html)
        self.assertNotIn('KS đóng', html)
        for bad in ('abc', '-5', '999999999', ''):
            self._assert_redirect(self._post(page, action, {'survey_instance_id': bad, 'answer_data': 'A'}),
                                  'invalid_survey')
        for survey in (self.survey_closed, self.survey_expired):
            self._assert_redirect(
                self._post(page, action, {'survey_instance_id': survey.id, 'answer_data': 'A'}),
                'closed_survey')
        self._assert_redirect(
            self._post(page, action, {'survey_instance_id': self.survey_open.id, 'answer_data': '  '}),
            'invalid_answer')
        self.assertFalse(Resp.search_count([('student_id', '=', self.student_a.id)]))

        self._assert_redirect(
            self._post(page, action, {'survey_instance_id': self.survey_open.id, 'answer_data': 'Tốt'}),
            'submitted')
        self._assert_redirect(
            self._post(page, action, {'survey_instance_id': self.survey_open.id, 'answer_data': 'Đổi ý'}),
            'already_answered')
        resp = Resp.search([('student_id', '=', self.student_a.id)])
        self.assertEqual(len(resp), 1)
        self.assertEqual(resp.answer_data, 'Tốt')
        self.assertEqual(resp.state, 'submitted')

    # ─── Góp ý ──────────────────────────────────────────────────────────────
    def test_feedback_validation_and_duplicate(self):
        self._login(self.user_a)
        page, action = '/my/academic/feedback', '/my/academic/feedback/create'
        Fb = self.env['univ.sms.feedback']
        base = {'category': 'facility', 'subject': 'Wifi yếu', 'description': 'Phòng A1'}
        cases = [
            (dict(base, category='hack'), 'invalid_category'),
            (dict(base, subject=''), 'invalid_subject'),
            (dict(base, subject='x' * 201), 'invalid_subject'),
            (dict(base, description=' '), 'invalid_description'),
            (dict(base, department_id='abc'), 'invalid_department'),
            (dict(base, department_id='987654321'), 'invalid_department'),
        ]
        for data, code in cases:
            self._assert_redirect(self._post(page, action, data), code)
        self.assertFalse(Fb.search_count([('student_id', '=', self.student_a.id)]))
        self._assert_redirect(self._post(page, action, dict(base, department_id=self.department.id)),
                              'created')
        self._assert_redirect(self._post(page, action, base), 'duplicate_feedback')
        fbs = Fb.search([('student_id', '=', self.student_a.id)])
        self.assertEqual(len(fbs), 1)
        self.assertEqual(fbs.department_id, self.department)
        # Bộ phận không bắt buộc
        self._assert_redirect(self._post(page, action, dict(base, subject='Khác', department_id='')),
                              'created')

    def test_service_pages_render(self):
        self._login(self.user_a)
        for url in ('/my/academic', '/my/academic/transcript', '/my/academic/fees',
                    '/my/academic/certificates', '/my/academic/student-affairs',
                    '/my/academic/conduct', '/my/academic/surveys', '/my/academic/feedback',
                    '/my/academic/timetable'):
            resp = self.url_open(url)
            self.assertEqual(resp.status_code, 200, url)

    def test_get_on_post_routes_not_500(self):
        self._login(self.user_a)
        for url in ('/my/academic/certificates/create', '/my/academic/feedback/create',
                    '/my/academic/surveys/submit', '/my/academic/student-affairs/military/create'):
            resp = self.url_open(url, allow_redirects=False)
            self.assertLess(resp.status_code, 500, url)


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_portal')
class TestPublicStudentRegister(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        faculty = env['univ.sms.faculty'].create({'name': 'Khoa ĐK', 'code': 'KDK'})
        dept = env['univ.sms.department'].create({'name': 'BM ĐK', 'code': 'BMDK', 'faculty_id': faculty.id})
        cls.program = env['univ.sms.program'].create({'name': 'Ngành ĐK', 'code': 'NDK', 'department_id': dept.id})
        cls.year = env['univ.sms.academic.year'].create({
            'name': 'ĐK 2026', 'date_start': '2026-09-01', 'date_end': '2027-08-31'})
        portal = env.ref('base.group_portal')
        cls.existing_user = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Đã có', 'login': 'dk_taken', 'password': PASSWORD,
            'groups_id': [(6, 0, [portal.id])]})
        env['univ.sms.student'].create({
            'partner_id': cls.existing_user.partner_id.id, 'program_id': cls.program.id,
            'personal_email': 'taken@example.com', 'id_number': '012345678901'})
        cls.internal = new_test_user(env, login='dk_internal', password=PASSWORD,
                                     groups='base.group_user,univ_sms_base.group_univ_lecturer')

    def _valid(self, **over):
        dob = fields.Date.today().replace(year=fields.Date.today().year - 19)
        data = {
            'name': 'Nguyễn Văn Mới', 'login': 'dk_new_student', 'personal_email': 'moi@example.com',
            'password': 'MatKhau#2026', 'confirm_password': 'MatKhau#2026',
            'phone': '0901234567', 'mobile': '', 'date_of_birth': fields.Date.to_string(dob),
            'gender': 'male', 'id_number': '', 'program_id': str(self.program.id),
            'academic_year_id': str(self.year.id), 'training_system': 'regular',
            'home_address': 'Hà Nội', 'current_address': 'Hà Nội',
        }
        data.update(over)
        return data

    def _submit(self, data):
        resp = self.url_open('/student/register')
        self.assertEqual(resp.status_code, 200)
        token = CSRF_RE.search(resp.text).group(1)
        resp = self.url_open('/student/register/submit', data=dict(data, csrf_token=token),
                             allow_redirects=False)
        self.assertLess(resp.status_code, 500)
        return resp

    def test_invalid_inputs_create_nothing(self):
        today = fields.Date.today()
        cases = [
            ({'login': 'dk_taken'}, 'Tên đăng nhập đã tồn tại'),
            ({'login': 'DK_TAKEN'}, 'Tên đăng nhập đã tồn tại'),
            ({'login': 'a b'}, 'Tên đăng nhập chỉ gồm'),
            ({'personal_email': 'taken@example.com'}, 'Email này đã được dùng'),
            ({'personal_email': 'TAKEN@example.com'}, 'Email này đã được dùng'),
            ({'personal_email': 'khong-hop-le'}, 'Email liên hệ không đúng định dạng'),
            ({'password': 'ngan', 'confirm_password': 'ngan'}, 'ít nhất 8 ký tự'),
            ({'confirm_password': 'KhacNhau#1'}, 'Mật khẩu xác nhận không khớp'),
            ({'date_of_birth': fields.Date.to_string(today + timedelta(days=1))}, 'không được ở tương lai'),
            ({'date_of_birth': fields.Date.to_string(today.replace(year=today.year - 10))}, 'đủ 15 tuổi'),
            ({'date_of_birth': '31/31/2000'}, 'Ngày sinh không hợp lệ'),
            ({'id_number': 'abc123456'}, '9 đến 12 chữ số'),
            ({'id_number': '12345'}, '9 đến 12 chữ số'),
            ({'id_number': '012345678901'}, 'CCCD/CMND đã tồn tại'),
            ({'program_id': 'abc'}, 'Ngành học không hợp lệ'),
            ({'program_id': '999999'}, 'Ngành học không hợp lệ'),
            ({'academic_year_id': '-3'}, 'Niên khóa nhập học không hợp lệ'),
            ({'gender': 'robot'}, 'Giới tính không hợp lệ'),
            ({'training_system': 'x'}, 'Hệ đào tạo không hợp lệ'),
            ({'phone': '', 'mobile': ''}, 'ít nhất một số điện thoại'),
            ({'phone': 'abc'}, 'Số điện thoại không hợp lệ'),
        ]
        Users = self.env['res.users'].with_context(active_test=False)
        users_before = Users.search_count([])
        students_before = self.env['univ.sms.student'].search_count([])
        for over, expected in cases:
            resp = self._submit(self._valid(**over))
            self.assertEqual(resp.status_code, 200, over)
            self.assertIn(expected, resp.text, over)
        self.assertEqual(Users.search_count([]), users_before)
        self.assertEqual(self.env['univ.sms.student'].search_count([]), students_before)

    def test_valid_registration(self):
        resp = self._submit(self._valid())
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Đăng ký thành công', resp.text)
        user = self.env['res.users'].search([('login', '=', 'dk_new_student')])
        self.assertTrue(user.has_group('base.group_portal'))
        self.assertFalse(user._is_internal())
        student = self.env['univ.sms.student'].search([('partner_id', '=', user.partner_id.id)])
        self.assertEqual(student.state, 'draft')
        self.assertEqual(student.program_id, self.program)
        # Gửi lại cùng thông tin: bị chặn, không tạo thêm
        resp = self._submit(self._valid())
        self.assertIn('Tên đăng nhập đã tồn tại', resp.text)
        self.assertEqual(self.env['res.users'].search_count([('login', '=', 'dk_new_student')]), 1)

    def test_internal_user_redirected(self):
        self.authenticate('dk_internal', PASSWORD)
        resp = self.url_open('/student/register', allow_redirects=False)
        self.assertIn(resp.status_code, (302, 303))
        students_before = self.env['univ.sms.student'].search_count([])
        resp = self.url_open('/student/register/submit', data={'name': 'x'}, allow_redirects=False)
        self.assertLess(resp.status_code, 500)
        self.assertEqual(self.env['univ.sms.student'].search_count([]), students_before)
