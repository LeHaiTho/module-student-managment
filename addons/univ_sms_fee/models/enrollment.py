from odoo import api, models

_FEE_FIELDS = ('state', 'student_id', 'term_id', 'subject_id')


class UnivSmsEnrollmentFee(models.Model):
    """Enrollment đổi (tạo / đổi trạng thái / xóa) thì tính lại học phí của (sinh viên, học kỳ)."""
    _inherit = 'univ.sms.enrollment'

    def _fee_keys(self):
        return {(rec.student_id.id, rec.term_id.id) for rec in self}

    def _recompute_fees(self, keys):
        self.env['univ.sms.fee'].sudo()._recompute_for_student_terms(keys)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._recompute_fees(records._fee_keys())
        return records

    def write(self, vals):
        if not any(f in vals for f in _FEE_FIELDS):
            return super().write(vals)
        keys = self._fee_keys()
        res = super().write(vals)
        self._recompute_fees(keys | self._fee_keys())
        return res

    def unlink(self):
        keys = self._fee_keys()
        res = super().unlink()
        self._recompute_fees(keys)
        return res
