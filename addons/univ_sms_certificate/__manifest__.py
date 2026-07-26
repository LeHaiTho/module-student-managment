{
    'name': 'University SMS - Certificate',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Giấy chứng nhận sinh viên (bản sao VBCC, giấy xác nhận SV, xác nhận công nhận)',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'univ_sms_base', 'univ_sms_student'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'views/certificate_type_views.xml',
        'views/certificate_request_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
}
