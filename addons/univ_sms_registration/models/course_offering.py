import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from .registration import OCCUPYING_STATES

_logger = logging.getLogger(__name__)


class UnivSmsCourseOffering(models.Model):
    _name = 'univ.sms.course.offering'
    _description = 'Lớp môn học (mở trong học kỳ)'
    _order = 'term_id desc, subject_id'

    name = fields.Char(compute='_compute_name', store=True)
    subject_id = fields.Many2one('univ.sms.subject', required=True)
    term_id = fields.Many2one('univ.sms.term', required=True)
    lecturer_id = fields.Many2one('res.partner', string='Giảng viên')
    class_id = fields.Many2one('univ.sms.class', string='Lớp tín chỉ')
    max_seats = fields.Integer(required=True, default=60)
    registered_count = fields.Integer(compute='_compute_registered_count', string='Đã đăng ký')
    waitlist_count = fields.Integer(compute='_compute_registered_count', string='Đang chờ')
    available_seats = fields.Integer(compute='_compute_seat_status', string='Còn chỗ')
    is_full = fields.Boolean(compute='_compute_seat_status', string='Đã đầy')
    prerequisite_subject_ids = fields.Many2many(
        related='subject_id.prerequisite_ids',
        string='Môn tiên quyết')
    registration_ids = fields.One2many(
        'univ.sms.registration', 'offering_id', string='Đăng ký')
    waitlist_ids = fields.One2many(
        'univ.sms.registration.waitlist', 'offering_id', string='Danh sách chờ')
    active = fields.Boolean(default=True)

    @api.depends('subject_id', 'term_id')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.subject_id.code} - {rec.term_id.name}"

    @api.depends('registration_ids.state', 'waitlist_ids.state')
    def _compute_registered_count(self):
        # Chỉ đếm trạng thái chiếm chỗ (registered, confirmed); draft không chiếm chỗ.
        reg_counts = {}
        wait_counts = {}
        ids = [i for i in self.ids if i]
        if ids:
            for offering, count in self.env['univ.sms.registration'].sudo()._read_group(
                    [('offering_id', 'in', ids), ('state', 'in', OCCUPYING_STATES)],
                    ['offering_id'], ['__count']):
                reg_counts[offering.id] = count
            for offering, count in self.env['univ.sms.registration.waitlist'].sudo()._read_group(
                    [('offering_id', 'in', ids), ('state', '=', 'waiting')],
                    ['offering_id'], ['__count']):
                wait_counts[offering.id] = count
        for rec in self:
            rec.registered_count = reg_counts.get(rec.id, 0)
            rec.waitlist_count = wait_counts.get(rec.id, 0)

    @api.depends('max_seats', 'registered_count')
    def _compute_seat_status(self):
        for rec in self:
            rec.available_seats = max((rec.max_seats or 0) - rec.registered_count, 0)
            rec.is_full = bool(rec.max_seats and rec.registered_count >= rec.max_seats)

    def write(self, vals):
        old_seats = {rec.id: rec.max_seats for rec in self} if 'max_seats' in vals else {}
        res = super().write(vals)
        if old_seats:
            increased = self.filtered(
                lambda r: not r.max_seats or r.max_seats > (old_seats.get(r.id) or 0))
            if increased:
                increased._promote_waitlist()
        return res

    def _promote_waitlist(self):
        """Tự động nhận người chờ đầu tiên (FIFO theo request_date, id) khi lớp còn chỗ.

        Mỗi người được kiểm tra lại toàn bộ điều kiện; không đạt thì đánh dấu
        'rejected' kèm lý do rồi xét người kế tiếp. Nếu đợt đăng ký của người chờ
        đã đóng/hết hạn thì giữ nguyên 'waiting' và dừng (không tự nhận ngoài đợt).
        Trả về các bản ghi waitlist đã được nhận.
        """
        Registration = self.env['univ.sms.registration'].sudo()
        Waitlist = self.env['univ.sms.registration.waitlist'].sudo()
        promoted = Waitlist
        for offering in self.sudo():
            Registration._lock_offering(offering)
            while True:
                offering.invalidate_recordset(['registered_count', 'waitlist_count',
                                               'available_seats', 'is_full'])
                if offering.max_seats and offering.registered_count >= offering.max_seats:
                    break
                entry = Waitlist.search([
                    ('offering_id', '=', offering.id),
                    ('state', '=', 'waiting'),
                ], order='request_date, id', limit=1)
                if not entry:
                    break
                reason = Registration._get_block_reason(
                    entry.student_id, offering, entry.period_id)
                if reason and reason[0] == 'period':
                    break
                now = fields.Datetime.now()
                if reason:
                    entry.write({'state': 'rejected', 'note': reason[1], 'processed_date': now})
                    continue
                message = _('Được nhận từ danh sách chờ vào lớp %s.') % offering.name
                try:
                    with self.env.cr.savepoint():
                        reg = Registration._activate_registration(
                            entry.student_id, offering, entry.period_id, message)
                except (ValidationError, UserError) as exc:  # ràng buộc an toàn chặn: từ chối, xét người kế
                    _logger.info('Waitlist %s rejected on promotion: %s', entry.id, exc)
                    msg = exc.args[0] if exc.args else str(exc)
                    entry.write({'state': 'rejected', 'note': msg, 'processed_date': now})
                    continue
                entry.write({'state': 'promoted', 'registration_id': reg.id, 'processed_date': now})
                promoted |= entry
        return promoted
