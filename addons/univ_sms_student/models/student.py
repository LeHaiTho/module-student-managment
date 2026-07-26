from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class UnivSmsStudent(models.Model):
    _name = 'univ.sms.student'
    _description = 'Sinh viên'
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'student_code'

    partner_id = fields.Many2one(
        'res.partner',
        string='Đối tác liên hệ',
        required=True,
        ondelete='cascade',
    )

    # ─── Mã số sinh viên ───────────────────────────────────────────────────
    student_code = fields.Char(
        string='Mã số sinh viên',
        required=True,
        readonly=True,
        copy=False,
        default='New',
        tracking=True,
    )

    # ─── Thông tin cơ bản ──────────────────────────────────────────────────
    date_of_birth = fields.Date(string='Ngày sinh')
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác'),
    ], string='Giới tính')
    id_number = fields.Char(string='Số CCCD/CMND')
    id_issue_date = fields.Date(string='Ngày cấp')
    id_issue_place = fields.Char(string='Nơi cấp')
    ethnicity = fields.Char(string='Dân tộc', default='Kinh')
    religion = fields.Char(string='Tôn giáo', default='Không')
    policy_object = fields.Selection([
        ('none', 'Không có'),
        ('poor', 'Hộ nghèo'),
        ('near_poor', 'Hộ cận nghèo'),
        ('ethnic_minority', 'Dân tộc thiểu số'),
        ('martyr_family', 'Con liệt sĩ'),
        ('disabled', 'Người khuyết tật'),
        ('other_policy', 'Đối tượng chính sách khác'),
    ], string='Đối tượng chính sách', default='none')

    # ─── Thông tin liên lạc ────────────────────────────────────────────────
    personal_email = fields.Char(string='Email cá nhân')
    school_email = fields.Char(
        string='Email trường',
        compute='_compute_school_email',
        store=True,
        readonly=True,
    )
    # Địa chỉ thường trú (khác với street của res.partner dùng làm tạm trú)
    home_address = fields.Char(string='Địa chỉ thường trú')
    home_province_id = fields.Many2one(
        'res.country.state',
        string='Tỉnh/Thành phố (thường trú)',
        domain=[('country_id.code', '=', 'VN')],
    )
    current_address = fields.Char(string='Địa chỉ tạm trú')

    # ─── Thông tin gia đình ────────────────────────────────────────────────
    father_name = fields.Char(string='Họ tên cha')
    father_phone = fields.Char(string='SĐT cha')
    father_job = fields.Char(string='Nghề nghiệp cha')
    mother_name = fields.Char(string='Họ tên mẹ')
    mother_phone = fields.Char(string='SĐT mẹ')
    mother_job = fields.Char(string='Nghề nghiệp mẹ')
    emergency_contact_name = fields.Char(string='Người liên hệ khẩn cấp')
    emergency_contact_phone = fields.Char(string='SĐT liên hệ khẩn cấp')

    # ─── Thông tin học vụ ──────────────────────────────────────────────────
    program_id = fields.Many2one(
        'univ.sms.program',
        string='Ngành học',
        required=True,
        tracking=True,
    )
    home_class_id = fields.Many2one(
        'univ.sms.home.class',
        string='Lớp hành chính',
        tracking=True,
    )
    academic_year_id = fields.Many2one(
        'univ.sms.academic.year',
        string='Niên khóa nhập học',
        tracking=True,
    )
    training_system = fields.Selection([
        ('regular', 'Chính quy'),
        ('part_time', 'Vừa làm vừa học'),
        ('transfer', 'Liên thông'),
        ('advanced', 'Chất lượng cao'),
    ], string='Hệ đào tạo', default='regular', tracking=True)
    advisor_id = fields.Many2one(
        'res.partner',
        string='Cố vấn học tập',
        domain=[('is_company', '=', False)],
    )
    enrollment_date = fields.Date(
        string='Ngày nhập học',
        default=fields.Date.today,
    )

    # ─── Trạng thái học vụ ─────────────────────────────────────────────────
    state = fields.Selection([
        ('draft', 'Hồ sơ mới'),
        ('studying', 'Đang học'),
        ('on_leave', 'Bảo lưu'),
        ('graduated', 'Đã tốt nghiệp'),
        ('dropped', 'Bị buộc thôi học'),
        ('dismissed', 'Thôi học tự nguyện'),
    ], string='Trạng thái', default='draft', tracking=True)

    academic_warning_level = fields.Selection([
        ('none', 'Không cảnh báo'),
        ('level1', 'Cảnh báo lần 1'),
        ('level2', 'Cảnh báo lần 2'),
        ('dismissed', 'Buộc thôi học'),
    ], string='Mức cảnh báo học vụ', default='none', tracking=True)

    # ─── Quan hệ ───────────────────────────────────────────────────────────
    enrollment_ids = fields.One2many(
        'univ.sms.enrollment',
        'student_id',
        string='Đăng ký học',
    )

    _sql_constraints = [
        ('student_code_uniq', 'unique(student_code)', 'Mã số sinh viên đã tồn tại!'),
        ('id_number_uniq', 'unique(id_number)', 'Số CCCD/CMND đã tồn tại trong hệ thống!'),
    ]

    _student_partner_create_fields = {
        'name',
        'phone',
        'mobile',
        'email',
        'image_1920',
        'street',
        'street2',
        'city',
        'state_id',
        'zip',
        'country_id',
    }

    # ─── Computed fields ───────────────────────────────────────────────────
    @api.depends('student_code')
    def _compute_school_email(self):
        for record in self:
            if record.student_code and record.student_code != 'New':
                record.school_email = f"{record.student_code.lower()}@student.edu.vn"
            else:
                record.school_email = False

    # ─── Create: sinh MSSV tự động theo format [năm][mã ngành][seq] ───────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('student_code', 'New') == 'New':
                seq_num = self.env['ir.sequence'].next_by_code('univ.sms.student') or '0000'
                year = str(fields.Date.today().year)[2:]  # 2 số cuối năm, VD: '24'
                program = self.env['univ.sms.program'].browse(vals.get('program_id'))
                prog_code = (program.code or 'SV')[:5].upper() if program else 'SV'
                vals['student_code'] = f"{year}{prog_code}{seq_num}"
            if not vals.get('partner_id'):
                partner_vals = self._prepare_partner_vals(vals)
                vals['partner_id'] = self.env['res.partner'].sudo().create(partner_vals).id
        return super().create(vals_list)

    def _prepare_partner_vals(self, vals):
        partner_vals = {}
        for field_name in self._student_partner_create_fields:
            if field_name in vals:
                partner_vals[field_name] = vals.pop(field_name)
        partner_vals.setdefault('name', vals.get('student_code') or 'Sinh viên mới')
        partner_vals.setdefault('is_company', False)
        return partner_vals

    def write(self, vals):
        if 'student_code' in vals:
            for record in self:
                if record.student_code and record.student_code != 'New' and vals['student_code'] != record.student_code:
                    raise UserError('MSSV được sinh tự động và không được sửa sau khi tạo hồ sơ sinh viên.')
        return super().write(vals)

    # ─── Ghi đè unlink: chỉ xóa được khi hồ sơ mới và chưa có đăng ký ────
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(
                    f'Không thể xóa sinh viên "{record.name}" vì đang ở trạng thái '
                    f'"{dict(self._fields["state"].selection).get(record.state)}". '
                    'Chỉ có thể xóa sinh viên ở trạng thái Hồ sơ mới.'
                )
            if record.enrollment_ids:
                raise UserError(
                    f'Không thể xóa sinh viên "{record.name}" vì đã có lịch sử đăng ký học. '
                    'Hãy dùng chức năng Lưu trữ thay vì xóa.'
                )
        return super().unlink()

    # ─── State machine actions ─────────────────────────────────────────────
    def action_confirm(self):
        for record in self:
            record.state = 'studying'

    def action_on_leave(self):
        for record in self:
            record.state = 'on_leave'

    def action_graduate(self):
        for record in self:
            # Kiểm tra điều kiện tốt nghiệp
            record._check_graduation_conditions()
            record.state = 'graduated'

    def action_drop(self):
        """Buộc thôi học (do kỷ luật hoặc học vụ)"""
        for record in self:
            record.state = 'dropped'

    def action_dismiss(self):
        """Thôi học tự nguyện"""
        for record in self:
            record.state = 'dismissed'

    def action_reset_draft(self):
        for record in self:
            record.state = 'draft'
            record.academic_warning_level = 'none'

    # ─── Nghiệp vụ cảnh báo học vụ ────────────────────────────────────────
    def action_check_academic_warning(self):
        """Xét cảnh báo học vụ dựa trên bảng điểm kỳ gần nhất.
        Transcript nằm ở univ_sms_exam — dùng env[] để tránh hard dependency.
        """
        if 'univ.sms.transcript' not in self.env:
            raise UserError('Module Điểm số (univ_sms_exam) chưa được cài đặt.')

        for record in self:
            if record.state != 'studying':
                continue

            last_transcript = self.env['univ.sms.transcript'].search(
                [('student_id', '=', record.id)],
                order='id desc',
                limit=1,
            )
            if not last_transcript:
                continue

            gpa = last_transcript.term_gpa
            current_level = record.academic_warning_level

            if gpa < 1.0:
                if current_level == 'none':
                    record.academic_warning_level = 'level1'
                    record.message_post(
                        body=f'<b>Cảnh báo học vụ lần 1</b>: GPA học kỳ {last_transcript.term_id.name} = {gpa:.2f} (dưới 1.0). Sinh viên cần cải thiện kết quả học tập.',
                    )
                elif current_level == 'level1':
                    record.academic_warning_level = 'level2'
                    record.message_post(
                        body=f'<b>Cảnh báo học vụ lần 2</b>: GPA học kỳ {last_transcript.term_id.name} = {gpa:.2f}. Nguy cơ bị buộc thôi học.',
                    )
                elif current_level == 'level2':
                    record.academic_warning_level = 'dismissed'
                    record.state = 'dropped'
                    record.message_post(
                        body=f'<b>Buộc thôi học</b>: GPA học kỳ {last_transcript.term_id.name} = {gpa:.2f}. Đã 3 lần cảnh báo học vụ liên tiếp.',
                    )
            else:
                if current_level not in ('dismissed',):
                    record.academic_warning_level = 'none'

    # ─── Điều kiện xét tốt nghiệp ─────────────────────────────────────────
    def _check_graduation_conditions(self):
        self.ensure_one()
        errors = []

        # Kiểm tra đủ tổng số tín chỉ — chỉ chạy nếu module exam đã cài
        required_credits = self.program_id.total_credits
        if required_credits and 'univ.sms.transcript' in self.env:
            earned_credits = sum(
                line.credit
                for transcript in self.env['univ.sms.transcript'].search(
                    [('student_id', '=', self.id)]
                )
                for line in transcript.line_ids
                if line.final_score >= 5.0
            )
            if earned_credits < required_credits:
                errors.append(
                    f'Chưa đủ tín chỉ tốt nghiệp: tích lũy {earned_credits}/{required_credits} TC.'
                )

        # Kiểm tra không còn nợ học phí — chỉ chạy nếu module fee đã cài
        if 'univ.sms.fee' in self.env:
            outstanding_fee = self.env['univ.sms.fee'].search([
                ('student_id', '=', self.id),
                ('remaining_amount', '>', 0),
            ])
            if outstanding_fee:
                errors.append(
                    f'Còn nợ học phí: {sum(outstanding_fee.mapped("remaining_amount")):,.0f} VNĐ.'
                )

        if errors:
            raise ValidationError(
                'Sinh viên chưa đủ điều kiện tốt nghiệp:\n' + '\n'.join(f'• {e}' for e in errors)
            )
