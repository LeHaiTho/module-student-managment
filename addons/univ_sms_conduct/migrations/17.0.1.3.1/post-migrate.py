"""Tính lại xếp loại rèn luyện cho dữ liệu cũ: chỉ phiếu khoa đã duyệt mới có xếp loại.

Odoo không tự tính lại field compute đã lưu khi chỉ đổi logic tính, nên phải làm ở migration.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    scores = env['univ.sms.conduct.score'].search([])
    env.add_to_compute(scores._fields['classification'], scores)
    scores.flush_recordset(['classification'])
