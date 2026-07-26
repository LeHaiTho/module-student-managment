{
    'name': 'University SMS - Feedback',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Phản hồi/Góp ý của sinh viên',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'univ_sms_base', 'univ_sms_student'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'views/feedback_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
}
