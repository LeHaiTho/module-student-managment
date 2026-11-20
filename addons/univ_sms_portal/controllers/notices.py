# Owned by Agent F4 (personal notices on portal).
from odoo import http
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.http import request

NOTICES_PER_PAGE = 20


class UnivSmsPortalNotices(http.Controller):

    def _notice_student(self):
        """Sinh viên gắn với user đang đăng nhập (recordset rỗng nếu không phải sinh viên)."""
        return request.env['univ.sms.student.notice']._portal_student(request.env.user)

    def _own_notices_domain(self, student):
        return [('student_id', '=', student.id)]

    @http.route(['/my/academic/notices', '/my/academic/notices/page/<int:page>'],
                type='http', auth='user', website=True, methods=['GET'])
    def portal_notices(self, page=1, **kw):
        student = self._notice_student()
        values = {
            'student': student,
            'page_name': 'academic_notices',
            'notices': request.env['univ.sms.student.notice'],
            'unread_count': 0,
            'pager': False,
            'marked': kw.get('marked'),
        }
        if student:
            Notice = request.env['univ.sms.student.notice'].sudo()
            domain = self._own_notices_domain(student)
            total = Notice.search_count(domain)
            pager = portal_pager(
                url='/my/academic/notices', total=total, page=page, step=NOTICES_PER_PAGE)
            values.update({
                'notices': Notice.search(domain, limit=NOTICES_PER_PAGE, offset=pager['offset']),
                'unread_count': Notice.search_count(domain + [('is_read', '=', False)]),
                'pager': pager,
            })
        return request.render('univ_sms_portal.portal_notices', values)

    @http.route(['/my/academic/notices/<int:notice_id>/read'],
                type='http', auth='user', website=True, methods=['POST'])
    def portal_notice_read(self, notice_id, page=None, **kw):
        student = self._notice_student()
        status = 'denied'
        if student:
            # Kiểm tra quyền sở hữu TRƯỚC khi dùng sudo.
            notice = request.env['univ.sms.student.notice'].sudo().search(
                self._own_notices_domain(student) + [('id', '=', notice_id)], limit=1)
            if notice:
                notice.action_mark_read()
                status = 'ok'
        return request.redirect(self._back_url(page, status))

    @http.route(['/my/academic/notices/read-all'],
                type='http', auth='user', website=True, methods=['POST'])
    def portal_notice_read_all(self, **kw):
        student = self._notice_student()
        status = 'denied'
        if student:
            request.env['univ.sms.student.notice'].sudo().search(
                self._own_notices_domain(student) + [('is_read', '=', False)]).action_mark_read()
            status = 'ok'
        return request.redirect(self._back_url(None, status))

    @staticmethod
    def _back_url(page, status):
        try:
            page = int(page or 1)
        except (TypeError, ValueError):
            page = 1
        base = '/my/academic/notices' if page <= 1 else '/my/academic/notices/page/%s' % page
        return '%s?marked=%s' % (base, status)
