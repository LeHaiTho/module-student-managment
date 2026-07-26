from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request, route


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
        if NotifModel:
            try:
                notifications = NotifModel.sudo().search(
                    [('state', '=', 'published')],
                    limit=6, order='publish_date desc, id desc',
                )
            except Exception:
                pass
        return request.render('univ_sms_portal.university_landing', {
            'notifications': notifications,
        })

    def _get_student(self):
        """Helper: lấy sinh viên của user hiện tại"""
        return request.env['univ.sms.student'].sudo().search(
            [('partner_id', '=', request.env.user.partner_id.id)], limit=1
        )

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'enrollment_count' in counters:
            student = self._get_student()
            values['enrollment_count'] = len(student.enrollment_ids) if student else 0
        return values

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
        }

    @route(['/student/register'], type='http', auth='public', website=True)
    def portal_student_register(self, **kw):
        student = False if request.env.user._is_public() else self._get_student()
        if student:
            return request.redirect('/my/academic')
        values = self._prepare_student_registration_values()
        return request.render('univ_sms_portal.portal_student_register', values)

    @route(['/student/register/submit'], type='http', auth='public', website=True, methods=['POST'])
    def portal_student_register_submit(self, **post):
        current_user = request.env.user
        is_public_user = current_user._is_public()
        student_model = request.env['univ.sms.student'].sudo()
        user_model = request.env['res.users'].sudo().with_context(no_reset_password=True)
        form_values = {
            'name': (post.get('name') or '').strip(),
            'login': (post.get('login') or '').strip(),
            'personal_email': (post.get('personal_email') or '').strip(),
            'phone': (post.get('phone') or '').strip(),
            'mobile': (post.get('mobile') or '').strip(),
            'home_address': (post.get('home_address') or '').strip(),
            'current_address': (post.get('current_address') or '').strip(),
            'date_of_birth': (post.get('date_of_birth') or '').strip(),
            'gender': (post.get('gender') or '').strip(),
            'id_number': (post.get('id_number') or '').strip(),
            'program_id': (post.get('program_id') or '').strip(),
            'academic_year_id': (post.get('academic_year_id') or '').strip(),
            'training_system': (post.get('training_system') or 'regular').strip(),
        }
        password = post.get('password') or ''
        confirm_password = post.get('confirm_password') or ''
        errors = []

        if not form_values['name']:
            errors.append('Vui lòng nhập họ và tên.')
        if not form_values['program_id']:
            errors.append('Vui lòng chọn ngành học.')
        if not form_values['academic_year_id']:
            errors.append('Vui lòng chọn niên khóa nhập học.')
        if not form_values['date_of_birth']:
            errors.append('Vui lòng nhập ngày sinh.')
        if not form_values['personal_email']:
            errors.append('Vui lòng nhập email liên hệ.')
        if not form_values['phone'] and not form_values['mobile']:
            errors.append('Vui lòng nhập ít nhất một số điện thoại liên hệ.')

        if is_public_user:
            if not form_values['login']:
                errors.append('Vui lòng nhập tên đăng nhập.')
            if not password:
                errors.append('Vui lòng nhập mật khẩu.')
            if password != confirm_password:
                errors.append('Mật khẩu xác nhận không khớp.')
            if form_values['login'] and user_model.with_context(active_test=False).search([('login', '=', form_values['login'])], limit=1):
                errors.append('Tên đăng nhập đã tồn tại, vui lòng chọn tên khác.')
        elif self._get_student():
            return request.redirect('/my/academic')

        if form_values['id_number'] and student_model.search([('id_number', '=', form_values['id_number'])], limit=1):
            errors.append('Số CCCD/CMND đã tồn tại trong hệ thống.')

        try:
            program_id = int(form_values['program_id']) if form_values['program_id'] else False
            academic_year_id = int(form_values['academic_year_id']) if form_values['academic_year_id'] else False
        except ValueError:
            program_id = False
            academic_year_id = False
            errors.append('Thông tin ngành học hoặc niên khóa không hợp lệ.')

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

                home_class = request.env['univ.sms.home.class'].sudo().search([
                    ('program_id', '=', program_id),
                    ('academic_year_id', '=', academic_year_id),
                ], limit=1)

                student = student_model.create({
                    'partner_id': partner.id,
                    'program_id': program_id,
                    'home_class_id': home_class.id if home_class else False,
                    'academic_year_id': academic_year_id,
                    'training_system': form_values['training_system'],
                    'date_of_birth': form_values['date_of_birth'],
                    'gender': form_values['gender'] or 'male',
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
        except Exception as exc:
            errors.append(getattr(exc, 'name', str(exc)))
            values = self._prepare_student_registration_values(form_values=form_values, errors=errors)
            return request.render('univ_sms_portal.portal_student_register', values)

        if not is_public_user:
            return request.redirect('/my/academic')

        values = self._prepare_student_registration_values(success_data=success_data)
        return request.render('univ_sms_portal.portal_student_register', values)

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

    # ─── ĐĂNG KÝ MÔN HỌC ONLINE ──────────────────────────────────────────────

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
            'page_name': 'academic_certificates',
        })

    @route(['/my/academic/certificates/create'], type='http', auth='user', website=True, methods=['POST'])
    def portal_certificate_create(self, certificate_type_id=None, reason=None, **kw):
        student = self._get_student()
        if student and certificate_type_id:
            request.env['univ.sms.certificate.request'].sudo().create({
                'student_id': student.id,
                'certificate_type_id': int(certificate_type_id),
                'reason': reason,
            })
        return request.redirect('/my/academic/certificates')

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
            'page_name': 'academic_student_affairs',
        })

    @route(['/my/academic/student-affairs/military/create'], type='http', auth='user', website=True, methods=['POST'])
    def portal_military_create(self, registration_status=None, **kw):
        student = self._get_student()
        if student and registration_status:
            military = request.env['univ.sms.military.service'].sudo().create({
                'student_id': student.id,
                'registration_status': registration_status,
            })
            military.action_submit()
        return request.redirect('/my/academic/student-affairs')

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

    @route(['/my/academic/surveys'], type='http', auth='user', website=True)
    def portal_surveys(self, **kw):
        student = self._get_student()
        surveys = request.env['univ.sms.survey.instance'].sudo().search(
            [('state', '=', 'open')], order='date_end asc'
        )
        responses = request.env['univ.sms.survey.response'].sudo().search(
            [('student_id', '=', student.id)], order='create_date desc'
        ) if student else []
        answered_ids = responses.mapped('survey_instance_id').ids if responses else []
        return request.render('univ_sms_portal.portal_surveys', {
            'student': student,
            'surveys': surveys,
            'responses': responses,
            'answered_ids': answered_ids,
            'page_name': 'academic_surveys',
        })

    @route(['/my/academic/surveys/submit'], type='http', auth='user', website=True, methods=['POST'])
    def portal_survey_submit(self, survey_instance_id=None, answer_data=None, **kw):
        student = self._get_student()
        if student and survey_instance_id:
            response = request.env['univ.sms.survey.response'].sudo().search([
                ('student_id', '=', student.id),
                ('survey_instance_id', '=', int(survey_instance_id)),
            ], limit=1)
            if response:
                response.write({'answer_data': answer_data})
            else:
                response = request.env['univ.sms.survey.response'].sudo().create({
                    'student_id': student.id,
                    'survey_instance_id': int(survey_instance_id),
                    'answer_data': answer_data,
                })
            response.action_submit()
        return request.redirect('/my/academic/surveys')

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
            'page_name': 'academic_feedback',
        })

    @route(['/my/academic/feedback/create'], type='http', auth='user', website=True, methods=['POST'])
    def portal_feedback_create(self, category=None, subject=None, description=None, department_id=None, **kw):
        student = self._get_student()
        if student and category and subject and description:
            vals = {
                'student_id': student.id,
                'category': category,
                'subject': subject,
                'description': description,
            }
            if department_id:
                vals['department_id'] = int(department_id)
            request.env['univ.sms.feedback'].sudo().create(vals)
        return request.redirect('/my/academic/feedback')

    @route(['/my/academic/registration'], type='http', auth='user', website=True)
    def portal_registration(self, **kw):
        student = self._get_student()
        period = request.env['univ.sms.registration.period'].sudo().search([
            ('state', '=', 'open'),
            ('reg_type', '=', 'regular'),
        ], limit=1)

        if period:
            offerings = request.env['univ.sms.course.offering'].sudo().search([
                ('term_id', '=', period.term_id.id),
                ('active', '=', True),
            ], order='subject_id')
        else:
            offerings = request.env['univ.sms.course.offering'].sudo().browse()

        if student and period:
            my_registrations = request.env['univ.sms.registration'].sudo().search([
                ('student_id', '=', student.id),
                ('period_id', '=', period.id),
                ('state', '!=', 'cancelled'),
            ])
        else:
            my_registrations = request.env['univ.sms.registration'].sudo().browse()

        return request.render('univ_sms_portal.portal_registration', {
            'student': student,
            'period': period,
            'offerings': offerings,
            'my_registrations': my_registrations,
            'registered_offering_ids': my_registrations.mapped('offering_id').ids,
            'page_name': 'academic_registration',
        })

    @route(['/my/academic/registration/add'], type='json', auth='user', website=True)
    def portal_registration_add(self, offering_id=None, **kw):
        student = self._get_student()
        if not student:
            return {'error': 'Không tìm thấy thông tin sinh viên'}
        period = request.env['univ.sms.registration.period'].sudo().search([
            ('state', '=', 'open'),
            ('reg_type', '=', 'regular'),
        ], limit=1)
        if not period:
            return {'error': 'Không có đợt đăng ký nào đang mở'}
        try:
            request.env['univ.sms.registration'].sudo().create({
                'student_id': student.id,
                'offering_id': int(offering_id),
                'period_id': period.id,
            })
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    @route(['/my/academic/registration/cancel/<int:reg_id>'],
           type='http', auth='user', website=True, methods=['POST'])
    def portal_registration_cancel(self, reg_id, **kw):
        student = self._get_student()
        if student:
            reg = request.env['univ.sms.registration'].sudo().search([
                ('id', '=', reg_id),
                ('student_id', '=', student.id),
                ('state', 'in', ('draft', 'registered')),
            ], limit=1)
            if reg:
                reg.action_cancel()
        return request.redirect('/my/academic/registration')

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
