from odoo import models, fields, api
from odoo.exceptions import UserError


class UnivSmsFee(models.Model):
    _name = 'univ.sms.fee'
    _description = 'Học phí sinh viên'
    _order = 'student_id, term_id'

    name = fields.Char(
        string='Tên khoản phí',
        compute='_compute_name',
        store=True,
    )
    student_id = fields.Many2one(
        'univ.sms.student',
        string='Sinh viên',
        required=True,
    )
    term_id = fields.Many2one(
        'univ.sms.term',
        string='Học kỳ',
        required=True,
    )
    fee_per_credit = fields.Monetary(
        string='Đơn giá/tín chỉ',
        currency_field='currency_id',
        required=True,
        default=500000.0,
    )
    total_credits = fields.Integer(
        string='Tổng số tín chỉ',
        compute='_compute_total_credits',
        store=True,
    )
    total_amount = fields.Monetary(
        string='Tổng học phí',
        currency_field='currency_id',
        compute='_compute_total_amount',
        store=True,
    )
    paid_amount = fields.Monetary(
        string='Đã thanh toán',
        currency_field='currency_id',
        compute='_compute_paid_amount',
        store=True,
    )
    remaining_amount = fields.Monetary(
        string='Còn lại',
        currency_field='currency_id',
        compute='_compute_remaining_amount',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Đơn vị tiền tệ',
        default=lambda self: self.env['res.currency'].with_context(active_test=False).search(
            [('name', '=', 'VND')], limit=1
        ) or self.env.company.currency_id,
    )
    invoice_ids = fields.One2many(
        'univ.sms.fee.invoice',
        'fee_id',
        string='Hóa đơn',
    )
    state = fields.Selection([
        ('draft', 'Dự kiến'),
        ('invoiced', 'Đã lập hóa đơn'),
        ('paid', 'Đã thanh toán'),
    ], string='Trạng thái', default='draft', compute='_compute_state', store=True)

    _sql_constraints = [
        (
            'fee_uniq',
            'unique(student_id, term_id)',
            'Đã có học phí cho sinh viên và học kỳ này!',
        ),
    ]

    @api.depends('student_id', 'term_id')
    def _compute_name(self):
        for record in self:
            student_name = record.student_id.name or ''
            term_name = record.term_id.name or ''
            record.name = f'{student_name} - {term_name}'

    @api.depends('student_id', 'term_id')
    def _compute_total_credits(self):
        Enrollment = self.env['univ.sms.enrollment']
        for record in self:
            if record.student_id and record.term_id:
                enrollments = Enrollment.search([
                    ('student_id', '=', record.student_id.id),
                    ('term_id', '=', record.term_id.id),
                    ('state', '=', 'registered'),
                ])
                record.total_credits = sum(
                    enr.subject_id.credit for enr in enrollments
                )
            else:
                record.total_credits = 0

    @api.depends('fee_per_credit', 'total_credits')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.fee_per_credit * record.total_credits

    @api.depends('invoice_ids', 'invoice_ids.state', 'invoice_ids.amount_total')
    def _compute_paid_amount(self):
        for record in self:
            paid = sum(
                inv.amount_total for inv in record.invoice_ids
                if inv.state == 'paid'
            )
            record.paid_amount = paid

    @api.depends('total_amount', 'paid_amount')
    def _compute_remaining_amount(self):
        for record in self:
            record.remaining_amount = record.total_amount - record.paid_amount

    @api.depends('invoice_ids.state')
    def _compute_state(self):
        for record in self:
            if not record.invoice_ids:
                record.state = 'draft'
            elif all(inv.state == 'paid' for inv in record.invoice_ids):
                record.state = 'paid'
            else:
                record.state = 'invoiced'

    def action_create_invoice(self):
        """Tạo hóa đơn cho học phí"""
        self.ensure_one()
        if not self.student_id or not self.student_id.partner_id:
            raise UserError('Sinh viên chưa có đối tác liên hệ!')

        invoice_vals = {
            'fee_id': self.id,
            'student_id': self.student_id.id,
            'partner_id': self.student_id.partner_id.id,
            'term_id': self.term_id.id,
            'amount_total': self.total_amount,
        }
        invoice = self.env['univ.sms.fee.invoice'].create(invoice_vals)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hóa đơn',
            'res_model': 'univ.sms.fee.invoice',
            'view_mode': 'form',
            'res_id': invoice.id,
        }


class UnivSmsFeeInvoice(models.Model):
    _name = 'univ.sms.fee.invoice'
    _description = 'Hóa đơn học phí'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(
        string='Số hóa đơn',
        readonly=True,
        copy=False,
        default='New',
    )
    fee_id = fields.Many2one(
        'univ.sms.fee',
        string='Khoản học phí',
        required=True,
    )
    student_id = fields.Many2one(
        'univ.sms.student',
        string='Sinh viên',
        required=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Đối tác',
        required=True,
    )
    term_id = fields.Many2one(
        'univ.sms.term',
        string='Học kỳ',
        required=True,
    )
    invoice_date = fields.Date(
        string='Ngày lập hóa đơn',
        default=fields.Date.today,
    )
    amount_total = fields.Monetary(
        string='Tổng tiền',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Đơn vị tiền tệ',
        default=lambda self: self.env['res.currency'].with_context(active_test=False).search(
            [('name', '=', 'VND')], limit=1
        ) or self.env.company.currency_id,
    )
    line_ids = fields.One2many(
        'univ.sms.fee.invoice.line',
        'invoice_id',
        string='Chi tiết hóa đơn',
    )
    account_move_id = fields.Many2one(
        'account.move',
        string='Hóa đơn kế toán',
        readonly=True,
        copy=False,
    )
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Đã xác nhận'),
        ('paid', 'Đã thanh toán'),
        ('cancel', 'Đã hủy'),
    ], string='Trạng thái', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('univ.sms.fee.invoice') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'

    def action_paid(self):
        for record in self:
            record.state = 'paid'

    def action_cancel(self):
        for record in self:
            record.state = 'cancel'

    def action_reset(self):
        for record in self:
            record.state = 'draft'

    def action_create_account_move(self):
        """Tạo hóa đơn kế toán (account.move)"""
        self.ensure_one()
        if self.account_move_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Hóa đơn kế toán',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': self.account_move_id.id,
            }

        move_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': self.invoice_date,
        }
        move = self.env['account.move'].create(move_vals)

        if self.line_ids:
            for line in self.line_ids:
                self.env['account.move.line'].create({
                    'move_id': move.id,
                    'name': line.name,
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                })

        self.account_move_id = move.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hóa đơn kế toán',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': move.id,
        }


class UnivSmsFeeInvoiceLine(models.Model):
    _name = 'univ.sms.fee.invoice.line'
    _description = 'Chi tiết hóa đơn học phí'

    invoice_id = fields.Many2one(
        'univ.sms.fee.invoice',
        string='Hóa đơn',
        required=True,
        ondelete='cascade',
    )
    name = fields.Char(string='Mô tả', required=True)
    subject_id = fields.Many2one(
        'univ.sms.subject',
        string='Môn học',
    )
    credit = fields.Integer(string='Số tín chỉ')
    quantity = fields.Float(string='Số lượng', default=1.0)
    price_unit = fields.Monetary(
        string='Đơn giá',
        currency_field='currency_id',
    )
    price_subtotal = fields.Monetary(
        string='Thành tiền',
        currency_field='currency_id',
        compute='_compute_price_subtotal',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Đơn vị tiền tệ',
        related='invoice_id.currency_id',
    )

    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        for record in self:
            record.price_subtotal = record.quantity * record.price_unit
