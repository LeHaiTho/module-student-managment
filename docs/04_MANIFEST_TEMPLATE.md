# addons/univ_sms_base/__manifest__.py
{
    'name': 'University SMS - Base',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Core master data for University Student Management System',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/academic_period_data.xml',
        'views/faculty_views.xml',
        'views/department_views.xml',
        'views/program_views.xml',
        'views/subject_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
}
Quy ước: mỗi module phụ thuộc đều khai báo rõ trong depends. Thứ tự load: univ_sms_base → univ_sms_student → univ_sms_class → univ_sms_attendance → univ_sms_exam → univ_sms_fee → univ_sms_portal → univ_sms_report.