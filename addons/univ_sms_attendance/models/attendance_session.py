import hashlib
import logging
import secrets
from datetime import timedelta
from urllib.parse import quote

from psycopg2 import IntegrityError

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import mute_logger

_logger = logging.getLogger(__name__)

MAX_SESSION_MINUTES = 10

# Thông điệp hiển thị cho từng kết quả check-in (tiếng Việt).
CHECKIN_MESSAGES = {
    'ok_present': 'Điểm danh thành công: bạn được ghi nhận Có mặt.',
    'ok_late': 'Điểm danh thành công nhưng bạn được ghi nhận Đi trễ.',
    'already': 'Bạn đã điểm danh bằng QR trong buổi học này rồi. Không cần quét lại.',
    'expired': 'Mã QR đã hết hạn. Hãy liên hệ giảng viên để được điểm danh.',
    'closed': 'Phiên điểm danh đã đóng hoặc chưa mở.',
    'not_enrolled': 'Bạn không có tên trong danh sách lớp này nên không thể điểm danh.',
    'not_student': 'Tài khoản này không phải tài khoản sinh viên nên không thể điểm danh.',
    'invalid': 'Mã QR không hợp lệ.',
}


def hash_token(token):
    return hashlib.sha256((token or '').encode('utf-8')).hexdigest()


class UnivSmsAttendanceSession(models.Model):
    _name = 'univ.sms.attendance.session'
    _description = 'Phiên điểm danh QR'
    _order = 'start_time desc, id desc'

    name = fields.Char(string='Tên phiên', related='sheet_id.name')
    sheet_id = fields.Many2one(
        'univ.sms.attendance.sheet',
        string='Phiếu điểm danh',
        required=True,
        ondelete='cascade',
        index=True,
    )
    class_id = fields.Many2one(
        'univ.sms.class',
        string='Lớp',
        related='sheet_id.class_id',
        store=True,
        index=True,
    )
    token_hash = fields.Char(string='Mã băm token', index=True, copy=False, readonly=True)
    start_time = fields.Datetime(string='Bắt đầu', default=fields.Datetime.now, required=True)
    expire_time = fields.Datetime(string='Hết hạn', required=True)
    late_after_minutes = fields.Integer(string='Tính trễ sau (phút)', default=5)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('active', 'Đang mở'),
        ('closed', 'Đã đóng'),
    ], string='Trạng thái', default='draft', required=True, index=True)
    qr_url = fields.Char(
        string='URL điểm danh',
        copy=False,
        readonly=True,
        groups='univ_sms_base.group_univ_lecturer',
    )
    qr_image_src = fields.Char(
        string='Mã QR',
        compute='_compute_qr_image_src',
        groups='univ_sms_base.group_univ_lecturer',
    )
    checkin_count = fields.Integer(string='Số lượt quét', compute='_compute_checkin_count')
    line_ids = fields.One2many('univ.sms.attendance.line', 'session_id', string='Dòng đã quét')

    def init(self):
        # Mỗi phiếu chỉ có tối đa một phiên đang mở.
        self.env.cr.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS univ_sms_attendance_session_one_active
            ON univ_sms_attendance_session (sheet_id) WHERE state = 'active'
        """)

    # ─── Compute / constraint ─────────────────────────────────────────────
    def _get_qr_image_src(self):
        self.ensure_one()
        url = self.sudo().qr_url
        if not url or self.state != 'active':
            return False
        return '/report/barcode/?barcode_type=QR&value=%s&width=300&height=300' % quote(url, safe='')

    @api.depends('qr_url', 'state')
    def _compute_qr_image_src(self):
        for record in self:
            record.qr_image_src = record._get_qr_image_src()

    def _compute_checkin_count(self):
        Line = self.env['univ.sms.attendance.line'].sudo()
        counts = {}
        if self.ids:
            for group in Line.read_group([('session_id', 'in', self.ids)], ['session_id'], ['session_id']):
                counts[group['session_id'][0]] = group['session_id_count']
        for record in self:
            record.checkin_count = counts.get(record.id, 0)

    @api.constrains('start_time', 'expire_time', 'late_after_minutes')
    def _check_times(self):
        for record in self:
            if record.expire_time <= record.start_time:
                raise ValidationError('Thời điểm hết hạn phải sau thời điểm bắt đầu phiên QR.')
            if record.expire_time > record.start_time + timedelta(minutes=MAX_SESSION_MINUTES):
                raise ValidationError(
                    f'Phiên điểm danh QR chỉ được kéo dài tối đa {MAX_SESSION_MINUTES} phút.'
                )
            if record.late_after_minutes < 0:
                raise ValidationError('Số phút tính trễ không được âm.')

    @api.constrains('state', 'sheet_id')
    def _check_one_active(self):
        for record in self.filtered(lambda s: s.state == 'active'):
            if self.sudo().search_count([
                ('sheet_id', '=', record.sheet_id.id),
                ('state', '=', 'active'),
                ('id', '!=', record.id),
            ]):
                raise ValidationError('Mỗi phiếu điểm danh chỉ được có một phiên QR đang mở.')

    # ─── Mở / đóng phiên ──────────────────────────────────────────────────
    @api.model
    def _get_public_base_url(self):
        """Địa chỉ public để sinh QR.

        Ưu tiên địa chỉ mà giảng viên đang truy cập (Host / X-Forwarded-Host qua
        proxy_mode), để QR luôn đúng khi chạy sau Cloudflare quick tunnel có URL đổi
        mỗi lần khởi động. Không có request (cron, shell) thì dùng web.base.url.
        """
        try:
            from odoo.http import request
            if request and request.httprequest:
                url = request.httprequest.host_url.rstrip('/')
                # cloudflared gửi X-Forwarded-Proto nhưng không gửi X-Forwarded-Host,
                # nên ProxyFix của Odoo không áp dụng: tự đổi sang https khi cần.
                proto = request.httprequest.headers.get('X-Forwarded-Proto', '')
                if proto.split(',')[0].strip() == 'https' and url.startswith('http://'):
                    url = 'https://' + url[len('http://'):]
                return url
        except RuntimeError:
            pass
        return self.env['ir.config_parameter'].sudo().get_param('web.base.url', '').rstrip('/')

    def _create_for_sheet(self, sheet, late_after_minutes=5, duration_minutes=MAX_SESSION_MINUTES):
        """Tạo phiên đang mở cho phiếu. Trả về (session, token thô).

        Chỉ lưu SHA-256 của token. Token thô nằm trong qr_url (chỉ giảng viên đọc
        được) để hiển thị lại mã QR, và bị xóa khi đóng phiên.
        """
        token = secrets.token_urlsafe(32)
        base_url = self._get_public_base_url()
        now = fields.Datetime.now()
        session = self.create({
            'sheet_id': sheet.id,
            'token_hash': hash_token(token),
            'start_time': now,
            'expire_time': now + timedelta(minutes=duration_minutes),
            'late_after_minutes': late_after_minutes,
            'state': 'active',
            'qr_url': f'{base_url}/attendance/qr/{token}',
        })
        return session, token

    def action_close(self):
        self.filtered(lambda s: s.state != 'closed').sudo().write({
            'state': 'closed',
            'qr_url': False,
        })
        # Ghi xuống DB ngay để chỉ mục "một phiên active / phiếu" thấy trạng thái mới
        # trước khi mở phiên kế tiếp trong cùng transaction.
        self.env['univ.sms.attendance.session'].flush_model(['state', 'qr_url'])
        return True

    @api.model
    def _cron_close_expired(self):
        expired = self.sudo().search([
            ('state', '=', 'active'),
            ('expire_time', '<', fields.Datetime.now()),
        ])
        expired.action_close()
        return len(expired)

    # ─── Check-in ─────────────────────────────────────────────────────────
    def _find_line(self, sheet, student):
        return self.env['univ.sms.attendance.line'].sudo().search([
            ('sheet_id', '=', sheet.id),
            ('student_id', '=', student.id),
        ], limit=1)

    @api.model
    def _checkin(self, user, token):
        """Ghi nhận điểm danh QR cho ``user`` với ``token`` thô.

        Trả về dict(result, message, session, line, student). ``result`` thuộc
        CHECKIN_MESSAGES. Chỉ ghi dữ liệu khi mọi kiểm tra đã đạt.
        """
        res = {'session': self.browse(), 'line': self.env['univ.sms.attendance.line'],
               'student': self.env['univ.sms.student']}

        def done(result):
            res.update(result=result, message=CHECKIN_MESSAGES[result])
            return res

        if not token or not isinstance(token, str) or len(token) > 128:
            return done('invalid')
        # Tra cứu theo mã băm: người quét (portal) không có quyền đọc phiên.
        session = self.sudo().search([('token_hash', '=', hash_token(token))], limit=1)
        if not session:
            return done('invalid')
        res['session'] = session
        now = fields.Datetime.now()
        if session.state == 'active' and now > session.expire_time:
            return done('expired')
        if session.state == 'closed':
            return done('expired' if now > session.expire_time else 'closed')
        if session.state != 'active' or now < session.start_time:
            return done('closed')
        sheet = session.sheet_id
        if sheet.state != 'draft':
            return done('closed')

        if not user or user._is_public():
            return done('not_student')
        student = self.env['univ.sms.student'].sudo().search(
            [('partner_id', '=', user.partner_id.id)], limit=1)
        if not student:
            return done('not_student')
        res['student'] = student
        enrolled = self.env['univ.sms.enrollment'].sudo().search_count([
            ('student_id', '=', student.id),
            ('class_id', '=', session.class_id.id),
            ('state', '=', 'registered'),
        ])
        if not enrolled:
            return done('not_enrolled')

        # Mọi kiểm tra đã đạt: ghi dữ liệu bằng sudo, chỉ trên dòng của sinh viên này.
        line = self._find_line(sheet, student)
        if line and line.checkin_source == 'qr' and line.checkin_time:
            res['line'] = line
            return done('already')
        is_late = now > session.start_time + timedelta(minutes=session.late_after_minutes or 0)
        vals = {
            'state': 'late' if is_late else 'present',
            'checkin_time': now,
            'checkin_source': 'qr',
            'session_id': session.id,
        }
        if line:
            line.write(vals)
        else:
            Line = self.env['univ.sms.attendance.line'].sudo()
            try:
                with mute_logger('odoo.sql_db'), self.env.cr.savepoint():
                    line = Line.create(dict(vals, sheet_id=sheet.id, student_id=student.id))
            except IntegrityError:
                # Hai lần quét đồng thời: lần còn lại đã tạo dòng.
                self.env.invalidate_all()
                res['line'] = self._find_line(sheet, student)
                return done('already')
        res['line'] = line
        return done('ok_late' if is_late else 'ok_present')
