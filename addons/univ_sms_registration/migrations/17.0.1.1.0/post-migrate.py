"""F1: liên kết đăng ký đang chiếm chỗ với enrollment (backfill enrollment_id).

- Đăng ký 'registered'/'confirmed' chưa có enrollment_id: gắn enrollment
  (student, subject, term) sẵn có, nếu chưa có thì tạo (qua _sync_enrollment).
- Chạy lại an toàn: chỉ xử lý bản ghi chưa có enrollment_id.
"""
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    regs = env['univ.sms.registration'].search([
        ('state', 'in', ('registered', 'confirmed')),
        ('enrollment_id', '=', False),
    ])
    regs._sync_enrollment()
    _logger.info('univ_sms_registration 17.0.1.1.0: synced enrollment for %s registrations', len(regs))
