{
    'name': 'University SMS - Notification',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Thông báo từ ban quản trị',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'univ_sms_base', 'univ_sms_student', 'univ_sms_class'],
    'data': [
        'security/ir.model.access.csv',
        'views/notification_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
}