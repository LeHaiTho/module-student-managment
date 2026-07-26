{
    'name': 'University SMS - Conduct Score',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Đánh giá rèn luyện sinh viên (workflow 3 cấp)',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'univ_sms_base', 'univ_sms_student', 'univ_sms_class'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'data/conduct_criteria_data.xml',
        'views/conduct_criteria_views.xml',
        'views/conduct_score_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
}
