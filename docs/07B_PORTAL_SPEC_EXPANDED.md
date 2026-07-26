Route mới bổ sung vào univ_sms_portal/controllers/portal.py
pythonclass UnivSmsPortalExpanded(UnivSmsPortal):

    # --- Đăng ký môn học ---
    @route(['/my/academic/registration'], type='http', auth='user', website=True)
    def portal_registration(self, **kw):
        student = self._get_student()
        period = request.env['univ.sms.registration.period'].sudo().search(
            [('state', '=', 'open'), ('reg_type', '=', 'regular')], limit=1)
        offerings = request.env['univ.sms.course.offering'].sudo().search(
            [('term_id', '=', period.term_id.id)]) if period else []
        my_registrations = request.env['univ.sms.registration'].sudo().search(
            [('student_id', '=', student.id), ('period_id', '=', period.id)]) if period else []
        return request.render('univ_sms_portal.portal_registration', {
            'student': student, 'period': period,
            'offerings': offerings, 'my_registrations': my_registrations,
        })

    @route(['/my/academic/registration/submit'], type='http', auth='user',
           website=True, methods=['POST'], csrf=True)
    def portal_registration_submit(self, **post):
        student = self._get_student()
        offering_id = int(post.get('offering_id'))
        request.env['univ.sms.registration'].sudo().create({
            'student_id': student.id,
            'offering_id': offering_id,
            'period_id': int(post.get('period_id')),
        })
        return request.redirect('/my/academic/registration')

    # --- Thông báo ---
    @route(['/my/academic/notifications'], type='http', auth='user', website=True)
    def portal_notifications(self, **kw):
        student = self._get_student()
        domain = ['|', ('target_audience', '=', 'all'),
                  ('program_ids', 'in', student.program_id.id)]
        domain += [('state', '=', 'published')]
        notifications = request.env['univ.sms.notification'].sudo().search(
            domain, order='is_pinned desc, publish_date desc')
        return request.render('univ_sms_portal.portal_notifications', {
            'notifications': notifications,
        })

    # --- Form ý kiến ---
    @route(['/my/academic/feedback', '/my/academic/feedback/new'],
           type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_feedback(self, **post):
        student = self._get_student()
        if request.httprequest.method == 'POST':
            request.env['univ.sms.feedback'].sudo().create({
                'student_id': student.id,
                'category': post.get('category'),
                'subject': post.get('subject'),
                'description': post.get('description'),
                'department_id': int(post['department_id']) if post.get('department_id') else False,
            })
            return request.redirect('/my/academic/feedback')
        feedbacks = request.env['univ.sms.feedback'].sudo().search(
            [('student_id', '=', student.id)], order='create_date desc')
        departments = request.env['univ.sms.department'].sudo().search([])
        return request.render('univ_sms_portal.portal_feedback', {
            'feedbacks': feedbacks, 'departments': departments,
        })

    # --- Đánh giá rèn luyện ---
    @route(['/my/academic/conduct'], type='http', auth='user', website=True)
    def portal_conduct(self, **kw):
        student = self._get_student()
        scores = request.env['univ.sms.conduct.score'].sudo().search(
            [('student_id', '=', student.id)])
        return request.render('univ_sms_portal.portal_conduct', {
            'scores': scores, 'student': student,
        })

    # --- Xin giấy chứng nhận / phiếu ---
    @route(['/my/academic/certificate', '/my/academic/certificate/new'],
           type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_certificate(self, **post):
        student = self._get_student()
        if request.httprequest.method == 'POST':
            request.env['univ.sms.certificate.request'].sudo().create({
                'student_id': student.id,
                'certificate_type_id': int(post.get('certificate_type_id')),
                'purpose': post.get('purpose'),
                'quantity': int(post.get('quantity', 1)),
            })
            return request.redirect('/my/academic/certificate')
        requests_ = request.env['univ.sms.certificate.request'].sudo().search(
            [('student_id', '=', student.id)], order='request_date desc')
        cert_types = request.env['univ.sms.certificate.type'].sudo().search([])
        return request.render('univ_sms_portal.portal_certificate', {
            'requests': requests_, 'cert_types': cert_types,
        })

    # --- Common helper ---
    def _get_student(self):
        return request.env['univ.sms.student'].sudo().search(
            [('partner_id', '=', request.env.user.partner_id.id)], limit=1)

⚠️ Lưu ý bảo mật quan trọng: tất cả các route POST đều dùng .sudo() để create, nhưng student_id luôn được gán server-side từ _get_student() — KHÔNG đọc student_id từ post data của client để tránh injection (sinh viên A submit hộ sinh viên B). Đây là pattern bắt buộc cho mọi controller portal trong dự án.

Cập nhật menu Portal Dashboard (portal_my_home_academic mở rộng)
xml<template id="portal_my_home_academic_v2" inherit_id="univ_sms_portal.portal_my_home_academic">
    <xpath expr="//div[hasclass('row')][1]" position="after">
        <div class="row mt-2">
            <a href="/my/academic/registration" class="btn btn-outline-primary col-md-3 mx-2">Đăng ký môn học</a>
            <a href="/my/academic/notifications" class="btn btn-outline-primary col-md-3 mx-2">Thông báo</a>
            <a href="/my/academic/conduct" class="btn btn-outline-primary col-md-3 mx-2">Điểm rèn luyện</a>
            <a href="/my/academic/certificate" class="btn btn-outline-primary col-md-3 mx-2">Xin giấy chứng nhận</a>
            <a href="/my/academic/feedback" class="btn btn-outline-primary col-md-3 mx-2">Góp ý / Phản hồi</a>
        </div>
    </xpath>
</template>