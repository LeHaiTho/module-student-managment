from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_notification')
class TestNotification(TransactionCase):

    def test_expire_after_publish(self):
        Notif = self.env['univ.sms.notification']
        now = fields.Datetime.now()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            Notif.create({'title': 'Sai', 'content': '<p>x</p>',
                          'publish_date': now, 'expire_date': now - timedelta(days=1)})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            Notif.create({'title': 'Bằng', 'content': '<p>x</p>',
                          'publish_date': now, 'expire_date': now})
        ok = Notif.create({'title': 'Đúng', 'content': '<p>x</p>',
                           'publish_date': now, 'expire_date': now + timedelta(days=3)})
        ok.action_publish()
        self.assertEqual(ok.state, 'published')
        # Đăng một thông báo đã hết hạn: publish_date mới > expire_date -> từ chối
        old = Notif.create({'title': 'Cũ', 'content': '<p>x</p>',
                            'publish_date': now - timedelta(days=10),
                            'expire_date': now - timedelta(days=5)})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            old.action_publish()

    def test_workflow_guards(self):
        n = self.env['univ.sms.notification'].create({'title': 'T', 'content': '<p>x</p>'})
        with self.assertRaises(UserError):
            n.action_archive()
        with self.assertRaises(UserError):
            n.action_draft()
        n.action_publish()
        with self.assertRaises(UserError):
            n.action_publish()
        n.action_archive()
        n.action_publish()
        self.assertEqual(n.state, 'published')
