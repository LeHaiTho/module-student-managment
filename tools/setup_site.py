# -*- coding: utf-8 -*-
"""Cấu hình hệ thống cho bản demo/production. Chạy lặp lại an toàn.

Chạy: docker compose run --rm -T odoo odoo shell -c /etc/odoo/odoo.conf -d <db> --no-http < tools/setup_site.py

- Kích hoạt tiếng Việt, nạp bản dịch, đặt làm ngôn ngữ cho mọi người dùng (kể cả public)
- Định dạng ngày dd/mm/yyyy, múi giờ Asia/Ho_Chi_Minh
- Tên trường và logo công ty (thay "Your logo" / "My Company")
- Tắt đăng ký tài khoản Odoo mặc định (/web/signup) và đặt lại mật khẩu qua email
  (không có SMTP); sinh viên đăng ký qua /student/register
- Trang chủ backend của cán bộ: danh sách sinh viên thay vì Discuss
"""
import base64
import os

LANG = 'vi_VN'
TZ = 'Asia/Ho_Chi_Minh'
SCHOOL_NAME = 'Trường Đại học Demo - University SMS'

Lang = env['res.lang'].with_context(active_test=False)
lang = Lang.search([('code', '=', LANG)], limit=1)
if not lang.active:
    env['res.lang']._activate_lang(LANG)
    lang = Lang.search([('code', '=', LANG)], limit=1)
lang.write({'date_format': '%d/%m/%Y', 'time_format': '%H:%M:%S',
            'thousands_sep': '.', 'decimal_point': ','})
installed = env['ir.module.module'].search([('state', '=', 'installed')])
installed._update_translations([LANG])
print('[setup] language', LANG, 'active, translations loaded for', len(installed), 'modules')

users = env['res.users'].with_context(active_test=False).search([])
users.write({'lang': LANG, 'tz': TZ})
env.ref('base.public_user').partner_id.write({'lang': LANG, 'tz': TZ})
env['ir.default'].set('res.partner', 'lang', LANG)
env['ir.default'].set('res.partner', 'tz', TZ)
print('[setup] lang/tz set for', len(users), 'users')

company = env.ref('base.main_company')
vals = {'name': SCHOOL_NAME}
icon = '/mnt/extra-addons/univ_sms_base/static/description/school_logo.png'
if os.path.exists(icon):
    with open(icon, 'rb') as f:
        vals['logo'] = base64.b64encode(f.read())
vn = env.ref('base.vn', raise_if_not_found=False)
if vn:
    vals['country_id'] = vn.id
company.write(vals)
company.partner_id.write({'lang': LANG})
print('[setup] company:', company.name)

# Khách chưa đăng nhập (trang login, đăng ký SV) nhận ngôn ngữ mặc định: chỉ giữ tiếng Việt
en = Lang.search([('code', '=', 'en_US'), ('active', '=', True)], limit=1)
if en and not env['res.users'].with_context(active_test=False).search_count([('lang', '=', 'en_US')]):
    try:
        with env.cr.savepoint():
            en.active = False
        print('[setup] en_US deactivated')
    except Exception as exc:
        print('[setup] could not deactivate en_US:', exc)

ICP = env['ir.config_parameter'].sudo()
ICP.set_param('auth_signup.invitation_scope', 'b2b')   # tắt /web/signup công khai
ICP.set_param('auth_signup.reset_password', 'False')   # không có SMTP
print('[setup] public signup and email password reset disabled')

home = env.ref('univ_sms_student.action_univ_sms_student', raise_if_not_found=False)
if home:
    staff = users.filtered(lambda u: not u.share and u.id != env.ref('base.user_root').id)
    staff.write({'action_id': home.id})
    print('[setup] home action set for', len(staff), 'internal users')

env.cr.commit()
print('[setup] done')
