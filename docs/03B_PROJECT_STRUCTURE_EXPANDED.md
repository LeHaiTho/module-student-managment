addons/
├── univ_sms_base/              [Phase 1] đã định nghĩa
├── univ_sms_student/           [Phase 1] đã định nghĩa
├── univ_sms_class/             [Phase 2] đã định nghĩa
├── univ_sms_attendance/        [Phase 2] đã định nghĩa
├── univ_sms_exam/              [Phase 3] đã định nghĩa
├── univ_sms_fee/               [Phase 3] đã định nghĩa
│
├── univ_sms_registration/      [Phase 6] MỚI
│   ├── models/
│   │   ├── registration_period.py    # univ.sms.registration.period
│   │   ├── course_offering.py        # univ.sms.course.offering (môn mở trong kỳ)
│   │   ├── registration.py           # univ.sms.registration (DKMH)
│   │   └── elective_wish.py          # univ.sms.elective.wish (DKMNV)
│   ├── wizard/
│   │   └── registration_wizard.py
│   └── ...
│
├── univ_sms_notification/      [Phase 6] MỚI
│   ├── models/
│   │   └── notification.py           # univ.sms.notification (kế thừa mail.thread)
│   └── ...
│
├── univ_sms_feedback/          [Phase 6] MỚI
│   ├── models/
│   │   └── feedback.py               # univ.sms.feedback (form ý kiến)
│   └── ...
│
├── univ_sms_student_affairs/   [Phase 7] MỚI
│   ├── models/
│   │   ├── health_insurance.py       # univ.sms.health.insurance
│   │   ├── residence_info.py         # univ.sms.residence.info (ngoại trú)
│   │   └── military_service.py       # univ.sms.military.service (NVQS)
│   └── ...
│
├── univ_sms_conduct/            [Phase 7] MỚI
│   ├── models/
│   │   ├── conduct_period.py         # univ.sms.conduct.period
│   │   ├── conduct_criteria.py       # univ.sms.conduct.criteria
│   │   └── conduct_score.py          # univ.sms.conduct.score (workflow 3 cấp)
│   └── ...
│
├── univ_sms_certificate/        [Phase 7] MỚI
│   ├── models/
│   │   ├── certificate_type.py       # univ.sms.certificate.type
│   │   └── certificate_request.py    # univ.sms.certificate.request
│   ├── reports/
│   │   └── certificate_report.xml
│   └── ...
│
├── univ_sms_survey/              [Phase 7] MỚI (kế thừa survey)
│   └── ...
│
├── univ_sms_portal/              [Phase 4] mở rộng thêm route mới ở Phase 6-7
│
└── univ_sms_report/              [Phase 9] mở rộng mạnh — Dashboard tổng + theo role
    ├── reports/                   # QWeb PDF: bảng điểm, hóa đơn, giấy chứng nhận, phiếu điểm danh
    ├── dashboards/
    │   ├── admin_dashboard_views.xml
    │   ├── lecturer_dashboard_views.xml
    │   └── student_dashboard_views.xml (portal widget)
    └── ...

FILE: 05B_MODEL_SPEC_PHASE6_REGISTRATION.md (Đăng ký môn học)
Model: univ.sms.registration.period
pythonclass UnivSmsRegistrationPeriod(models.Model):
    _name = 'univ.sms.registration.period'
    _description = 'Đợt đăng ký môn học'

    name = fields.Char(required=True)
    term_id = fields.Many2one('univ.sms.term', required=True)
    date_start = fields.Datetime(required=True)
    date_end = fields.Datetime(required=True)
    reg_type = fields.Selection([
        ('regular', 'Đăng ký chính thức (DKMH)'),
        ('elective', 'Đăng ký nguyện vọng (DKMNV)'),
    ], required=True, default='regular')
    min_credit = fields.Integer(string='Tín chỉ tối thiểu')   # ⚠️ OPEN_Q1
    max_credit = fields.Integer(string='Tín chỉ tối đa')      # ⚠️ OPEN_Q1
    state = fields.Selection([
        ('draft', 'Chưa mở'),
        ('open', 'Đang mở'),
        ('closed', 'Đã đóng'),
    ], default='draft', tracking=True)
Model: univ.sms.course.offering (Môn học mở trong kỳ — lớp tín chỉ)
pythonclass UnivSmsCourseOffering(models.Model):
    _name = 'univ.sms.course.offering'
    _description = 'Lớp môn học (mở trong học kỳ)'

    name = fields.Char(compute='_compute_name', store=True)
    subject_id = fields.Many2one('univ.sms.subject', required=True)
    term_id = fields.Many2one('univ.sms.term', required=True)
    lecturer_id = fields.Many2one('res.partner', string='Giảng viên')
    class_id = fields.Many2one('univ.sms.class', string='Lớp tín chỉ')
    max_seats = fields.Integer(required=True, default=60)
    registered_count = fields.Integer(compute='_compute_registered_count')
    prerequisite_subject_ids = fields.Many2many(
        related='subject_id.prerequisite_ids', string='Môn tiên quyết')

    @api.depends('subject_id', 'term_id')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.subject_id.code} - {rec.term_id.name}"

    def _compute_registered_count(self):
        for rec in self:
            rec.registered_count = self.env['univ.sms.registration'].search_count(
                [('offering_id', '=', rec.id), ('state', '!=', 'cancelled')])

Lưu ý kỹ thuật: trường prerequisite_subject_ids yêu cầu mở rộng model univ.sms.subject (Phase 1) thêm field prerequisite_ids = fields.Many2many('univ.sms.subject', 'subject_prerequisite_rel', 'subject_id', 'prereq_id'). Đây là Class Inheritance trên model có sẵn — viết trong file mới univ_sms_registration/models/subject_inherit.py, KHÔNG sửa file gốc univ_sms_base/models/subject.py.

python# univ_sms_registration/models/subject_inherit.py
class UnivSmsSubjectInherit(models.Model):
    _inherit = 'univ.sms.subject'

    prerequisite_ids = fields.Many2many(
        'univ.sms.subject', 'subject_prerequisite_rel',
        'subject_id', 'prereq_id', string='Môn tiên quyết')
Model: univ.sms.registration (DKMH)
pythonclass UnivSmsRegistration(models.Model):
    _name = 'univ.sms.registration'
    _description = 'Đăng ký môn học'

    student_id = fields.Many2one('univ.sms.student', required=True, ondelete='cascade')
    offering_id = fields.Many2one('univ.sms.course.offering', required=True)
    period_id = fields.Many2one('univ.sms.registration.period', required=True)
    registration_date = fields.Datetime(default=fields.Datetime.now)
    state = fields.Selection([
        ('draft', 'Chờ duyệt'),
        ('confirmed', 'Đã xác nhận'),
        ('cancelled', 'Đã hủy'),
    ], default='draft', tracking=True)

    @api.constrains('offering_id', 'student_id')
    def _check_prerequisite(self):
        for rec in self:
            prereqs = rec.offering_id.subject_id.prerequisite_ids
            if prereqs:
                passed = self.env['univ.sms.exam.result'].search([
                    ('student_id', '=', rec.student_id.id),
                    ('subject_id', 'in', prereqs.ids),
                    ('is_passed', '=', True),
                ]).mapped('subject_id')
                missing = prereqs - passed
                if missing:
                    raise ValidationError(
                        f"Chưa hoàn thành môn tiên quyết: {', '.join(missing.mapped('name'))}")

    @api.constrains('student_id', 'period_id')
    def _check_credit_limit(self):
        # ⚠️ Cần OPEN_Q1 xác nhận min/max_credit trước khi enable constraint này
        for rec in self:
            total_credit = sum(self.search([
                ('student_id', '=', rec.student_id.id),
                ('period_id', '=', rec.period_id.id),
                ('state', '!=', 'cancelled'),
            ]).mapped('offering_id.subject_id.credit'))
            if rec.period_id.max_credit and total_credit > rec.period_id.max_credit:
                raise ValidationError(f"Vượt quá số tín chỉ tối đa ({rec.period_id.max_credit})")

    _sql_constraints = [
        ('reg_uniq', 'unique(student_id, offering_id)', 'Đã đăng ký môn này!')
    ]
Model: univ.sms.elective.wish (DKMNV)
pythonclass UnivSmsElectiveWish(models.Model):
    _name = 'univ.sms.elective.wish'
    _description = 'Đăng ký môn nguyện vọng'

    student_id = fields.Many2one('univ.sms.student', required=True)
    offering_id = fields.Many2one('univ.sms.course.offering', required=True,
        domain=[('subject_id.subject_type', '=', 'elective')])  # ⚠️ cần thêm field subject_type vào univ.sms.subject
    priority = fields.Integer(string='Độ ưu tiên', default=1)
    state = fields.Selection([
        ('pending', 'Chờ xử lý'),
        ('approved', 'Được chọn'),
        ('rejected', 'Không đủ slot'),
    ], default='pending')

⚠️ OPEN: model univ.sms.subject (Phase 1) cần bổ sung field subject_type = Selection([('required','Bắt buộc'),('elective','Tự chọn')]). Vì Phase 1 đã "đóng băng" theo Rule R5/09_AGENT_WORKFLOW — Agent phải đề xuất migration: thêm field qua Class Inheritance trong univ_sms_registration/models/subject_inherit.py (gộp cùng file prerequisite_ids ở trên), không sửa Phase 1.