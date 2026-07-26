from odoo import models, fields, api


class UnivSmsEnrollment(models.Model):
    _inherit = 'univ.sms.enrollment'

    class_id = fields.Many2one(
        'univ.sms.class',
        string='Lớp',
    )

    # ─── Thống kê chuyên cần (tính động từ attendance nếu module đã cài) ───
    total_sessions = fields.Integer(
        string='Tổng buổi học',
        compute='_compute_attendance_stats',
    )
    absence_count = fields.Integer(
        string='Số buổi vắng',
        compute='_compute_attendance_stats',
    )
    absence_rate = fields.Float(
        string='Tỷ lệ vắng (%)',
        compute='_compute_attendance_stats',
        digits=(5, 1),
    )
    has_attendance_warning = fields.Boolean(
        string='Cảnh báo chuyên cần',
        compute='_compute_attendance_stats',
    )

    def _compute_attendance_stats(self):
        AttendanceSheet = self.env.get('univ.sms.attendance.sheet')
        AttendanceLine = self.env.get('univ.sms.attendance.line')
        for rec in self:
            if not rec.class_id or not AttendanceSheet or not AttendanceLine:
                rec.total_sessions = 0
                rec.absence_count = 0
                rec.absence_rate = 0.0
                rec.has_attendance_warning = False
                continue
            total = AttendanceSheet.search_count([
                ('class_id', '=', rec.class_id.id),
                ('state', '=', 'confirmed'),
            ])
            absence = AttendanceLine.search_count([
                ('sheet_id.class_id', '=', rec.class_id.id),
                ('student_id', '=', rec.student_id.id),
                ('state', '=', 'absent'),
            ])
            rec.total_sessions = total
            rec.absence_count = absence
            rec.absence_rate = round(absence / total * 100, 1) if total else 0.0
            rec.has_attendance_warning = rec.absence_rate > 20.0
