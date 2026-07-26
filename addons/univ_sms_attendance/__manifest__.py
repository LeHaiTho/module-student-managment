{
    'name': 'University SMS - Attendance',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Quản lý điểm danh sinh viên',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['univ_sms_class'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'data/admin_user_data.xml',
        'views/attendance_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
