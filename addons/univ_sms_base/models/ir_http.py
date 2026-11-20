from odoo import models
from odoo.http import request

SITE_LANG = 'vi_VN'


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _pre_dispatch(cls, rule, args):
        """Khách chưa đăng nhập luôn thấy giao diện tiếng Việt (trang đăng nhập,
        đăng ký sinh viên, trang giới thiệu), bất kể ngôn ngữ trình duyệt."""
        super()._pre_dispatch(rule, args)
        env = request.env
        # Route auth='none' (vd. /web/login) chưa có user: coi như khách
        is_guest = not env.uid or not env.user or env.user._is_public()
        if env.context.get('lang') != SITE_LANG and is_guest:
            if env(su=True)['res.lang']._lang_get_id(SITE_LANG):
                request.update_context(lang=SITE_LANG)
