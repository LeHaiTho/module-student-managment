from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_certificate')
class TestCertificateRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        faculty = env['univ.sms.faculty'].create({'name': 'Khoa GCN', 'code': 'KGCN'})
        dept = env['univ.sms.department'].create({'name': 'BM GCN', 'code': 'BMGCN', 'faculty_id': faculty.id})
        program = env['univ.sms.program'].create({'name': 'Ngành GCN', 'code': 'NGCN', 'department_id': dept.id})
        cls.student = env['univ.sms.student'].create({'name': 'SV GCN', 'program_id': program.id})
        Type = env['univ.sms.certificate.type']
        cls.ctype = Type.create({'name': 'Giấy xác nhận SV', 'code': 'GCN_SV'})
        cls.ctype2 = Type.create({'name': 'Bảng điểm', 'code': 'GCN_BD'})
        cls.inactive = Type.create({'name': 'Ngừng nhận', 'code': 'GCN_OFF', 'active': False})

    def _req(self, ctype=None):
        return self.env['univ.sms.certificate.request'].create({
            'student_id': self.student.id, 'certificate_type_id': (ctype or self.ctype).id,
            'reason': 'Bổ sung hồ sơ'})

    def test_workflow_guards(self):
        req = self._req()
        with self.assertRaises(UserError):
            req.action_complete()
        with self.assertRaises(UserError):
            req.action_draft()
        req.action_approve()
        with self.assertRaises(UserError):
            req.action_approve()
        req.action_complete()
        self.assertEqual(req.state, 'completed')
        with self.assertRaises(UserError):
            req.action_reject()

    def test_reject_from_draft_and_approved(self):
        r1 = self._req()
        r1.action_reject()
        r2 = self._req()
        r2.action_approve()
        r2.action_reject()
        self.assertEqual((r1 | r2).mapped('state'), ['rejected', 'rejected'])

    def test_duplicate_pending_refused(self):
        req = self._req()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self._req()
        req.action_approve()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self._req()
        # Loại khác thì được
        self._req(self.ctype2)
        # Sau khi hoàn thành có thể yêu cầu lại
        req.action_complete()
        again = self._req()
        again.action_reject()
        self._req()
        # Không mở lại yêu cầu bị từ chối khi đang có yêu cầu khác cùng loại
        with self.assertRaises(ValidationError), self.cr.savepoint():
            again.action_draft()

    def test_inactive_type_refused(self):
        with self.assertRaises(ValidationError):
            self._req(self.inactive)
