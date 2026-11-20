from odoo import _, models
from odoo.exceptions import UserError


class UnivSmsWorkflowGuardMixin(models.AbstractModel):
    """Kiểm tra chuyển trạng thái phía server (không chỉ ẩn nút ở view)."""
    _name = 'univ.sms.workflow.guard.mixin'
    _description = 'Kiểm tra chuyển trạng thái'

    def _check_states(self, allowed, action_label):
        labels = dict(self._fields['state'].selection)
        for rec in self:
            if rec.state not in allowed:
                raise UserError(_('Không thể %(action)s bản ghi ở trạng thái "%(state)s".',
                                  action=action_label, state=labels.get(rec.state, rec.state)))
