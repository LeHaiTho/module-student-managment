import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


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
    # Không còn là field compute: được tính lại chủ động mỗi khi enrollment của
    # (sinh viên, học kỳ) thay đổi, và CHỈ khi khoản phí còn 'draft' (xem
    # _recompute_total_credits). Khoản phí đã lập hóa đơn giữ nguyên số tín chỉ/số tiền.
    total_credits = fields.Integer(
        string='Tổng số tín chỉ',
        readonly=True,
        default=0,
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
    due_date = fields.Date(
        string='Hạn thanh toán',
        help='Quá hạn mà còn nợ sẽ phát sinh cảnh báo sớm về học phí.',
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

    # ─── Tín chỉ học phí (F1, schema 2.6) ─────────────────────────────────
    def _get_enrolled_credits(self):
        """Tổng tín chỉ các enrollment còn hiệu lực (không tính 'cancelled')."""
        self.ensure_one()
        if not self.student_id or not self.term_id:
            return 0
        enrollments = self.env['univ.sms.enrollment'].sudo().search([
            ('student_id', '=', self.student_id.id),
            ('term_id', '=', self.term_id.id),
            ('state', '!=', 'cancelled'),
        ])
        return int(round(sum(enrollments.mapped('subject_id.credit'))))

    def _recompute_total_credits(self):
        """Tính lại tổng tín chỉ cho khoản phí còn 'draft'.

        Khoản phí đã lập hóa đơn / đã thanh toán thì KHÔNG đổi số tiền. Model
        univ.sms.fee không có mail.thread nên không ghi chatter; chỉ ghi log server
        khi số tín chỉ thực tế lệch với số đã chốt.
        """
        for fee in self:
            credits = fee._get_enrolled_credits()
            if fee.state != 'draft':
                if credits != fee.total_credits:
                    _logger.info(
                        'Fee %s (%s) đã lập hóa đơn: giữ nguyên %s TC, enrollment hiện có %s TC.',
                        fee.id, fee.state, fee.total_credits, credits)
                continue
            if fee.total_credits != credits:
                fee.total_credits = credits

    # Giữ tên cũ để các script seed/mock gọi trực tiếp vẫn chạy.
    def _compute_total_credits(self):
        self._recompute_total_credits()

    @api.model
    def _recompute_for_student_terms(self, keys):
        """keys: iterable (student_id, term_id). Tính lại các khoản phí tương ứng."""
        keys = {(s, t) for s, t in keys if s and t}
        if not keys:
            return
        fees = self.sudo().search([
            ('student_id', 'in', list({k[0] for k in keys})),
            ('term_id', 'in', list({k[1] for k in keys})),
        ]).filtered(lambda f: (f.student_id.id, f.term_id.id) in keys)
        fees._recompute_total_credits()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._recompute_total_credits()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'student_id' in vals or 'term_id' in vals:
            self._recompute_total_credits()
        return res

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

        existing = self.invoice_ids.filtered(lambda inv: inv.state != 'cancel')[:1]
        if existing:
            # Không tạo hóa đơn trùng: trả về hóa đơn còn hiệu lực.
            return {
                'type': 'ir.actions.act_window',
                'name': 'Hóa đơn',
                'res_model': 'univ.sms.fee.invoice',
                'view_mode': 'form',
                'res_id': existing.id,
            }
        self._recompute_total_credits()
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
