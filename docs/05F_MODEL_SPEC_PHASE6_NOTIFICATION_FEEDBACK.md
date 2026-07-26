Model: univ.sms.notification (Thông báo từ ban quản trị)
pythonclass UnivSmsNotification(models.Model):
    _name = 'univ.sms.notification'
    _inherit = ['mail.thread']  # để dùng follower + activity nếu cần
    _description = 'Thông báo'

    title = fields.Char(required=True, tracking=True)
    content = fields.Html(required=True)
    publish_date = fields.Datetime(default=fields.Datetime.now)
    expire_date = fields.Datetime()
    target_audience = fields.Selection([
        ('all', 'Toàn trường'),
        ('program', 'Theo ngành'),
        ('class', 'Theo lớp'),
    ], default='all')
    program_ids = fields.Many2many('univ.sms.program')
    class_ids = fields.Many2many('univ.sms.class')
    is_pinned = fields.Boolean(string='Ghim lên đầu')
    attachment_ids = fields.Many2many('ir.attachment')
    state = fields.Selection([
        ('draft', 'Soạn'),
        ('published', 'Đã đăng'),
        ('archived', 'Lưu trữ'),
    ], default='draft')
Model: univ.sms.feedback (Form ý kiến)
pythonclass UnivSmsFeedback(models.Model):
    _name = 'univ.sms.feedback'
    _description = 'Phản hồi/Góp ý của sinh viên'
    _inherit = ['mail.thread']

    student_id = fields.Many2one('univ.sms.student', required=True,
        default=lambda s: s._default_student())
    category = fields.Selection([
        ('academic', 'Học vụ'),
        ('facility', 'Cơ sở vật chất'),
        ('service', 'Dịch vụ hành chính'),
        ('other', 'Khác'),
    ], required=True)
    subject = fields.Char(required=True)
    description = fields.Text(required=True)
    department_id = fields.Many2one('univ.sms.department', string='Gửi đến bộ phận')
    state = fields.Selection([
        ('new', 'Mới'),
        ('in_progress', 'Đang xử lý'),
        ('resolved', 'Đã xử lý'),
        ('closed', 'Đã đóng'),
    ], default='new', tracking=True)
    response = fields.Text(string='Phản hồi từ phòng ban')

    def _default_student(self):
        return self.env['univ.sms.student'].search(
            [('partner_id', '=', self.env.user.partner_id.id)], limit=1)