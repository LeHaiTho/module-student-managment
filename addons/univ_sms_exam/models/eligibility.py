from odoo import api, fields, models


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
        for rec in self:
            total, absent = counts.get(rec.id, (0, 0))
            rate = absent / total * 100 if total else 0.0
            if rate > threshold:
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
        return True


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
