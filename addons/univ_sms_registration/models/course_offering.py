from odoo import models, fields, api


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
    registered_count = fields.Integer(compute='_compute_registered_count')
    available_seats = fields.Integer(compute='_compute_seat_status', string='Còn chỗ')
    is_full = fields.Boolean(compute='_compute_seat_status', string='Đã đầy')
    prerequisite_subject_ids = fields.Many2many(
        related='subject_id.prerequisite_ids',
        string='Môn tiên quyết')
    active = fields.Boolean(default=True)

    @api.depends('subject_id', 'term_id')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.subject_id.code} - {rec.term_id.name}"

    def _compute_registered_count(self):
        for rec in self:
            rec.registered_count = self.env['univ.sms.registration'].search_count(
                [('offering_id', '=', rec.id), ('state', 'in', ('draft', 'registered', 'confirmed'))])

    @api.depends('max_seats', 'registered_count')
    def _compute_seat_status(self):
        for rec in self:
            rec.available_seats = max((rec.max_seats or 0) - rec.registered_count, 0)
            rec.is_full = bool(rec.max_seats and rec.registered_count >= rec.max_seats)
