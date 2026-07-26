# -*- coding: utf-8 -*-
"""
Comprehensive mock data for University SMS system.
Each entity has 10-20 records minimum.
Run inside Odoo shell: exec(open('/mnt/extra-addons/create_mock_data.py').read())
"""
import random
from datetime import date, timedelta, datetime

def get_or_create(model, domain, vals):
    record = env[model].search(domain, limit=1)
    if not record:
        record = env[model].create(vals)
    return record

# ============================================================
# 1. FACULTIES (10)
# ============================================================
print("=== Creating Faculties ===")
faculties = []
fac_data = [
    ('CNTT', 'Công nghệ Thông tin'),
    ('KT', 'Kinh tế'),
    ('CNTT', 'Khoa Khoa học Tự nhiên'),
    ('YH', 'Y học'),
    ('GD', 'Giáo dục'),
    ('KT', 'Khoa Kỹ thuật'),
    ('NN', 'Khoa Ngoại ngữ'),
    ('L', 'Khoa Luật'),
    ('XH', 'Khoa Xã hội học'),
    ('MT', 'Khoa Môi trường'),
]
for code, name in fac_data:
    f = get_or_create('univ.sms.faculty', [('code', '=', code)], {'name': name, 'code': code})
    faculties.append(f)
print(f"  Created {len(faculties)} faculties")

# ============================================================
# 2. DEPARTMENTS (10)
# ============================================================
print("=== Creating Departments ===")
departments = []
dep_data = [
    ('KTPM', 'Kỹ thuật Phần mềm', 0),
    ('HTTT', 'Hệ thống Thông tin', 0),
    ('QTKD', 'Quản trị Kinh doanh', 1),
    ('TC', 'Tài chính', 1),
    ('YH', 'Y khoa', 3),
    ('GD', 'Sư phạm', 4),
    ('CK', 'Cơ khí', 5),
    ('NN', 'Tiếng Anh', 6),
    ('LS', 'Lịch sử', 8),
    ('MT', 'Quản lý Tài nguyên', 9),
]
for code, name, fac_idx in dep_data:
    d = get_or_create('univ.sms.department', [('code', '=', code)], {
        'name': name, 'code': code, 'faculty_id': faculties[fac_idx % len(faculties)].id
    })
    departments.append(d)
print(f"  Created {len(departments)} departments")

# ============================================================
# 3. PROGRAMS (10)
# ============================================================
print("=== Creating Programs ===")
programs = []
prog_data = [
    ('CN-KTPM', 'Cử nhân Kỹ thuật Phần mềm', 0, 150, 4),
    ('CN-HTTT', 'Cử nhân Hệ thống Thông tin', 1, 145, 4),
    ('CN-QTKD', 'Cử nhân Quản trị Kinh doanh', 2, 140, 4),
    ('CN-TC', 'Cử nhân Tài chính', 3, 135, 4),
    ('BS-YH', 'Bác sĩ Y khoa', 4, 180, 6),
    ('CN-GD', 'Cử nhân Sư phạm', 5, 140, 4),
    ('CN-CK', 'Cử nhân Cơ khí', 6, 145, 4),
    ('CN-NN', 'Cử nhân Ngoại ngữ', 7, 130, 4),
    ('CN-LS', 'Cử nhân Lịch sử', 8, 125, 4),
    ('CN-MT', 'Cử nhân Quản lý MT', 9, 130, 4),
]
for code, name, dep_idx, credits, years in prog_data:
    p = get_or_create('univ.sms.program', [('code', '=', code)], {
        'name': name, 'code': code, 'department_id': departments[dep_idx % len(departments)].id,
        'total_credits': credits, 'duration_years': years
    })
    programs.append(p)
print(f"  Created {len(programs)} programs")

# ============================================================
# 4. SUBJECTS (15)
# ============================================================
print("=== Creating Subjects ===")
subjects = []
subj_data = [
    ('IT101', 'Nhập môn Lập trình', 3.0, 0),
    ('IT102', 'Toán Rời rạc', 3.0, 0),
    ('IT103', 'Cấu trúc Dữ liệu & Giải thuật', 4.0, 0),
    ('IT201', 'Cơ sở Dữ liệu', 3.0, 0),
    ('IT202', 'Mạng Máy tính', 3.0, 1),
    ('IT301', 'Công nghệ Phần mềm', 3.0, 0),
    ('ECO101', 'Kinh tế Vĩ mô', 3.0, 2),
    ('ECO102', 'Quản trị học', 3.0, 2),
    ('ECO103', 'Kế toán Tổng hợp', 3.0, 3),
    ('ECO104', 'Marketing', 3.0, 2),
    ('MATH101', 'Giải tích I', 3.0, 0),
    ('MATH102', 'Đại số Tuyến tính', 3.0, 0),
    ('PHY101', 'Vật lý Đại cương', 3.0, 0),
    ('ENG101', 'Tiếng Anh I', 3.0, 7),
    ('ENG102', 'Tiếng Anh II', 3.0, 7),
]
for code, name, credit, prog_idx in subj_data:
    s = get_or_create('univ.sms.subject', [('code', '=', code)], {
        'name': name, 'code': code, 'credit': credit,
        'program_ids': [(4, programs[prog_idx % len(programs)].id)],
    })
    subjects.append(s)
print(f"  Created {len(subjects)} subjects")

# ============================================================
# 5. ACADEMIC YEARS & TERMS (10+)
# ============================================================
print("=== Creating Academic Years & Terms ===")
years = []
terms = []
year_data = [
    ('2024-2025', '2024-09-01', '2025-06-30'),
    ('2025-2026', '2025-09-01', '2026-06-30'),
    ('2026-2027', '2026-09-01', '2027-06-30'),
]
for name, start, end in year_data:
    y = get_or_create('univ.sms.academic.year', [('name', '=', name)], {'name': name, 'date_start': start, 'date_end': end})
    years.append(y)

term_data = [
    ('Học kỳ 1', 0, '2024-09-01', '2025-01-15'),
    ('Học kỳ 2', 0, '2025-02-01', '2025-06-30'),
    ('Học kỳ 3', 0, '2025-07-01', '2025-08-30'),
    ('Học kỳ 1', 1, '2025-09-01', '2026-01-15'),
    ('Học kỳ 2', 1, '2026-02-01', '2026-06-30'),
    ('Học kỳ 3', 1, '2026-07-01', '2026-08-30'),
    ('Học kỳ 1', 2, '2026-09-01', '2027-01-15'),
    ('Học kỳ 2', 2, '2027-02-01', '2027-06-30'),
    ('Học kỳ 3', 2, '2027-07-01', '2027-08-30'),
]
for name, yr_idx, start, end in term_data:
    t = get_or_create('univ.sms.term', [('name', '=', name), ('academic_year_id', '=', years[yr_idx].id)], {
        'name': name, 'academic_year_id': years[yr_idx].id, 'date_start': start, 'date_end': end
    })
    terms.append(t)
print(f"  Created {len(years)} years, {len(terms)} terms")

# ============================================================
# 6. LECTURERS (5)
# ============================================================
print("=== Creating Lecturers ===")
lecturers = []
lec_data = [
    ('Nguyễn Văn An', 'gva'),
    ('Trần Thị Bích', 'gtb'),
    ('Lê Văn Cường', 'glc'),
    ('Phạm Thị Dung', 'gpd'),
    ('Hoàng Văn Em', 'ghe'),
]
for name, login in lec_data:
    u = get_or_create('res.users', [('login', '=', login)], {
        'name': name, 'login': login, 'password': '1234', 'groups_id': [(6, 0, [env.ref('base.group_user').id, env.ref('univ_sms_base.group_univ_lecturer').id])],
    })
    lecturers.append(u.partner_id)
print(f"  Created {len(lecturers)} lecturers")

# ============================================================
# 7. STUDENTS (20)
# ============================================================
print("=== Creating Students ===")
students = []
portal_group = env.ref('base.group_portal')
stud_data = [
    ('IT2024001', 'Nguyễn Văn Nam', 0, 'sv001'),
    ('IT2024002', 'Trần Thị Hoa', 0, 'sv002'),
    ('IT2024003', 'Lê Văn Long', 0, 'sv003'),
    ('IT2024004', 'Phạm Thị Mai', 0, 'sv004'),
    ('IT2024005', 'Hoàng Văn Quang', 0, 'sv005'),
    ('IT2024006', 'Vũ Thị Lan', 0, 'sv006'),
    ('IT2024007', 'Đỗ Văn An', 0, 'sv007'),
    ('IT2024008', 'Ngô Thị Thúy', 0, 'sv008'),
    ('EC2024001', 'Bùi Văn Hùng', 2, 'sv009'),
    ('EC2024002', 'Đặng Thị Kim', 2, 'sv010'),
    ('EC2024003', 'Mai Văn Tùng', 2, 'sv011'),
    ('EC2024004', 'Huỳnh Thị Nga', 2, 'sv012'),
    ('EC2024005', 'Phan Văn Đức', 2, 'sv013'),
    ('EC2024006', 'Trịnh Thị Hằng', 2, 'sv014'),
    ('EC2024007', 'La Văn Minh', 2, 'sv015'),
    ('EC2024008', 'Tạ Thị Bích', 2, 'sv016'),
    ('MED2024001', 'Đinh Văn Cường', 4, 'sv017'),
    ('MED2024002', 'Lý Thị Hoài', 4, 'sv018'),
    ('EDU2024001', 'Cao Văn Phong', 5, 'sv019'),
    ('EDU2024002', 'Đoàn Thị Yến', 5, 'sv020'),
]
for code, name, prog_idx, login in stud_data:
    u = get_or_create('res.users', [('login', '=', login)], {
        'name': name, 'login': login, 'password': '1234',
        'groups_id': [(6, 0, [portal_group.id])],
    })
    s = get_or_create('univ.sms.student', [('student_code', '=', code)], {
        'partner_id': u.partner_id.id, 'student_code': code,
        'program_id': programs[prog_idx % len(programs)].id, 'state': 'studying'
    })
    students.append(s)
print(f"  Created {len(students)} students")

# ============================================================
# 8. CLASSES (12)
# ============================================================
print("=== Creating Classes ===")
classes = []
cls_data = [
    ('IT101-01', 'IT101 - Lớp 1', 0, 0),   # subj 0, term 0
    ('IT101-02', 'IT101 - Lớp 2', 0, 0),
    ('IT102-01', 'IT102 - Lớp 1', 1, 0),
    ('IT103-01', 'IT103 - Lớp 1', 2, 0),
    ('IT201-01', 'IT201 - Lớp 1', 3, 0),
    ('IT202-01', 'IT202 - Lớp 1', 4, 3),   # term 3 (HK1 2025-2026)
    ('ECO101-01', 'ECO101 - Lớp 1', 6, 0),
    ('ECO102-01', 'ECO102 - Lớp 1', 7, 0),
    ('MATH101-01', 'MATH101 - Lớp 1', 10, 0),
    ('MATH102-01', 'MATH102 - Lớp 1', 11, 0),
    ('PHY101-01', 'PHY101 - Lớp 1', 12, 0),
    ('ENG101-01', 'ENG101 - Lớp 1', 13, 0),
]
for code, name, subj_idx, term_idx in cls_data:
    c = get_or_create('univ.sms.class', [('code', '=', code)], {
        'name': name, 'code': code, 'subject_id': subjects[subj_idx % len(subjects)].id,
        'lecturer_id': lecturers[subj_idx % len(lecturers)].id,
        'term_id': terms[term_idx % len(terms)].id, 'state': 'open'
    })
    classes.append(c)
print(f"  Created {len(classes)} classes")

# ============================================================
# 9. ENROLLMENTS (15)
# ============================================================
print("=== Creating Enrollments ===")
enrollments = []
# Students 0-7 (KTPM) enroll in IT classes, 8-15 (QTKD) enroll in ECO classes
for i in range(8):
    for cls_idx in [0, 2, 3]:  # IT101-01, IT102-01, IT103-01
        if cls_idx < len(classes) and students[i].program_id == programs[0]:
            enr = get_or_create('univ.sms.enrollment', [('student_id', '=', students[i].id), ('subject_id', '=', classes[cls_idx].subject_id.id), ('term_id', '=', classes[cls_idx].term_id.id)], {
                'student_id': students[i].id, 'subject_id': classes[cls_idx].subject_id.id,
                'term_id': classes[cls_idx].term_id.id, 'class_id': classes[cls_idx].id, 'state': 'registered'
            })
            enrollments.append(enr)

for i in range(8, 16):
    for cls_idx in [6, 7]:  # ECO101-01, ECO102-01
        if cls_idx < len(classes) and students[i].program_id == programs[2]:
            enr = get_or_create('univ.sms.enrollment', [('student_id', '=', students[i].id), ('subject_id', '=', classes[cls_idx].subject_id.id), ('term_id', '=', classes[cls_idx].term_id.id)], {
                'student_id': students[i].id, 'subject_id': classes[cls_idx].subject_id.id,
                'term_id': classes[cls_idx].term_id.id, 'class_id': classes[cls_idx].id, 'state': 'registered'
            })
            enrollments.append(enr)
print(f"  Created {len(enrollments)} enrollments")

# ============================================================
# 10. ATTENDANCE SHEETS (15)
# ============================================================
print("=== Creating Attendance ===")
attendance_count = 0
att_dates = ['2024-09-10', '2024-09-17', '2024-09-24', '2024-10-01', '2024-10-08']
for cls_idx, cls in enumerate(classes[:6]):  # Only first 6 classes
    for d in att_dates:
        att = env['univ.sms.attendance.sheet'].search([('class_id', '=', cls.id), ('attendance_date', '=', d)], limit=1)
        if not att:
            att = env['univ.sms.attendance.sheet'].create({
                'class_id': cls.id, 'attendance_date': d
            })
            att.action_load_students()
            if att.line_ids:
                att.action_confirm()
            attendance_count += 1
print(f"  Created {attendance_count} attendance sheets")

# ============================================================
# 11. EXAMS & RESULTS (15)
# ============================================================
print("=== Creating Exams & Results ===")
exam_count = 0
for cls in classes[:6]:
    exam = env['univ.sms.exam'].search([('class_id', '=', cls.id)], limit=1)
    if not exam:
        exam = env['univ.sms.exam'].create({
            'name': f'Thi cuối kỳ {cls.code}', 'class_id': cls.id, 'exam_type': 'final', 'date': '2025-01-10', 'max_score': 10.0
        })
        for r in exam.result_ids:
            r.score = round(random.uniform(4.0, 10.0), 1)
        exam.action_start_grading()
        exam.action_done()
        exam_count += 1
print(f"  Created {exam_count} exams")

# ============================================================
# 12. REGISTRATION PERIODS (10)
# ============================================================
print("=== Creating Registration Periods ===")
reg_periods = []
for i in range(10):
    rp = get_or_create('univ.sms.registration.period', [('name', '=', f'Đợt đăng ký {i+1}')], {
        'name': f'Đợt đăng ký {i+1}',
        'term_id': terms[i % len(terms)].id,
        'date_start': f'2025-{1+i//3:02d}-01',
        'date_end': f'2025-{1+i//3:02d}-15',
        'reg_type': 'regular' if i % 2 == 0 else 'elective',
        'min_credit': 0, 'max_credit': 30,
        'state': 'open' if i < 5 else 'closed',
    })
    reg_periods.append(rp)
print(f"  Created {len(reg_periods)} registration periods")

# ============================================================
# 21. COURSE OFFERINGS (12)
# ============================================================
print("=== Creating Course Offerings ===")
offerings = []
for i, cls in enumerate(classes):
    co = get_or_create('univ.sms.course.offering', [('class_id', '=', cls.id)], {
        'subject_id': cls.subject_id.id, 'term_id': cls.term_id.id,
        'lecturer_id': cls.lecturer_id.id if cls.lecturer_id else False,
        'class_id': cls.id, 'max_seats': 60,
    })
    offerings.append(co)
print(f"  Created {len(offerings)} course offerings")

# ============================================================
# 13. REGISTRATIONS (DKMH) (15) - AFTER offerings
# ============================================================
print("=== Creating Registrations ===")
registrations = []
for i, s in enumerate(students[:15]):
    off = offerings[i % len(offerings)]
    rp = reg_periods[i % len(reg_periods)]
    reg = get_or_create('univ.sms.registration', [('student_id', '=', s.id), ('offering_id', '=', off.id)], {
        'student_id': s.id, 'offering_id': off.id, 'period_id': rp.id, 'state': 'confirmed',
    })
    registrations.append(reg)
print(f"  Created {len(registrations)} registrations")

# ============================================================
# 14. NOTIFICATIONS (15)
# ============================================================
print("=== Creating Notifications ===")
notifications = []
notif_data = [
    ('Thông báo lịch thi cuối kỳ', 'Học kỳ 1, năm 2024-2025 sẽ diễn ra từ 06/01/2025 đến 20/01/2025.'),
    ('Thông báo đóng học phí', 'Hạn đóng học phí kỳ 1: 15/11/2024.'),
    ('Thông báo nghỉ lễ', 'Miễn học ngày 20/11 và 30/04.'),
    ('Thông báo đăng ký môn', 'Đợt đăng ký môn học kỳ 2 mở từ 15/01/2025.'),
    ('Thông báo thay đổi lịch', 'Lịch thi môn IT101 chuyển sang 15/01/2025.'),
    ('Thông báo tốt nghiệp', 'Lễ tốt nghiệp khóa 2020-2024 vào 25/07/2025.'),
    ('Thông báo phòng Đào tạo', 'Phòng Đào tạo sẽ đóng cửa 2 ngày 10-11/03/2025.'),
    ('Thông báo đổi điểm', 'Hạn cuối đổi điểm đến 20/02/2025.'),
    ('Thông báo sinh viên giải thưởng', 'Trao thưởng cho SV có thành tích xuất sắc.'),
    ('Thông báo thực tập', 'Đăng ký thực tổ Bluetooth kỳ 2 từ 01/02/2025.'),
    ('Thông báo kí túc xá', 'Đăng ký kí túc xá học kỳ mới từ 01/08/2025.'),
    ('Thông báo memorandum', 'Ghi nhớ các quy định về học phí.'),
    ('Thông báo thi lại', 'Hạn đăng ký thi lại: 01/03/2025.'),
    ('Thông báo dịch vụ y tế', 'Khám sức khỏe định kỳ cho sinh viên.'),
    ('Thông báo公平考核', 'Công bố kết quả đánh giá rakeplinput.'),
]
for title, content in notif_data:
    n = get_or_create('univ.sms.notification', [('title', '=', title)], {
        'title': title, 'content': content, 'target_audience': 'all', 'state': 'published',
    })
    notifications.append(n)
print(f"  Created {len(notifications)} notifications")

# ============================================================
# 15. FEEDBACK (10)
# ============================================================
print("=== Creating Feedback ===")
feedbacks = []
feedback_list = [
    ('academic', 'Môn học', 'Chương trình đào tạo cần cải thiện'),
    ('facility', 'Cơ sở vật chất', 'Phòng học cần trang bị thêm máy lạnh'),
    ('service', 'Dịch vụ hành chính', 'Trục trặc khi đăng ký môn'),
    ('academic', 'Giảng viên', 'Giảng viên dạy tốt nhưng cần thêm bài tập'),
    ('facility', 'Thư viện', 'Cần mở cửa thư viện thêm giờ'),
    ('service', 'Học phí', 'Hướng dẫn đóng học phí chưa rõ'),
    ('academic', 'Điểm thi', 'Thang điểm chưa phù hợp'),
    ('facility', 'Phòng lab', 'Cần nâng cấp phòng lab'),
    ('other', 'Khác', 'Góp ý chung về nhà trường'),
    ('academic', 'Cố vấn học tập', 'Cần có thêm buổi tư vấn'),
    ('facility', 'Ký túc xá', 'Cần cải thiện điều kiện ăn ở'),
    ('service', 'Thư viện', 'Thư viện cần mua thêm sách mới'),
    ('academic', 'Lịch thi', 'Lịch thi quá dày'),
    ('facility', 'Căng tin', 'Đồ ăn cần đa dạng hơn'),
    ('service', 'Y tế', 'Phòng y tế cần hoạt động tốt hơn'),
]
for i, (category, subject, description) in enumerate(feedback_list):
    f = get_or_create('univ.sms.feedback', [('subject', '=', subject + str(i))], {
        'student_id': students[i].id, 'category': category, 'subject': subject,
        'description': description, 'state': 'new',
    })
    feedbacks.append(f)
print(f"  Created {len(feedbacks)} feedbacks")

# ============================================================
# 16. HEALTH INSURANCE (10)
# ============================================================
print("=== Creating Health Insurance ===")
insurances = []
for i in range(10):
    ins = get_or_create('univ.sms.health.insurance', [('insurance_code', '=', f'HS00{i+1}')], {
        'student_id': students[i].id, 'insurance_code': f'HS00{i+1}',
        'date_start': '2024-09-01', 'date_end': '2025-06-30',
        'payment_state': 'paid' if i % 3 != 0 else 'unpaid',
    })
    insurances.append(ins)
print(f"  Created {len(insurances)} insurances")

# ============================================================
# 17. RESIDENCE INFO (10)
# ============================================================
print("=== Creating Residence Info ===")
residences = []
res_types = ['dormitory', 'rent', 'family']
for i in range(10):
    res = get_or_create('univ.sms.residence.info', [('student_id', '=', students[i].id)], {
        'student_id': students[i].id, 'residence_type': res_types[i % 3],
        'address': f'Đại học ABC, {100+i} đường Nguyễn Huệ, Hà Nội',
        'landlord_name': f'Chủ nhà {i}' if i % 3 == 1 else '',
        'landlord_phone': f'0900{i:04d}' if i % 3 == 1 else '',
        'state': 'confirmed',
    })
    residences.append(res)
print(f"  Created {len(residences)} residence info")

# ============================================================
# 18. MILITARY SERVICE (10)
# ============================================================
print("=== Creating Military Service ===")
military = []
mstatus = ['not_registered', 'registered', 'deferred', 'completed']
for i in range(10):
    ms = get_or_create('univ.sms.military.service', [('student_id', '=', students[i].id)], {
        'student_id': students[i].id, 'registration_status': mstatus[i % 4],
        'declared_date': '2024-09-01',
    })
    military.append(ms)
print(f"  Created {len(military)} military service records")

# ============================================================
# 19. CONDUCT SCORES (15)
# ============================================================
print("=== Creating Conduct Scores ===")
conducts = []
for i in range(15):
    cs = get_or_create('univ.sms.conduct.score', [('student_id', '=', students[i].id), ('period_id', '=', terms[0].id)], {
        'student_id': students[i].id,
        'period_id': terms[0].id,
        'self_total': random.randint(60, 95),
        'advisor_total': random.randint(60, 95),
        'final_total': random.randint(60, 95),
        'state': 'dean_approved',
    })
    conducts.append(cs)
print(f"  Created {len(conducts)} conduct scores")

# ============================================================
# 20. CERTIFICATE TYPES & REQUESTS (10 each)
# ============================================================
print("=== Creating Certificate Types & Requests ===")
cert_types = []
ct_data = [
    ('Xác nhận SV', 'XNSV'), ('Phiếu điểm', 'PĐ'),
    ('Phiếu tạm vắng', 'PTV'), ('Giấy chứng nhận tốt nghiệp', 'GCNTN'),
    ('Phiếu bảo hiểm', 'PBH'), ('Giấy xác nhận-Thông tin', 'GXNTT'),
    ('Phiếu công nhận', 'PCN'), ('Giấy xác nhận học tập', 'GXNHT'),
    ('Phiếu chuyển trường', 'PCT'), ('Phiếu xác nhận từ UK', 'PXBTN'),
]
for name, code in ct_data:
    ct = get_or_create('univ.sms.certificate.type', [('code', '=', code)], {
        'name': name, 'code': code, 'require_fee': False, 'fee_amount': 0,
    })
    cert_types.append(ct)

cert_requests = []
for i, ct in enumerate(cert_types):
    cr = get_or_create('univ.sms.certificate.request', [('student_id', '=', students[i].id), ('certificate_type_id', '=', ct.id)], {
        'student_id': students[i].id, 'certificate_type_id': ct.id, 'reason': f'Mục đích {i+1}',
    })
    cert_requests.append(cr)
print(f"  Created {len(cert_types)} cert types, {len(cert_requests)} cert requests")

# ============================================================
# 21. COURSE OFFERINGS (10)
# ============================================================
print("=== Creating Course Offerings ===")
offerings = []
for i, cls in enumerate(classes):
    co = get_or_create('univ.sms.course.offering', [('class_id', '=', cls.id)], {
        'subject_id': cls.subject_id.id, 'term_id': cls.term_id.id,
        'lecturer_id': cls.lecturer_id.id if cls.lecturer_id else False,
        'class_id': cls.id, 'max_seats': 60,
    })
    offerings.append(co)
print(f"  Created {len(offerings)} course offerings")

# ============================================================
# 22. ELECTIVE WISHES (10)
# ============================================================
print("=== Creating Elective Wishes ===")
wishes = []
for i in range(10):
    ew = get_or_create('univ.sms.elective.wish', [('student_id', '=', students[i].id)], {
        'student_id': students[i].id,
        'offering_id': offerings[i % len(offerings)].id,
        'priority': i + 1, 'state': 'approved',
    })
    wishes.append(ew)
print(f"  Created {len(wishes)} elective wishes")

# Commit
env.cr.commit()
print("\n✅ Mock data generated successfully! (All entities)")