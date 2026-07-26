from odoo import models, fields, api
from odoo.exceptions import ValidationError


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

    def action_load_students(self):
        """Tự động tải danh sách sinh viên từ lớp vào phiếu điểm danh"""
        self.ensure_one()
        if self.state == 'confirmed':
            raise ValidationError('Không thể sửa phiếu đã xác nhận!')

        existing_student_ids = self.line_ids.mapped('student_id').ids
        enrollments = self.env['univ.sms.enrollment'].search([
            ('class_id', '=', self.class_id.id),
            ('state', '=', 'registered'),
        ])

        lines = []
        for enrollment in enrollments:
            if enrollment.student_id.id not in existing_student_ids:
                lines.append({
                    'sheet_id': self.id,
                    'student_id': enrollment.student_id.id,
                    'state': 'present',
                })

        if lines:
            self.env['univ.sms.attendance.line'].create(lines)

    def action_confirm(self):
        for record in self:
            if not record.line_ids:
                raise ValidationError('Vui lòng tải danh sách sinh viên trước khi xác nhận!')
            record.state = 'confirmed'

    def action_reset_draft(self):
        for record in self:
            record.state = 'draft'


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

    _sql_constraints = [
        (
            'line_uniq',
            'unique(sheet_id, student_id)',
            'Sinh viên đã được điểm danh trong phiếu này!',
        ),
    ]
