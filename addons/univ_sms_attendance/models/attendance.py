from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class UnivSmsAttendanceSheet(models.Model):
    _name = 'univ.sms.attendance.sheet'
    _description = 'Phiếu điểm danh'
    _order = 'attendance_date desc'

    name = fields.Char(
        string='Tên phiếu',
        compute='_compute_name',
        store=True,
    )
    class_id = fields.Many2one(
        'univ.sms.class',
        string='Lớp',
        required=True,
    )
    attendance_date = fields.Date(
        string='Ngày điểm danh',
        required=True,
        default=fields.Date.today,
    )
    lecturer_id = fields.Many2one(
        'res.partner',
        string='Giảng viên',
        related='class_id.lecturer_id',
        store=True,
    )
    line_ids = fields.One2many(
        'univ.sms.attendance.line',
        'sheet_id',
        string='Chi tiết điểm danh',
    )
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
    ], string='Trạng thái', default='draft')

    total_present = fields.Integer(string='Có mặt', compute='_compute_totals')
    total_absent = fields.Integer(string='Vắng mặt', compute='_compute_totals')
    total_late = fields.Integer(string='Đi trễ', compute='_compute_totals')
    total_excused = fields.Integer(string='Có phép', compute='_compute_totals')

    # ─── Điểm danh QR ─────────────────────────────────────────────────────
    session_ids = fields.One2many(
        'univ.sms.attendance.session',
        'sheet_id',
        string='Phiên điểm danh QR',
    )
    active_session_id = fields.Many2one(
        'univ.sms.attendance.session',
        string='Phiên QR đang mở',
        compute='_compute_active_session',
    )
    qr_image_src = fields.Char(
        string='Mã QR',
        compute='_compute_active_session',
        groups='univ_sms_base.group_univ_lecturer',
    )
    qr_expire_time = fields.Datetime(
        string='QR hết hạn lúc',
        compute='_compute_active_session',
    )
    qr_checkin_count = fields.Integer(
        string='Đã quét QR',
        compute='_compute_active_session',
    )

    @api.depends('class_id', 'attendance_date')
    def _compute_name(self):
        for record in self:
            class_name = record.class_id.name or ''
            date_str = record.attendance_date and record.attendance_date.strftime('%d/%m/%Y') or ''
            record.name = f'{class_name} - {date_str}'

    @api.depends('line_ids', 'line_ids.state')
    def _compute_totals(self):
        for record in self:
            record.total_present = len(record.line_ids.filtered(lambda l: l.state == 'present'))
            record.total_absent = len(record.line_ids.filtered(lambda l: l.state == 'absent'))
            record.total_late = len(record.line_ids.filtered(lambda l: l.state == 'late'))
            record.total_excused = len(record.line_ids.filtered(lambda l: l.state == 'excused'))

    @api.depends('session_ids.state')
    def _compute_active_session(self):
        Session = self.env['univ.sms.attendance.session']
        for record in self:
            session = Session.search([
                ('sheet_id', '=', record.id),
                ('state', '=', 'active'),
            ], limit=1) if record.id else Session
            record.active_session_id = session
            record.qr_expire_time = session.expire_time
            record.qr_checkin_count = session.checkin_count
            record.qr_image_src = session._get_qr_image_src() if session else False

    # ─── Nạp danh sách ────────────────────────────────────────────────────
    def _get_registered_enrollments(self):
        self.ensure_one()
        return self.env['univ.sms.enrollment'].search([
            ('class_id', '=', self.class_id.id),
            ('state', '=', 'registered'),
        ])

    def _load_students(self, default_state='present'):
        """Tạo dòng (mặc định 'Có mặt'; điểm danh QR dùng 'Vắng') cho sinh viên đã đăng ký mà chưa có dòng.

        Lặp lại an toàn: sinh viên đã có dòng thì bỏ qua. Trả về số dòng mới.
        """
        self.ensure_one()
        if self.state == 'confirmed':
            raise UserError('Phiếu điểm danh đã xác nhận, không thể nạp thêm sinh viên.')
        existing_student_ids = set(self.line_ids.mapped('student_id').ids)
        vals_list = []
        for student in self._get_registered_enrollments().mapped('student_id'):
            if student.id not in existing_student_ids:
                existing_student_ids.add(student.id)
                vals_list.append({
                    'sheet_id': self.id,
                    'student_id': student.id,
                    'state': default_state,
                    'checkin_source': 'manual',
                })
        if vals_list:
            self.env['univ.sms.attendance.line'].create(vals_list)
        return len(vals_list)

    def action_load_students(self):
        """Tự động tải danh sách sinh viên từ lớp vào phiếu điểm danh"""
        for record in self:
            record._load_students()
        return True

    def action_confirm(self):
        for record in self:
            if not record.line_ids:
                raise ValidationError('Vui lòng tải danh sách sinh viên trước khi xác nhận!')
            record.session_ids.filtered(lambda s: s.state == 'active').action_close()
            record.state = 'confirmed'

    def action_reset_draft(self):
        if not (self.env.su or self.env.user.has_group('univ_sms_base.group_univ_academic_officer')):
            raise UserError('Chỉ Phòng Đào tạo hoặc Quản trị viên mới được đưa phiếu đã xác nhận về nháp.')
        for record in self:
            record.state = 'draft'

    # ─── Phiên QR ─────────────────────────────────────────────────────────
    def action_start_qr_session(self):
        """Mở phiên điểm danh QR mới (đóng phiên cũ nếu còn)."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError('Chỉ mở được phiên QR cho phiếu điểm danh ở trạng thái Nháp.')
        if not self._get_registered_enrollments():
            raise UserError(
                f'Lớp "{self.class_id.name}" chưa có sinh viên ở trạng thái Đã đăng ký, '
                'không thể mở phiên điểm danh QR.'
            )
        if not self.session_ids:
            # Phiên QR đầu tiên: ai chưa quét mặc định là vắng. Dòng giảng viên đã
            # chỉnh tay (vắng, trễ, có phép, có ghi chú) được giữ nguyên.
            self.line_ids.filtered(
                lambda l: l.checkin_source == 'manual' and not l.checkin_time
                and l.state == 'present' and not l.note
            ).write({'state': 'absent'})
        self._load_students(default_state='absent')
        self.session_ids.filtered(lambda s: s.state == 'active').action_close()
        self.env['univ.sms.attendance.session']._create_for_sheet(self)
        return True

    def action_close_qr_session(self):
        self.session_ids.filtered(lambda s: s.state == 'active').action_close()
        return True


class UnivSmsAttendanceLine(models.Model):
    _name = 'univ.sms.attendance.line'
    _description = 'Chi tiết điểm danh'
    _order = 'sheet_id, student_id'

    sheet_id = fields.Many2one(
        'univ.sms.attendance.sheet',
        string='Phiếu điểm danh',
        required=True,
        ondelete='cascade',
    )
    student_id = fields.Many2one(
        'univ.sms.student',
        string='Sinh viên',
        required=True,
    )
    state = fields.Selection([
        ('present', 'Có mặt'),
        ('absent', 'Vắng mặt'),
        ('late', 'Đi trễ'),
        ('excused', 'Có phép'),
    ], string='Trạng thái', default='present')
    note = fields.Char(string='Ghi chú')
    checkin_time = fields.Datetime(string='Giờ check-in', readonly=True, copy=False)
    checkin_source = fields.Selection([
        ('manual', 'Thủ công'),
        ('qr', 'Quét QR'),
    ], string='Nguồn điểm danh', default='manual', required=True, readonly=True, copy=False)
    session_id = fields.Many2one(
        'univ.sms.attendance.session',
        string='Phiên QR',
        ondelete='set null',
        readonly=True,
        copy=False,
    )

    _sql_constraints = [
        (
            'line_uniq',
            'unique(sheet_id, student_id)',
            'Sinh viên đã được điểm danh trong phiếu này!',
        ),
    ]

    _LOCK_MESSAGE = (
        'Phiếu điểm danh "%s" đã xác nhận nên không thể thêm, sửa hoặc xóa dòng điểm danh. '
        'Cần Phòng Đào tạo đưa phiếu về Nháp trước.'
    )

    def _check_sheets_editable(self, sheets):
        for sheet in sheets:
            if sheet.state == 'confirmed':
                raise UserError(self._LOCK_MESSAGE % sheet.name)

    @api.model_create_multi
    def create(self, vals_list):
        sheet_ids = {vals.get('sheet_id') for vals in vals_list if vals.get('sheet_id')}
        self._check_sheets_editable(self.env['univ.sms.attendance.sheet'].browse(sheet_ids))
        return super().create(vals_list)

    def write(self, vals):
        sheets = self.mapped('sheet_id')
        if vals.get('sheet_id'):
            sheets |= self.env['univ.sms.attendance.sheet'].browse(vals['sheet_id'])
        self._check_sheets_editable(sheets)
        return super().write(vals)

    def unlink(self):
        self._check_sheets_editable(self.mapped('sheet_id'))
        return super().unlink()
