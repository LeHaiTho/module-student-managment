{
    'name': 'University SMS - Reports & Dashboard',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'PDF Reports & Dashboard for University Student Management System',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': [
        'univ_sms_student', 'univ_sms_exam', 'univ_sms_fee', 'account',
        'univ_sms_attendance', 'univ_sms_registration', 'univ_sms_conduct',
        'univ_sms_certificate', 'univ_sms_student_affairs',
    ],
    'data': [
        # Dashboard views
        'views/student_dashboard_views.xml',
        'views/attendance_dashboard_views.xml',
        'views/exam_dashboard_views.xml',
        'views/fee_dashboard_views.xml',
        'views/registration_dashboard_views.xml',
        'views/conduct_dashboard_views.xml',
        'views/dashboard_menu_views.xml',
        # QWeb PDF Reports
        'reports/transcript_report.xml',
        'reports/invoice_report.xml',
        'reports/conduct_score_report.xml',
        'reports/certificate_report.xml',
        'reports/registration_slip_report.xml',
        'reports/attendance_sheet_report.xml',
    ],
    'installable': True,
    'application': False,
}
