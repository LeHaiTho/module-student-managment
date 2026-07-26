from odoo import models, fields


class UnivSmsCertificateType(models.Model):
    _name = 'univ.sms.certificate.type'
    _description = 'Loại giấy chứng nhận'

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
    require_fee = fields.Boolean(string='Yêu cầu phí')
    fee_amount = fields.Float(string='Phí (VNĐ)')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã loại giấy chứng nhận phải là duy nhất!'),
    ]