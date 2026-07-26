univ_sms/                              # repo root
├── docker-compose.yml
├── odoo.conf
├── addons/
│   ├── univ_sms_base/
│   │   ├── __init__.py
│   │   ├── __manifest__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── faculty.py            # univ.sms.faculty
│   │   │   ├── department.py         # univ.sms.department
│   │   │   ├── program.py            # univ.sms.program
│   │   │   ├── subject.py            # univ.sms.subject
│   │   │   └── academic_period.py    # univ.sms.academic.year / .term
│   │   ├── security/
│   │   │   ├── ir.model.access.csv
│   │   │   └── security_groups.xml
│   │   ├── views/
│   │   │   ├── faculty_views.xml
│   │   │   ├── department_views.xml
│   │   │   ├── program_views.xml
│   │   │   ├── subject_views.xml
│   │   │   └── menu_views.xml
│   │   └── data/
│   │       └── academic_period_data.xml
│   │
│   ├── univ_sms_student/
│   │   ├── __init__.py
│   │   ├── __manifest__.py
│   │   ├── models/
│   │   │   ├── student.py            # univ.sms.student
│   │   │   ├── enrollment.py         # univ.sms.enrollment
│   │   │   └── res_partner.py        # _inherit res.partner (link portal)
│   │   ├── security/
│   │   ├── views/
│   │   ├── data/
│   │   └── wizard/
│   │       └── enrollment_wizard.py
│   │
│   ├── univ_sms_class/
│   │   ├── models/
│   │   │   ├── class_batch.py        # univ.sms.class
│   │   │   └── timetable.py          # univ.sms.timetable
│   │   └── ...
│   │
│   ├── univ_sms_attendance/
│   │   ├── models/
│   │   │   └── attendance.py         # univ.sms.attendance.sheet / .line
│   │   └── ...
│   │
│   ├── univ_sms_exam/
│   │   ├── models/
│   │   │   ├── exam.py               # univ.sms.exam
│   │   │   ├── exam_result.py        # univ.sms.exam.result
│   │   │   └── transcript.py
│   │   └── ...
│   │
│   ├── univ_sms_fee/
│   │   ├── models/
│   │   │   └── fee.py                # univ.sms.fee.term / .invoice (kế thừa account.move)
│   │   └── ...
│   │
│   ├── univ_sms_portal/
│   │   ├── controllers/
│   │   │   └── portal.py             # CustomerPortal inherit
│   │   ├── views/
│   │   │   └── portal_templates.xml  # QWeb templates
│   │   └── ...
│   │
│   └── univ_sms_report/
│       ├── reports/
│       │   ├── transcript_report.xml
│       │   └── invoice_report.xml
│       └── ...
└── docs/
    └── (toàn bộ file .md này)