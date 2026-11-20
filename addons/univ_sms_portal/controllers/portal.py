import logging
import re
from datetime import date

from odoo import fields
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import UserError, ValidationError
from odoo.http import request, route
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$')
LOGIN_RE = re.compile(r'^[A-Za-z0-9._@+\-]{3,64}$')
PHONE_RE = re.compile(r'^[0-9+\s().\-]{8,20}$')
ID_NUMBER_RE = re.compile(r'^[0-9]{9,12}$')
MIN_PASSWORD_LENGTH = 8
MIN_STUDENT_AGE = 15

# Thông báo hiển thị sau khi gửi form dịch vụ (query param ?msg=<mã>).
# Chỉ mã có trong bảng mới được hiển thị: không phản chiếu nội dung tùy ý từ URL.
SERVICE_MESSAGES = {
    'created': ('success', 'Đã gửi yêu cầu thành công.'),
    'submitted': ('success', 'Đã gửi phản hồi khảo sát. Cảm ơn bạn!'),
    'no_student': ('danger', 'Tài khoản này chưa gắn với hồ sơ sinh viên.'),
    'invalid_type': ('danger', 'Loại giấy không hợp lệ hoặc không còn nhận yêu cầu.'),
    'invalid_reason': ('danger', 'Vui lòng nhập lý do yêu cầu (tối đa 1000 ký tự).'),
    'duplicate_cert': ('warning', 'Bạn đã có yêu cầu đang xử lý cho loại giấy này.'),
    'invalid_status': ('danger', 'Trạng thái khai báo nghĩa vụ quân sự không hợp lệ.'),
    'duplicate_military': ('warning', 'Bạn đã có khai báo nghĩa vụ quân sự đang chờ duyệt.'),
    'invalid_survey': ('danger', 'Đợt khảo sát không tồn tại.'),
    'closed_survey': ('warning', 'Đợt khảo sát đã đóng hoặc chưa đến thời gian nhận phản hồi.'),
    'already_answered': ('warning', 'Bạn đã gửi phản hồi cho đợt khảo sát này. Phản hồi đã gửi không thể sửa.'),
    'invalid_answer': ('danger', 'Vui lòng nhập nội dung phản hồi (tối đa 5000 ký tự).'),
    'invalid_category': ('danger', 'Loại góp ý không hợp lệ.'),
    'invalid_department': ('danger', 'Bộ phận nhận góp ý không hợp lệ.'),
    'invalid_subject': ('danger', 'Vui lòng nhập tiêu đề góp ý (tối đa 200 ký tự).'),
    'invalid_description': ('danger', 'Vui lòng nhập nội dung góp ý (tối đa 5000 ký tự).'),
    'duplicate_feedback': ('warning', 'Bạn vừa gửi góp ý với cùng tiêu đề. Vui lòng chờ ít nhất 1 phút.'),
    'error': ('danger', 'Không thể xử lý yêu cầu lúc này. Vui lòng thử lại sau.'),
}


def _parse_id(value):
    """Chuỗi -> số nguyên dương, sai định dạng trả về None (không ném lỗi)."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if 0 < number < 2 ** 31 else None


def _clean_text(value, max_len):
    """Chuỗi đã strip; None nếu rỗng hoặc vượt độ dài."""
    text = (value or '').strip() if isinstance(value, str) else ''
    if not text or len(text) > max_len:
        return None
    return text


class UnivSmsPortal(CustomerPortal):

    # ─── AUTO-REDIRECT SINH VIÊN SAU KHI ĐĂNG NHẬP ─────────────────────────────

    @route(['/my', '/my/home'], type='http', auth='user', website=True)
    def home(self, **kw):
        if not request.env.user._is_public():
            student = self._get_student()
            if student:
                return request.redirect('/my/academic')
        return super().home(**kw)

    # ─── LANDING PAGE ────────────────────────────────────────────────────────

    @route(['/university', '/university/'], type='http', auth='public', website=False)
    def university_landing(self, **kw):
        if not request.env.user._is_public():
            student = self._get_student()
            if student:
                return request.redirect('/my/academic')
        NotifModel = request.env.get('univ.sms.notification')
        notifications = []
        snippets = {}
        if NotifModel is not None:
            try:
                now = fields.Datetime.now()
                notifications = NotifModel.sudo().search(
                    [('state', '=', 'published'),
                     '|', ('expire_date', '=', False), ('expire_date', '>=', now)],
                    limit=6, order='publish_date desc, id desc',
                )
                for notif in notifications:
                    text = ' '.join(html2plaintext(notif.content or '').split())
                    snippets[notif.id] = text if len(text) <= 150 else text[:150].rstrip() + '…'
            except Exception:
                _logger.exception('Cannot load landing notifications')
        return request.render('univ_sms_portal.university_landing', {
            'notifications': notifications,
            'notification_snippets': snippets,
        })

    def _get_student(self):
        """Helper: sinh viên của user hiện tại (recordset rỗng với user public)."""
        user = request.env.user
        if user._is_public():
            return request.env['univ.sms.student'].sudo().browse()
        return request.env['univ.sms.student'].sudo().search(
            [('partner_id', '=', user.partner_id.id)], limit=1
        )

    @staticmethod
    def _service_flash(kw):
        code = kw.get('msg')
        if isinstance(code, str) and code in SERVICE_MESSAGES:
            level, text = SERVICE_MESSAGES[code]
            return {'level': level, 'text': text}
        return False

    @staticmethod
    def _service_redirect(url, code):
        return request.redirect('%s?msg=%s' % (url, code))

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'enrollment_count' in counters:
            student = self._get_student()
            values['enrollment_count'] = len(student.enrollment_ids) if student else 0
        return values

    # ─── ĐĂNG KÝ HỒ SƠ SINH VIÊN (PUBLIC) ───────────────────────────────────

    def _prepare_student_registration_values(self, form_values=None, errors=None, success_data=None):
        user = request.env.user
        partner = user.partner_id if not user._is_public() else request.env['res.partner']
        defaults = {
            'name': partner.name if partner else '',
            'login': user.login if not user._is_public() else '',
            'personal_email': partner.email if partner else '',
            'phone': partner.phone if partner else '',
            'mobile': partner.mobile if partner else '',
            'home_address': '',
            'current_address': '',
            'date_of_birth': '',
            'gender': 'male',
            'id_number': '',
            'program_id': '',
            'academic_year_id': '',
            'training_system': 'regular',
        }
        defaults.update(form_values or {})
        return {
            'form_values': defaults,
            'errors': errors or [],
            'success_data': success_data,
            'programs': request.env['univ.sms.program'].sudo().search([], order='name'),
            'academic_years': request.env['univ.sms.academic.year'].sudo().search([], order='date_start desc, id desc'),
            'training_systems': request.env['univ.sms.student']._fields['training_system'].selection,
            'genders': request.env['univ.sms.student']._fields['gender'].selection,
            'is_public_user': user._is_public(),
            'max_birth_date': fields.Date.to_string(self._max_birth_date()),
        }

    @staticmethod
    def _max_birth_date(today=None):
        today = today or fields.Date.context_today(request.env.user)
        try:
            return today.replace(year=today.year - MIN_STUDENT_AGE)
        except ValueError:  # 29/02
            return today.replace(year=today.year - MIN_STUDENT_AGE, day=28)

    def _student_register_blocked(self):
        """Redirect nếu user không được tự tạo hồ sơ (đã là SV, hoặc là user nội bộ)."""
        user = request.env.user
        if user._is_public():
            return None
        if self._get_student():
            return request.redirect('/my/academic')
        if user._is_internal():
            # Cán bộ/giảng viên không tự tạo hồ sơ sinh viên cho chính mình.
            return request.redirect('/my')
        return None

    @route(['/student/register'], type='http', auth='public', website=True)
    def portal_student_register(self, **kw):
        blocked = self._student_register_blocked()
        if blocked:
            return blocked
        values = self._prepare_student_registration_values()
        return request.render('univ_sms_portal.portal_student_register', values)

    @staticmethod
    def _exists_ci(model, fname, value):
        """So khớp không phân biệt hoa thường, KHÔNG coi _ và % là ký tự đại diện."""
        lowered = value.lower()
        return any((rec[fname] or '').lower() == lowered
                   for rec in model.search([(fname, 'ilike', value)]))

    def _validate_student_registration(self, form_values, password, confirm_password, is_public_user):
        """Trả về (errors, cleaned) — không ném lỗi với mọi input."""
        errors = []
        cleaned = {}
        student_model = request.env['univ.sms.student'].sudo()
        user_model = request.env['res.users'].sudo().with_context(active_test=False)

        if not form_values['name']:
            errors.append('Vui lòng nhập họ và tên.')
        elif len(form_values['name']) > 128:
            errors.append('Họ và tên quá dài (tối đa 128 ký tự).')

        # Ngành, niên khóa phải tồn tại.
        program_id = _parse_id(form_values['program_id'])
        program = student_model.env['univ.sms.program'].browse(program_id).exists() if program_id else None
        if not form_values['program_id']:
            errors.append('Vui lòng chọn ngành học.')
        elif not program:
            errors.append('Ngành học không hợp lệ.')
        year_id = _parse_id(form_values['academic_year_id'])
        year = student_model.env['univ.sms.academic.year'].browse(year_id).exists() if year_id else None
        if not form_values['academic_year_id']:
            errors.append('Vui lòng chọn niên khóa nhập học.')
        elif not year:
            errors.append('Niên khóa nhập học không hợp lệ.')
        cleaned['program'] = program
        cleaned['academic_year'] = year

        # Ngày sinh: đúng định dạng, không ở tương lai, đủ tuổi.
        dob = None
        if not form_values['date_of_birth']:
            errors.append('Vui lòng nhập ngày sinh.')
        else:
            try:
                dob = fields.Date.to_date(form_values['date_of_birth'])
            except (TypeError, ValueError):
                dob = None
            if not isinstance(dob, date):
                errors.append('Ngày sinh không hợp lệ.')
                dob = None
            elif dob > fields.Date.context_today(request.env.user):
                errors.append('Ngày sinh không được ở tương lai.')
                dob = None
            elif dob > self._max_birth_date():
                errors.append('Sinh viên phải đủ %s tuổi trở lên.' % MIN_STUDENT_AGE)
                dob = None
            elif dob.year < 1900:
                errors.append('Ngày sinh không hợp lệ.')
                dob = None
        cleaned['date_of_birth'] = dob

        email = form_values['personal_email']
        if not email:
            errors.append('Vui lòng nhập email liên hệ.')
        elif len(email) > 254 or not EMAIL_RE.match(email):
            errors.append('Email liên hệ không đúng định dạng.')
        elif self._exists_ci(student_model.with_context(active_test=False), 'personal_email', email):
            errors.append('Email này đã được dùng cho một hồ sơ sinh viên khác.')

        phone, mobile = form_values['phone'], form_values['mobile']
        if not phone and not mobile:
            errors.append('Vui lòng nhập ít nhất một số điện thoại liên hệ.')
        for label, value in (('Số điện thoại', phone), ('Số di động', mobile)):
            if value and not PHONE_RE.match(value):
                errors.append('%s không hợp lệ.' % label)

        if form_values['gender'] not in dict(student_model._fields['gender'].selection):
            errors.append('Giới tính không hợp lệ.')
        if form_values['training_system'] not in dict(student_model._fields['training_system'].selection):
            errors.append('Hệ đào tạo không hợp lệ.')

        id_number = form_values['id_number']
        if id_number:
            if not ID_NUMBER_RE.match(id_number):
                errors.append('Số CCCD/CMND chỉ gồm 9 đến 12 chữ số.')
            elif student_model.with_context(active_test=False).search_count([('id_number', '=', id_number)]):
                errors.append('Số CCCD/CMND đã tồn tại trong hệ thống.')

        for fname, label in (('home_address', 'Địa chỉ thường trú'), ('current_address', 'Địa chỉ tạm trú')):
            if len(form_values[fname]) > 255:
                errors.append('%s quá dài (tối đa 255 ký tự).' % label)

        if is_public_user:
            login = form_values['login']
            if not login:
                errors.append('Vui lòng nhập tên đăng nhập.')
            elif not LOGIN_RE.match(login):
                errors.append('Tên đăng nhập chỉ gồm chữ, số và . _ - @ + (3 đến 64 ký tự).')
            elif self._exists_ci(user_model, 'login', login):
                errors.append('Tên đăng nhập đã tồn tại, vui lòng chọn tên khác.')
            if not password:
                errors.append('Vui lòng nhập mật khẩu.')
            elif len(password) < MIN_PASSWORD_LENGTH:
                errors.append('Mật khẩu phải có ít nhất %s ký tự.' % MIN_PASSWORD_LENGTH)
            elif len(password) > 128:
                errors.append('Mật khẩu quá dài.')
            if password != confirm_password:
                errors.append('Mật khẩu xác nhận không khớp.')
        return errors, cleaned

    @route(['/student/register/submit'], type='http', auth='public', website=True, methods=['POST'])
    def portal_student_register_submit(self, **post):
        current_user = request.env.user
        is_public_user = current_user._is_public()
        blocked = self._student_register_blocked()
        if blocked:
            return blocked
        student_model = request.env['univ.sms.student'].sudo()
        user_model = request.env['res.users'].sudo().with_context(no_reset_password=True)

        def _text(key, default=''):
            value = post.get(key)
            return value.strip() if isinstance(value, str) else default

        form_values = {
            'name': _text('name'),
            'login': _text('login'),
            'personal_email': _text('personal_email'),
            'phone': _text('phone'),
            'mobile': _text('mobile'),
            'home_address': _text('home_address'),
            'current_address': _text('current_address'),
            'date_of_birth': _text('date_of_birth'),
            'gender': _text('gender') or 'male',
            'id_number': _text('id_number'),
            'program_id': _text('program_id'),
            'academic_year_id': _text('academic_year_id'),
            'training_system': _text('training_system') or 'regular',
        }
        password = post.get('password') if isinstance(post.get('password'), str) else ''
        confirm_password = post.get('confirm_password') if isinstance(post.get('confirm_password'), str) else ''

        errors, cleaned = self._validate_student_registration(
            form_values, password, confirm_password, is_public_user)
        if errors:
            values = self._prepare_student_registration_values(form_values=form_values, errors=errors)
            return request.render('univ_sms_portal.portal_student_register', values)

        success_data = None
        try:
            with request.env.cr.savepoint():
                if is_public_user:
                    new_user = user_model.create({
                        'name': form_values['name'],
                        'login': form_values['login'],
                        'password': password,
                        'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])],
                    })
                else:
                    new_user = current_user.sudo()

                partner = new_user.partner_id.sudo()
                partner.write({
                    'name': form_values['name'],
                    'email': form_values['personal_email'],
                    'phone': form_values['phone'] or form_values['mobile'],
                    'mobile': form_values['mobile'] or form_values['phone'],
                    'street': form_values['current_address'],
                })

                program = cleaned['program']
                year = cleaned['academic_year']
                home_class = request.env['univ.sms.home.class'].sudo().search([
                    ('program_id', '=', program.id),
                    ('academic_year_id', '=', year.id),
                ], limit=1)

                student = student_model.create({
                    'partner_id': partner.id,
                    'program_id': program.id,
                    'home_class_id': home_class.id if home_class else False,
                    'academic_year_id': year.id,
                    'training_system': form_values['training_system'],
                    'date_of_birth': cleaned['date_of_birth'],
                    'gender': form_values['gender'],
                    'id_number': form_values['id_number'] or False,
                    'personal_email': form_values['personal_email'],
                    'home_address': form_values['home_address'],
                    'current_address': form_values['current_address'],
                    'state': 'draft',
                })

                success_data = {
                    'student_name': student.name,
                    'student_code': student.student_code,
                    'login': new_user.login,
                    'is_public_user': is_public_user,
                }
        except (UserError, ValidationError) as exc:
            message = exc.args[0] if exc.args else ''
            errors.append(message if isinstance(message, str) and message
                          else 'Không thể tạo hồ sơ, vui lòng kiểm tra lại thông tin.')
        except Exception:
            # Không để lộ chi tiết lỗi (SQL, traceback) ra trang public.
            _logger.exception('Public student registration failed (login=%s)', form_values['login'])
            errors.append('Không thể tạo hồ sơ lúc này. Có thể tên đăng nhập hoặc thông tin '
                          'đã được dùng; vui lòng kiểm tra lại hoặc thử lại sau.')
        if errors:
            values = self._prepare_student_registration_values(form_values=form_values, errors=errors)
            return request.render('univ_sms_portal.portal_student_register', values)

        if not is_public_user:
            return request.redirect('/my/academic')

        values = self._prepare_student_registration_values(success_data=success_data)
        return request.render('univ_sms_portal.portal_student_register', values)

    # ─── TRANG HỌC VỤ ────────────────────────────────────────────────────────

    @route(['/my/academic'], type='http', auth='user', website=True)
    def portal_academic_home(self, **kw):
        student = self._get_student()
        return request.render('univ_sms_portal.portal_academic_home', {
            'student': student,
            'page_name': 'academic_home',
        })

    @route(['/my/academic/transcript'], type='http', auth='user', website=True)
    def portal_transcript(self, **kw):
        student = self._get_student()
        results = request.env['univ.sms.exam.result'].sudo().search(
            [('student_id', '=', student.id)],
            order='term_id desc, subject_id',
        ) if student else []
        return request.render('univ_sms_portal.portal_transcript', {
            'student': student,
            'results': results,
            'page_name': 'academic_transcript',
        })

    @route(['/my/academic/attendance'], type='http', auth='user', website=True)
    def portal_attendance(self, **kw):
        student = self._get_student()
        attendance_lines = request.env['univ.sms.attendance.line'].sudo().search(
            [('student_id', '=', student.id)],
            order='sheet_id desc',
        ) if student else []
        return request.render('univ_sms_portal.portal_attendance', {
            'student': student,
            'attendance_lines': attendance_lines,
            'page_name': 'academic_attendance',
        })

    @route(['/my/academic/fees'], type='http', auth='user', website=True)
    def portal_fees(self, **kw):
        student = self._get_student()
        fees = request.env['univ.sms.fee'].sudo().search(
            [('student_id', '=', student.id)],
            order='term_id desc',
        ) if student else []
        return request.render('univ_sms_portal.portal_fees', {
            'student': student,
            'fees': fees,
            'page_name': 'academic_fees',
        })

    # ─── GIẤY CHỨNG NHẬN ─────────────────────────────────────────────────────

    @route(['/my/academic/certificates'], type='http', auth='user', website=True)
    def portal_certificates(self, **kw):
        student = self._get_student()
        certificate_types = request.env['univ.sms.certificate.type'].sudo().search(
            [('active', '=', True)], order='name'
        )
        requests = request.env['univ.sms.certificate.request'].sudo().search(
            [('student_id', '=', student.id)], order='create_date desc'
        ) if student else []
        return request.render('univ_sms_portal.portal_certificates', {
            'student': student,
            'certificate_types': certificate_types,
            'certificate_requests': requests,
            'flash': self._service_flash(kw),
            'page_name': 'academic_certificates',
        })

    @route(['/my/academic/certificates/create'], type='http', auth='user', website=True, methods=['POST'])
    def portal_certificate_create(self, certificate_type_id=None, reason=None, **kw):
        url = '/my/academic/certificates'
        student = self._get_student()
        if not student:
            return self._service_redirect(url, 'no_student')
        type_id = _parse_id(certificate_type_id)
        ctype = request.env['univ.sms.certificate.type'].sudo().search(
            [('id', '=', type_id), ('active', '=', True)], limit=1) if type_id else None
        if not ctype:
            return self._service_redirect(url, 'invalid_type')
        reason = _clean_text(reason, 1000)
        if not reason:
            return self._service_redirect(url, 'invalid_reason')
        # Phạm vi đã kiểm tra (SV của user, loại giấy còn hiệu lực) -> dùng sudo để ghi.
        Request = request.env['univ.sms.certificate.request'].sudo()
        if Request.search_count([
            ('student_id', '=', student.id),
            ('certificate_type_id', '=', ctype.id),
            ('state', 'in', ('draft', 'approved')),
        ]):
            return self._service_redirect(url, 'duplicate_cert')
        try:
            with request.env.cr.savepoint():
                Request.create({
                    'student_id': student.id,
                    'certificate_type_id': ctype.id,
                    'reason': reason,
                })
        except ValidationError:
            return self._service_redirect(url, 'duplicate_cert')
        except Exception:
            _logger.exception('Portal certificate request failed (student %s)', student.id)
            return self._service_redirect(url, 'error')
        return self._service_redirect(url, 'created')

    # ─── CÔNG TÁC SINH VIÊN ──────────────────────────────────────────────────

    @route(['/my/academic/student-affairs'], type='http', auth='user', website=True)
    def portal_student_affairs(self, **kw):
        student = self._get_student()
        health_insurances = request.env['univ.sms.health.insurance'].sudo().search(
            [('student_id', '=', student.id)], order='date_end desc'
        ) if student else []
        residences = request.env['univ.sms.residence.info'].sudo().search(
            [('student_id', '=', student.id)], order='effective_date desc'
        ) if student else []
        military_services = request.env['univ.sms.military.service'].sudo().search(
            [('student_id', '=', student.id)], order='declared_date desc'
        ) if student else []
        return request.render('univ_sms_portal.portal_student_affairs', {
            'student': student,
            'health_insurances': health_insurances,
            'residences': residences,
            'military_services': military_services,
            'military_statuses': request.env['univ.sms.military.service']._fields['registration_status'].selection,
            'flash': self._service_flash(kw),
            'page_name': 'academic_student_affairs',
        })

    @route(['/my/academic/student-affairs/military/create'], type='http', auth='user', website=True, methods=['POST'])
    def portal_military_create(self, registration_status=None, **kw):
        url = '/my/academic/student-affairs'
        student = self._get_student()
        if not student:
            return self._service_redirect(url, 'no_student')
        Military = request.env['univ.sms.military.service'].sudo()
        allowed = dict(Military._fields['registration_status'].selection)
        if not isinstance(registration_status, str) or registration_status not in allowed:
            return self._service_redirect(url, 'invalid_status')
        if Military.search_count([
            ('student_id', '=', student.id),
            ('state', 'in', ('draft', 'submitted')),
        ]):
            return self._service_redirect(url, 'duplicate_military')
        try:
            with request.env.cr.savepoint():
                military = Military.create({
                    'student_id': student.id,
                    'registration_status': registration_status,
                })
                military.action_submit()
        except Exception:
            _logger.exception('Portal military declaration failed (student %s)', student.id)
            return self._service_redirect(url, 'error')
        return self._service_redirect(url, 'created')

    # ─── RÈN LUYỆN ───────────────────────────────────────────────────────────

    @route(['/my/academic/conduct'], type='http', auth='user', website=True)
    def portal_conduct(self, **kw):
        student = self._get_student()
        scores = request.env['univ.sms.conduct.score'].sudo().search(
            [('student_id', '=', student.id)], order='period_id desc'
        ) if student else []
        return request.render('univ_sms_portal.portal_conduct', {
            'student': student,
            'conduct_scores': scores,
            'page_name': 'academic_conduct',
        })

    # ─── KHẢO SÁT ────────────────────────────────────────────────────────────

    def _open_survey_domain(self):
        today = fields.Date.context_today(request.env.user)
        return [('state', '=', 'open'), ('date_start', '<=', today), ('date_end', '>=', today)]

    @route(['/my/academic/surveys'], type='http', auth='user', website=True)
    def portal_surveys(self, **kw):
        student = self._get_student()
        surveys = request.env['univ.sms.survey.instance'].sudo().search(
            self._open_survey_domain(), order='date_end asc'
        )
        responses = request.env['univ.sms.survey.response'].sudo().search(
            [('student_id', '=', student.id)], order='create_date desc'
        ) if student else []
        answered_ids = responses.filtered(
            lambda r: r.state == 'submitted').mapped('survey_instance_id').ids if responses else []
        return request.render('univ_sms_portal.portal_surveys', {
            'student': student,
            'surveys': surveys,
            'responses': responses,
            'answered_ids': answered_ids,
            'flash': self._service_flash(kw),
            'page_name': 'academic_surveys',
        })

    @route(['/my/academic/surveys/submit'], type='http', auth='user', website=True, methods=['POST'])
    def portal_survey_submit(self, survey_instance_id=None, answer_data=None, **kw):
        url = '/my/academic/surveys'
        student = self._get_student()
        if not student:
            return self._service_redirect(url, 'no_student')
        instance_id = _parse_id(survey_instance_id)
        instance = request.env['univ.sms.survey.instance'].sudo().browse(instance_id).exists() \
            if instance_id else None
        if not instance:
            return self._service_redirect(url, 'invalid_survey')
        if not instance._is_accepting_responses():
            return self._service_redirect(url, 'closed_survey')
        answer = _clean_text(answer_data, 5000)
        if not answer:
            return self._service_redirect(url, 'invalid_answer')
        Response = request.env['univ.sms.survey.response'].sudo()
        response = Response.search([
            ('student_id', '=', student.id),
            ('survey_instance_id', '=', instance.id),
        ], limit=1)
        if response and response.state == 'submitted':
            return self._service_redirect(url, 'already_answered')
        try:
            with request.env.cr.savepoint():
                if response:
                    response.write({'answer_data': answer})
                else:
                    response = Response.create({
                        'student_id': student.id,
                        'survey_instance_id': instance.id,
                        'answer_data': answer,
                    })
                response.action_submit()
        except Exception:
            # Gửi đồng thời hai lần: ràng buộc unique(student, đợt) chặn bản ghi thứ hai.
            _logger.info('Portal survey submit rejected (student %s, survey %s)',
                         student.id, instance.id, exc_info=True)
            return self._service_redirect(url, 'already_answered')
        return self._service_redirect(url, 'submitted')

    # ─── GÓP Ý ───────────────────────────────────────────────────────────────

    @route(['/my/academic/feedback'], type='http', auth='user', website=True)
    def portal_feedback(self, **kw):
        student = self._get_student()
        feedbacks = request.env['univ.sms.feedback'].sudo().search(
            [('student_id', '=', student.id)], order='create_date desc'
        ) if student else []
        departments = request.env['univ.sms.department'].sudo().search([], order='name')
        return request.render('univ_sms_portal.portal_feedback', {
            'student': student,
            'feedbacks': feedbacks,
            'departments': departments,
            'categories': request.env['univ.sms.feedback']._fields['category'].selection,
            'flash': self._service_flash(kw),
            'page_name': 'academic_feedback',
        })

    @route(['/my/academic/feedback/create'], type='http', auth='user', website=True, methods=['POST'])
    def portal_feedback_create(self, category=None, subject=None, description=None, department_id=None, **kw):
        url = '/my/academic/feedback'
        student = self._get_student()
        if not student:
            return self._service_redirect(url, 'no_student')
        Feedback = request.env['univ.sms.feedback'].sudo()
        if not isinstance(category, str) or category not in dict(Feedback._fields['category'].selection):
            return self._service_redirect(url, 'invalid_category')
        subject = _clean_text(subject, 200)
        if not subject:
            return self._service_redirect(url, 'invalid_subject')
        description = _clean_text(description, 5000)
        if not description:
            return self._service_redirect(url, 'invalid_description')
        vals = {
            'student_id': student.id,
            'category': category,
            'subject': subject,
            'description': description,
        }
        if department_id not in (None, ''):
            dep_id = _parse_id(department_id)
            department = request.env['univ.sms.department'].sudo().browse(dep_id).exists() \
                if dep_id else None
            if not department:
                return self._service_redirect(url, 'invalid_department')
            vals['department_id'] = department.id
        try:
            with request.env.cr.savepoint():
                Feedback.create(vals)
        except ValidationError:
            return self._service_redirect(url, 'duplicate_feedback')
        except Exception:
            _logger.exception('Portal feedback failed (student %s)', student.id)
            return self._service_redirect(url, 'error')
        return self._service_redirect(url, 'created')

    # ─── ĐĂNG KÝ MÔN HỌC (F1) ───────────────────────────────────────────────

    def _get_open_registration_period(self):
        """Đợt đăng ký chính thức đang mở (mới nhất)."""
        return request.env['univ.sms.registration.period'].sudo().search([
            ('state', '=', 'open'),
            ('reg_type', '=', 'regular'),
        ], order='date_start desc, id desc', limit=1)

    @route(['/my/academic/registration'], type='http', auth='user', website=True)
    def portal_registration(self, **kw):
        student = self._get_student()
        period = self._get_open_registration_period()
        Registration = request.env['univ.sms.registration'].sudo()
        Waitlist = request.env['univ.sms.registration.waitlist'].sudo()

        if period:
            offerings = request.env['univ.sms.course.offering'].sudo().search([
                ('term_id', '=', period.term_id.id),
                ('active', '=', True),
            ], order='subject_id')
        else:
            offerings = request.env['univ.sms.course.offering'].sudo().browse()

        my_registrations = Registration.browse()
        my_waitlist = Waitlist.browse()
        if student and period:
            # Toàn bộ đăng ký trong HỌC KỲ của đợt (kể cả đợt trước đã đóng), vì kiểm tra
            # trùng môn / trùng lịch xét theo cả học kỳ.
            my_registrations = Registration.search([
                ('student_id', '=', student.id),
                ('term_id', '=', period.term_id.id),
                ('state', '!=', 'cancelled'),
            ])
            my_waitlist = Waitlist.search([
                ('student_id', '=', student.id),
                ('period_id', '=', period.id),
                ('state', 'in', ('waiting', 'rejected')),
            ], order='request_date desc, id desc')

        occupying = my_registrations.filtered(lambda r: r.state in ('registered', 'confirmed'))
        waiting = my_waitlist.filtered(lambda w: w.state == 'waiting')
        cancel_status = kw.get('cancel')
        return request.render('univ_sms_portal.portal_registration', {
            'student': student,
            'period': period,
            'offerings': offerings,
            'my_registrations': my_registrations,
            'my_waitlist': my_waitlist,
            'registered_offering_ids': occupying.mapped('offering_id').ids,
            'waiting_positions': {w.offering_id.id: w.position for w in waiting},
            'total_credits': sum(occupying.filtered(
                lambda r: r.period_id == period).mapped('subject_credit')),
            'term_credits': sum(occupying.mapped('subject_credit')),
            'cancel_status': cancel_status if cancel_status in ('ok', 'denied') else False,
            'page_name': 'academic_registration',
        })

    @route(['/my/academic/registration/add'], type='json', auth='user', website=True)
    def portal_registration_add(self, offering_id=None, **kw):
        def _reply(status, message, position=0):
            return {'status': status, 'message': message, 'position': position}

        student = self._get_student()
        if not student:
            return _reply('rejected', 'Không tìm thấy thông tin sinh viên của tài khoản này.')
        # offering_id phải là số nguyên dương (không nhận bool / chuỗi lạ).
        if isinstance(offering_id, bool):
            offering_id = None
        try:
            offering_id = int(offering_id)
        except (TypeError, ValueError):
            offering_id = 0
        if offering_id <= 0:
            return _reply('rejected', 'Lớp môn học không hợp lệ.')
        period = self._get_open_registration_period()
        if not period:
            return _reply('rejected', 'Hiện không có đợt đăng ký nào đang mở.')
        # Kiểm tra phạm vi TRƯỚC khi dùng sudo cho nghiệp vụ.
        offering = request.env['univ.sms.course.offering'].sudo().search([
            ('id', '=', offering_id),
            ('term_id', '=', period.term_id.id),
            ('active', '=', True),
        ], limit=1)
        if not offering:
            return _reply('rejected', 'Lớp môn học không thuộc đợt đăng ký đang mở.')
        try:
            with request.env.cr.savepoint():
                res = request.env['univ.sms.registration'].sudo().register_student(
                    student, offering, period)
        except (ValidationError, UserError) as exc:
            message = exc.args[0] if exc.args else 'Đăng ký không thành công.'
            return _reply('rejected', message)
        except Exception:
            _logger.exception('Portal registration failed (student %s, offering %s)',
                              student.id, offering.id)
            return _reply('error', 'Đã có lỗi xảy ra khi đăng ký. Vui lòng thử lại sau.')
        return _reply(res.get('status'), res.get('message'), res.get('position') or 0)

    @route(['/my/academic/registration/cancel/<int:reg_id>'],
           type='http', auth='user', website=True, methods=['POST'])
    def portal_registration_cancel(self, reg_id, **kw):
        student = self._get_student()
        status = 'denied'
        if student:
            # Chỉ đăng ký của chính sinh viên, còn hiệu lực, trong đợt đang mở.
            reg = request.env['univ.sms.registration'].sudo().search([
                ('id', '=', reg_id),
                ('student_id', '=', student.id),
                ('state', 'in', ('draft', 'registered', 'confirmed')),
                ('period_id.state', '=', 'open'),
            ], limit=1)
            if reg:
                reg.action_cancel()
                status = 'ok'
        return request.redirect('/my/academic/registration?cancel=%s' % status)

    # ─── THỜI KHÓA BIỂU ──────────────────────────────────────────────────────

    @route(['/my/academic/timetable'], type='http', auth='user', website=True)
    def portal_timetable(self, **kw):
        student = self._get_student()
        timetable_slots = request.env['univ.sms.timetable'].sudo()
        if student:
            class_ids = request.env['univ.sms.enrollment'].sudo().search([
                ('student_id', '=', student.id),
                ('state', '=', 'registered'),
                ('class_id', '!=', False),
            ]).mapped('class_id').ids
            if class_ids:
                timetable_slots = timetable_slots.search(
                    [('class_id', 'in', class_ids)],
                    order='day_of_week, start_time',
                )
            else:
                timetable_slots = timetable_slots.browse()
        else:
            timetable_slots = timetable_slots.browse()

        days = [
            ('0', 'Thứ Hai'), ('1', 'Thứ Ba'), ('2', 'Thứ Tư'),
            ('3', 'Thứ Năm'), ('4', 'Thứ Sáu'), ('5', 'Thứ Bảy'),
        ]
        return request.render('univ_sms_portal.portal_timetable', {
            'student': student,
            'timetable_slots': timetable_slots,
            'days': days,
            'page_name': 'academic_timetable',
        })
