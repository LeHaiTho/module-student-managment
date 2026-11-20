"""FEE03: tạo hóa đơn kế toán (account.move) từ hóa đơn học phí."""
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_fee')
class TestFeeAccountMove(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        faculty = env['univ.sms.faculty'].create({'name': 'Khoa KT', 'code': 'KKTAM'})
        dept = env['univ.sms.department'].create({'name': 'BM KT', 'code': 'BMKTAM', 'faculty_id': faculty.id})
        program = env['univ.sms.program'].create({'name': 'Ngành KT', 'code': 'NKTAM', 'department_id': dept.id})
        year = env['univ.sms.academic.year'].create({
            'name': 'AM', 'date_start': '2037-09-01', 'date_end': '2038-08-31'})
        cls.term = env['univ.sms.term'].create({
            'name': 'HK AM', 'academic_year_id': year.id, 'date_start': '2037-09-01', 'date_end': '2038-01-15'})
        cls.student = env['univ.sms.student'].create({'name': 'SV AM', 'program_id': program.id})
        cls.fee = env['univ.sms.fee'].create({'student_id': cls.student.id, 'term_id': cls.term.id})
        cls.finance = new_test_user(
            env, login='am_finance', groups='base.group_user,univ_sms_base.group_univ_finance_office')
        cls.lecturer = new_test_user(
            env, login='am_lecturer', groups='base.group_user,univ_sms_base.group_univ_lecturer')

    def _invoice(self, lines=True):
        invoice = self.env['univ.sms.fee.invoice'].create({
            'fee_id': self.fee.id, 'student_id': self.student.id,
            'partner_id': self.student.partner_id.id, 'term_id': self.term.id,
            'amount_total': 1500000,
        })
        if lines:
            self.env['univ.sms.fee.invoice.line'].create([
                {'invoice_id': invoice.id, 'name': 'Môn A', 'quantity': 3, 'price_unit': 300000},
                {'invoice_id': invoice.id, 'name': 'Môn B', 'quantity': 2, 'price_unit': 300000},
            ])
        invoice.action_confirm()
        return invoice

    def _has_sale_journal(self, company):
        return bool(self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1))

    def test_create_out_invoice_with_lines_idempotent(self):
        if not self._has_sale_journal(self.env.company):
            self.skipTest('Công ty chính chưa có sổ bán hàng (chưa cài hệ thống tài khoản)')
        invoice = self._invoice()
        action = invoice.with_user(self.finance).action_create_account_move()
        move = invoice.account_move_id
        self.assertTrue(move)
        self.assertEqual(action['res_id'], move.id)
        self.assertEqual(move.move_type, 'out_invoice')
        self.assertEqual(move.partner_id, self.student.partner_id)
        self.assertEqual(move.journal_id.type, 'sale')
        self.assertEqual(sorted(move.invoice_line_ids.mapped('name')), ['Môn A', 'Môn B'])
        self.assertEqual(sorted(move.invoice_line_ids.mapped('quantity')), [2.0, 3.0])
        self.assertAlmostEqual(sum(move.invoice_line_ids.mapped('price_subtotal')), 1500000)
        # Gọi lại: không tạo thêm
        count = self.env['account.move'].search_count([])
        action2 = invoice.action_create_account_move()
        self.assertEqual(action2['res_id'], move.id)
        self.assertEqual(self.env['account.move'].search_count([]), count)

    def test_create_without_lines_uses_total(self):
        if not self._has_sale_journal(self.env.company):
            self.skipTest('Công ty chính chưa có sổ bán hàng (chưa cài hệ thống tài khoản)')
        invoice = self._invoice(lines=False)
        invoice.action_create_account_move()
        line = invoice.account_move_id.invoice_line_ids
        self.assertEqual(len(line), 1)
        self.assertAlmostEqual(line.price_subtotal, 1500000)

    def test_refused_without_sale_journal(self):
        company = self.env['res.company'].create({'name': 'Trường chưa có kế toán'})
        self.env.user.company_ids |= company
        if self._has_sale_journal(company):
            self.skipTest('Công ty mới được tự cài hệ thống tài khoản')
        invoice = self._invoice()
        with self.assertRaises(UserError) as ctx:
            invoice.with_company(company).action_create_account_move()
        self.assertIn('sổ nhật ký bán hàng', str(ctx.exception))
        self.assertFalse(invoice.account_move_id)

    def test_refused_for_draft_invoice_and_lecturer(self):
        invoice = self._invoice()
        invoice.action_reset()
        with self.assertRaises(UserError):
            invoice.action_create_account_move()
        invoice.action_confirm()
        with self.assertRaises(UserError):
            invoice.with_user(self.lecturer).action_create_account_move()
        self.assertFalse(invoice.account_move_id)
