{
    'name': 'University SMS - Survey',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Khảo sát sinh viên (hội nhập, hài lòng, FEEDBACK)',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'univ_sms_base', 'univ_sms_student'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'views/survey_type_views.xml',
        'views/survey_instance_views.xml',
        'views/survey_response_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
}
