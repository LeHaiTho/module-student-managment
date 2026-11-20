from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UnivSmsRegistrationWaitlist(models.Model):
    _name = 'univ.sms.registration.waitlist'
    _description = 'Danh sách chờ đăng ký môn'
    _order = 'offering_id, request_date, id'

    student_id = fields.Many2one(
        'univ.sms.student', string='Sinh viên', required=True, ondelete='cascade', index=True)
    offering_id = fields.Many2one(
        'univ.sms.course.offering', string='Lớp môn học', required=True, ondelete='cascade',
        index=True)
    period_id = fields.Many2one(
        'univ.sms.registration.period', string='Đợt đăng ký', required=True)
    subject_id = fields.Many2one(
        related='offering_id.subject_id', string='Môn học', store=True, readonly=True)
    term_id = fields.Many2one(
        related='offering_id.term_id', string='Học kỳ', store=True, readonly=True)
    request_date = fields.Datetime(
        string='Thời điểm xin chờ', default=fields.Datetime.now, required=True)
    position = fields.Integer(string='Vị trí chờ', compute='_compute_position')
    state = fields.Selection([
        ('waiting', 'Đang chờ'),
        ('promoted', 'Đã được nhận'),
        ('cancelled', 'Đã hủy'),
        ('rejected', 'Bị từ chối'),
    ], string='Trạng thái', default='waiting', required=True, index=True)
    processed_date = fields.Datetime(string='Thời điểm xử lý', readonly=True)
    registration_id = fields.Many2one(
        'univ.sms.registration', string='Đăng ký được tạo', readonly=True, ondelete='set null')
    note = fields.Char(string='Ghi chú / lý do')

    def init(self):
        # Mỗi sinh viên chỉ có một bản ghi 'waiting' trên một lớp môn học.
        self.env.cr.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS univ_sms_reg_waitlist_waiting_uniq
            ON univ_sms_registration_waitlist (student_id, offering_id)
            WHERE state = 'waiting'
        """)

    @api.depends('student_id', 'offering_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'{rec.student_id.name or ""} - {rec.offering_id.name or ""}'

    def _compute_position(self):
        waiting = self.filtered(lambda r: r.state == 'waiting' and r.offering_id)
        positions = {}
        for offering in waiting.mapped('offering_id'):
            queue = self.sudo().search([
                ('offering_id', '=', offering.id),
                ('state', '=', 'waiting'),
            ], order='request_date, id')
            for index, entry in enumerate(queue, start=1):
                positions[entry.id] = index
        for rec in self:
            rec.position = positions.get(rec.id, 0)

    @api.constrains('student_id', 'offering_id', 'state')
    def _check_single_waiting(self):
        for rec in self:
            if rec.state != 'waiting':
                continue
            if self.search_count([
                ('id', '!=', rec.id),
                ('student_id', '=', rec.student_id.id),
                ('offering_id', '=', rec.offering_id.id),
                ('state', '=', 'waiting'),
            ]):
                raise ValidationError(_('Sinh viên đã ở trong danh sách chờ của lớp này.'))

    def _notify_waitlist_result(self):
        """F4: thông báo cho sinh viên kết quả xét danh sách chờ (được nhận / bị loại)."""
        Notice = self.env['univ.sms.student.notice']
        for entry in self:
            subject = entry.offering_id.subject_id.name or entry.offering_id.name
            if entry.state == 'promoted':
                Notice._notify(
                    entry.student_id, 'waitlist_promoted',
                    _('Đã được nhận vào lớp môn %s') % subject,
                    _('Lớp %s vừa có chỗ trống, bạn đã được tự động đăng ký từ danh sách chờ. '
                      'Hãy kiểm tra lại thời khóa biểu.') % entry.offering_id.name,
                    entry)
            elif entry.state == 'rejected':
                Notice._notify(
                    entry.student_id, 'waitlist_rejected',
                    _('Không được nhận vào lớp môn %s') % subject,
                    _('Lớp %(offering)s có chỗ trống nhưng bạn chưa thể được nhận: %(note)s',
                      offering=entry.offering_id.name, note=entry.note or ''),
                    entry)

    def action_cancel(self):
        self.filtered(lambda r: r.state == 'waiting').write({
            'state': 'cancelled',
            'processed_date': fields.Datetime.now(),
        })
        return True

    def action_promote_now(self):
        """Cho phép phòng đào tạo chạy lại việc nhận người chờ của các lớp liên quan."""
        self.mapped('offering_id')._promote_waitlist()
        return True
