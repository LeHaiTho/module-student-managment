# -*- coding: utf-8 -*-
"""
University SMS - Comprehensive Realistic Mock Data Generator v3
Generates realistic Vietnamese data for all models.
Includes generated PIL avatars, file attachments, timetables, and fee invoices.
Run: exec(open('/mnt/extra-addons/create_mock_data_v3.py').read())
"""
import random
import base64
import io
from PIL import Image, ImageDraw

def get_or_create(model, domain, vals):
    r = env[model].search(domain, limit=1)
    if not r:
        r = env[model].create(vals)
    return r

def generate_avatar_png(initials, bg_color):
    """Draw a modern profile silhouette on a colored background using PIL (guaranteed in Odoo)"""
    img = Image.new('RGB', (128, 128), bg_color)
    draw = ImageDraw.Draw(img)
    # Circle frame
    draw.ellipse([10, 10, 118, 118], outline="#ffffff", width=4)
    # Draw head
    draw.ellipse([49, 35, 79, 65], fill="#ffffff")
    # Draw shoulders
    draw.arc([34, 65, 94, 115], start=180, end=360, fill="#ffffff", width=10)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Colors for avatars
colors = [
    '#1a73e8', '#34a853', '#ea4335', '#fbbc04', '#9c27b0', 
    '#00acc1', '#ff7043', '#7cb342', '#009688', '#3f51b5'
]

# Minimal valid PDF file
demo_pdf = "JVBERi0xLjUKJb/3ov4KMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFszIDAgUiBdIC9Db3VudCAxID4+CmVuZG9iagozIDAgb2JqCjw8IC9UeXBlIC9QYWdlIC9QYXJlbnQgMiAwIFIgL1Jlc291cmNlcyA8PCAvRm9udCA8PCAvRjEgPDwgL1R5cGUgL0ZvbnQgL1N1YnR5cGUgL1R5cGUxIC9CYXNlRm9udCAvSGVsdmV0aWNhID4+ID4+ID4+IC9NZWRpYUJveCBbMCAwIDYxMiA3OTJdID4+CmVuZG9iagp4cmVmCjAgNAowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMDkgMDAwMDAgbiAKMDAwMDAwMDA1OCAwMDAwMCBuIAowMDAwMDAwMTE3IDAwMDAwIG4gCnRyYWlsZXIKPDwgL1NpemUgNCAvUm9vdCAxIDAgUiA+PgpzdGFydHhyZWYKMjg5CiUlRU9G"

# ============================================================
# 1. FACULTIES (15 realistic Vietnamese faculties)
# ============================================================
print("=== Creating Faculties ===")
faculties = []
fac_data = [
    ('CNTT-TT', 'Khoa Công nghệ Thông tin & Truyền thông'),
    ('KT-KD', 'Khoa Kinh tế - Kinh doanh'),
    ('YH', 'Khoa Y học'),
    ('SP-GD', 'Khoa Sư phạm & Giáo dục'),
    ('KT', 'Khoa Kỹ thuật'),
    ('NN-VH', 'Khoa Ngoại ngữ & Văn hóa'),
    ('Luat', 'Khoa Luật'),
    ('XH-NV', 'Khoa Xã hội - Nhân văn'),
    ('MT', 'Khoa Môi trường & Tài nguyên'),
    ('XD', 'Khoa Xây dựng'),
    ('CK-DL', 'Khoa Cơ khí - Động lực'),
    ('DK-TD', 'Khoa Điện tử - Tự động hóa'),
    ('NN-LN', 'Khoa Nông - Lâm nghiệp'),
    ('TPL', 'Khoa Thể dục Thể thao'),
    ('MTA', 'Khoa Mỹ thuật Ứng dụng'),
]
for code, name in fac_data:
    f = get_or_create('univ.sms.faculty', [('code', '=', code)], {'name': name, 'code': code})
    faculties.append(f)
print(f"  Created {len(faculties)} faculties")

# ============================================================
# 2. DEPARTMENTS (30)
# ============================================================
print("=== Creating Departments ===")
departments = []
dep_data = [
    ('KTPM', 'Kỹ thuật Phần mềm', 0), ('HTTT', 'Hệ thống Thông tin', 0),
    ('MMT', 'Mạng Máy tính & TT', 0), ('KHMT', 'Khoa học Máy tính', 0),
    ('QTKD', 'Quản trị Kinh doanh', 1), ('TC-NH', 'Tài chính - Ngân hàng', 1),
    ('KT', 'Kế toán', 1), ('Marketing', 'Marketing & PR', 1),
    ('YHPL', 'Y học Phổ thông', 2), ('NHS', 'Nuôi học Sức', 2),
    ('DLS', 'Dược học', 2), ('SPTH', 'Sư phạm Tiểu học', 3),
    ('SPTHCS', 'Sư phạm THCS', 3), ('GDDB', 'Giáo dục Đặc biệt', 3),
    ('CNVL', 'Công nghệ Vật liệu', 4), ('DDK', 'Điện - Điện tử', 4),
    ('TTLL', 'Tiếng Anh', 5), ('TNH', 'Tiếng Nhật', 5),
    ('TQ', 'Tiếng Trung', 5), ('LSD', 'Luật Dân sự', 6),
    ('LKT', 'Luật Kinh tế', 6), ('CT-XH', 'Chính trị Xã hội', 7),
    ('TLCN', 'Tâm lý học', 7), ('QLTN', 'Quản lý Tài nguyên', 8),
    ('MTDT', 'Môi trường Đô thị', 8), ('CTXD', 'Cầu - Xây dựng', 9),
    ('CKCN', 'Cơ khí Chế tạo', 10), ('TDH', 'Tự động hóa', 11),
    ('MTA', 'Mỹ thuật Đa phương tiện', 14), ('TGS', 'Trí tuệ Nhân tạo', 0),
]
for code, name, fac_idx in dep_data:
    d = get_or_create('univ.sms.department', [('code', '=', code)], {
        'name': name, 'code': code, 'faculty_id': faculties[fac_idx % len(faculties)].id
    })
    departments.append(d)
print(f"  Created {len(departments)} departments")

# ============================================================
# 3. PROGRAMS (20)
# ============================================================
print("=== Creating Programs ===")
programs = []
prog_data = [
    ('7480201', 'Công nghệ Thông tin', 0, 150, 4.5),
    ('7480103', 'Kỹ thuật Phần mềm', 0, 145, 4.5),
    ('7340101', 'Quản trị Kinh doanh', 4, 140, 4),
    ('7340301', 'Kế toán', 6, 138, 4),
    ('7340201', 'Tài chính - Ngân hàng', 5, 140, 4),
    ('7720101', 'Y học Dự phòng', 8, 180, 6),
    ('7720201', 'Dược học', 9, 175, 5),
    ('7140201', 'Sư phạm Tin học', 11, 140, 4),
    ('7140101', 'Sư phạm Tiểu học', 12, 138, 4),
    ('7520201', 'Công nghệ Kỹ thuật Điện', 14, 145, 4.5),
    ('7520101', 'Cơ khí Chế tạo', 22, 145, 4.5),
    ('7580201', 'Xây dựng Dân dụng', 23, 150, 5),
    ('7220201', 'Ngôn ngữ Anh', 17, 130, 4),
    ('7220101', 'Ngôn ngữ Nhật', 18, 130, 4),
    ('7380101', 'Luật Kinh tế', 20, 135, 4),
    ('7440301', 'Môi trường & PTBV', 24, 140, 4),
    ('7210401', 'Mỹ thuật Đa phương tiện', 28, 145, 4),
    ('7310201', 'Quản lý Nhà nước', 19, 130, 4),
    ('7480300', 'Trí tuệ Nhân tạo', 29, 145, 4.5),
    ('7340102', 'Marketing Số', 7, 140, 4),
]
for code, name, dep_idx, credits, years in prog_data:
    p = get_or_create('univ.sms.program', [('code', '=', code)], {
        'name': name, 'code': code, 'department_id': departments[dep_idx % len(departments)].id,
        'total_credits': credits, 'duration_years': years
    })
    programs.append(p)
print(f"  Created {len(programs)} programs")

# ============================================================
# 4. SUBJECTS (30)
# ============================================================
print("=== Creating Subjects ===")
subjects = []
subj_data = [
    ('IT101', 'Nhập môn Lập trình', 3.0), ('IT102', 'Toán Rời rạc', 3.0),
    ('IT103', 'Cấu trúc Dữ liệu', 4.0), ('IT104', 'Lập trình Python', 3.0),
    ('IT105', 'Lập trình Hướng đối tượng', 4.0), ('IT106', 'Cơ sở Dữ liệu', 3.0),
    ('IT201', 'Mạng Máy tính', 3.0), ('IT202', 'Hệ điều hành', 3.0),
    ('IT203', 'Phân tích & TK HTTT', 3.0), ('IT204', 'An toàn Thông tin', 3.0),
    ('IT301', 'Công nghệ Phần mềm', 3.0), ('IT302', 'Khai phá Dữ liệu', 3.0),
    ('IT303', 'Học Máy & AI', 4.0), ('IT304', 'Lập trình Web', 3.0),
    ('IT305', 'Lập trình Mobile', 3.0), ('ECO101', 'Kinh tế Vi mô', 3.0),
    ('ECO102', 'Kinh tế Vĩ mô', 3.0), ('ECO103', 'Quản trị học', 3.0),
    ('ECO104', 'Marketing Căn bản', 3.0), ('ECO105', 'Kế toán Tổng hợp', 3.0),
    ('ECO201', 'Tài chính Doanh nghiệp', 3.0), ('ECO202', 'Quản trị Nhân sự', 3.0),
    ('MATH101', 'Giải tích I', 3.0), ('MATH102', 'Giải tích II', 3.0),
    ('MATH103', 'Đại số Tuyến tính', 3.0), ('MATH104', 'Xác suất Thống kê', 3.0),
    ('PHY101', 'Vật lý Đại cương', 3.0), ('ENG101', 'Tiếng Anh I', 3.0),
    ('ENG102', 'Tiếng Anh II', 3.0), ('ENG103', 'Tiếng Anh Chuyên ngành', 2.0),
]
for code, name, credit in subj_data:
    s = get_or_create('univ.sms.subject', [('code', '=', code)], {
        'name': name, 'code': code, 'credit': credit,
        'program_ids': [(4, programs[random.randint(0, len(programs)-1)].id)],
    })
    subjects.append(s)
print(f"  Created {len(subjects)} subjects")

# ============================================================
# 5. ACADEMIC YEARS & TERMS (10+)
# ============================================================
print("=== Creating Academic Years & Terms ===")
years = []; terms = []
for y in range(2023, 2027):
    name = f'{y}-{y+1}'
    y_obj = get_or_create('univ.sms.academic.year', [('name', '=', name)], {
        'name': name, 'date_start': f'{y}-09-01', 'date_end': f'{y+1}-06-30'
    })
    years.append(y_obj)
    for hk in range(1, 4):
        t_name = f'Học kỳ {hk}'
        s = f'{y}-{9 if hk==1 else 2 if hk==2 else 7:02d}-01'
        e = f'{y+1}-{1 if hk==1 else 6 if hk==2 else 8:02d}-{15 if hk==1 else 30 if hk==2 else 30:02d}'
        t = get_or_create('univ.sms.term', [('name', '=', t_name), ('academic_year_id', '=', y_obj.id)], {
            'name': t_name, 'academic_year_id': y_obj.id, 'date_start': s, 'date_end': e
        })
        terms.append(t)
print(f"  Created {len(years)} years, {len(terms)} terms")

# ============================================================
# 6. LECTURERS (10)
# ============================================================
print("=== Creating Lecturers ===")
lecturers = []
lec_data = [
    ('Nguyễn Văn An', 'gva'), ('Trần Thị Bích', 'gtb'), ('Lê Văn Cường', 'glc'),
    ('Phạm Thị Dung', 'gpd'), ('Hoàng Văn Em', 'ghe'), ('Đỗ Thị Phương', 'gtp'),
    ('Ngô Văn Giang', 'gvg'), ('Bùi Thị Hạnh', 'gth'), ('Vũ Văn Hải', 'gvh'),
    ('Lý Thị Hồng', 'gthg'),
]
for name, login in lec_data:
    u = get_or_create('res.users', [('login', '=', login)], {
        'name': name, 'login': login, 'password': '1234',
        'image_1920': generate_avatar_png(name[:2], random.choice(colors)),
        'groups_id': [(6, 0, [env.ref('base.group_user').id, env.ref('univ_sms_base.group_univ_lecturer').id])],
    })
    lecturers.append(u.partner_id)
print(f"  Created {len(lecturers)} lecturers")

# ============================================================
# 7. STUDENTS (50)
# ============================================================
print("=== Creating Students ===")
students = []
portal_group = env.ref('base.group_portal')
first_names = ['Nam','Hoa','Long','Mai','Quang','Lan','An','Thúy','Hùng','Kim','Tùng','Nga','Đức','Hằng','Minh','Bích',
               'Cường','Hoài','Phong','Yến','Sơn','Thảo','Dũng','Linh','Tuấn','Trang','Phúc','Ngọc','Khoa','Hương',
               'Huy','Thơ','Hiếu','Hậu','Bảo','Ly','Dương','Châu','Thành','My','Tân','Phượng','Bình','Oanh','Đạt','Quỳnh','Nhật','Giang','Tùng','Hà']
last_names = ['Nguyễn','Trần','Lê','Phạm','Hoàng','Vũ','Đỗ','Ngô','Bùi','Đặng','Mai','Huỳnh','Phan','Trịnh','La','Tạ','Đinh','Lý','Cao','Đoàn',
              'Dương','Hồ','Chu','Diệp','Trương','Hà','Lương','Tô','Quách','Vương']
streets = [
    '15 Tôn Thất Thuyết', '241 Xuân Thủy', '88 Cầu Giấy', '102 Nguyễn Trãi', '45 Lê Thanh Nghị',
    '12 Điện Biên Phủ', '302 Kim Mã', '19 Trần Hưng Đạo', '85 Lý Thường Kiệt', '156 Đội Cấn',
    '33 Nguyễn Chí Thanh', '22 Láng Hạ', '50 Hoàng Hoa Thám', '74 Bà Triệu', '96 Phố Huế'
]
cities = ['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ']

for i in range(50):
    lastname = random.choice(last_names)
    firstname = random.choice(first_names)
    full = f'{lastname} {firstname}'
    login = f'sv{i+1:03d}'
    prog = programs[random.randint(0, len(programs)-1)]
    code = f'STU2025{i+1:04d}'
    
    # Generate clean avatar
    initials = "".join([part[0] for part in full.split() if part][:2]).upper()
    avatar_b64 = generate_avatar_png(initials, random.choice(colors))
    
    # Generate realistic contact details
    phone = f'0912{random.randint(100000, 999999)}'
    email = f'{login}@univ.edu.vn'
    street = random.choice(streets)
    city = random.choice(cities)
    
    u = get_or_create('res.users', [('login', '=', login)], {
        'name': full,
        'login': login,
        'password': '1234',
        'image_1920': avatar_b64,
        'groups_id': [(6, 0, [portal_group.id])],
    })
    
    # Write details to partner (inherited fields)
    u.partner_id.write({
        'email': email,
        'phone': phone,
        'mobile': phone,
        'street': street,
        'city': city,
        'country_id': env.ref('base.vn').id if env.ref('base.vn', False) else False
    })
    
    s = get_or_create('univ.sms.student', [('student_code', '=', code)], {
        'partner_id': u.partner_id.id,
        'student_code': code,
        'program_id': prog.id,
        'state': random.choice(['studying','studying','studying','studying','graduated','on_leave'])
    })
    students.append(s)
print(f"  Created {len(students)} students with complete details and custom avatars")

# ============================================================
# 8. CLASSES (20) & TIMETABLES
# ============================================================
print("=== Creating Classes & Timetables ===")
classes = []
rooms = ['Phòng 101-A1', 'Phòng 204-B3', 'Phòng 305-C1', 'Phòng 402-A2', 'Phòng 102-D5', 'Phòng Lab 3']
for i in range(20):
    subj = subjects[i % len(subjects)]
    code = f'{subj.code}-{i//15+1:02d}'
    name = f'{subj.name} - Lớp {i//15+1}'
    term_idx = min(i, len(terms)-1)
    lec_idx = i % len(lecturers)
    c = get_or_create('univ.sms.class', [('code', '=', code)], {
        'name': name,
        'code': code,
        'subject_id': subj.id,
        'lecturer_id': lecturers[lec_idx].id,
        'term_id': terms[term_idx].id,
        'state': random.choice(['draft','open','open','open','closed'])
    })
    classes.append(c)
    
    # Add 1-2 timetables per class
    start = random.choice([7.0, 9.0, 13.0, 15.0])
    duration = random.choice([1.5, 2.0, 2.5, 3.0])
    get_or_create('univ.sms.timetable', [('class_id', '=', c.id)], {
        'class_id': c.id,
        'day_of_week': str(random.randint(0, 5)), # Mon to Sat
        'start_time': start,
        'end_time': start + duration,
        'room': random.choice(rooms),
        'building': 'Tòa nhà A' if 'A' in rooms else 'Khu giảng đường chính'
    })
print(f"  Created {len(classes)} classes with timetable schedules")

# ============================================================
# 9. ENROLLMENTS (150)
# ============================================================
print("=== Creating Enrollments ===")
enrollments = []
for i in range(min(150, len(students)*3)):
    s = students[i % len(students)]
    cls = classes[random.randint(0, len(classes)-1)]
    enr = get_or_create('univ.sms.enrollment', [('student_id', '=', s.id), ('subject_id', '=', cls.subject_id.id), ('term_id', '=', cls.term_id.id)], {
        'student_id': s.id,
        'subject_id': cls.subject_id.id,
        'term_id': cls.term_id.id,
        'class_id': cls.id,
        'state': random.choice(['registered','registered','registered','completed','cancelled'])
    })
    enrollments.append(enr)
print(f"  Created {len(enrollments)} enrollments")

# ============================================================
# 10. ATTENDANCE SHEETS (30)
# ============================================================
print("=== Creating Attendance ===")
att_dates = ['2025-03-10','2025-03-17','2025-03-24','2025-04-01','2025-04-08','2025-04-15']
att_count = 0
for cls in classes[:5]:
    for d in att_dates:
        att = get_or_create('univ.sms.attendance.sheet', [('class_id', '=', cls.id), ('attendance_date', '=', d)], {'class_id': cls.id, 'attendance_date': d})
        if not att.line_ids:
            att.action_load_students()
            if att.line_ids:
                for line in att.line_ids:
                    if random.random() < 0.10:
                        line.state = 'absent'
                    elif random.random() < 0.15:
                        line.state = 'late'
                    else:
                        line.state = 'present'
                att.action_confirm()
                att_count += 1
print(f"  Created {att_count} attendance sheets")

# ============================================================
# 11. EXAMS & RESULTS (30)
# ============================================================
print("=== Creating Exams & Scores ===")
exam_types = ['midterm', 'final', 'quiz', 'project', 'other']
exam_count = 0
for cls in classes:
    e_name = random.choice(['Giữa kỳ', 'Cuối kỳ', 'Bài kiểm tra', 'Thực hành']) + ' ' + cls.code
    etype = random.choice(exam_types)
    exam = get_or_create('univ.sms.exam', [('class_id', '=', cls.id), ('name', '=', e_name)], {
        'name': e_name,
        'class_id': cls.id,
        'exam_type': etype,
        'date': '2025-05-15',
        'max_score': 10.0
    })
    exam_count += 1
    if exam.result_ids:
        for r in exam.result_ids:
            r.score = round(random.uniform(5.0, 10.0), 1)
        exam.action_start_grading()
        exam.action_done()
print(f"  Created {exam_count} exams and grades")

# ============================================================
# 12. REGISTRATION PERIODS & OFFERINGS
# ============================================================
print("=== Creating Registration Periods & Wishes ===")
reg_periods = []
for i in range(5):
    rp = get_or_create('univ.sms.registration.period', [('name', '=', f'Đợt đăng ký Học kỳ {i+1}')], {
        'name': f'Đợt đăng ký Học kỳ {i+1}',
        'term_id': terms[i % len(terms)].id,
        'date_start': f'2025-{1+i:02d}-01 08:00:00',
        'date_end': f'2025-{1+i:02d}-15 17:00:00',
        'reg_type': 'regular' if i % 2 == 0 else 'elective',
        'min_credit': 12,
        'max_credit': 25,
        'state': 'open' if i < 2 else 'closed',
    })
    reg_periods.append(rp)

offerings = []
for cls in classes:
    co = get_or_create('univ.sms.course.offering', [('class_id', '=', cls.id)], {
        'subject_id': cls.subject_id.id,
        'term_id': cls.term_id.id,
        'lecturer_id': cls.lecturer_id.id if cls.lecturer_id else False,
        'class_id': cls.id,
        'max_seats': random.randint(40, 80),
    })
    offerings.append(co)

# Temporarily disable min_credit during generation to avoid single-record validation error
for rp in reg_periods:
    rp.write({'min_credit': 0})

for s in students[:40]:
    rp = random.choice(reg_periods)
    # Find offerings in the same term
    term_offerings = [o for o in offerings if o.term_id == rp.term_id]
    if not term_offerings:
        term_offerings = offerings
    # Pick 4 random unique offerings to satisfy the 12 credits min limit
    sampled = random.sample(term_offerings, min(4, len(term_offerings)))
    for off in sampled:
        get_or_create('univ.sms.registration', [('student_id', '=', s.id), ('offering_id', '=', off.id)], {
            'student_id': s.id,
            'offering_id': off.id,
            'period_id': rp.id,
            'state': 'confirmed',
        })

# Restore min_credit constraint
for rp in reg_periods:
    rp.write({'min_credit': 12})

# ============================================================
# 13. NOTIFICATIONS & FEEDBACK
# ============================================================
print("=== Creating Notifications & Feedbacks ===")
notif_msgs = [
    ('📢 Thông báo Lịch thi HK1-2024-2025','Từ ngày 06/01/2025 đến 20/01/2025, sinh viên vui lòng check lịch trên cổng thông tin.'),
    ('💰 Thông báo Học phí HK2-2024-2025','Hạn đóng học phí: 28/02/2025. Mức đóng: 15.000.000 VNĐ.'),
    ('🏖️ Thông báo Lịch nghỉ Tết Nguyên Đán','Nghỉ từ 25/01/2025 đến 05/02/2025. Chúc mừng năm mới!'),
    ('📝 Mở đợt ĐKHK HK2-2024-2025','Đợt ĐKHK chính thức từ 15/12/2024 đến 31/12/2024.'),
    ('🎓 Lễ Tốt nghiệp đợt 1/2025','Sẽ được tổ chức vào ngày 15/03/2025 tại Hội trường A.'),
]
for title, content in notif_msgs:
    get_or_create('univ.sms.notification', [('title', '=', title)], {
        'title': title, 'content': content, 'target_audience': 'all', 'state': 'published',
    })

fb_items = [
    ('academic','Môn học','Chương trình đào tạo cần cập nhật nhiều hơn'),
    ('facility','CSVC', 'Phòng học thiếu máy chiếu'),
    ('service','Hành chính', 'Đăng ký còn phức tạp'),
]
for i, (cat, subject, desc) in enumerate(fb_items):
    get_or_create('univ.sms.feedback', [('student_id', '=', students[i].id), ('subject', '=', subject)], {
        'student_id': students[i].id, 'category': cat, 'subject': subject,
        'description': desc, 'state': random.choice(['new','in_progress','resolved','closed']),
    })

# ============================================================
# 14. STUDENT AFFAIRS (Health, Residence, Military) with PDF attachments
# ============================================================
print("=== Creating Student Affairs (Attachments & Scans) ===")
for i in range(min(30, len(students))):
    s = students[i]
    
    # 14a. Health Insurance
    get_or_create('univ.sms.health.insurance', [('student_id', '=', s.id)], {
        'student_id': s.id,
        'insurance_code': f'GD{i+1:04d}000{random.randint(10000, 99999)}',
        'date_start': '2024-09-01',
        'date_end': '2025-08-31',
        'payment_state': random.choice(['paid','paid','paid','unpaid']),
        'state': 'confirmed'
    })
    
    # 14b. Residence Info
    get_or_create('univ.sms.residence.info', [('student_id', '=', s.id)], {
        'student_id': s.id,
        'residence_type': random.choice(['dormitory','rent','family']),
        'address': f'{random.randint(10, 500)} Đường {random.choice(["Lê Duẩn","Nguyễn Trãi","Cầu Giấy","Cách Mạng Tháng Tám"])}, {random.choice(cities)}',
        'landlord_name': f'{random.choice(last_names)} {random.choice(first_names)}',
        'landlord_phone': f'0934{random.randint(100000, 999999)}',
        'state': 'confirmed'
    })
    
    # 14c. Military Service Exemption / Registration with Attachments
    mil = get_or_create('univ.sms.military.service', [('student_id', '=', s.id)], {
        'student_id': s.id,
        'registration_status': random.choice(['registered','deferred','completed']),
        'declared_date': '2024-09-10',
        'state': 'approved'
    })
    
    # Create an Odoo attachment for military service
    attachment = env['ir.attachment'].create({
        'name': f'Chung_nhan_NVQS_{s.student_code}.pdf',
        'type': 'binary',
        'datas': demo_pdf,
        'res_model': 'univ.sms.military.service',
        'res_id': mil.id,
    })
    mil.write({'document_attachment_ids': [(4, attachment.id)]})

# ============================================================
# 15. CONDUCT SCORES & CERTIFICATE REQUESTS (with PDFs)
# ============================================================
print("=== Creating Conduct Scores & Certificates ===")
for i in range(min(25, len(students))):
    score = random.randint(65, 96)
    get_or_create('univ.sms.conduct.score', [('student_id', '=', students[i].id), ('period_id', '=', terms[0].id)], {
        'student_id': students[i].id,
        'period_id': terms[0].id,
        'self_total': score,
        'advisor_total': score + random.randint(-4, 4),
        'final_total': score + random.randint(-2, 2),
        'state': 'dean_approved',
    })

cert_types = []
for name, code in [
    ('Giấy xác nhận Sinh viên', 'XNSV'),
    ('Bảng điểm chính thức', 'BDCT'),
    ('Giấy giới thiệu Thực tập', 'GGTTT'),
]:
    ct = get_or_create('univ.sms.certificate.type', [('code', '=', code)], {
        'name': name, 'code': code, 'require_fee': random.random() < 0.5, 'fee_amount': 20000,
    })
    cert_types.append(ct)

for i, ct in enumerate(cert_types):
    for s in students[i*3:i*3+3]:
        req = get_or_create('univ.sms.certificate.request', [('student_id', '=', s.id), ('certificate_type_id', '=', ct.id)], {
            'student_id': s.id,
            'certificate_type_id': ct.id,
            'reason': 'Nộp hồ sơ xin việc / học bổng',
            'fee_payment_state': 'paid' if ct.require_fee else 'unpaid',
            'state': 'completed',
            'output_file': demo_pdf # Fake PDF output
        })

# ============================================================
# 16. DETAILED STUDENT FEES & INVOICES
# ============================================================
print("=== Creating Student Fees & Invoices ===")
# Clear existing fee invoices to avoid duplicate key issues
env['univ.sms.fee.invoice'].search([]).unlink()
env['univ.sms.fee'].search([]).unlink()

for s in students[:35]:
    # Let's create fees for the student in Term 1 (which is active / has enrollments)
    term = terms[0]
    
    # Check if student has registered enrollments in this term
    enrolls = env['univ.sms.enrollment'].search([
        ('student_id', '=', s.id),
        ('term_id', '=', term.id),
        ('state', '=', 'registered')
    ])
    
    if not enrolls:
        # If no registered enrollment, assign a couple of subjects to test fees
        for sub in subjects[:3]:
            env['univ.sms.enrollment'].create({
                'student_id': s.id,
                'subject_id': sub.id,
                'term_id': term.id,
                'class_id': classes[random.randint(0, len(classes)-1)].id,
                'state': 'registered'
            })
        enrolls = env['univ.sms.enrollment'].search([
            ('student_id', '=', s.id),
            ('term_id', '=', term.id),
            ('state', '=', 'registered')
        ])
    
    # Calculate fee
    fee = env['univ.sms.fee'].create({
        'student_id': s.id,
        'term_id': term.id,
        'fee_per_credit': 550000.0,
    })
    
    # Force recompute
    fee._compute_total_credits()
    fee._compute_total_amount()
    
    # Create invoice for some fees
    if random.random() < 0.8: # 80% have invoices
        invoice_vals = {
            'fee_id': fee.id,
            'student_id': s.id,
            'partner_id': s.partner_id.id,
            'term_id': term.id,
            'amount_total': fee.total_amount,
            'state': random.choice(['paid', 'paid', 'confirmed', 'draft'])
        }
        invoice = env['univ.sms.fee.invoice'].create(invoice_vals)
        
        # Create invoice lines for each subject
        for enr in enrolls:
            env['univ.sms.fee.invoice.line'].create({
                'invoice_id': invoice.id,
                'name': f'Học phần: {enr.subject_id.name} ({enr.subject_id.code})',
                'subject_id': enr.subject_id.id,
                'credit': enr.subject_id.credit,
                'quantity': float(enr.subject_id.credit),
                'price_unit': 550000.0,
            })
            
        # Trigger paid count and states
        fee._compute_paid_amount()
        fee._compute_remaining_amount()
        fee._compute_state()

# ============================================================
# 17. SURVEY RESPONSES
# ============================================================
print("=== Creating Surveys ===")
survey_types = []
for name, code in [
    ('Khảo sát cuối Học kỳ', 'KSHK'),
    ('Đánh giá chất lượng giảng dạy', 'ĐGGV'),
]:
    st = get_or_create('univ.sms.survey.type', [('code', '=', code)], {
        'name': name, 'code': code, 'description': f'Khảo sát {name}',
    })
    survey_types.append(st)
    
    for i in range(2):
        si = get_or_create('univ.sms.survey.instance', [('survey_type_id', '=', st.id), ('name', '=', f'{name} năm học 2024-2025 Đợt {i+1}')], {
            'name': f'{name} năm học 2024-2025 Đợt {i+1}',
            'survey_type_id': st.id,
            'date_start': f'2025-{3+i:02d}-01',
            'date_end': f'2025-{3+i:02d}-28',
            'state': 'open' if i == 0 else 'closed',
        })
        for s in students[:20]:
            get_or_create('univ.sms.survey.response', [('survey_instance_id', '=', si.id), ('student_id', '=', s.id)], {
                'survey_instance_id': si.id,
                'student_id': s.id,
                'answer_data': random.choice([
                    'Chất lượng giảng dạy tốt, tài liệu học tập đầy đủ.',
                    'Giảng viên nhiệt tình, hỗ trợ sinh viên chu đáo.',
                    'Phòng học sạch sẽ nhưng thỉnh thoảng wifi bị yếu.',
                    'Nội dung môn học thực tế, sát với nhu cầu công việc.',
                    'Rất hài lòng với đợt khảo sát và dịch vụ hỗ trợ sinh viên.'
                ]),
                'state': 'submitted',
            })

env.cr.commit()
print("\n✅ SUCCESS: All realistic mock data version 3 successfully generated!")
print("   Faculties, Depts, Programs, Subjects: Created")
print("   Students: 50 records with full email, phone, addresses, and circular SILHOUETTE avatars")
print("   Classes & Timetables: Created schedule records")
print("   Student Affairs: Added attachment PDFs for Military Service")
print("   Certificates: Added pre-loaded output PDF files")
print("   Fees & Invoices: Detailed fee invoice line items created")
