import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

NOTICE_EVENT_TYPES = [
    ('reg_success', 'Đăng ký môn thành công'),
    ('reg_rejected', 'Đăng ký môn bị từ chối'),
    ('waitlisted', 'Vào danh sách chờ'),
    ('waitlist_promoted', 'Được nhận từ danh sách chờ'),
    ('waitlist_rejected', 'Bị loại khỏi danh sách chờ'),
    ('exam_ineligible', 'Không đủ điều kiện dự thi'),
    ('early_warning', 'Cảnh báo học vụ'),
    ('other', 'Khác'),
]

# Trang portal liên quan đến từng loại thông báo.
_PORTAL_URL_BY_EVENT = {
    'reg_success': '/my/academic/registration',
    'reg_rejected': '/my/academic/registration',
    'waitlisted': '/my/academic/registration',
    'waitlist_promoted': '/my/academic/registration',
    'waitlist_rejected': '/my/academic/registration',
    'exam_ineligible': '/my/academic/attendance',
}

# Field người dùng portal được phép ghi (đánh dấu đã đọc).
PORTAL_WRITABLE_FIELDS = frozenset({'is_read', 'read_at'})


class UnivSmsStudentNotice(models.Model):
    _name = 'univ.sms.student.notice'
    _description = 'Thông báo cá nhân sinh viên'
    _order = 'notice_date desc, id desc'
    _rec_name = 'title'

    student_id = fields.Many2one(
        'univ.sms.student', string='Sinh viên', required=True, index=True, ondelete='cascade')
    student_code = fields.Char(related='student_id.student_code', string='MSSV')
    title = fields.Char(string='Tiêu đề', required=True)
    body = fields.Text(string='Nội dung')
    event_type = fields.Selection(
        NOTICE_EVENT_TYPES, string='Loại sự kiện', required=True, default='other', index=True)
    res_model = fields.Char(string='Model liên quan', readonly=True)
    res_id = fields.Integer(string='ID bản ghi liên quan', readonly=True)
    notice_date = fields.Datetime(
        string='Thời điểm', default=fields.Datetime.now, required=True, index=True,
        help='Thời điểm phát sinh (cập nhật khi sự kiện lặp lại trên thông báo chưa đọc).')
    is_read = fields.Boolean(string='Đã đọc', default=False, index=True)
    read_at = fields.Datetime(string='Đọc lúc')

    # ─── Bảo vệ ghi từ portal ─────────────────────────────────────────────
    def write(self, vals):
        if not self.env.su and self.env.user.share and set(vals) - PORTAL_WRITABLE_FIELDS:
            raise AccessError(_('Bạn chỉ có thể đánh dấu đã đọc thông báo của mình.'))
        return super().write(vals)

    def action_mark_read(self):
        """Đánh dấu đã đọc. Dùng quyền của người gọi (ACL + record rule)."""
        unread = self.filtered(lambda n: not n.is_read)
        if unread:
            unread.write({'is_read': True, 'read_at': fields.Datetime.now()})
        return True

    def action_mark_unread(self):
        self.filtered('is_read').write({'is_read': False, 'read_at': False})
        return True

    def _portal_url(self):
        self.ensure_one()
        return _PORTAL_URL_BY_EVENT.get(self.event_type, '/my/academic')

    # ─── Portal helpers ───────────────────────────────────────────────────
    @api.model
    def _portal_student(self, user):
        if not user or user._is_public():
            return self.env['univ.sms.student']
        return self.env['univ.sms.student'].sudo().search(
            [('partner_id', '=', user.partner_id.id)], limit=1)

    @api.model
    def _portal_unread_count(self, user=None):
        """Số thông báo chưa đọc của sinh viên gắn với ``user`` (0 nếu không phải sinh viên)."""
        student = self._portal_student(user or self.env.user)
        if not student:
            return 0
        return self.sudo().search_count([('student_id', '=', student.id), ('is_read', '=', False)])

    # ─── Service tạo thông báo ────────────────────────────────────────────
    @api.model
    def _notify(self, student, event_type, title, body=None, record=None):
        """Tạo (hoặc cập nhật) một thông báo cá nhân cho sinh viên.

        - Chạy bằng sudo, trong savepoint riêng.
        - Không bao giờ ném lỗi: nghiệp vụ gọi hàm này không được hỏng vì thông báo.
        - Chống trùng: đã có thông báo CHƯA ĐỌC cùng (sinh viên, loại, bản ghi liên quan)
          thì cập nhật tiêu đề, nội dung và thời điểm thay vì tạo mới.

        :return: bản ghi thông báo (sudo) hoặc recordset rỗng nếu lỗi / không có sinh viên.
        """
        Notice = self.sudo()
        if self.env.context.get('univ_sms_skip_notice'):
            # Nhập liệu hàng loạt / seed: không tạo thông báo cá nhân
            return Notice.browse()
        try:
            student = student and student[:1]
            if not student:
                return Notice.browse()
            res_model = record._name if record else False
            res_id = record[:1].id if record else 0
            vals = {
                'title': (title or '').strip()[:250] or dict(NOTICE_EVENT_TYPES).get(event_type, _('Thông báo')),
                'body': body or False,
                'notice_date': fields.Datetime.now(),
            }
            with self.env.cr.savepoint():
                existing = Notice.search([
                    ('student_id', '=', student.id),
                    ('event_type', '=', event_type),
                    ('res_model', '=', res_model),
                    ('res_id', '=', res_id),
                    ('is_read', '=', False),
                ], limit=1)
                if existing:
                    existing.write(vals)
                    return existing
                vals.update({
                    'student_id': student.id,
                    'event_type': event_type,
                    'res_model': res_model,
                    'res_id': res_id,
                })
                return Notice.create(vals)
        except Exception:
            _logger.exception('Không tạo được thông báo %s cho sinh viên %s', event_type,
                              student.ids if student else student)
            return Notice.browse()
