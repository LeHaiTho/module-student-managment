Model: univ.sms.health.insurance (BHYT)
pythonclass UnivSmsHealthInsurance(models.Model):
    _name = 'univ.sms.health.insurance'
    _description = 'Bảo hiểm y tế sinh viên'

    student_id = fields.Many2one('univ.sms.student', required=True)
    insurance_code = fields.Char(string='Mã thẻ BHYT', required=True)
    issue_place_id = fields.Many2one('res.country.state', string='Nơi đăng ký KCB')
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    payment_state = fields.Selection([
        ('unpaid', 'Chưa đóng'),
        ('paid', 'Đã đóng'),
    ], default='unpaid', tracking=True)

    @api.depends('date_end')
    def _compute_is_expired(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_expired = rec.date_end < today
    is_expired = fields.Boolean(compute='_compute_is_expired', store=True)
Model: univ.sms.residence.info (Thông tin ngoại trú)
pythonclass UnivSmsResidenceInfo(models.Model):
    _name = 'univ.sms.residence.info'
    _description = 'Thông tin cư trú/ngoại trú'

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
    ], default='draft', tracking=True)
Model: univ.sms.military.service (NVQS)
pythonclass UnivSmsMilitaryService(models.Model):
    _name = 'univ.sms.military.service'
    _description = 'Khai báo nghĩa vụ quân sự'

    student_id = fields.Many2one('univ.sms.student', required=True)
    registration_status = fields.Selection([
        ('not_registered', 'Chưa đăng ký NVQS'),
        ('registered', 'Đã đăng ký'),
        ('deferred', 'Tạm hoãn (đang học)'),
        ('completed', 'Đã hoàn thành NVQS'),
    ], required=True)
    local_authority_id = fields.Many2one('res.country.state', string='Đơn vị quản lý')
    document_attachment_ids = fields.Many2many('ir.attachment', string='Hồ sơ kèm')
    declared_date = fields.Date(default=fields.Date.today)
    # ⚠️ OPEN_Q8: nếu cần export báo cáo định kỳ → bổ sung wizard export Excel theo mẫu