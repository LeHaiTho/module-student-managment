from odoo import _, fields, models


class UnivSmsWarningEvaluationWizard(models.TransientModel):
    _name = 'univ.sms.warning.evaluation.wizard'
    _description = 'Chạy đánh giá cảnh báo sớm'

    home_class_ids = fields.Many2many('univ.sms.home.class', string='Lớp hành chính')
    program_ids = fields.Many2many('univ.sms.program', string='Ngành')
    state = fields.Selection([('draft', 'Chuẩn bị'), ('done', 'Hoàn tất')], default='draft')
    checked_count = fields.Integer(string='Số sinh viên đã xét', readonly=True)
    created_count = fields.Integer(string='Cảnh báo mới', readonly=True)
    updated_count = fields.Integer(string='Cảnh báo cập nhật', readonly=True)
    error_count = fields.Integer(string='Lỗi', readonly=True)

    def _get_students(self):
        self.ensure_one()
        if not self.home_class_ids and not self.program_ids:
            return None  # toàn trường
        domain = [('state', '=', 'studying')]
        if self.home_class_ids:
            domain.append(('home_class_id', 'in', self.home_class_ids.ids))
        if self.program_ids:
            domain.append(('program_id', 'in', self.program_ids.ids))
        return self.env['univ.sms.student'].sudo().search(domain)

    def action_run(self):
        self.ensure_one()
        res = self.env['univ.sms.warning'].run_evaluation(self._get_students())
        self.write({
            'state': 'done',
            'checked_count': res.get('checked', 0),
            'created_count': res.get('created', 0),
            'updated_count': res.get('updated', 0),
            'error_count': res.get('errors', 0),
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Chạy đánh giá cảnh báo'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_view_warnings(self):
        return self.env['ir.actions.act_window']._for_xml_id(
            'univ_sms_early_warning.action_univ_sms_warning')
