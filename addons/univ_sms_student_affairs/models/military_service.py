from odoo import models, fields


class UnivSmsMilitaryService(models.Model):
    _name = 'univ.sms.military.service'
    _description = 'Khai báo nghĩa vụ quân sự'
    _order = 'student_id'

    student_id = fields.Many2one('univ.sms.student', required=True)
    registration_status = fields.Selection([
        ('not_registered', 'Chưa đăng ký NVQS'),
        ('registered', 'Đã đăng ký'),
        ('deferred', 'Tạm hoãn (đang học)'),
        ('completed', 'Đã hoàn thành NVQS'),
    ], required=True)
    local_authority_id = fields.Many2one('res.country.state', string='Đơn vị quản lý')
    document_attachment_ids = fields.Many2many('ir.attachment', string='Hồ sơ kèm')
    declared_date = fields.Date(default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Chờ duyệt'),
        ('submitted', 'Đã nộp'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Bị từ chối'),
    ], default='draft')

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_draft(self):
        self.write({'state': 'draft'})