from odoo import api, fields, models

WARNING_GROUPS = (
    'univ_sms_base.group_univ_advisor,'
    'univ_sms_base.group_univ_academic_officer,'
    'univ_sms_base.group_univ_student_affairs_office'
)


class UnivSmsStudent(models.Model):
    _inherit = 'univ.sms.student'

    warning_ids = fields.One2many(
        'univ.sms.warning', 'student_id', string='Cảnh báo sớm', groups=WARNING_GROUPS)
    warning_open_count = fields.Integer(
        string='Cảnh báo đang mở', compute='_compute_warning_open_count', groups=WARNING_GROUPS)

    @api.depends_context('uid')
    def _compute_warning_open_count(self):
        data = self.env['univ.sms.warning']._read_group(
            [('student_id', 'in', self.ids), ('state', '!=', 'closed')],
            ['student_id'], ['__count'])
        counts = {student.id: count for student, count in data}
        for rec in self:
            rec.warning_open_count = counts.get(rec.id, 0)

    def action_view_warnings(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'univ_sms_early_warning.action_univ_sms_warning')
        action['domain'] = [('student_id', '=', self.id)]
        action['context'] = {'default_student_id': self.id, 'search_default_open': 0}
        action['name'] = 'Cảnh báo sớm - %s' % self.display_name
        return action
