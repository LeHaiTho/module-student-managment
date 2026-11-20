from odoo import _, api, fields, models


class UnivSmsEnrollment(models.Model):
    _inherit = 'univ.sms.enrollment'

    exam_eligible = fields.Boolean(
        string='Đủ điều kiện dự thi',
        default=True,
        copy=False,
    )
    exam_ineligible_reason = fields.Char(
        string='Lý do không đủ điều kiện',
        copy=False,
    )
    eligibility_checked_at = fields.Datetime(
        string='Xét điều kiện lúc',
        copy=False,
    )

    def _compute_exam_eligibility(self):
        """Xét điều kiện dự thi theo tỷ lệ vắng trên các phiếu đã xác nhận.

        Ghi bằng sudo (giảng viên chỉ có quyền đọc enrollment); người gọi phải
        kiểm tra quyền trước.
        """
        threshold = self._get_max_absence_rate()
        counts = self._get_attendance_counts()
        now = fields.Datetime.now()
        eligible = self.browse()
        newly_ineligible = self.browse()
        for rec in self:
            total, absent = counts.get(rec.id, (0, 0))
            rate = absent / total * 100 if total else 0.0
            if rate > threshold:
                # F4: chỉ báo khi chuyển từ đủ điều kiện sang không đủ (không báo lặp).
                if rec.sudo().exam_eligible:
                    newly_ineligible |= rec
                rec.sudo().write({
                    'exam_eligible': False,
                    'exam_ineligible_reason': (
                        f'Vắng {absent}/{total} buổi ({rate:.1f}%) vượt ngưỡng {threshold:g}%'
                    ),
                    'eligibility_checked_at': now,
                })
            else:
                eligible |= rec
        if eligible:
            eligible.sudo().write({
                'exam_eligible': True,
                'exam_ineligible_reason': False,
                'eligibility_checked_at': now,
            })
        newly_ineligible._notify_exam_ineligible()
        return True

    def _notify_exam_ineligible(self):
        Notice = self.env['univ.sms.student.notice']
        for rec in self.sudo():
            subject = rec.subject_id.name or rec.class_id.name or ''
            Notice._notify(
                rec.student_id, 'exam_ineligible',
                _('Không đủ điều kiện dự thi môn %s') % subject,
                _('Lớp %(klass)s: %(reason)s. Liên hệ giảng viên hoặc phòng đào tạo '
                  'nếu bạn có minh chứng vắng có phép.',
                  klass=rec.class_id.name or subject, reason=rec.exam_ineligible_reason or ''),
                rec)


class UnivSmsClass(models.Model):
    _inherit = 'univ.sms.class'

    exam_ineligible_count = fields.Integer(
        string='SV không đủ điều kiện thi',
        compute='_compute_exam_ineligible_count',
    )

    def _compute_exam_ineligible_count(self):
        Enrollment = self.env['univ.sms.enrollment'].sudo()
        for record in self:
            record.exam_ineligible_count = Enrollment.search_count([
                ('class_id', '=', record.id),
                ('state', '=', 'registered'),
                ('exam_eligible', '=', False),
            ]) if record.id else 0

    def _recompute_exam_eligibility(self):
        """Tính lại điều kiện dự thi cho các đăng ký 'registered' của lớp. Trả về enrollment."""
        # Người gọi phải đọc được lớp (giảng viên lớp / phòng đào tạo).
        self.check_access_rights('read')
        self.check_access_rule('read')
        enrollments = self.env['univ.sms.enrollment'].sudo().search([
            ('class_id', 'in', self.ids),
            ('state', '=', 'registered'),
        ])
        enrollments._compute_exam_eligibility()
        return enrollments

    def action_compute_exam_eligibility(self):
        enrollments = self._recompute_exam_eligibility()
        ineligible = enrollments.filtered(lambda e: not e.exam_eligible)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Xét điều kiện dự thi',
                'message': (
                    f'Đã xét {len(enrollments)} sinh viên: '
                    f'{len(enrollments) - len(ineligible)} đủ điều kiện, '
                    f'{len(ineligible)} không đủ điều kiện.'
                ),
                'type': 'warning' if ineligible else 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            },
        }

    def action_view_exam_ineligible(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Không đủ điều kiện thi - {self.name}',
            'res_model': 'univ.sms.enrollment',
            'view_mode': 'tree,form',
            'domain': [('class_id', '=', self.id), ('state', '=', 'registered'),
                       ('exam_eligible', '=', False)],
        }
