from odoo import api, models

DEFAULT_MAX_ABSENCE_RATE = 20.0


class UnivSmsEnrollment(models.Model):
    _inherit = 'univ.sms.enrollment'

    @api.model
    def _get_max_absence_rate(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'univ_sms.max_absence_rate', DEFAULT_MAX_ABSENCE_RATE)
        try:
            return float(value)
        except (TypeError, ValueError):
            return DEFAULT_MAX_ABSENCE_RATE

    def _get_attendance_counts(self):
        """Trả về {enrollment_id: (số phiếu confirmed của lớp, số dòng absent trên phiếu confirmed)}.

        Theo khóa schema 3.4: chỉ phiếu `confirmed` được tính; `excused` không
        tính vắng; `late` tính có mặt.
        """
        Sheet = self.env['univ.sms.attendance.sheet'].sudo()
        Line = self.env['univ.sms.attendance.line'].sudo()
        class_ids = self.mapped('class_id').ids
        student_ids = self.mapped('student_id').ids
        sessions_by_class = {}
        absent_by_key = {}
        if class_ids:
            for group in Sheet.read_group(
                    [('class_id', 'in', class_ids), ('state', '=', 'confirmed')],
                    ['class_id'], ['class_id']):
                sessions_by_class[group['class_id'][0]] = group['class_id_count']
            for line in Line.search([
                    ('sheet_id.class_id', 'in', class_ids),
                    ('sheet_id.state', '=', 'confirmed'),
                    ('student_id', 'in', student_ids),
                    ('state', '=', 'absent')]):
                key = (line.student_id.id, line.sheet_id.class_id.id)
                absent_by_key[key] = absent_by_key.get(key, 0) + 1
        result = {}
        for rec in self:
            if not rec.class_id:
                result[rec.id] = (0, 0)
                continue
            result[rec.id] = (
                sessions_by_class.get(rec.class_id.id, 0),
                absent_by_key.get((rec.student_id.id, rec.class_id.id), 0),
            )
        return result

    def _compute_attendance_stats(self):
        # Ghi đè univ_sms_class: không đếm dòng vắng trên phiếu nháp, ngưỡng lấy từ cấu hình.
        threshold = self._get_max_absence_rate()
        counts = self._get_attendance_counts()
        for rec in self:
            total, absence = counts.get(rec.id, (0, 0))
            rate = absence / total * 100 if total else 0.0
            rec.total_sessions = total
            rec.absence_count = absence
            rec.absence_rate = round(rate, 1)
            rec.has_attendance_warning = rate > threshold
