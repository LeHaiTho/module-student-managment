{
    'name': 'University SMS - Student Affairs',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Phòng Công tác Sinh viên: BHYT, Ngoại trú, NVQS',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'univ_sms_base', 'univ_sms_student'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'views/health_insurance_views.xml',
        'views/residence_info_views.xml',
        'views/military_service_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
}
