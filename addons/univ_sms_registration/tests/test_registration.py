from datetime import timedelta

from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import RegistrationCase


@tagged('post_install', '-at_install', 'univ_sms', 'univ_sms_registration')
class TestRegistrationService(RegistrationCase):

    # ─── AT01 ──────────────────────────────────────────────────────────────
    def test_at01_valid_registration_creates_enrollment_and_updates_fee(self):
        fee = False
        if 'univ.sms.fee' in self.env:
            fee = self.env['univ.sms.fee'].create({
                'student_id': self.s1.id, 'term_id': self.term.id, 'fee_per_credit': 500000})
            self.assertEqual(fee.total_credits, 0)

        res = self._register(self.s1, self.off_a)
        self.assertEqual(res['status'], 'registered', res['message'])
        reg = self.Registration.browse(res['registration_id'])
        self.assertEqual(reg.state, 'registered')
        self.assertTrue(reg.result_message)
        self.assertEqual(self.off_a.registered_count, 1)
        self.assertEqual(self.off_a.available_seats, 29)

        enrollment = self._enrollment(self.s1, self.sub_a)
        self.assertEqual(len(enrollment), 1)
        self.assertEqual(enrollment.state, 'registered')
        self.assertEqual(enrollment.class_id, self.cls_a)
        self.assertEqual(reg.enrollment_id, enrollment)
        self.assertEqual(self.cls_a.enrollment_count, 1)

        if fee:
            self.assertEqual(fee.total_credits, 3)
            self.assertEqual(fee.total_amount, 1500000)

    # ─── AT02 / tín chỉ ────────────────────────────────────────────────────
    def test_at02_missing_prerequisite_rejected(self):
        res = self._register(self.s1, self.off_b)
        self.assertEqual(res['status'], 'rejected')
        self.assertIn('tiên quyết', res['message'])
        self.assertIn(self.sub_a.name, res['message'])
        self.assertFalse(self._occupying(self.off_b, self.s1))
        self.assertEqual(self.off_b.registered_count, 0)
        self.assertFalse(self._enrollment(self.s1, self.sub_b))

        # Đã đạt môn tiên quyết thì đăng ký được.
        self._pass_subject(self.s1, self.cls_old_a)
        res = self._register(self.s1, self.off_b)
        self.assertEqual(res['status'], 'registered', res['message'])

    def test_prerequisite_failed_score_still_rejected(self):
        self._pass_subject(self.s1, self.cls_old_a, score=3.0)
        res = self._register(self.s1, self.off_b)
        self.assertEqual(res['status'], 'rejected')

    def test_over_max_credit_rejected(self):
        self.period.max_credit = 6
        self.assertEqual(self._register(self.s1, self.off_a)['status'], 'registered')
        res = self._register(self.s1, self.off_c)  # 3 + 4 > 6
        self.assertEqual(res['status'], 'rejected')
        self.assertIn('tín chỉ tối đa', res['message'])
        self.assertEqual(self.off_c.registered_count, 0)
        # Môn 2 TC vẫn vừa (3 + 2 <= 6).
        self.assertEqual(self._register(self.s1, self.off_e)['status'], 'registered')

    # ─── AT03 ──────────────────────────────────────────────────────────────
    def test_at03_timetable_conflict_rejected(self):
        self.assertEqual(self._register(self.s1, self.off_a)['status'], 'registered')
        seats_before = self.off_d.available_seats
        res = self._register(self.s1, self.off_d)
        self.assertEqual(res['status'], 'rejected')
        self.assertIn('Trùng lịch', res['message'])
        self.assertIn(self.sub_a.name, res['message'])
        self.assertIn('Thứ Hai', res['message'])
        self.assertIn('07:00-09:00', res['message'])
        self.off_d.invalidate_recordset()
        self.assertEqual(self.off_d.available_seats, seats_before)
        self.assertEqual(self.off_d.registered_count, 0)
        self.assertFalse(self._enrollment(self.s1, self.sub_d))

    def test_timetable_overlap_rule(self):
        Timetable = self.env['univ.sms.timetable']
        slot_a = self.cls_a.timetable_ids
        touching = Timetable.create({'class_id': self.cls_c.id, 'day_of_week': '0',
                                     'start_time': 9.0, 'end_time': 11.0})
        other_day = Timetable.create({'class_id': self.cls_c.id, 'day_of_week': '5',
                                      'start_time': 7.0, 'end_time': 9.0})
        self.assertTrue(slot_a._overlaps(self.cls_d.timetable_ids))
        self.assertFalse(slot_a._overlaps(touching))
        self.assertFalse(slot_a._overlaps(other_day))
        conflicts = self.Registration._find_timetable_conflicts(self.s1, self.off_d)
        self.assertFalse(conflicts)  # chưa đăng ký gì

    def test_offering_without_timetable_not_checked(self):
        klass = self.env['univ.sms.class'].create({
            'name': 'F1-NOTT', 'code': 'F1-NOTT', 'subject_id': self.sub_d.id,
            'term_id': self.term.id})
        offering = self.env['univ.sms.course.offering'].create({
            'subject_id': self.sub_d.id, 'term_id': self.term.id, 'class_id': klass.id,
            'max_seats': 5})
        self._register(self.s1, self.off_a)
        self.assertEqual(self._register(self.s1, offering)['status'], 'registered')

    # ─── AT04 / AT05 ───────────────────────────────────────────────────────
    def test_at04_full_class_goes_to_waitlist_with_positions(self):
        self.assertEqual(self._register(self.s1, self.off_e)['status'], 'registered')
        self.assertTrue(self.off_e.is_full)
        r2 = self._register(self.s2, self.off_e)
        r3 = self._register(self.s3, self.off_e)
        self.assertEqual(r2['status'], 'waitlisted')
        self.assertEqual(r2['position'], 1)
        self.assertIn('vị trí chờ số 1', r2['message'])
        self.assertEqual(r3['status'], 'waitlisted')
        self.assertEqual(r3['position'], 2)
        self.off_e.invalidate_recordset()
        self.assertEqual(self.off_e.waitlist_count, 2)
        self.assertEqual(self.off_e.registered_count, 1)
        self.assertFalse(self._occupying(self.off_e, self.s2))
        self.assertFalse(self._enrollment(self.s2, self.sub_e))
        # Đăng ký lại khi đang chờ: không tạo bản ghi chờ mới.
        again = self._register(self.s2, self.off_e)
        self.assertEqual(again['status'], 'already')
        self.assertEqual(again['position'], 1)
        self.assertEqual(self.Waitlist.search_count([
            ('student_id', '=', self.s2.id), ('offering_id', '=', self.off_e.id)]), 1)

    def test_waitlist_single_waiting_constraint(self):
        self._register(self.s1, self.off_e)
        self._register(self.s2, self.off_e)
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError),                 self.cr.savepoint():
            self.Waitlist.create({'student_id': self.s2.id, 'offering_id': self.off_e.id,
                                  'period_id': self.period.id})

    def test_at05_cancel_promotes_first_waiting(self):
        reg1 = self.Registration.browse(self._register(self.s1, self.off_e)['registration_id'])
        w2 = self.Waitlist.browse(self._register(self.s2, self.off_e)['waitlist_id'])
        w3 = self.Waitlist.browse(self._register(self.s3, self.off_e)['waitlist_id'])

        reg1.action_cancel()
        self.assertEqual(reg1.state, 'cancelled')
        self.assertEqual(reg1.enrollment_id.state, 'cancelled')
        self.assertEqual(w2.state, 'promoted')
        self.assertTrue(w2.processed_date)
        reg2 = w2.registration_id
        self.assertEqual(reg2.student_id, self.s2)
        self.assertEqual(reg2.state, 'registered')
        enrollment2 = self._enrollment(self.s2, self.sub_e)
        self.assertEqual(enrollment2.state, 'registered')
        self.assertEqual(reg2.enrollment_id, enrollment2)
        self.off_e.invalidate_recordset()
        self.assertEqual(self.off_e.registered_count, 1)
        self.assertEqual(self.off_e.waitlist_count, 1)
        self.assertEqual(w3.state, 'waiting')
        w3.invalidate_recordset(['position'])
        self.assertEqual(w3.position, 1)
        self.assertEqual(self.cls_e.enrollment_count, 1)

    def test_cancel_decreases_seat_count_without_waitlist(self):
        res = self._register(self.s1, self.off_a)
        self._register(self.s2, self.off_a)
        self.assertEqual(self.off_a.registered_count, 2)
        self.Registration.browse(res['registration_id']).action_cancel()
        self.off_a.invalidate_recordset()
        self.assertEqual(self.off_a.registered_count, 1)
        self.assertEqual(self.cls_a.enrollment_count, 1)

    def test_promotion_skips_ineligible_student(self):
        reg1 = self.Registration.browse(self._register(self.s1, self.off_e)['registration_id'])
        w2 = self.Waitlist.browse(self._register(self.s2, self.off_e)['waitlist_id'])
        w3 = self.Waitlist.browse(self._register(self.s3, self.off_e)['waitlist_id'])
        self.s2.action_on_leave()  # bảo lưu → không còn đủ điều kiện
        reg1.action_cancel()
        self.assertEqual(w2.state, 'rejected')
        self.assertIn('đang học', w2.note)
        self.assertEqual(w3.state, 'promoted')
        self.assertTrue(self._occupying(self.off_e, self.s3))

    def test_promotion_rejects_timetable_conflict(self):
        reg1 = self.Registration.browse(self._register(self.s1, self.off_e)['registration_id'])
        w2 = self.Waitlist.browse(self._register(self.s2, self.off_e)['waitlist_id'])
        # Trong lúc chờ, s2 đăng ký lớp khác trùng giờ Thứ Tư.
        klass = self.env['univ.sms.class'].create({
            'name': 'F1-WED', 'code': 'F1-WED', 'subject_id': self.sub_c.id, 'term_id': self.term.id})
        self.env['univ.sms.timetable'].create({'class_id': klass.id, 'day_of_week': '2',
                                               'start_time': 8.0, 'end_time': 10.0})
        off_wed = self.env['univ.sms.course.offering'].create({
            'subject_id': self.sub_c.id, 'term_id': self.term.id, 'class_id': klass.id,
            'max_seats': 10})
        self.assertEqual(self._register(self.s2, off_wed)['status'], 'registered')
        reg1.action_cancel()
        self.assertEqual(w2.state, 'rejected')
        self.assertIn('Trùng lịch', w2.note)
        self.assertEqual(self.off_e.registered_count, 0)

    def test_max_seats_increase_promotes(self):
        self._register(self.s1, self.off_e)
        w2 = self.Waitlist.browse(self._register(self.s2, self.off_e)['waitlist_id'])
        w3 = self.Waitlist.browse(self._register(self.s3, self.off_e)['waitlist_id'])
        self.off_e.max_seats = 2
        self.assertEqual(w2.state, 'promoted')
        self.assertEqual(w3.state, 'waiting')
        self.assertEqual(self.off_e.registered_count, 2)

    def test_closed_period_keeps_waitlist(self):
        reg1 = self.Registration.browse(self._register(self.s1, self.off_e)['registration_id'])
        w2 = self.Waitlist.browse(self._register(self.s2, self.off_e)['waitlist_id'])
        self.period.action_close()
        reg1.action_cancel()
        self.assertEqual(w2.state, 'waiting')

    # ─── Các trường hợp từ chối khác ───────────────────────────────────────
    def test_duplicate_subject_rejected(self):
        self.assertEqual(self._register(self.s1, self.off_a)['status'], 'registered')
        res = self._register(self.s1, self.off_a2)
        self.assertEqual(res['status'], 'rejected')
        self.assertIn('đã đăng ký môn', res['message'])
        self.assertEqual(self.off_a2.registered_count, 0)

    def test_non_studying_student_rejected(self):
        student = self.env['univ.sms.student'].create({'name': 'SV nháp', 'program_id': self.program.id})
        res = self._register(student, self.off_a)
        self.assertEqual(res['status'], 'rejected')
        self.assertIn('đang học', res['message'])
        self.assertEqual(self.off_a.registered_count, 0)

    def test_closed_period_rejected(self):
        self.period.action_close()
        res = self._register(self.s1, self.off_a)
        self.assertEqual(res['status'], 'rejected')
        self.assertIn('đã đóng', res['message'])

    def test_expired_period_rejected(self):
        self.period.write({'date_start': fields.Datetime.now() - timedelta(days=10),
                           'date_end': fields.Datetime.now() - timedelta(days=1)})
        res = self._register(self.s1, self.off_a)
        self.assertEqual(res['status'], 'rejected')
        self.assertIn('hết hạn', res['message'])

    def test_offering_of_other_term_rejected(self):
        res = self._register(self.s1, self.off_old)
        self.assertEqual(res['status'], 'rejected')
        self.assertIn('học kỳ', res['message'])

    # ─── Idempotency / đăng ký lại ─────────────────────────────────────────
    def test_idempotent_register_and_sync(self):
        first = self._register(self.s1, self.off_a)
        second = self._register(self.s1, self.off_a)
        self.assertEqual(first['status'], 'registered')
        self.assertEqual(second['status'], 'already')
        self.assertEqual(second['registration_id'], first['registration_id'])
        self.assertEqual(self.Registration.search_count([
            ('student_id', '=', self.s1.id), ('offering_id', '=', self.off_a.id)]), 1)
        reg = self.Registration.browse(first['registration_id'])
        enrollment_count = self.Enrollment.search_count([('student_id', '=', self.s1.id)])
        reg._sync_enrollment()
        reg._sync_enrollment()
        self.assertEqual(self.Enrollment.search_count([('student_id', '=', self.s1.id)]),
                         enrollment_count)
        self.assertEqual(reg.enrollment_id, self._enrollment(self.s1, self.sub_a))
        self.assertEqual(self.off_a.registered_count, 1)

    def test_reregister_after_cancel_reuses_record(self):
        first = self._register(self.s1, self.off_a)
        reg = self.Registration.browse(first['registration_id'])
        enrollment = reg.enrollment_id
        reg.action_cancel()
        self.assertEqual(enrollment.state, 'cancelled')
        again = self._register(self.s1, self.off_a)
        self.assertEqual(again['status'], 'registered')
        self.assertEqual(again['registration_id'], reg.id)
        self.assertEqual(reg.state, 'registered')
        self.assertEqual(reg.enrollment_id, enrollment)
        self.assertEqual(enrollment.state, 'registered')
        self.assertEqual(self.Enrollment.search_count([
            ('student_id', '=', self.s1.id), ('subject_id', '=', self.sub_a.id)]), 1)

    def test_existing_enrollment_is_reused(self):
        enrollment = self.Enrollment.create({
            'student_id': self.s1.id, 'subject_id': self.sub_a.id, 'term_id': self.term.id,
            'state': 'cancelled'})
        res = self._register(self.s1, self.off_a)
        reg = self.Registration.browse(res['registration_id'])
        self.assertEqual(reg.enrollment_id, enrollment)
        self.assertEqual(enrollment.state, 'registered')
        self.assertEqual(enrollment.class_id, self.cls_a)

    # ─── Back-office / trạng thái chiếm chỗ ────────────────────────────────
    def test_draft_registration_does_not_occupy(self):
        reg = self.Registration.create({
            'student_id': self.s1.id, 'offering_id': self.off_e.id,
            'period_id': self.period.id, 'state': 'draft'})
        self.assertEqual(self.off_e.registered_count, 0)
        self.assertFalse(reg.enrollment_id)
        # Người khác vẫn đăng ký được chỗ duy nhất.
        self.assertEqual(self._register(self.s2, self.off_e)['status'], 'registered')
        # Đưa bản nháp lên 'registered' bị chặn vì hết chỗ.
        with self.assertRaises(ValidationError), self.cr.savepoint():
            reg.action_register()

    def test_backoffice_create_still_validated(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.Registration.create({
                'student_id': self.s1.id, 'offering_id': self.off_b.id,
                'period_id': self.period.id})
        self._register(self.s1, self.off_a)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.Registration.create({
                'student_id': self.s1.id, 'offering_id': self.off_d.id,
                'period_id': self.period.id})

    def test_backoffice_create_syncs_enrollment(self):
        reg = self.Registration.create({
            'student_id': self.s1.id, 'offering_id': self.off_c.id, 'period_id': self.period.id})
        self.assertEqual(reg.state, 'registered')
        self.assertEqual(reg.enrollment_id, self._enrollment(self.s1, self.sub_c))
        reg.action_confirm()
        self.assertEqual(reg.enrollment_id.state, 'registered')
        reg.unlink()
        self.assertEqual(self._enrollment(self.s1, self.sub_c).state, 'cancelled')
