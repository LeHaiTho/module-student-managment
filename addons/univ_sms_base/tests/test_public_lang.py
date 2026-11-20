from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_base')
class TestPublicLang(HttpCase):

    def test_login_page_vietnamese_for_english_browser(self):
        self.env['res.lang']._activate_lang('vi_VN')
        self.env['ir.module.module'].search([('name', '=', 'web')])._update_translations(['vi_VN'])
        res = self.url_open('/web/login', headers={'Accept-Language': 'en-US,en;q=0.9'})
        self.assertEqual(res.status_code, 200)
        self.assertIn('Đăng nhập', res.text)
