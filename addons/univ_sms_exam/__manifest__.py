{
    'name': 'University SMS - Exam',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Quản lý kỳ thi, điểm số và bảng điểm',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['univ_sms_attendance', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/admin_user_data.xml',
        'views/exam_views.xml',
        'views/exam_result_views.xml',
        'views/transcript_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
