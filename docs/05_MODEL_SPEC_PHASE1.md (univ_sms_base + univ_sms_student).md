File này là đặc tả kỹ thuật mà AI Agent dùng làm input duy nhất để sinh code. Mỗi field đều có comment lý do.

Model: univ.sms.faculty
pythonclass UnivSmsFaculty(models.Model):
    _name = 'univ.sms.faculty'
    _description = 'Khoa'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)  # mã khoa, unique
    dean_id = fields.Many2one('res.partner', string='Trưởng khoa')
    department_ids = fields.One2many('univ.sms.department', 'faculty_id')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã khoa đã tồn tại!')
    ]
Model: univ.sms.department
pythonclass UnivSmsDepartment(models.Model):
    _name = 'univ.sms.department'
    _description = 'Bộ môn / Ngành'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    faculty_id = fields.Many2one('univ.sms.faculty', required=True, ondelete='cascade')
    program_ids = fields.One2many('univ.sms.program', 'department_id')
Model: univ.sms.program
pythonclass UnivSmsProgram(models.Model):
    _name = 'univ.sms.program'
    _description = 'Ngành đào tạo'

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    department_id = fields.Many2one('univ.sms.department', required=True)
    total_credits = fields.Integer(string='Tổng số tín chỉ')  # ✅ CONFIRMED: tín chỉ (credits), cumulative target ~150
    duration_years = fields.Integer(string='Thời gian đào tạo (năm)', default=4)
Model: univ.sms.subject
pythonclass UnivSmsSubject(models.Model):
    _name = 'univ.sms.subject'
    _description = 'Môn học'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    credit = fields.Float(required=True, string='Số tín chỉ')
    program_ids = fields.Many2many('univ.sms.program', string='Thuộc ngành')
    is_active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã môn học đã tồn tại!')
    ]
Model: univ.sms.academic.year / univ.sms.term
pythonclass UnivSmsAcademicYear(models.Model):
    _name = 'univ.sms.academic.year'
    name = fields.Char(required=True)  # VD: "2025-2026"
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    term_ids = fields.One2many('univ.sms.term', 'academic_year_id')

class UnivSmsTerm(models.Model):
    _name = 'univ.sms.term'
    name = fields.Char(required=True)  # VD: "Học kỳ 1"
    academic_year_id = fields.Many2one('univ.sms.academic.year', required=True)
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
Model: univ.sms.student (module univ_sms_student)
pythonclass UnivSmsStudent(models.Model):
    _name = 'univ.sms.student'
    _description = 'Sinh viên'
    _inherits = {'res.partner': 'partner_id'}  # Delegation Inheritance - dùng lại Partner cho liên hệ/email/portal
    _order = 'student_code'

    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    student_code = fields.Char(required=True, string='MSSV')  # ✅ CONFIRMED: auto-increment sequential (tự sinh, tăng dần)
    program_id = fields.Many2one('univ.sms.program', required=True, string='Ngành học')
    enrollment_date = fields.Date(default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Hồ sơ mới'),
        ('studying', 'Đang học'),
        ('on_leave', 'Tạm nghỉ'),
        ('graduated', 'Đã tốt nghiệp'),
        ('dropped', 'Đã thôi học'),
    ], default='draft', tracking=True)
    enrollment_ids = fields.One2many('univ.sms.enrollment', 'student_id')

    _sql_constraints = [
        ('student_code_uniq', 'unique(student_code)', 'MSSV đã tồn tại!')
    ]

Lý do chọn _inherits (Delegation Inheritance): tận dụng res.partner có sẵn email, địa chỉ, và liên kết portal user (res.users linked via partner_id) — đây là cơ sở để Phase 4 (Portal) hoạt động mà không cần tạo cơ chế đăng nhập riêng.

Model: univ.sms.enrollment
pythonclass UnivSmsEnrollment(models.Model):
    _name = 'univ.sms.enrollment'
    _description = 'Đăng ký học môn'

    student_id = fields.Many2one('univ.sms.student', required=True, ondelete='cascade')
    subject_id = fields.Many2one('univ.sms.subject', required=True)
    term_id = fields.Many2one('univ.sms.term', required=True)
    class_id = fields.Many2one('univ.sms.class', string='Lớp')  # cross-module, cần univ_sms_class
    state = fields.Selection([
        ('registered', 'Đã đăng ký'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ], default='registered')

    _sql_constraints = [
        ('enroll_uniq', 'unique(student_id, subject_id, term_id)',
         'Sinh viên đã đăng ký môn này trong học kỳ này!')
    ]