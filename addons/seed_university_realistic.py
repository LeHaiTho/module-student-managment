# -*- coding: utf-8 -*-
"""
Realistic university dataset for University SMS.

Run inside Odoo:
docker compose exec -T odoo odoo shell -d univ_sms_db < addons/seed_university_realistic.py
"""

import random
from datetime import date, datetime, timedelta


random.seed(20260708)
RESET_UNIVERSITY_DATA = True


def log(message):
    print("[seed] %s" % message)


def ref(xmlid):
    return env.ref(xmlid)


def get_or_create(model, domain, vals=None, update=None):
    record = env[model].search(domain, limit=1)
    if record:
        if update:
            record.write(update)
        return record
    return env[model].create(vals or update or {})


def reset_university_data():
    env.cr.execute("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename LIKE 'univ_sms_%'
        ORDER BY tablename
    """)
    tables = [row[0] for row in env.cr.fetchall()]
    if not tables:
        return

    env.cr.execute("DELETE FROM ir_model_data WHERE model LIKE 'univ.sms.%'")
    quoted_tables = ', '.join('"%s"' % table.replace('"', '""') for table in tables)
    env.cr.execute("TRUNCATE TABLE %s RESTART IDENTITY CASCADE" % quoted_tables)

    sequence = env["ir.sequence"].search([("code", "=", "univ.sms.student")], limit=1)
    if sequence:
        sequence.number_next_actual = 1


def user(login, name, email, groups, phone=None, password="123456"):
    partner_vals = {
        "name": name,
        "email": email,
        "phone": phone or "",
        "mobile": phone or "",
        "is_company": False,
    }
    existing_user = env["res.users"].with_context(active_test=False).search([("login", "=", login)], limit=1)
    if existing_user:
        existing_user.write({
            "name": name,
            "active": True,
            "password": password,
            "groups_id": [(6, 0, groups)],
        })
        existing_user.partner_id.write(partner_vals)
        return existing_user

    partner = get_or_create("res.partner", [("email", "=", email)], partner_vals, partner_vals)
    return env["res.users"].create({
        "name": name,
        "login": login,
        "password": password,
        "partner_id": partner.id,
        "groups_id": [(6, 0, groups)],
    })


def archive_generic_demo_users():
    for login in ["sinhvien", "giangvien"]:
        demo = env["res.users"].with_context(active_test=False).search([("login", "=", login)], limit=1)
        if demo:
            demo.write({"active": False})


def selection_label(record, field_name, key):
    return dict(record._fields[field_name].selection).get(key, key)


base_user = ref("base.group_user").id
portal_group = ref("base.group_portal").id
admin_group = ref("univ_sms_base.group_univ_admin").id
academic_group = ref("univ_sms_base.group_univ_academic_officer").id
lecturer_group = ref("univ_sms_base.group_univ_lecturer").id
advisor_group = ref("univ_sms_base.group_univ_advisor").id
dean_group = ref("univ_sms_base.group_univ_dean").id
finance_group = ref("univ_sms_base.group_univ_finance_office").id
student_affairs_group = ref("univ_sms_base.group_univ_student_affairs_office").id

if RESET_UNIVERSITY_DATA:
    log("Resetting all univ.sms business data before seeding")
    reset_university_data()

archive_generic_demo_users()

log("Creating role-based staff accounts")
staff_accounts = {
    "admin": user("admin.sms", "Nguyễn Minh Quân - Quản trị hệ thống", "admin.sms@tdtu.edu.vn", [base_user, admin_group], "0901000001"),
    "academic": user("dt.nguyenthilan", "Nguyễn Thị Lan - Phòng Đào tạo", "lan.nt@tdtu.edu.vn", [base_user, academic_group], "0901000002"),
    "finance": user("tc.phamquanghuy", "Phạm Quang Huy - Phòng Tài chính", "huy.pq@tdtu.edu.vn", [base_user, finance_group], "0901000003"),
    "affairs": user("ctsv.levanhoa", "Lê Văn Hòa - Phòng Công tác SV", "hoa.lv@tdtu.edu.vn", [base_user, student_affairs_group], "0901000004"),
}

lecturer_specs = [
    ("gv.tranminhduc", "Trần Minh Đức", "duc.tm@tdtu.edu.vn", "0902000001", [base_user, lecturer_group]),
    ("gv.nguyenthuthao", "Nguyễn Thu Thảo", "thao.nt@tdtu.edu.vn", "0902000002", [base_user, lecturer_group]),
    ("gv.levietanh", "Lê Việt Anh", "anh.lv@tdtu.edu.vn", "0902000003", [base_user, lecturer_group]),
    ("gv.phamhaian", "Phạm Hải An", "an.ph@tdtu.edu.vn", "0902000004", [base_user, lecturer_group]),
    ("cvht.dangminhchau", "Đặng Minh Châu - Cố vấn học tập", "chau.dm@tdtu.edu.vn", "0902000005", [base_user, advisor_group]),
    ("tk.vothanhbinh", "Võ Thanh Bình - Trưởng khoa", "binh.vt@tdtu.edu.vn", "0902000006", [base_user, dean_group]),
    ("gv.hoangngocmai", "Hoàng Ngọc Mai", "mai.hn@tdtu.edu.vn", "0902000007", [base_user, lecturer_group]),
    ("gv.buitrungkien", "Bùi Trung Kiên", "kien.bt@tdtu.edu.vn", "0902000008", [base_user, lecturer_group]),
]
lecturer_users = [user(login, name, email, groups, phone) for login, name, email, phone, groups in lecturer_specs]
lecturers = [u.partner_id for u in lecturer_users]
advisor_partner = lecturer_users[4].partner_id
dean_partner = lecturer_users[5].partner_id

log("Creating faculties, departments, programs, subjects")
faculty_rows = [
    ("CNTT", "Khoa Công nghệ thông tin", dean_partner),
    ("KT", "Khoa Kinh tế", False),
    ("NN", "Khoa Ngoại ngữ", False),
    ("DDT", "Khoa Điện - Điện tử", False),
    ("CTSV", "Phòng Công tác Sinh viên", staff_accounts["affairs"].partner_id),
    ("TCKT", "Phòng Tài chính - Kế toán", staff_accounts["finance"].partner_id),
    ("PDT", "Phòng Đào tạo", staff_accounts["academic"].partner_id),
]
faculties = {}
for code, name, dean in faculty_rows:
    faculties[code] = get_or_create("univ.sms.faculty", [("code", "=", code)], {
        "code": code,
        "name": name,
        "dean_id": dean.id if dean else False,
    }, {
        "name": name,
        "dean_id": dean.id if dean else False,
    })

department_rows = [
    ("KTPM", "Bộ môn Kỹ thuật phần mềm", "CNTT"),
    ("HTTT", "Bộ môn Hệ thống thông tin", "CNTT"),
    ("KHMT", "Bộ môn Khoa học máy tính", "CNTT"),
    ("QTKD", "Bộ môn Quản trị kinh doanh", "KT"),
    ("MKT", "Bộ môn Marketing", "KT"),
    ("NNA", "Bộ môn Ngôn ngữ Anh", "NN"),
    ("TUD", "Bộ môn Tự động hóa", "DDT"),
]
departments = {}
for code, name, faculty_code in department_rows:
    departments[code] = get_or_create("univ.sms.department", [("code", "=", code)], {
        "code": code,
        "name": name,
        "faculty_id": faculties[faculty_code].id,
    }, {
        "name": name,
        "faculty_id": faculties[faculty_code].id,
    })

program_rows = [
    ("7480103", "Kỹ thuật phần mềm", "KTPM", 145, 4),
    ("7480201", "Công nghệ thông tin", "HTTT", 145, 4),
    ("7480101", "Khoa học máy tính", "KHMT", 145, 4),
    ("7340101", "Quản trị kinh doanh", "QTKD", 132, 4),
    ("7340115", "Marketing", "MKT", 132, 4),
    ("7220201", "Ngôn ngữ Anh", "NNA", 130, 4),
    ("7520216", "Kỹ thuật điều khiển và tự động hóa", "TUD", 150, 4),
]
programs = {}
for code, name, dep_code, credits, years in program_rows:
    programs[code] = get_or_create("univ.sms.program", [("code", "=", code)], {
        "code": code,
        "name": name,
        "department_id": departments[dep_code].id,
        "total_credits": credits,
        "duration_years": years,
    }, {
        "name": name,
        "department_id": departments[dep_code].id,
        "total_credits": credits,
        "duration_years": years,
    })

subject_rows = [
    ("MATH101", "Giải tích 1", 3, ["7480103", "7480201", "7480101", "7520216"]),
    ("MATH102", "Đại số tuyến tính", 3, ["7480103", "7480201", "7480101", "7520216"]),
    ("IT101", "Nhập môn lập trình", 3, ["7480103", "7480201", "7480101"]),
    ("IT102", "Cấu trúc dữ liệu và giải thuật", 4, ["7480103", "7480201", "7480101"]),
    ("IT201", "Cơ sở dữ liệu", 3, ["7480103", "7480201", "7480101"]),
    ("IT202", "Lập trình Web", 3, ["7480103", "7480201"]),
    ("IT203", "Công nghệ phần mềm", 3, ["7480103"]),
    ("IT204", "Trí tuệ nhân tạo", 3, ["7480101", "7480201"]),
    ("IT205", "Mạng máy tính", 3, ["7480201", "7480101"]),
    ("BUS101", "Kinh tế vi mô", 3, ["7340101", "7340115"]),
    ("BUS102", "Quản trị học", 3, ["7340101"]),
    ("MKT201", "Marketing căn bản", 3, ["7340115", "7340101"]),
    ("ACC101", "Nguyên lý kế toán", 3, ["7340101", "7340115"]),
    ("ENG101", "Academic English 1", 3, ["7220201", "7480103", "7480201"]),
    ("ENG201", "Translation Practice", 3, ["7220201"]),
    ("AUT101", "Mạch điện", 3, ["7520216"]),
    ("AUT202", "Điều khiển tự động", 4, ["7520216"]),
    ("GEN101", "Pháp luật đại cương", 2, list(programs.keys())),
    ("GEN102", "Kỹ năng học đại học", 2, list(programs.keys())),
]
subjects = {}
for code, name, credit, program_codes in subject_rows:
    subject = get_or_create("univ.sms.subject", [("code", "=", code)], {
        "code": code,
        "name": name,
        "credit": credit,
        "program_ids": [(6, 0, [programs[p].id for p in program_codes])],
    }, {
        "name": name,
        "credit": credit,
        "program_ids": [(6, 0, [programs[p].id for p in program_codes])],
    })
    subjects[code] = subject

if "prerequisite_ids" in env["univ.sms.subject"]._fields:
    subjects["IT102"].write({"prerequisite_ids": [(6, 0, [subjects["IT101"].id])]})
    subjects["IT202"].write({"prerequisite_ids": [(6, 0, [subjects["IT101"].id, subjects["IT201"].id])]})
    subjects["IT203"].write({"prerequisite_ids": [(6, 0, [subjects["IT102"].id])]})
    subjects["AUT202"].write({"prerequisite_ids": [(6, 0, [subjects["AUT101"].id])]})

log("Creating academic years, terms and registration periods")
year_2025 = get_or_create("univ.sms.academic.year", [("name", "=", "2025-2026")], {
    "name": "2025-2026",
    "date_start": "2025-09-01",
    "date_end": "2026-08-31",
})
year_2026 = get_or_create("univ.sms.academic.year", [("name", "=", "2026-2027")], {
    "name": "2026-2027",
    "date_start": "2026-09-01",
    "date_end": "2027-08-31",
})
terms = {}
term_rows = [
    ("HK1 2025-2026", year_2025, "2025-09-01", "2026-01-15"),
    ("HK2 2025-2026", year_2025, "2026-02-01", "2026-06-15"),
    ("HK Hè 2025-2026", year_2025, "2026-06-20", "2026-08-15"),
    ("HK1 2026-2027", year_2026, "2026-09-01", "2027-01-15"),
]
for name, year, start, end in term_rows:
    terms[name] = get_or_create("univ.sms.term", [("name", "=", name), ("academic_year_id", "=", year.id)], {
        "name": name,
        "academic_year_id": year.id,
        "date_start": start,
        "date_end": end,
    }, {
        "date_start": start,
        "date_end": end,
    })

period_current = get_or_create("univ.sms.registration.period", [("name", "=", "Đợt đăng ký HK1 2026-2027 - chính thức")], {
    "name": "Đợt đăng ký HK1 2026-2027 - chính thức",
    "term_id": terms["HK1 2026-2027"].id,
    "date_start": "2026-07-01 08:00:00",
    "date_end": "2026-08-15 17:00:00",
    "reg_type": "regular",
    "min_credit": 0,
    "max_credit": 24,
    "state": "open",
}, {
    "term_id": terms["HK1 2026-2027"].id,
    "date_start": "2026-07-01 08:00:00",
    "date_end": "2026-08-15 17:00:00",
    "state": "open",
})
period_future = get_or_create("univ.sms.registration.period", [("name", "=", "Đợt điều chỉnh đăng ký HK1 2026-2027")], {
    "name": "Đợt điều chỉnh đăng ký HK1 2026-2027",
    "term_id": terms["HK1 2026-2027"].id,
    "date_start": "2026-08-20 08:00:00",
    "date_end": "2026-08-25 17:00:00",
    "reg_type": "regular",
    "min_credit": 0,
    "max_credit": 24,
    "state": "draft",
}, {
    "date_start": "2026-08-20 08:00:00",
    "date_end": "2026-08-25 17:00:00",
    "state": "draft",
})

log("Creating home classes and realistic student accounts")
home_classes = {}
for program in programs.values():
    class_code = "DH25-%s-01" % program.code
    cls = get_or_create("univ.sms.home.class", [("code", "=", class_code)], {
        "name": "Đại học K25 - %s - Lớp 01" % program.name,
        "code": class_code,
        "program_id": program.id,
        "academic_year_id": year_2025.id,
        "advisor_id": advisor_partner.id,
    }, {
        "program_id": program.id,
        "academic_year_id": year_2025.id,
        "advisor_id": advisor_partner.id,
    })
    home_classes[program.code] = cls

student_rows = [
    ("sv.nguyenvanan", "Nguyễn Văn An", "7480103", "0903000001"),
    ("sv.tranthibichngoc", "Trần Thị Bích Ngọc", "7480103", "0903000002"),
    ("sv.levietcuong", "Lê Việt Cường", "7480201", "0903000003"),
    ("sv.phamminhduy", "Phạm Minh Duy", "7480201", "0903000004"),
    ("sv.hoanglananh", "Hoàng Lan Anh", "7480101", "0903000005"),
    ("sv.vuthanhdat", "Vũ Thành Đạt", "7480101", "0903000006"),
    ("sv.dangphuonglinh", "Đặng Phương Linh", "7340101", "0903000007"),
    ("sv.buitrungkien", "Bùi Trung Kiên", "7340101", "0903000008"),
    ("sv.dothuha", "Đỗ Thu Hà", "7340115", "0903000009"),
    ("sv.ngotuananh", "Ngô Tuấn Anh", "7340115", "0903000010"),
    ("sv.maidieulinh", "Mai Diệu Linh", "7220201", "0903000011"),
    ("sv.huynhquanghuy", "Huỳnh Quang Huy", "7220201", "0903000012"),
    ("sv.phanngocmai", "Phan Ngọc Mai", "7520216", "0903000013"),
    ("sv.trinhbaonam", "Trịnh Bảo Nam", "7520216", "0903000014"),
]

students = []
country_vn = env.ref("base.vn", raise_if_not_found=False)
for login, full_name, program_code, phone in student_rows:
    email = "%s@student.tdtu.edu.vn" % login.replace("sv.", "")
    u = user(login, full_name, email, [portal_group], phone)
    u.partner_id.write({
        "street": "%s Nguyễn Hữu Thọ" % random.randint(12, 280),
        "city": "TP. Hồ Chí Minh",
        "country_id": country_vn.id if country_vn else False,
    })
    student = env["univ.sms.student"].search([("partner_id", "=", u.partner_id.id)], limit=1)
    vals = {
        "partner_id": u.partner_id.id,
        "program_id": programs[program_code].id,
        "home_class_id": home_classes[program_code].id,
        "academic_year_id": year_2025.id,
        "training_system": "regular",
        "advisor_id": advisor_partner.id,
        "state": "studying",
        "personal_email": "%s@gmail.com" % login.replace("sv.", ""),
        "date_of_birth": "2005-%02d-%02d" % (random.randint(1, 12), random.randint(1, 25)),
        "gender": random.choice(["male", "female"]),
        "id_number": "079205%06d" % random.randint(100000, 999999),
        "home_address": "Quê quán %s" % random.choice(["Đồng Nai", "Bình Dương", "Long An", "Tiền Giang", "Bến Tre"]),
        "current_address": "Ký túc xá khu B, TP. Hồ Chí Minh",
    }
    if student:
        student.write({k: v for k, v in vals.items() if k != "partner_id"})
    else:
        student = env["univ.sms.student"].create(vals)
    students.append(student)

log("Creating course classes, offerings and timetables")
class_plan = [
    ("IT101", "HK1 2025-2026"), ("IT102", "HK2 2025-2026"), ("IT201", "HK2 2025-2026"),
    ("IT202", "HK1 2026-2027"), ("IT203", "HK1 2026-2027"), ("IT204", "HK1 2026-2027"),
    ("BUS101", "HK1 2025-2026"), ("BUS102", "HK2 2025-2026"), ("MKT201", "HK1 2026-2027"),
    ("ACC101", "HK1 2026-2027"), ("ENG101", "HK1 2025-2026"), ("ENG201", "HK1 2026-2027"),
    ("AUT101", "HK1 2025-2026"), ("AUT202", "HK1 2026-2027"), ("GEN101", "HK1 2025-2026"),
    ("GEN102", "HK2 2025-2026"), ("MATH101", "HK1 2025-2026"), ("MATH102", "HK2 2025-2026"),
]
classes = {}
offerings = {}
for idx, (subject_code, term_name) in enumerate(class_plan, start=1):
    subject = subjects[subject_code]
    term = terms[term_name]
    code = "%s-%s-01" % (subject_code, term_name.split()[0].replace("HK", ""))
    course_class = get_or_create("univ.sms.class", [("code", "=", code)], {
        "name": "%s - Nhóm 01" % subject.name,
        "code": code,
        "subject_id": subject.id,
        "lecturer_id": lecturers[idx % len(lecturers)].id,
        "term_id": term.id,
        "max_students": 45,
        "state": "open" if term_name == "HK1 2026-2027" else "closed",
    }, {
        "lecturer_id": lecturers[idx % len(lecturers)].id,
        "term_id": term.id,
        "state": "open" if term_name == "HK1 2026-2027" else "closed",
    })
    classes[subject_code] = course_class
    offerings[subject_code] = get_or_create("univ.sms.course.offering", [("class_id", "=", course_class.id)], {
        "subject_id": subject.id,
        "term_id": term.id,
        "lecturer_id": course_class.lecturer_id.id,
        "class_id": course_class.id,
        "max_seats": 45,
        "active": True,
    }, {
        "term_id": term.id,
        "lecturer_id": course_class.lecturer_id.id,
        "max_seats": 45,
        "active": True,
    })
    start_time = random.choice([7.0, 9.0, 13.0, 15.0])
    get_or_create("univ.sms.timetable", [("class_id", "=", course_class.id), ("day_of_week", "=", str(idx % 6))], {
        "class_id": course_class.id,
        "day_of_week": str(idx % 6),
        "start_time": start_time,
        "end_time": start_time + 2.0,
        "room": "P.%s" % random.choice(["A101", "A203", "B305", "C402", "LAB1", "LAB2"]),
        "building": random.choice(["Nhà A", "Nhà B", "Khu thực hành"]),
    })

log("Creating enrollments, course registrations and cancellations")
program_subject_map = {
    "7480103": ["IT101", "IT102", "IT201", "IT202", "IT203", "MATH101", "MATH102", "GEN101", "GEN102"],
    "7480201": ["IT101", "IT102", "IT201", "IT202", "IT204", "IT205", "MATH101", "MATH102", "GEN101"],
    "7480101": ["IT101", "IT102", "IT201", "IT204", "IT205", "MATH101", "MATH102", "GEN101"],
    "7340101": ["BUS101", "BUS102", "ACC101", "MKT201", "GEN101", "GEN102", "ENG101"],
    "7340115": ["BUS101", "MKT201", "ACC101", "GEN101", "GEN102", "ENG101"],
    "7220201": ["ENG101", "ENG201", "GEN101", "GEN102"],
    "7520216": ["AUT101", "AUT202", "MATH101", "MATH102", "GEN101", "GEN102"],
}
past_terms = {"HK1 2025-2026", "HK2 2025-2026"}
for student in students:
    program_code = student.program_id.code
    subject_codes = program_subject_map.get(program_code, ["GEN101", "GEN102"])
    for subject_code in subject_codes:
        if subject_code not in classes:
            continue
        course_class = classes[subject_code]
        term_name = next(name for name, term in terms.items() if term.id == course_class.term_id.id)
        state = "completed" if term_name in past_terms else "registered"
        get_or_create("univ.sms.enrollment", [
            ("student_id", "=", student.id),
            ("subject_id", "=", subjects[subject_code].id),
            ("term_id", "=", course_class.term_id.id),
        ], {
            "student_id": student.id,
            "subject_id": subjects[subject_code].id,
            "term_id": course_class.term_id.id,
            "class_id": course_class.id,
            "state": state,
        }, {
            "class_id": course_class.id,
            "state": state,
        })

log("Creating attendance, exams, results and transcripts")
for course_class in classes.values():
    registered_enrollments = env["univ.sms.enrollment"].search([
        ("class_id", "=", course_class.id),
        ("state", "in", ["registered", "completed"]),
    ])
    if not registered_enrollments:
        continue
    for week in range(1, 4):
        attendance_date = course_class.term_id.date_start + timedelta(days=7 * week)
        sheet = get_or_create("univ.sms.attendance.sheet", [
            ("class_id", "=", course_class.id),
            ("attendance_date", "=", attendance_date),
        ], {
            "class_id": course_class.id,
            "attendance_date": attendance_date,
            "state": "draft",
        })
        if not sheet.line_ids:
            sheet.action_load_students()
        for enrollment in registered_enrollments:
            if not sheet.line_ids.filtered(lambda line: line.student_id == enrollment.student_id):
                env["univ.sms.attendance.line"].create({
                    "sheet_id": sheet.id,
                    "student_id": enrollment.student_id.id,
                    "state": "present",
                })
        for line in sheet.line_ids:
            line.state = random.choices(["present", "late", "excused", "absent"], weights=[78, 10, 7, 5])[0]
        if sheet.line_ids and sheet.state != "confirmed":
            sheet.action_confirm()

    for exam_type, suffix, offset in [("midterm", "Giữa kỳ", 45), ("final", "Cuối kỳ", 95)]:
        exam_date = course_class.term_id.date_start + timedelta(days=offset)
        exam = get_or_create("univ.sms.exam", [
            ("class_id", "=", course_class.id),
            ("exam_type", "=", exam_type),
        ], {
            "name": "%s - %s" % (suffix, course_class.name),
            "class_id": course_class.id,
            "exam_type": exam_type,
            "date": exam_date,
            "max_score": 10.0,
            "state": "draft",
        }, {
            "date": exam_date,
        })
        exam.action_load_students()
        for enrollment in registered_enrollments:
            if not exam.result_ids.filtered(lambda result: result.student_id == enrollment.student_id):
                env["univ.sms.exam.result"].create({
                    "exam_id": exam.id,
                    "student_id": enrollment.student_id.id,
                    "score": 0.0,
                })
        for result in exam.result_ids:
            result.score = round(random.uniform(5.0, 9.6), 1)
        exam.action_start_grading()
        exam.action_done()

for student in students:
    student_terms = env["univ.sms.enrollment"].search([("student_id", "=", student.id)]).mapped("term_id")
    for term in student_terms:
        transcript = get_or_create("univ.sms.transcript", [
            ("student_id", "=", student.id),
            ("term_id", "=", term.id),
        ], {
            "student_id": student.id,
            "term_id": term.id,
        })
        transcript.action_generate_from_enrollments()
        for line in transcript.line_ids:
            if not line.final_score:
                line.final_score = round(random.uniform(5.0, 9.4), 1)

log("Creating current course registrations and one cancelled registration")
for student in students:
    current_enrollments = env["univ.sms.enrollment"].search([
        ("student_id", "=", student.id),
        ("term_id", "=", terms["HK1 2026-2027"].id),
        ("state", "=", "registered"),
    ])
    for enrollment in current_enrollments:
        offering = offerings.get(enrollment.subject_id.code)
        if not offering:
            continue
        get_or_create("univ.sms.registration", [
            ("student_id", "=", student.id),
            ("offering_id", "=", offering.id),
        ], {
            "student_id": student.id,
            "offering_id": offering.id,
            "period_id": period_current.id,
            "state": "registered",
        }, {
            "period_id": period_current.id,
            "state": "registered",
        })

cancel_student = students[0]
if "IT204" in offerings:
    get_or_create("univ.sms.registration", [
        ("student_id", "=", cancel_student.id),
        ("offering_id", "=", offerings["IT204"].id),
    ], {
        "student_id": cancel_student.id,
        "offering_id": offerings["IT204"].id,
        "period_id": period_current.id,
        "state": "cancelled",
    }, {"state": "cancelled"})

log("Creating fees and invoices")
for student in students:
    for term in [terms["HK1 2025-2026"], terms["HK2 2025-2026"], terms["HK1 2026-2027"]]:
        if not env["univ.sms.enrollment"].search_count([("student_id", "=", student.id), ("term_id", "=", term.id)]):
            continue
        fee = get_or_create("univ.sms.fee", [
            ("student_id", "=", student.id),
            ("term_id", "=", term.id),
        ], {
            "student_id": student.id,
            "term_id": term.id,
            "fee_per_credit": 650000.0,
        }, {
            "fee_per_credit": 650000.0,
        })
        if not fee.invoice_ids:
            invoice = env["univ.sms.fee.invoice"].create({
                "fee_id": fee.id,
                "student_id": student.id,
                "partner_id": student.partner_id.id,
                "term_id": term.id,
                "amount_total": fee.total_amount,
                "state": random.choice(["paid", "confirmed", "draft"]),
            })
            enrollments = env["univ.sms.enrollment"].search([
                ("student_id", "=", student.id),
                ("term_id", "=", term.id),
                ("state", "!=", "cancelled"),
            ])
            for enrollment in enrollments:
                env["univ.sms.fee.invoice.line"].create({
                    "invoice_id": invoice.id,
                    "name": "Học phần %s (%s)" % (enrollment.subject_id.name, enrollment.subject_id.code),
                    "subject_id": enrollment.subject_id.id,
                    "credit": enrollment.subject_id.credit,
                    "quantity": enrollment.subject_id.credit,
                    "price_unit": 650000.0,
                })

log("Creating student affairs, certificates, conduct, surveys, feedback")
conduct_criteria_rows = [
    ("Chuyên cần học tập", "study_attitude", 10),
    ("Đạt kết quả học tập", "study_attitude", 10),
    ("Chấp hành nội quy trường", "discipline", 10),
    ("Tham dự đầy đủ các buổi học", "discipline", 10),
    ("Tham gia câu lạc bộ, đội nhóm", "activity", 10),
    ("Tình nguyện, hoạt động xã hội", "activity", 10),
    ("Quan hệ tốt với bạn bè", "citizen", 10),
    ("Tham gia hoạt động lớp", "class_role", 10),
]
for name, group_name, max_score in conduct_criteria_rows:
    get_or_create("univ.sms.conduct.criteria", [
        ("name", "=", name),
        ("group_name", "=", group_name),
    ], {
        "name": name,
        "group_name": group_name,
        "max_score": max_score,
        "active": True,
    }, {
        "max_score": max_score,
        "active": True,
    })

for student in students:
    get_or_create("univ.sms.health.insurance", [("student_id", "=", student.id)], {
        "student_id": student.id,
        "insurance_code": "HS%08d" % random.randint(10000000, 99999999),
        "date_start": "2025-09-01",
        "date_end": "2026-08-31",
        "payment_state": random.choice(["paid", "paid", "unpaid"]),
        "state": "confirmed",
    })
    get_or_create("univ.sms.residence.info", [("student_id", "=", student.id)], {
        "student_id": student.id,
        "residence_type": random.choice(["dormitory", "rent", "family"]),
        "address": random.choice(["KTX Khu B", "120 Nguyễn Hữu Thọ", "45 Lê Văn Lương", "Nhà riêng tại TP. Thủ Đức"]),
        "landlord_name": random.choice(["Nguyễn Văn Thành", "Trần Thị Hoa", "Ban quản lý KTX"]),
        "landlord_phone": "0904%06d" % random.randint(100000, 999999),
        "effective_date": "2025-09-01",
        "state": "confirmed",
    })
    military = get_or_create("univ.sms.military.service", [("student_id", "=", student.id)], {
        "student_id": student.id,
        "registration_status": random.choice(["registered", "deferred", "not_registered"]),
        "declared_date": "2025-09-15",
        "state": random.choice(["submitted", "approved"]),
    })

certificate_types = []
for code, name, fee in [("XNSV", "Giấy xác nhận sinh viên", 20000), ("VAYVON", "Giấy xác nhận vay vốn", 0), ("TAMHOAN", "Giấy xác nhận tạm hoãn NVQS", 0)]:
    certificate_types.append(get_or_create("univ.sms.certificate.type", [("code", "=", code)], {
        "code": code,
        "name": name,
        "require_fee": bool(fee),
        "fee_amount": fee,
    }, {
        "name": name,
        "require_fee": bool(fee),
        "fee_amount": fee,
    }))

for index, student in enumerate(students):
    cert_type = certificate_types[index % len(certificate_types)]
    get_or_create("univ.sms.certificate.request", [
        ("student_id", "=", student.id),
        ("certificate_type_id", "=", cert_type.id),
    ], {
        "student_id": student.id,
        "certificate_type_id": cert_type.id,
        "reason": random.choice(["Nộp hồ sơ học bổng", "Bổ sung hồ sơ vay vốn", "Xác nhận đang học tại trường"]),
        "fee_payment_state": "paid" if cert_type.require_fee else "unpaid",
        "state": random.choice(["draft", "approved", "completed"]),
    })

criteria = env["univ.sms.conduct.criteria"].search([("active", "=", True)], limit=8)
for student in students:
    score = get_or_create("univ.sms.conduct.score", [
        ("student_id", "=", student.id),
        ("period_id", "=", terms["HK2 2025-2026"].id),
    ], {
        "student_id": student.id,
        "period_id": terms["HK2 2025-2026"].id,
        "state": random.choice(["submitted", "advisor_approved", "dean_approved"]),
    })
    for criterion in criteria:
        get_or_create("univ.sms.conduct.score.line", [
            ("conduct_score_id", "=", score.id),
            ("criteria_id", "=", criterion.id),
        ], {
            "conduct_score_id": score.id,
            "criteria_id": criterion.id,
            "self_score": min(criterion.max_score, random.randint(max(1, criterion.max_score - 4), criterion.max_score)),
            "advisor_score": min(criterion.max_score, random.randint(max(1, criterion.max_score - 3), criterion.max_score)),
            "final_score": min(criterion.max_score, random.randint(max(1, criterion.max_score - 2), criterion.max_score)),
        })

survey_type = get_or_create("univ.sms.survey.type", [("code", "=", "DGGD2026")], {
    "code": "DGGD2026",
    "name": "Đánh giá chất lượng giảng dạy 2026",
    "description": "Khảo sát mức độ hài lòng về học phần và giảng viên",
})
survey = get_or_create("univ.sms.survey.instance", [("name", "=", "Khảo sát giảng dạy HK2 2025-2026")], {
    "name": "Khảo sát giảng dạy HK2 2025-2026",
    "survey_type_id": survey_type.id,
    "date_start": "2026-07-01",
    "date_end": "2026-07-31",
    "state": "open",
})
for student in students[:10]:
    response = get_or_create("univ.sms.survey.response", [
        ("student_id", "=", student.id),
        ("survey_instance_id", "=", survey.id),
    ], {
        "student_id": student.id,
        "survey_instance_id": survey.id,
        "answer_data": random.choice([
            "Giảng viên phản hồi nhanh, bài giảng dễ hiểu.",
            "Mong tăng thêm bài tập thực hành theo nhóm.",
            "Phòng học ổn, hệ thống đăng ký môn đã dễ dùng hơn.",
        ]),
        "state": "submitted",
    })
    if response.state != "submitted":
        response.action_submit()

feedback_subjects = ["Wifi phòng học yếu", "Cần mở thêm lớp Lập trình Web", "Thắc mắc học phí HK1", "Đề xuất bổ sung tài liệu môn AI"]
for idx, student in enumerate(students[:8]):
    get_or_create("univ.sms.feedback", [
        ("student_id", "=", student.id),
        ("subject", "=", feedback_subjects[idx % len(feedback_subjects)]),
    ], {
        "student_id": student.id,
        "category": random.choice(["academic", "facility", "service", "other"]),
        "subject": feedback_subjects[idx % len(feedback_subjects)],
        "description": "Sinh viên gửi góp ý qua cổng portal để nhà trường xử lý.",
        "department_id": random.choice(list(departments.values())).id,
        "state": random.choice(["new", "in_progress", "resolved"]),
        "response": "Nhà trường đã tiếp nhận và đang xử lý." if idx % 2 else "",
    })

log("Creating published notifications")
notifications = [
    ("Lịch đăng ký học kỳ 1 năm học 2026-2027", "Đợt đăng ký chính thức mở từ 01/07/2026 đến 15/08/2026."),
    ("Thông báo đóng học phí học kỳ 1", "Sinh viên kiểm tra công nợ và hóa đơn trong mục Học phí trên portal."),
    ("Khai báo nghĩa vụ quân sự năm học mới", "Sinh viên hoàn tất khai báo trong mục Công tác SV trước 31/08/2026."),
    ("Khảo sát chất lượng giảng dạy", "Nhà trường mời sinh viên phản hồi khảo sát để cải thiện chất lượng đào tạo."),
]
for title, body in notifications:
    get_or_create("univ.sms.notification", [("title", "=", title)], {
        "title": title,
        "content": body,
        "target_audience": "all",
        "is_pinned": title.startswith("Lịch"),
        "state": "published",
    }, {
        "content": body,
        "state": "published",
    })

log("Cleaning up records created with broken terminal encoding")
bad_current_periods = env["univ.sms.registration.period"].search([
    ("name", "like", "?"),
    ("date_start", "=", "2026-07-01 08:00:00"),
])
if bad_current_periods:
    env["univ.sms.registration"].search([("period_id", "in", bad_current_periods.ids)]).write({
        "period_id": period_current.id,
    })
    bad_current_periods.unlink()

bad_future_periods = env["univ.sms.registration.period"].search([
    ("name", "like", "?"),
    ("date_start", "=", "2026-08-20 08:00:00"),
])
if bad_future_periods:
    env["univ.sms.registration"].search([("period_id", "in", bad_future_periods.ids)]).write({
        "period_id": period_future.id,
    })
    bad_future_periods.unlink()

env["univ.sms.notification"].search([
    "|",
    ("title", "like", "?"),
    ("content", "like", "?"),
]).unlink()

bad_surveys = env["univ.sms.survey.instance"].search([("name", "like", "?")])
if bad_surveys:
    env["univ.sms.survey.response"].search([("survey_instance_id", "in", bad_surveys.ids)]).unlink()
    bad_surveys.unlink()
bad_survey_types = env["univ.sms.survey.type"].search([
    "|",
    ("name", "like", "?"),
    ("description", "like", "?"),
])
for survey_type_record in bad_survey_types:
    if survey_type_record.code == "DGGD2026":
        survey_type_record.write({
            "name": "Đánh giá chất lượng giảng dạy 2026",
            "description": "Khảo sát mức độ hài lòng về học phần và giảng viên",
        })
    elif not env["univ.sms.survey.instance"].search_count([("survey_type_id", "=", survey_type_record.id)]):
        survey_type_record.unlink()

env["univ.sms.feedback"].search([
    "|", "|", "|",
    ("subject", "like", "?"),
    ("description", "like", "?"),
    ("response", "like", "?"),
    ("category", "like", "?"),
]).unlink()

env["univ.sms.certificate.request"].search([("reason", "like", "?")]).write({
    "reason": "Xác nhận đang học tại trường",
})

env.cr.commit()
log("Done. Realistic university dataset is ready.")
log("Sample accounts:")
log("  Student: sv.nguyenvanan / 123456")
log("  Student: sv.tranthibichngoc / 123456")
log("  Lecturer: gv.tranminhduc / 123456")
log("  Academic office: dt.nguyenthilan / 123456")
log("  Student affairs: ctsv.levanhoa / 123456")
log("  Finance office: tc.phamquanghuy / 123456")
