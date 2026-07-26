{
    'name': 'University SMS - Class',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Quản lý lớp học và thời khóa biểu',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['univ_sms_student'],
    'data': [
        'security/ir.model.access.csv',
        'data/admin_user_data.xml',
        'views/class_views.xml',
        'views/timetable_views.xml',
        'views/enrollment_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
