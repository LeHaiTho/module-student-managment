"""Render 6 báo cáo QWeb (có dữ liệu và rỗng) + dashboard read_group theo nhóm quyền."""
from odoo.tests import TransactionCase, tagged

from .common import ReportDataMixin

REPORTS = {
    'transcript': 'univ_sms_report.action_report_student_transcript',
    'registration_slip': 'univ_sms_report.action_report_registration_slip',
    'attendance_sheet': 'univ_sms_report.action_report_attendance_sheet',
    'conduct_score': 'univ_sms_report.action_report_conduct_score',
    'certificate': 'univ_sms_report.action_report_certificate',
    'invoice': 'univ_sms_report.action_report_student_fee_invoice',
}


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_report')
class TestReports(ReportDataMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_report_data()
        env = cls.env
        cls.sheet = env['univ.sms.attendance.sheet'].create({
            'class_id': cls.class_a.id, 'attendance_date': '2039-10-01'})
        cls.sheet.action_load_students()
        cls.empty_sheet = env['univ.sms.attendance.sheet'].create({
            'class_id': cls.class_b.id, 'attendance_date': '2039-10-02'})
        criteria = env['univ.sms.conduct.criteria'].create({
            'name': 'Tiêu chí BC', 'group_name': 'discipline', 'max_score': 25})
        cls.conduct = env['univ.sms.conduct.score'].create({
            'student_id': cls.st1.id, 'period_id': cls.term.id,
            'line_ids': [(0, 0, {'criteria_id': criteria.id, 'self_score': 20,
                                 'advisor_score': 20, 'final_score': 19})]})
        cls.empty_conduct = env['univ.sms.conduct.score'].create({
            'student_id': cls.st_empty.id, 'period_id': cls.term.id})
        ctype = env['univ.sms.certificate.type'].create({'name': 'Giấy xác nhận BC', 'code': 'BC_GXN'})
        cls.cert = env['univ.sms.certificate.request'].create({
            'student_id': cls.st1.id, 'certificate_type_id': ctype.id, 'reason': 'Vay vốn'})
        cls.empty_cert = env['univ.sms.certificate.request'].create({
            'student_id': cls.st_empty.id, 'certificate_type_id': ctype.id})
        cls.move = env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': cls.st1.partner_id.id,
            'invoice_line_ids': [(0, 0, {'name': 'Học phí BC', 'quantity': 3, 'price_unit': 500000})],
        }) if env['account.journal'].search_count(
            [('type', '=', 'sale'), ('company_id', '=', env.company.id)]) else env['account.move']
        cls.empty_move = env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': cls.st_empty.partner_id.id,
        }) if cls.move else env['account.move']

    def _render(self, key, records):
        report = self.env.ref(REPORTS[key])
        html, _fmt = report._render_qweb_html(report.report_name, records.ids)
        return html.decode() if isinstance(html, bytes) else html

    def test_transcript(self):
        html = self._render('transcript', self.st1)
        self.assertIn('BẢNG ĐIỂM SINH VIÊN', html)
        self.assertIn('Môn BC A', html)
        self.assertNotIn('Môn BC B', html, 'Bảng điểm lộ điểm của SV khác')
        html = self._render('transcript', self.st_empty)
        self.assertIn('Chưa có dữ liệu điểm số', html)

    def test_transcript_as_lecturer_only_own_class(self):
        # Giảng viên lớp B in bảng điểm SV1 (học lớp A): không thấy điểm lớp A
        report = self.env.ref(REPORTS['transcript']).with_user(self.lecturer_b)
        html, _fmt = report._render_qweb_html(report.report_name, self.st1.ids)
        html = html.decode()
        self.assertIn('BẢNG ĐIỂM SINH VIÊN', html)
        self.assertNotIn('Môn BC A', html)

    def test_registration_slip(self):
        html = self._render('registration_slip', self.st1)
        self.assertIn('SV BC 1', html)
        html = self._render('registration_slip', self.st_empty)
        self.assertIn('SV BC rỗng', html)

    def test_attendance_sheet(self):
        html = self._render('attendance_sheet', self.sheet)
        self.assertIn('BẢNG ĐIỂM DANH', html)
        self.assertIn('SV BC 1', html)
        self.assertNotIn('SV BC 3', html)
        html = self._render('attendance_sheet', self.empty_sheet)
        self.assertIn('BẢNG ĐIỂM DANH', html)

    def test_conduct_score(self):
        html = self._render('conduct_score', self.conduct)
        self.assertIn('Tiêu chí BC', html)
        html = self._render('conduct_score', self.empty_conduct)
        self.assertIn('SV BC rỗng', html)

    def test_certificate(self):
        html = self._render('certificate', self.cert)
        self.assertIn('Giấy xác nhận BC', html)
        self.assertIn('Vay vốn', html)
        html = self._render('certificate', self.empty_cert)
        self.assertIn('SV BC rỗng', html)

    def test_invoice(self):
        if not self.move:
            self.skipTest('Chưa có sổ bán hàng')
        html = self._render('invoice', self.move)
        self.assertIn('BIÊN LAI THU HỌC PHÍ', html)
        self.assertIn('Học phí BC', html)
        html = self._render('invoice', self.empty_move)
        self.assertIn('BIÊN LAI THU HỌC PHÍ', html)

    def test_dashboards_read_group(self):
        dashboards = [
            ('univ_sms_report.action_student_dashboard', ['program_id', 'state']),
            ('univ_sms_report.action_attendance_dashboard', ['class_id', 'state']),
            ('univ_sms_report.action_exam_dashboard', ['exam_id']),
            ('univ_sms_report.action_fee_dashboard', ['term_id', 'state']),
            ('univ_sms_report.action_registration_dashboard', ['period_id', 'state']),
            ('univ_sms_report.action_conduct_dashboard', ['classification', 'period_id']),
        ]
        conduct_menu = self.env.ref('univ_sms_report.menu_conduct_dashboard')
        for user in (self.officer, self.advisor, self.dean, self.finance, self.affairs,
                     self.lecturer_a, self.sms_admin):
            for xmlid, groupby in dashboards:
                if xmlid.endswith('conduct_dashboard') and not (conduct_menu.groups_id & user.groups_id):
                    continue  # menu ẩn với nhóm không có quyền xem rèn luyện
                action = self.env.ref(xmlid)
                Model = self.env[action.res_model].with_user(user)
                groups = Model.read_group([], ['__count'], groupby, lazy=False)
                self.assertIsInstance(groups, list, '%s / %s' % (user.login, xmlid))
                # Các view của action (graph/pivot/list) tải được
                for mode in action.view_mode.split(','):
                    Model.get_views([(False, mode)])
        # Cố vấn chỉ thấy điểm của SV mình cố vấn trong dashboard điểm thi
        Result = self.env['univ.sms.exam.result'].with_user(self.advisor)
        groups = Result.read_group([('exam_id', 'in', (self.exam_a | self.exam_b).ids)],
                                   ['__count'], ['exam_id'], lazy=False)
        self.assertEqual(sum(g['__count'] for g in groups), 2)
