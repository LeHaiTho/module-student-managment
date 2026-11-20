from odoo import _, fields, models


class UnivSmsResidenceInfo(models.Model):
    _name = 'univ.sms.residence.info'
    _inherit = ['univ.sms.workflow.guard.mixin']
    _description = 'Thông tin cư trú/ngoại trú'
    _order = 'student_id'

    student_id = fields.Many2one('univ.sms.student', required=True)
    residence_type = fields.Selection([
        ('dormitory', 'Ký túc xá'),
        ('rent', 'Nhà trọ'),
        ('family', 'Ở với gia đình'),
    ], required=True)
    address = fields.Text(required=True)
    landlord_name = fields.Char(string='Tên chủ nhà/Quản lý KTX')
    landlord_phone = fields.Char()
    effective_date = fields.Date(default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
    ], default='draft')

    def action_confirm(self):
        self._check_states(('draft',), _('xác nhận'))
        self.write({'state': 'confirmed'})

    def action_draft(self):
        self._check_states(('confirmed',), _('đặt lại nháp'))
        self.write({'state': 'draft'})