from odoo import models, fields


class UnivSmsSubjectInherit(models.Model):
    _inherit = 'univ.sms.subject'

    prerequisite_ids = fields.Many2many(
        'univ.sms.subject', 'subject_prerequisite_rel',
        'subject_id', 'prereq_id', string='Môn tiên quyết')

    subject_type = fields.Selection([
        ('required', 'Bắt buộc'),
        ('elective', 'Tự chọn'),
    ], string='Loại môn', default='required')