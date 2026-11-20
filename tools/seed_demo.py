# -*- coding: utf-8 -*-
"""Seed dữ liệu DEMO chuẩn cho University SMS (Odoo 17).

Chạy (Git Bash, thư mục gốc repo):
    MSYS_NO_PATHCONV=1 docker compose run --rm -T odoo odoo shell \
        -c /etc/odoo/odoo.conf -d <db> --no-http < tools/seed_demo.py

Nguyên tắc:
* Lặp an toàn (idempotent): chạy lại không sinh bản ghi trùng. Bản ghi được nhận
  diện bằng xml id trong ``ir.model.data`` (module ``__demo_seed__``) hoặc mã duy nhất.
* KHÔNG xóa dữ liệu có sẵn. Không đụng tài khoản admin gốc của Odoo.
* Dữ liệu hư cấu: tên giả, email ``@demo.univ.test``, số điện thoại 09xx giả.
* Ngày tháng tính theo ngày chạy (học kỳ hiện tại chứa hôm nay, học kỳ trước đã xong).
* Đi theo workflow thật: gọi action/service (register_student, action_load_students,
  action_generate_from_enrollments, run_evaluation, ...) thay vì ghi thẳng state.
* Mật khẩu mọi tài khoản demo: Demo@2026 (đặt lại mỗi lần chạy).

Tài liệu tài khoản + kịch bản demo: docs/TAI_KHOAN_DEMO.md
"""
import random
import traceback
from datetime import date, datetime, time, timedelta

from odoo import fields

PASSWORD = 'Demo@2026'
MOD = '__demo_seed__'
EMAIL_DOMAIN = 'demo.univ.test'

env = env(context=dict(env.context, tracking_disable=True, mail_create_nolog=True,  # noqa: F821
                       mail_notrack=True, no_reset_password=True, lang='vi_VN'))

TODAY = date.today()
NOW = fields.Datetime.now()
ERRORS = []
STATS = {}


def log(msg):
    print('[seed_demo] %s' % msg, flush=True)


def bump(key, n=1):
    STATS[key] = STATS.get(key, 0) + n


# ═════════════════════════════════════════════════════════════════════════════
# Tiện ích xml id / get-or-create
# ═════════════════════════════════════════════════════════════════════════════
IMD = env['ir.model.data'].sudo()
_XCACHE = {d.name: d for d in IMD.search([('module', '=', MOD)])}


def xref(name):
    d = _XCACHE.get(name)
    if not d:
        return None
    rec = env[d.model].browse(d.res_id).exists()
    return rec or None


def bind(name, rec):
    d = _XCACHE.get(name)
    if d:
        if d.res_id != rec.id or d.model != rec._name:
            d.write({'res_id': rec.id, 'model': rec._name})
        return
    _XCACHE[name] = IMD.create({
        'module': MOD, 'name': name, 'model': rec._name, 'res_id': rec.id, 'noupdate': True})


def ensure(name, model, vals, domain=None):
    """Lấy theo xml id → theo domain → tạo mới. Trả về (record, created)."""
    rec = xref(name)
    if not rec and domain:
        rec = env[model].with_context(active_test=False).search(domain, limit=1) or None
    created = False
    if not rec:
        rec = env[model].create(vals)
        created = True
        bump('created:' + model)
    bind(name, rec)
    return rec, created


def get_or_create(model, domain, vals):
    rec = env[model].with_context(active_test=False).search(domain, limit=1)
    if rec:
        return rec, False
    bump('created:' + model)
    return env[model].create(vals), True


class Section:
    """Bọc một phần seed tùy chọn trong savepoint: lỗi được ghi lại, phần khác vẫn chạy."""

    def __init__(self, name, optional=True):
        self.name, self.optional = name, optional

    def __enter__(self):
        log('── %s' % self.name)
        self.sp = env.cr.savepoint()
        self.sp.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.sp.__exit__(None, None, None)
            return False
        self.sp.__exit__(exc_type, exc, tb)  # rollback savepoint
        env.invalidate_all()
        ERRORS.append('%s: %s' % (self.name, exc))
        log('!! LỖI ở phần "%s": %s' % (self.name, exc))
        traceback.print_exception(exc_type, exc, tb)
        return self.optional  # phần bắt buộc: ném tiếp


def dt(d, hour=8, minute=0):
    return datetime.combine(d, time(hour, minute))


# ═════════════════════════════════════════════════════════════════════════════
# 0. Học kỳ: hiện tại chứa hôm nay, học kỳ trước đã kết thúc
# ═════════════════════════════════════════════════════════════════════════════
TERM_NAMES = {'HK1': 'Học kỳ 1', 'HK2': 'Học kỳ 2', 'HE': 'Học kỳ hè'}


def term_dates(code, ay):
    if code == 'HK1':
        return date(ay, 9, 1), date(ay + 1, 1, 15)
    if code == 'HK2':
        return date(ay + 1, 1, 16), date(ay + 1, 6, 30)
    return date(ay + 1, 7, 1), date(ay + 1, 8, 31)


def current_term_key(today):
    y = today.year
    if today >= date(y, 9, 1):
        return 'HK1', y
    if today <= date(y, 1, 15):
        return 'HK1', y - 1
    if today <= date(y, 6, 30):
        return 'HK2', y - 1
    return 'HE', y - 1


def previous_term_key(code, ay):
    if code == 'HK1':
        return 'HK2', ay - 1
    if code == 'HK2':
        return 'HK1', ay
    return 'HK2', ay  # kỳ hè: kỳ trước là HK2 cùng năm học


def ensure_year(ay):
    name = '%s-%s' % (ay, ay + 1)
    rec, _c = ensure('ay_%s' % ay, 'univ.sms.academic.year', {
        'name': name, 'date_start': date(ay, 9, 1), 'date_end': date(ay + 1, 8, 31),
    }, domain=[('name', '=', name)])
    return rec


def ensure_term(code, ay):
    year = ensure_year(ay)
    ds, de = term_dates(code, ay)
    rec, _c = ensure('term_%s_%s' % (ay, code), 'univ.sms.term', {
        'name': TERM_NAMES[code], 'academic_year_id': year.id, 'date_start': ds, 'date_end': de,
    }, domain=[('academic_year_id', '=', year.id), ('name', '=', TERM_NAMES[code])])
    return rec


def meeting_dates(days, start, before, n):
    out, d = [], start
    while d < before and len(out) < n:
        if str(d.weekday()) in days:
            out.append(d)
        d += timedelta(days=1)
    return out


# ═════════════════════════════════════════════════════════════════════════════
# Dữ liệu khai báo
# ═════════════════════════════════════════════════════════════════════════════
STAFF = [
    # key, login, tên, nhóm
    ('admin', 'admin.demo', 'Lê Minh Quân (Quản trị SMS)', ['univ_sms_base.group_univ_admin']),
    ('daotao', 'daotao.demo', 'Trần Thị Hồng (Phòng Đào tạo)', ['univ_sms_base.group_univ_academic_officer']),
    ('taichinh', 'taichinh.demo', 'Phạm Văn Tài (Phòng Tài chính)', ['univ_sms_base.group_univ_finance_office']),
    ('ctsv', 'ctsv.demo', 'Nguyễn Thị Thu (Phòng CTSV)', ['univ_sms_base.group_univ_student_affairs_office']),
    ('truongkhoa', 'truongkhoa.demo', 'PGS.TS. Võ Thanh Bình (Trưởng khoa CNTT)', ['univ_sms_base.group_univ_dean']),
    ('covan', 'covan.demo', 'ThS. Đặng Minh Châu (Cố vấn học tập)', ['univ_sms_base.group_univ_advisor']),
    ('covan2', 'covan2.demo', 'ThS. Hồ Thị Diễm (Cố vấn học tập)', ['univ_sms_base.group_univ_advisor']),
    ('gv', 'giangvien.demo', 'TS. Trần Minh Đức', ['univ_sms_base.group_univ_lecturer']),
    ('gv2', 'giangvien2.demo', 'ThS. Nguyễn Thu Thảo', ['univ_sms_base.group_univ_lecturer']),
]
# Giảng viên không có tài khoản (chỉ là partner) để chia lớp cho thực tế
EXTRA_LECTURERS = [('gv3', 'ThS. Lê Việt Anh'), ('gv4', 'ThS. Hoàng Ngọc Mai')]

FACULTIES = [('FIT', 'Khoa Công nghệ Thông tin', 'truongkhoa'), ('FEB', 'Khoa Kinh tế', None)]
DEPARTMENTS = [
    ('FIT-CNPM', 'Bộ môn Công nghệ Phần mềm', 'FIT'),
    ('FIT-HTTT', 'Bộ môn Hệ thống Thông tin', 'FIT'),
    ('FEB-QTKD', 'Bộ môn Quản trị Kinh doanh', 'FEB'),
]
PROGRAMS = [
    ('KTPM', 'Kỹ thuật Phần mềm', 'FIT-CNPM', 140),
    ('CNTT', 'Công nghệ Thông tin', 'FIT-HTTT', 140),
    ('QTKD', 'Quản trị Kinh doanh', 'FEB-QTKD', 125),
]
IT, BA = ['KTPM', 'CNTT'], ['QTKD']
ALL = IT + BA
SUBJECTS = [
    # code, tên, tín chỉ, ngành, tiên quyết
    ('IT1101', 'Lập trình cơ bản', 3, IT, []),
    ('IT1102', 'Toán rời rạc', 3, IT, []),
    ('IT1103', 'Kiến trúc máy tính', 3, IT, []),
    ('IT2101', 'Lập trình nâng cao', 3, IT, ['IT1101']),
    ('IT2102', 'Cấu trúc dữ liệu và giải thuật', 3, IT, ['IT1101']),
    ('IT2103', 'Cơ sở dữ liệu', 3, IT, []),
    ('IT2104', 'Mạng máy tính', 3, IT, []),
    ('IT2105', 'Hệ điều hành', 3, IT, []),
    ('IT3101', 'Công nghệ phần mềm', 3, IT, ['IT2102']),
    ('IT3102', 'Phát triển ứng dụng web', 3, IT, ['IT2103']),
    ('IT3103', 'Trí tuệ nhân tạo', 3, IT, []),
    ('IT3104', 'An toàn thông tin', 2, IT, []),
    ('GE1001', 'Triết học Mác - Lênin', 3, ALL, []),
    ('GE1002', 'Tiếng Anh 1', 2, ALL, []),
    ('GE1003', 'Tiếng Anh 2', 2, ALL, ['GE1002']),
    ('GE1004', 'Giải tích', 3, ALL, []),
    ('BA1101', 'Kinh tế vi mô', 3, BA, []),
    ('BA1102', 'Nguyên lý kế toán', 3, BA, []),
    ('BA2101', 'Quản trị học', 3, BA, []),
    ('BA2102', 'Marketing căn bản', 3, BA, []),
    ('BA2103', 'Tài chính doanh nghiệp', 3, BA, ['BA1102']),
]
HOME_CLASSES = [
    # key, mã, tên, ngành, cố vấn, số SV khối lượng (không tài khoản)
    ('A', 'DH20KTPM-A', 'Đại học Kỹ thuật Phần mềm K20 - Lớp A', 'KTPM', 'covan', 16),
    ('B', 'DH20CNTT-B', 'Đại học Công nghệ Thông tin K20 - Lớp B', 'CNTT', 'covan2', 24),
    ('C', 'DH20QTKD-C', 'Đại học Quản trị Kinh doanh K20 - Lớp C', 'QTKD', 'covan2', 30),
    ('D', 'DH20CNTT-D', 'Đại học Công nghệ Thông tin K20 - Lớp D', 'CNTT', 'covan', 30),
]
# Sinh viên có tài khoản portal + kịch bản
SCENARIO_STUDENTS = [
    # n, tên, giới tính, lớp HC
    (1, 'Nguyễn Văn An', 'male', 'A'),
    (2, 'Trần Thị Bình', 'female', 'A'),
    (3, 'Lê Hoàng Cường', 'male', 'A'),
    (4, 'Phạm Thu Dung', 'female', 'A'),
    (5, 'Hoàng Minh Đức', 'male', 'A'),
    (6, 'Vũ Thị Hà', 'female', 'A'),
    (7, 'Đặng Quốc Huy', 'male', 'A'),
    (8, 'Bùi Thanh Hương', 'female', 'A'),
    (9, 'Đỗ Văn Khánh', 'male', 'A'),
    (10, 'Ngô Thị Lan', 'female', 'A'),
    (11, 'Dương Văn Minh', 'male', 'B'),
    (12, 'Lý Thị Ngọc', 'female', 'B'),
]

HO = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng',
      'Bùi', 'Đỗ', 'Hồ', 'Ngô', 'Dương', 'Lý', 'Trương', 'Đinh', 'Mai', 'Tạ']
DEM_M = ['Văn', 'Minh', 'Quốc', 'Đức', 'Hữu', 'Thành', 'Gia', 'Hoàng', 'Anh', 'Tuấn']
DEM_F = ['Thị', 'Ngọc', 'Thu', 'Thanh', 'Bảo', 'Khánh', 'Mỹ', 'Phương', 'Hồng', 'Kim']
TEN_M = ['An', 'Bảo', 'Cường', 'Dũng', 'Hải', 'Hiếu', 'Huy', 'Khang', 'Khoa', 'Long',
         'Nam', 'Phúc', 'Quang', 'Sơn', 'Tài', 'Thắng', 'Tuấn', 'Việt', 'Vinh', 'Trung']
TEN_F = ['Anh', 'Chi', 'Dung', 'Giang', 'Hà', 'Hạnh', 'Hoa', 'Hương', 'Lan', 'Linh',
         'My', 'Ngân', 'Nhung', 'Oanh', 'Quỳnh', 'Trang', 'Uyên', 'Vy', 'Thảo', 'Yến']

# Lớp học kỳ trước: key, môn, giảng viên, lịch [(thứ, bắt đầu, kết thúc, phòng)], nhóm SV
PREV_CLASSES = [
    ('LTCB', 'IT1101', 'gv', [('0', 7.0, 9.5, 'A1.101')], 'IT'),
    ('TRR', 'IT1102', 'gv2', [('1', 7.0, 9.5, 'A1.102')], 'IT'),
    ('TRIET', 'GE1001', 'gv3', [('2', 7.0, 9.5, 'C1.101')], 'ALL'),
    ('TA1', 'GE1002', 'gv4', [('3', 7.0, 9.0, 'C3.301')], 'ALL'),
    ('GT', 'GE1004', 'gv3', [('4', 7.0, 9.5, 'C1.102')], 'ALL'),
    ('KTVM', 'BA1101', 'gv4', [('0', 13.0, 15.5, 'D1.101')], 'BA'),
    ('NLKT', 'BA1102', 'gv2', [('1', 13.0, 15.5, 'D1.102')], 'BA'),
]
# Lớp học kỳ hiện tại (+ lớp môn học mở đăng ký): key, môn, GV, lịch, số chỗ, nhãn nhóm
CUR_CLASSES = [
    ('LTNC', 'IT2101', 'gv', [('0', 7.0, 9.5, 'A1.101')], 90, ''),
    ('CTDL', 'IT2102', 'gv', [('1', 7.0, 9.5, 'A1.102')], 90, ''),
    ('CSDL1', 'IT2103', 'gv', [('2', 13.0, 15.5, 'A2.201')], 60, 'Nhóm 1'),
    ('CSDL2', 'IT2103', 'gv2', [('4', 7.0, 9.5, 'A2.202')], 45, 'Nhóm 2'),
    # Trùng lịch CÓ CHỦ Ý với LTNC (Thứ Hai 07:00-09:30)
    ('MMT', 'IT2104', 'gv2', [('0', 8.0, 10.5, 'B1.105')], 60, ''),
    ('HDH', 'IT2105', 'gv3', [('3', 7.0, 9.5, 'A1.103')], 90, ''),
    ('TA2N1', 'GE1003', 'gv2', [('5', 7.0, 9.0, 'C3.301')], 90, 'Nhóm 1'),
    ('TA2N2', 'GE1003', 'gv4', [('5', 9.5, 11.5, 'C3.302')], 40, 'Nhóm 2'),
    # Chỉ 2 chỗ: đã đầy để demo danh sách chờ
    ('AI', 'IT3103', 'gv2', [('4', 13.0, 15.5, 'A3.301')], 2, 'Chuyên đề (2 chỗ)'),
    ('ATTT', 'IT3104', 'gv3', [('5', 13.0, 15.0, 'A3.302')], 40, ''),
    ('QTH', 'BA2101', 'gv4', [('1', 13.0, 15.5, 'D1.101')], 40, ''),
    ('MKT', 'BA2102', 'gv2', [('2', 7.0, 9.5, 'D1.103')], 40, ''),
    ('TCDN', 'BA2103', 'gv4', [('3', 13.0, 15.5, 'D1.102')], 40, ''),
]

# Điểm học kỳ trước theo kịch bản (môn → điểm tổng kết)
SCENARIO_SCORES = {
    5: {'IT1101': 5.5, 'IT1102': 3.5, 'GE1001': 4.0, 'GE1002': 5.0, 'GE1004': 3.0},   # GPA < 5
    6: {'IT1101': 7.5, 'IT1102': 4.0, 'GE1001': 4.5, 'GE1002': 8.0, 'GE1004': 7.0},   # trượt 2 môn
    7: {'IT1101': 3.3, 'IT1102': 6.5, 'GE1001': 7.0, 'GE1002': 7.0, 'GE1004': 6.8},   # trượt tiên quyết
    12: {'IT1101': 9.5, 'IT1102': 9.2, 'GE1001': 9.0, 'GE1002': 9.4, 'GE1004': 9.1},  # xuất sắc
}
PREREQ_CODES = {'IT1101', 'GE1002', 'BA1102'}


# ═════════════════════════════════════════════════════════════════════════════
# 1. Tài khoản cán bộ / giảng viên
# ═════════════════════════════════════════════════════════════════════════════
def ensure_user(login, name, group_xmlids, partner=None, email=None, phone=None, portal=False):
    Users = env['res.users'].with_context(active_test=False, no_reset_password=True)
    groups = [env.ref('base.group_portal').id] if portal else [env.ref('base.group_user').id]
    groups += [env.ref(x).id for x in group_xmlids]
    vals = {'name': name, 'login': login, 'password': PASSWORD, 'active': True,
            'groups_id': [(6, 0, groups)]}
    user = Users.search([('login', '=', login)], limit=1)
    if user:
        user.write(vals)
    else:
        if partner:
            vals['partner_id'] = partner.id
        user = Users.create(vals)
        bump('created:res.users')
    pvals = {}
    if email and user.partner_id.email != email:
        pvals['email'] = email
    if phone and user.partner_id.phone != phone:
        pvals['phone'] = phone
    if pvals:
        user.partner_id.write(pvals)
    bind('user_%s' % login.replace('.', '_'), user)
    return user


log('Ngày chạy: %s' % TODAY)
users, partners = {}, {}
with Section('Tài khoản cán bộ, giảng viên', optional=False):
    for i, (key, login, name, groups) in enumerate(STAFF, start=1):
        u = ensure_user(login, name, groups, email='%s@%s' % (login, EMAIL_DOMAIN),
                        phone='0900000%03d' % i)
        users[key], partners[key] = u, u.partner_id
    for i, (key, name) in enumerate(EXTRA_LECTURERS, start=1):
        p, _c = ensure('partner_%s' % key, 'res.partner', {
            'name': name, 'email': '%s.demo@%s' % (key, EMAIL_DOMAIN),
            'phone': '0900001%03d' % i, 'is_company': False})
        partners[key] = p

# ═════════════════════════════════════════════════════════════════════════════
# 2. Khoa, bộ môn, ngành, môn học, học kỳ
# ═════════════════════════════════════════════════════════════════════════════
faculties, departments, programs, subjects = {}, {}, {}, {}
with Section('Khoa, bộ môn, ngành, môn học', optional=False):
    for code, name, dean in FACULTIES:
        rec, _c = ensure('faculty_%s' % code, 'univ.sms.faculty', {
            'code': code, 'name': name, 'dean_id': partners[dean].id if dean else False,
        }, domain=[('code', '=', code)])
        faculties[code] = rec
    for code, name, fac in DEPARTMENTS:
        departments[code], _c = ensure('dept_%s' % code, 'univ.sms.department', {
            'code': code, 'name': name, 'faculty_id': faculties[fac].id,
        }, domain=[('code', '=', code)])
    for code, name, dept, credits in PROGRAMS:
        programs[code], _c = ensure('program_%s' % code, 'univ.sms.program', {
            'code': code, 'name': name, 'department_id': departments[dept].id,
            'total_credits': credits, 'duration_years': 4,
        }, domain=[('code', '=', code)])
    for code, name, credit, progs, _pre in SUBJECTS:
        subjects[code], _c = ensure('subject_%s' % code, 'univ.sms.subject', {
            'code': code, 'name': name, 'credit': credit,
            'program_ids': [(6, 0, [programs[p].id for p in progs])],
        }, domain=[('code', '=', code)])
    for code, _n, _c2, _p, prereqs in SUBJECTS:
        want = set(subjects[p].id for p in prereqs)
        if set(subjects[code].prerequisite_ids.ids) != want:
            subjects[code].write({'prerequisite_ids': [(6, 0, list(want))]})

with Section('Năm học, học kỳ', optional=False):
    cur_code, cur_ay = current_term_key(TODAY)
    prev_code, prev_ay = previous_term_key(cur_code, cur_ay)
    term_cur = ensure_term(cur_code, cur_ay)
    term_prev = ensure_term(prev_code, prev_ay)
    cohort_year = ensure_year(prev_ay)
    TAG_CUR = '%s%s' % (str(cur_ay)[2:], cur_code)
    TAG_PREV = '%s%s' % (str(prev_ay)[2:], prev_code)
    log('Học kỳ hiện tại: %s %s (%s → %s); học kỳ trước: %s %s' % (
        term_cur.name, term_cur.academic_year_id.name, term_cur.date_start, term_cur.date_end,
        term_prev.name, term_prev.academic_year_id.name))

# ═════════════════════════════════════════════════════════════════════════════
# 3. Lớp hành chính, sinh viên (+ tài khoản portal)
# ═════════════════════════════════════════════════════════════════════════════
home_classes = {}
students = {}           # n → student
student_group = {}      # n → 'IT' | 'BA'
student_hc = {}         # n → key lớp HC
sv_users = {}


def volume_name(n):
    r = random.Random(1000 + n)
    female = r.random() < 0.5
    name = '%s %s %s' % (r.choice(HO), r.choice(DEM_F if female else DEM_M),
                         r.choice(TEN_F if female else TEN_M))
    return name, ('female' if female else 'male')


with Section('Lớp hành chính, sinh viên, tài khoản portal', optional=False):
    for key, code, name, prog, advisor, _vol in HOME_CLASSES:
        home_classes[key], _c = ensure('homeclass_%s' % key, 'univ.sms.home.class', {
            'code': code, 'name': name, 'program_id': programs[prog].id,
            'academic_year_id': cohort_year.id, 'advisor_id': partners[advisor].id,
        }, domain=[('code', '=', code)])

    roster = [(n, name, gender, hc) for n, name, gender, hc in SCENARIO_STUDENTS]
    n = 100
    for key, _code, _name, _prog, _adv, vol in HOME_CLASSES:
        for _i in range(vol):
            n += 1
            name, gender = volume_name(n)
            roster.append((n, name, gender, key))

    hc_rows = {r[0]: r for r in HOME_CLASSES}
    yy = str(cohort_year.date_start.year)[2:]
    for n, name, gender, hc in roster:
        _k, _code, _hcname, prog, advisor, _v = hc_rows[hc]
        login = 'sv%02d.demo' % n if n < 100 else None
        email = '%s@%s' % (login, EMAIL_DOMAIN) if login else 'sv%03d@%s' % (n, EMAIL_DOMAIN)
        r = random.Random(5000 + n)
        st, created = ensure('student_%03d' % n, 'univ.sms.student', {
            'name': name,
            'student_code': '%s%s%04d' % (yy, prog, 9000 + n),
            'email': email,
            'phone': '09%08d' % (12000000 + n),
            'gender': gender,
            'date_of_birth': date(2005, 1, 1) + timedelta(days=r.randint(0, 700)),
            'program_id': programs[prog].id,
            'home_class_id': home_classes[hc].id,
            'academic_year_id': cohort_year.id,
            'advisor_id': partners[advisor].id,
            'enrollment_date': cohort_year.date_start,
            'training_system': 'regular',
            'home_address': 'Số %s đường Demo, Quận Mẫu' % (n % 90 + 1),
        })
        if st.state == 'draft':
            st.action_confirm()
        students[n] = st
        student_group[n] = 'BA' if prog in BA else 'IT'
        student_hc[n] = hc
        if login:
            sv_users[n] = ensure_user(login, name, [], partner=st.partner_id, email=email, portal=True)
    log('Sinh viên: %s (có tài khoản: %s)' % (len(students), len(sv_users)))

SV = students  # viết tắt
IT_STUDENTS = [n for n in sorted(SV) if student_group[n] == 'IT']
BA_STUDENTS = [n for n in sorted(SV) if student_group[n] == 'BA']


# ═════════════════════════════════════════════════════════════════════════════
# 4. Học kỳ trước: lớp, enrollment, điểm danh, thi, bảng điểm, học phí
# ═════════════════════════════════════════════════════════════════════════════
def ensure_class(key, tag, term, subj_code, lect, slots, max_students, label=''):
    subj = subjects[subj_code]
    code = '%s-%s' % (key, tag)
    name = '%s%s - %s' % (subj.name, (' (%s)' % label) if label else '', tag)
    cls, created = ensure('class_%s' % code.replace('-', '_'), 'univ.sms.class', {
        'code': code, 'name': name, 'subject_id': subj.id, 'term_id': term.id,
        'lecturer_id': partners[lect].id, 'max_students': max_students,
    }, domain=[('code', '=', code)])
    if created:
        env['univ.sms.timetable'].create([{
            'class_id': cls.id, 'day_of_week': d, 'start_time': s, 'end_time': e,
            'room': room, 'building': 'Tòa %s' % room[0]} for d, s, e, room in slots])
    return cls


def score_for(n, subj_code):
    if n in SCENARIO_SCORES and subj_code in SCENARIO_SCORES[n]:
        return SCENARIO_SCORES[n][subj_code]
    r = random.Random('%s-%s' % (n, subj_code))
    if n < 100:  # sinh viên kịch bản khác: khá
        return round(r.uniform(6.8, 8.6), 1)
    ability = random.Random(n).uniform(6.0, 8.8)
    s = ability + r.uniform(-1.0, 1.0)
    if subj_code in PREREQ_CODES:
        s = max(s, 5.6)
    elif n % 23 == 0 and subj_code in ('IT1102', 'BA1101'):
        s = 4.2  # một vài SV trượt 1 môn (không đủ ngưỡng cảnh báo)
    else:
        s = max(s, 5.2)
    return round(min(s, 9.8), 1)


prev_classes = {}
with Section('Học kỳ trước: lớp và enrollment', optional=False):
    for key, subj, lect, slots, grp in PREV_CLASSES:
        cls = ensure_class(key, TAG_PREV, term_prev, subj, lect, slots, 150)
        prev_classes[key] = cls
        members = IT_STUDENTS if grp == 'IT' else BA_STUDENTS if grp == 'BA' else sorted(SV)
        Enr = env['univ.sms.enrollment']
        existing = {e.student_id.id for e in Enr.search([
            ('subject_id', '=', cls.subject_id.id), ('term_id', '=', term_prev.id)])}
        vals = [{'student_id': SV[n].id, 'subject_id': cls.subject_id.id, 'term_id': term_prev.id,
                 'class_id': cls.id, 'state': 'registered'}
                for n in members if SV[n].id not in existing]
        if vals:
            Enr.create(vals)
            bump('created:univ.sms.enrollment', len(vals))
        if cls.state == 'draft':
            cls.action_open()

with Section('Học kỳ trước: điểm danh đã xác nhận', optional=False):
    for key, cls in prev_classes.items():
        days = cls.timetable_ids.mapped('day_of_week')
        for i, d in enumerate(meeting_dates(days, term_prev.date_start, term_prev.date_end, 4)):
            sheet, created = ensure('sheet_%s_%s' % (cls.code.replace('-', '_'), d.isoformat()),
                                    'univ.sms.attendance.sheet',
                                    {'class_id': cls.id, 'attendance_date': d})
            if sheet.state != 'draft':
                continue
            sheet.action_load_students()
            for line in sheet.line_ids:
                r = random.Random('%s-%s-%s' % (cls.code, d, line.student_id.id)).random()
                # Không cho vắng ở học kỳ trước: 1/4 buổi đã là 25% > ngưỡng 20%, sinh viên
                # sẽ mất điều kiện dự thi và không có điểm (khác kịch bản mong muốn).
                if r < 0.04:
                    line.state = 'late'
                elif r < 0.06:
                    line.state = 'excused'
                    line.note = 'Có đơn xin phép'
            sheet.action_confirm()

with Section('Học kỳ trước: kỳ thi giữa kỳ + cuối kỳ', optional=False):
    code_by_student = {st.id: n for n, st in SV.items()}
    for key, cls in prev_classes.items():
        subj_code = cls.subject_id.code
        for etype, label, edate in (
                ('midterm', 'Giữa kỳ', term_prev.date_start + timedelta(days=56)),
                ('final', 'Cuối kỳ', term_prev.date_end - timedelta(days=10))):
            exam, created = ensure('exam_%s_%s' % (cls.code.replace('-', '_'), etype), 'univ.sms.exam', {
                'name': '%s - %s' % (label, cls.subject_id.name), 'class_id': cls.id,
                'exam_type': etype, 'date': edate, 'max_score': 10.0})
            if exam.state == 'done':
                continue
            if exam.state == 'draft':
                exam.action_start_grading()
            exam.action_load_students()
            for res in exam.result_ids:
                n = code_by_student.get(res.student_id.id)
                target = score_for(n, subj_code)
                if etype == 'midterm':
                    sc = target if (n in SCENARIO_SCORES or subj_code in PREREQ_CODES) else round(
                        min(10.0, max(0.0, target + random.Random('m%s%s' % (n, subj_code)).uniform(-0.8, 0.8))), 1)
                else:
                    mid = exam.class_id and env['univ.sms.exam.result'].search([
                        ('student_id', '=', res.student_id.id), ('class_id', '=', cls.id),
                        ('exam_id.exam_type', '=', 'midterm')], limit=1).score or target
                    sc = round(min(10.0, max(0.0, (target - 0.4 * mid) / 0.6)), 2)
                res.score = sc
            exam.action_done()

with Section('Học kỳ trước: bảng điểm, hoàn thành enrollment', optional=False):
    Tr = env['univ.sms.transcript']
    transcripts = Tr.browse()
    for n, st in SV.items():
        tr, created = get_or_create('univ.sms.transcript',
                                    [('student_id', '=', st.id), ('term_id', '=', term_prev.id)],
                                    {'student_id': st.id, 'term_id': term_prev.id})
        transcripts |= tr
    transcripts.action_generate_from_enrollments()
    env['univ.sms.enrollment'].search([
        ('term_id', '=', term_prev.id), ('student_id', 'in', [s.id for s in SV.values()]),
        ('state', '=', 'registered')]).action_complete()
    for cls in prev_classes.values():
        if cls.state != 'closed':
            cls.action_close()


def ensure_fee(st, term, due, mode):
    """mode: 'paid' | 'invoiced' | 'draft'. Chỉ tạo hóa đơn khi phí còn nháp."""
    fee, created = get_or_create('univ.sms.fee', [('student_id', '=', st.id), ('term_id', '=', term.id)],
                                 {'student_id': st.id, 'term_id': term.id, 'due_date': due})
    if not fee.due_date:
        fee.due_date = due
    if mode in ('paid', 'invoiced') and fee.state == 'draft' and not fee.invoice_ids and fee.total_credits:
        fee.action_create_invoice()
        inv = fee.invoice_ids[:1]
        inv.action_confirm()
        if mode == 'paid':
            inv.action_paid()
        bump('invoice:' + mode)
    return fee


with Section('Học kỳ trước: học phí (đã đóng, trừ sv09 nợ quá hạn)', optional=False):
    for n, st in SV.items():
        ensure_fee(st, term_prev, term_prev.date_start + timedelta(days=30),
                   'invoiced' if n == 9 else 'paid')

# ═════════════════════════════════════════════════════════════════════════════
# 5. Học kỳ hiện tại: lớp, lớp môn học, đợt đăng ký
# ═════════════════════════════════════════════════════════════════════════════
cur_classes, offerings = {}, {}
with Section('Học kỳ hiện tại: lớp, thời khóa biểu, lớp môn học', optional=False):
    for key, subj, lect, slots, seats, label in CUR_CLASSES:
        cls = ensure_class(key, TAG_CUR, term_cur, subj, lect, slots, max(seats, 40), label)
        if cls.state == 'draft':
            cls.action_open()
        cur_classes[key] = cls
        off, _c = ensure('offering_%s_%s' % (key, TAG_CUR), 'univ.sms.course.offering', {
            'subject_id': cls.subject_id.id, 'term_id': term_cur.id,
            'lecturer_id': cls.lecturer_id.id, 'class_id': cls.id, 'max_seats': seats})
        offerings[key] = off


def plan_round1(n):
    """Các lớp sinh viên đăng ký trong Đợt 1 (đã đóng)."""
    if n == 10:
        return ['HDH']  # thiếu tín chỉ: 3 < tối thiểu 10
    if n == 7:
        return ['CSDL1', 'MMT', 'HDH', 'TA2N1']  # không có tiên quyết LTCB
    if student_group[n] == 'BA':
        return ['QTH', 'MKT', 'TCDN', 'TA2N2']
    csdl = 'CSDL2' if student_hc[n] == 'D' else 'CSDL1'
    first = 'MMT' if (student_hc[n] == 'D' and n % 4 == 0) else 'LTNC'
    return [first, 'CTDL', csdl, 'HDH', 'TA2N1']


def occupying(st, off):
    return env['univ.sms.registration'].search_count([
        ('student_id', '=', st.id), ('offering_id', '=', off.id),
        ('state', 'in', ('registered', 'confirmed'))]) or env['univ.sms.registration.waitlist'].search_count([
            ('student_id', '=', st.id), ('offering_id', '=', off.id), ('state', '=', 'waiting')])


def register(st, off, period, expect):
    res = env['univ.sms.registration'].register_student(st, off, period)
    bump('register:' + res['status'])
    if res['status'] not in expect:
        ERRORS.append('Đăng ký %s → %s: %s (%s)' % (st.name, off.name, res['status'], res['message']))
        log('!! %s → %s: %s - %s' % (st.name, off.name, res['status'], res['message']))
    return res


with Section('Đợt 1 (ĐÃ ĐÓNG) + đăng ký qua service', optional=False):
    r1_start = dt(term_cur.date_start - timedelta(days=21), 1)
    r1_end = dt(term_cur.date_start - timedelta(days=7), 10)
    p1, created = ensure('period_round1_%s' % TAG_CUR, 'univ.sms.registration.period', {
        'name': 'Đợt 1 - Đăng ký học phần chính thức %s %s' % (term_cur.name, term_cur.academic_year_id.name),
        'term_id': term_cur.id, 'reg_type': 'regular', 'date_start': r1_start, 'date_end': r1_end,
        'min_credit': 10, 'max_credit': 22,
        'description': 'Đợt đăng ký chính đã kết thúc. Sinh viên đăng ký dưới 10 tín chỉ sẽ bị cảnh báo thiếu tín chỉ.'})
    todo = [(n, k) for n in sorted(SV) for k in plan_round1(n) if not occupying(SV[n], offerings[k])]
    if todo:
        # Mở tạm đợt để đăng ký đúng workflow (service + ràng buộc), sau đó đóng lại.
        p1.write({'state': 'open', 'date_start': min(p1.date_start, NOW - timedelta(days=1)),
                  'date_end': NOW + timedelta(hours=2)})
        for n, k in todo:
            register(SV[n], offerings[k], p1, ('registered', 'already'))
        p1.write({'date_start': r1_start, 'date_end': r1_end})
    if p1.state != 'closed':
        p1.action_close()
    log('Đợt 1: %s đăng ký mới' % len(todo))

with Section('Đợt 2 (ĐANG MỞ) + lớp đầy / danh sách chờ', optional=False):
    p2, created = ensure('period_round2_%s' % TAG_CUR, 'univ.sms.registration.period', {
        'name': 'Đợt 2 - Đăng ký bổ sung %s %s' % (term_cur.name, term_cur.academic_year_id.name),
        'term_id': term_cur.id, 'reg_type': 'regular',
        'date_start': NOW - timedelta(days=3), 'date_end': NOW + timedelta(days=14),
        'min_credit': 6, 'max_credit': 20,
        'description': 'Đợt đăng ký bổ sung dành cho buổi demo.'})
    if p2.date_end < NOW + timedelta(days=1):
        p2.date_end = NOW + timedelta(days=14)
    if p2.state != 'open':
        p2.action_open()
    # Lớp AI 2 chỗ: sv02, sv03 đăng ký → đầy; sv04 vào danh sách chờ (vị trí 1)
    for n, expect in ((2, ('registered', 'already')), (3, ('registered', 'already')),
                      (4, ('waitlisted', 'already'))):
        if not occupying(SV[n], offerings['AI']):
            register(SV[n], offerings['AI'], p2, expect)

# ═════════════════════════════════════════════════════════════════════════════
# 6. Điểm danh học kỳ hiện tại + điều kiện dự thi
# ═════════════════════════════════════════════════════════════════════════════
SV_IDX = {st.id: n for n, st in SV.items()}
with Section('Học kỳ hiện tại: phiếu điểm danh', optional=False):
    for key, cls in cur_classes.items():
        if not cls.enrollment_ids.filtered(lambda e: e.state == 'registered'):
            continue  # lớp chưa có sinh viên (ví dụ ATTT để tester tự đăng ký)
        days = cls.timetable_ids.mapped('day_of_week')
        dates = meeting_dates(days, term_cur.date_start, TODAY, 6)
        for i, d in enumerate(dates):
            sheet, created = ensure('sheet_%s_%s' % (cls.code.replace('-', '_'), d.isoformat()),
                                    'univ.sms.attendance.sheet',
                                    {'class_id': cls.id, 'attendance_date': d})
            if sheet.state != 'draft':
                continue
            sheet.action_load_students()
            for line in sheet.line_ids:
                n = SV_IDX.get(line.student_id.id)
                r = random.Random('%s-%s-%s' % (cls.code, d, n)).random()
                if n == 8 and key == 'CTDL' and i in (0, 2, 4):
                    line.state = 'absent'          # sv08: vắng 3/6 = 50%
                elif n is not None and n >= 100 and student_hc.get(n) in ('B', 'D') and n % 15 == 0 \
                        and key == 'HDH' and i in (1, 3):
                    line.state = 'absent'          # 4 SV lớp B, D vắng 2/6 = 33%
                elif n is not None and n >= 100 and i == (n % 6) and r < 0.25:
                    line.state = 'absent'          # tối đa 1 buổi/lớp
                elif r < 0.05:
                    line.state = 'late'
                elif r < 0.07:
                    line.state = 'excused'
                    line.note = 'Có đơn xin phép'
            sheet.action_confirm()
    # Phiếu NHÁP hôm nay cho lớp CSDL nhóm 1 (giangvien.demo) để demo QR
    qr_cls = cur_classes['CSDL1']
    qr_sheet, created = ensure('sheet_qr_today_%s' % TODAY.isoformat(), 'univ.sms.attendance.sheet',
                               {'class_id': qr_cls.id, 'attendance_date': TODAY})
    if qr_sheet.state == 'draft' and not qr_sheet.line_ids:
        qr_sheet.action_load_students()

with Section('Điều kiện dự thi + kỳ thi giữa kỳ nháp', optional=False):
    for cls in cur_classes.values():
        cls.action_compute_exam_eligibility()
    ensure('exam_%s_midterm' % cur_classes['CTDL'].code.replace('-', '_'), 'univ.sms.exam', {
        'name': 'Giữa kỳ - %s' % cur_classes['CTDL'].subject_id.name,
        'class_id': cur_classes['CTDL'].id, 'exam_type': 'midterm',
        'date': TODAY + timedelta(days=7), 'max_score': 10.0})

with Section('Học kỳ hiện tại: học phí', optional=False):
    due = TODAY + timedelta(days=21)
    for n, st in SV.items():
        if n in (2, 12):
            mode = 'paid'
        elif n == 3:
            mode = 'invoiced'
        elif n < 100:
            mode = 'draft'      # tài khoản test: học phí còn nháp nên tự tính lại khi đăng ký thêm
        else:
            mode = ('paid', 'invoiced', 'draft')[n % 3]
        ensure_fee(st, term_cur, due, mode)

# ═════════════════════════════════════════════════════════════════════════════
# 7. Rèn luyện, giấy chứng nhận, khảo sát, góp ý, CTSV, thông báo (tùy chọn)
# ═════════════════════════════════════════════════════════════════════════════
with Section('Điểm rèn luyện'):
    criteria = env['univ.sms.conduct.criteria'].search([])
    if not criteria:
        raise Exception('Chưa có tiêu chí rèn luyện (data module univ_sms_conduct)')
    plans = [(1, 'dean_approved', 0.85), (12, 'dean_approved', 0.95), (2, 'advisor_approved', 0.8),
             (11, 'submitted', 0.75), (3, 'draft', 0.7), (5, 'rejected', 0.6)]
    for n, target, frac in plans:
        st = SV[n]
        cs, created = get_or_create('univ.sms.conduct.score',
                                    [('student_id', '=', st.id), ('period_id', '=', term_prev.id)],
                                    {'student_id': st.id, 'period_id': term_prev.id, 'line_ids': [
                                        (0, 0, {'criteria_id': c.id, 'self_score': int(round(c.max_score * frac))})
                                        for c in criteria]})
        if not created:
            continue
        if target == 'draft':
            continue
        cs.action_submit()
        if target == 'submitted':
            continue
        if target == 'rejected':
            cs.action_reject()
            continue
        for line in cs.line_ids:
            line.advisor_score = max(0, line.self_score - (1 if line.id % 3 == 0 else 0))
        cs.action_advisor_approve()
        if target == 'advisor_approved':
            continue
        for line in cs.line_ids:
            line.final_score = line.advisor_score
        cs.action_dean_approve()

with Section('Giấy chứng nhận'):
    ctypes = {}
    for code, name, fee in (('XNSV', 'Giấy xác nhận sinh viên', 0),
                            ('BDSN', 'Bảng điểm song ngữ', 50000),
                            ('XNVV', 'Giấy xác nhận vay vốn ngân hàng CSXH', 0)):
        ctypes[code], _c = ensure('certtype_%s' % code, 'univ.sms.certificate.type', {
            'code': code, 'name': name, 'require_fee': bool(fee), 'fee_amount': fee,
            'description': 'Loại giấy demo'}, domain=[('code', '=', code)])
    for key, n, code, target, reason in (
            ('r1', 11, 'XNSV', 'draft', 'Bổ sung hồ sơ xin học bổng'),
            ('r2', 11, 'BDSN', 'approved', 'Nộp hồ sơ trao đổi sinh viên'),
            ('r3', 11, 'XNVV', 'completed', 'Vay vốn học tập'),
            ('r4', 1, 'XNSV', 'rejected', 'Thiếu ảnh thẻ'),
            ('r5', 12, 'BDSN', 'completed', 'Ứng tuyển thực tập'),
            ('r6', 2, 'XNVV', 'draft', 'Vay vốn học tập')):
        req, created = ensure('certreq_%s' % key, 'univ.sms.certificate.request', {
            'student_id': SV[n].id, 'certificate_type_id': ctypes[code].id, 'reason': reason,
            'request_date': TODAY - timedelta(days=5),
            'fee_payment_state': 'paid' if target in ('approved', 'completed') and ctypes[code].fee_amount else 'unpaid'})
        if not created:
            continue
        if target in ('approved', 'completed'):
            req.action_approve()
        if target == 'completed':
            req.action_complete()
        if target == 'rejected':
            req.action_reject()

with Section('Khảo sát'):
    stype, _c = ensure('surveytype_DGGD', 'univ.sms.survey.type', {
        'code': 'DGGD', 'name': 'Đánh giá hoạt động giảng dạy',
        'description': 'Sinh viên đánh giá giảng viên và môn học'}, domain=[('code', '=', 'DGGD')])
    stype2, _c = ensure('surveytype_CSVC', 'univ.sms.survey.type', {
        'code': 'CSVC', 'name': 'Khảo sát cơ sở vật chất',
        'description': 'Phòng học, thư viện, wifi'}, domain=[('code', '=', 'CSVC')])

    def respond(n, inst, text):
        resp, created = get_or_create('univ.sms.survey.response',
                                      [('student_id', '=', SV[n].id), ('survey_instance_id', '=', inst.id)],
                                      {'student_id': SV[n].id, 'survey_instance_id': inst.id, 'answer_data': text})
        accepting = inst._is_accepting_responses() if hasattr(inst, '_is_accepting_responses')             else inst.state == 'open'
        if resp.state == 'draft' and accepting:
            resp.action_submit()

    # Đợt đã đóng (học kỳ trước): mở tạm để nhận phản hồi đúng workflow rồi đóng
    closed, created = ensure('survey_closed_%s' % TAG_PREV, 'univ.sms.survey.instance', {
        'name': 'Khảo sát cơ sở vật chất %s %s' % (term_prev.name, term_prev.academic_year_id.name),
        'survey_type_id': stype2.id, 'date_start': TODAY - timedelta(days=1), 'date_end': TODAY + timedelta(days=1)})
    if created:
        closed.action_open()
        for n in [1, 11] + [x for x in sorted(SV) if x >= 100][:15]:
            respond(n, closed, 'Phòng học đủ ánh sáng; đề nghị tăng tốc độ wifi thư viện.')
        closed.action_close()
        closed.write({'date_start': term_prev.date_end - timedelta(days=20),
                      'date_end': term_prev.date_end - timedelta(days=5)})
    opened, created = ensure('survey_open_%s' % TAG_CUR, 'univ.sms.survey.instance', {
        'name': 'Đánh giá giảng dạy %s %s' % (term_cur.name, term_cur.academic_year_id.name),
        'survey_type_id': stype.id, 'date_start': TODAY - timedelta(days=5), 'date_end': TODAY + timedelta(days=14)})
    if opened.date_end < TODAY:
        opened.date_end = TODAY + timedelta(days=14)
    if opened.state == 'draft':
        opened.action_open()
    for n in [2, 12] + [x for x in sorted(SV) if x >= 100][20:30]:
        respond(n, opened, 'Giảng viên nhiệt tình, bài giảng rõ ràng. Mong có thêm bài tập thực hành.')

with Section('Góp ý / phản hồi'):
    for key, n, cat, subj, desc, dept, target, resp in (
            ('f1', 11, 'facility', 'Máy chiếu phòng A2.201 hay mất tín hiệu',
             'Máy chiếu phòng A2.201 thường mất tín hiệu HDMI giữa buổi học, ảnh hưởng tiết Cơ sở dữ liệu.',
             'FIT-HTTT', 'new', ''),
            ('f2', 1, 'academic', 'Đề nghị mở thêm lớp Trí tuệ nhân tạo',
             'Lớp Trí tuệ nhân tạo chỉ có 2 chỗ, nhiều bạn muốn học. Đề nghị mở thêm nhóm.',
             'FIT-CNPM', 'in_progress', ''),
            ('f3', 12, 'service', 'Thời gian cấp giấy xác nhận',
             'Thời gian chờ cấp giấy xác nhận sinh viên khá lâu, mong rút ngắn.',
             'FIT-HTTT', 'resolved', 'Phòng CTSV đã rút ngắn thời gian xử lý còn 2 ngày làm việc.'),
            ('f4', 2, 'other', 'Đề xuất thêm chỗ để xe',
             'Bãi xe khu A thường hết chỗ vào giờ cao điểm buổi sáng.',
             'FEB-QTKD', 'closed', 'Nhà trường đã mở thêm bãi xe khu C.'),
            ('f5', 5, 'academic', 'Xin tư vấn kế hoạch học lại',
             'Em muốn được tư vấn kế hoạch học lại các môn chưa đạt ở học kỳ trước.',
             'FIT-CNPM', 'new', '')):
        fb, created = ensure('feedback_%s' % key, 'univ.sms.feedback', {
            'student_id': SV[n].id, 'category': cat, 'subject': subj, 'description': desc,
            'department_id': departments[dept].id})
        if not created:
            continue
        if target in ('in_progress', 'resolved'):
            fb.action_in_progress()
        if resp:
            fb.response = resp
        if target in ('resolved', 'closed'):
            if target == 'resolved':
                fb.action_resolved()
            else:
                fb.action_close()

with Section('Công tác sinh viên: BHYT, cư trú, NVQS'):
    vn_state = env['res.country.state'].search([('country_id.code', '=', 'VN')], limit=1)
    y0 = date(TODAY.year, 1, 1)
    hi_list = [(1, 'confirmed', 'paid', 0), (11, 'draft', 'unpaid', 0), (12, 'confirmed', 'paid', 0),
               (5, 'confirmed', 'paid', -1)] + [(x, 'confirmed', 'paid', 0) for x in sorted(SV) if x >= 100][:20]
    for n, state, pay, yoff in hi_list:
        ds = date(y0.year + yoff, 1, 1)
        hi, created = ensure('hi_%03d_%s' % (n, ds.year), 'univ.sms.health.insurance', {
            'student_id': SV[n].id, 'insurance_code': 'DEMO-BHYT-%04d-%s' % (n, ds.year),
            'issue_place_id': vn_state.id or False, 'date_start': ds, 'date_end': date(ds.year, 12, 31),
            'payment_state': pay})
        if created and state == 'confirmed':
            hi.action_confirm()
    for n, rtype, addr, state in (
            (11, 'dormitory', 'Ký túc xá khu B, phòng B2-305', 'confirmed'),
            (1, 'rent', 'Số 12 hẻm 45 đường Demo, phường Mẫu', 'draft'),
            (12, 'family', 'Số 8 đường Thử Nghiệm, quận Mẫu', 'confirmed'),
            (8, 'rent', 'Số 3 ngõ 7 đường Demo, phường Mẫu', 'confirmed')):
        ri, created = ensure('residence_%03d' % n, 'univ.sms.residence.info', {
            'student_id': SV[n].id, 'residence_type': rtype, 'address': addr,
            'landlord_name': 'Chủ nhà demo' if rtype == 'rent' else 'Ban quản lý KTX' if rtype == 'dormitory' else False,
            'landlord_phone': '0900002%03d' % n if rtype != 'family' else False,
            'effective_date': term_cur.date_start})
        if created and state == 'confirmed':
            ri.action_confirm()
    for n, status, state in ((11, 'deferred', 'submitted'), (3, 'deferred', 'approved'), (7, 'registered', 'draft')):
        ms, created = ensure('military_%03d' % n, 'univ.sms.military.service', {
            'student_id': SV[n].id, 'registration_status': status,
            'local_authority_id': vn_state.id or False, 'declared_date': TODAY - timedelta(days=20)})
        if created and state in ('submitted', 'approved'):
            ms.action_submit()
            if state == 'approved':
                ms.action_approve()

with Section('Thông báo'):
    for key, title, content, pinned, mode in (
            ('n1', 'Lịch đăng ký học phần bổ sung (Đợt 2)',
             '<p>Đợt 2 đăng ký bổ sung đang mở trên cổng sinh viên. Sinh viên kiểm tra tiên quyết và '
             'trùng lịch trước khi đăng ký.</p>', True, 'published'),
            ('n2', 'Thông báo nộp học phí học kỳ hiện tại',
             '<p>Hạn nộp học phí là 21 ngày kể từ ngày thông báo. Quá hạn sẽ phát sinh cảnh báo công nợ.</p>',
             False, 'published'),
            ('n3', 'Lịch thi giữa kỳ học kỳ trước (đã hết hạn)',
             '<p>Thông báo cũ, đã hết hạn hiển thị.</p>', False, 'expired'),
            ('n4', 'Dự thảo: Kế hoạch Ngày hội việc làm',
             '<p>Bản nháp, chưa đăng.</p>', False, 'draft')):
        nt, created = ensure('notification_%s' % key, 'univ.sms.notification', {
            'title': title, 'content': content, 'is_pinned': pinned, 'target_audience': 'all'})
        if not created or mode == 'draft':
            continue
        nt.action_publish()
        if mode == 'expired':
            nt.write({'publish_date': NOW - timedelta(days=30), 'expire_date': NOW - timedelta(days=2)})

# ═════════════════════════════════════════════════════════════════════════════
# 8. Cảnh báo sớm
# ═════════════════════════════════════════════════════════════════════════════
with Section('Cảnh báo sớm: run_evaluation + một lần tư vấn mẫu'):
    res = env['univ.sms.warning'].run_evaluation()
    log('run_evaluation: %s' % res)
    STATS['run_evaluation'] = res
    w = env['univ.sms.warning'].search([('student_id', '=', SV[6].id),
                                         ('warning_type', '=', 'failed_subjects'),
                                         ('state', '!=', 'closed')], limit=1)
    if w and not w.consultation_ids:
        env['univ.sms.warning.consultation'].create({
            'warning_id': w.id, 'user_id': users['covan'].id, 'outcome': 'plan_agreed',
            'note': 'Đã gặp sinh viên, thống nhất kế hoạch học lại Toán rời rạc và Triết học ở học kỳ sau.'})

# ═════════════════════════════════════════════════════════════════════════════
# 9. Commit + tổng kết
# ═════════════════════════════════════════════════════════════════════════════
env.cr.commit()

COUNT_MODELS = [
    'res.users', 'univ.sms.faculty', 'univ.sms.department', 'univ.sms.program', 'univ.sms.subject',
    'univ.sms.academic.year', 'univ.sms.term', 'univ.sms.home.class', 'univ.sms.student',
    'univ.sms.class', 'univ.sms.timetable', 'univ.sms.enrollment', 'univ.sms.course.offering',
    'univ.sms.registration.period', 'univ.sms.registration', 'univ.sms.registration.waitlist',
    'univ.sms.attendance.sheet', 'univ.sms.attendance.line', 'univ.sms.exam', 'univ.sms.exam.result',
    'univ.sms.transcript', 'univ.sms.transcript.line', 'univ.sms.fee', 'univ.sms.fee.invoice',
    'univ.sms.conduct.score', 'univ.sms.certificate.type', 'univ.sms.certificate.request',
    'univ.sms.survey.type', 'univ.sms.survey.instance', 'univ.sms.survey.response', 'univ.sms.feedback',
    'univ.sms.health.insurance', 'univ.sms.residence.info', 'univ.sms.military.service',
    'univ.sms.notification', 'univ.sms.warning', 'univ.sms.warning.consultation',
    'univ.sms.student.notice',
]
print('\n' + '=' * 64)
print('%-40s %10s' % ('Model', 'Số bản ghi'))
print('-' * 64)
for m in COUNT_MODELS:
    if m in env:
        print('%-40s %10s' % (m, env[m].sudo().with_context(active_test=False).search_count([])))
print('-' * 64)
W = env['univ.sms.warning'].sudo() if 'univ.sms.warning' in env else None
if W is not None:
    for row in W._read_group([('state', '!=', 'closed')], ['warning_type'], ['__count']):
        print('  cảnh báo mở %-26s %10s' % (row[0], row[1]))
    demo_ids = [SV[n].id for n in range(1, 13)]
    for w in W.search([('student_id', 'in', demo_ids), ('state', '!=', 'closed')], order='student_id'):
        login = sv_users[SV_IDX[w.student_id.id]].login
        print('  %-14s %-16s %8.2f' % (login, w.warning_type, w.evidence_value))
print('-' * 64)
print('Thống kê lần chạy này: %s' % {k: v for k, v in sorted(STATS.items())})
print('Lỗi: %s' % (len(ERRORS),))
for e in ERRORS:
    print('  - %s' % e)
print('Mật khẩu mọi tài khoản demo: %s' % PASSWORD)
print('=' * 64)
