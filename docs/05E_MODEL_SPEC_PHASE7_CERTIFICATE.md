Model: univ.sms.certificate.type
pythonclass UnivSmsCertificateType(models.Model):
    _name = 'univ.sms.certificate.type'
    _description = 'Loại giấy chứng nhận/phiếu'

    name = fields.Char(required=True)  # VD: "Giấy xác nhận sinh viên", "Phiếu xin tạm vắng"
    code = fields.Char(required=True)
    report_template_id = fields.Many2one('ir.actions.report', string='Mẫu in PDF')
    requires_fee = fields.Boolean(string='Có lệ phí')
    fee_amount = fields.Monetary(currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
Model: univ.sms.certificate.request
pythonclass UnivSmsCertificateRequest(models.Model):
    _name = 'univ.sms.certificate.request'
    _description = 'Đơn xin giấy chứng nhận/phiếu'

    name = fields.Char(compute='_compute_name', store=True, readonly=False)
    student_id = fields.Many2one('univ.sms.student', required=True,
        default=lambda s: s._default_student())
    certificate_type_id = fields.Many2one('univ.sms.certificate.type', required=True)
    purpose = fields.Text(string='Mục đích sử dụng', required=True)
    request_date = fields.Date(default=fields.Date.today)
    quantity = fields.Integer(default=1, string='Số lượng')
    state = fields.Selection([
        ('draft', 'Mới tạo'),
        ('submitted', 'Đã nộp'),
        ('processing', 'Đang xử lý'),
        ('approved', 'PĐT đã duyệt'),
        ('issued', 'Đã cấp'),  # ⚠️ OPEN_Q3: có cần bước ký số trước issued?
        ('rejected', 'Từ chối'),
    ], default='draft', tracking=True)

    def _default_student(self):
        return self.env['univ.sms.student'].search(
            [('partner_id', '=', self.env.user.partner_id.id)], limit=1)

    @api.depends('certificate_type_id', 'student_id')
    def _compute_name(self):
        for rec in self:
            rec.name = f"YC-{rec.certificate_type_id.code or ''}-{rec.student_id.student_code or ''}"

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_issue(self):
        self.write({'state': 'issued'})

    def action_reject(self):
        self.write({'state': 'rejected'})