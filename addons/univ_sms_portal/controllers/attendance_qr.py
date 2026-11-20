# Owned by Agent F2 (QR check-in). See docs/SCHEMA_LOCK_F1_F3.md section 3.
from odoo import fields, http
from odoo.http import request


class UnivSmsAttendanceQr(http.Controller):

    @http.route('/attendance/qr/<string:token>', type='http', auth='user',
                website=True, methods=['GET'], sitemap=False)
    def attendance_qr_checkin(self, token, **kw):
        """Sinh viên quét QR: ghi nhận ngay (idempotent, quét lại trả 'already').

        Toàn bộ kiểm tra (phiên, thời gian, sinh viên, đăng ký lớp, phiếu nháp)
        nằm trong univ.sms.attendance.session._checkin, chỉ dùng sudo để ghi
        sau khi các kiểm tra đã đạt.
        """
        res = request.env['univ.sms.attendance.session']._checkin(request.env.user, token)
        line = res['line']
        checkin_time_str = False
        if line and line.checkin_time:
            local_dt = fields.Datetime.context_timestamp(request.env.user, line.checkin_time)
            checkin_time_str = local_dt.strftime('%H:%M:%S %d/%m/%Y')
        show_class = res['result'] in ('ok_present', 'ok_late', 'already')
        return request.render('univ_sms_portal.portal_attendance_qr_result', {
            'result': res['result'],
            'message': res['message'],
            'success': res['result'] in ('ok_present', 'ok_late', 'already'),
            'class_name': res['session'].class_id.name if show_class else False,
            'sheet_date': res['session'].sheet_id.attendance_date if show_class else False,
            'line_state': line.state if line else False,
            'checkin_time_str': checkin_time_str,
            'is_student': bool(res['student']),
        })
