# -*- coding: utf-8 -*-
"""Audit seeded University SMS data for broken text encoding."""

BAD_CHARS = ["?", "\u00c3", "\ufffd"]
TEXT_TYPES = {"char", "text", "html"}


def has_bad_text(value):
    return isinstance(value, str) and any(marker in value for marker in BAD_CHARS)


def log(message):
    print("[audit] %s" % message)


issues = []

models = env["ir.model"].search([("model", "like", "univ.sms.%")], order="model")
for model_info in models:
    model_name = model_info.model
    Model = env[model_name].sudo()
    fields_to_scan = [
        name for name, field in Model._fields.items()
        if field.type in TEXT_TYPES and not field.related
    ]
    if not fields_to_scan:
        continue

    for record in Model.search([]):
        bad_fields = []
        for field_name in fields_to_scan:
            value = record[field_name]
            if has_bad_text(value):
                bad_fields.append("%s=%r" % (field_name, value[:90]))
        if bad_fields:
            issues.append("%s,%s: %s" % (model_name, record.id, "; ".join(bad_fields)))

partner_domain = [
    "|", "|", "|", "|",
    ("email", "ilike", "@tdtu.edu.vn"),
    ("email", "ilike", "@student.tdtu.edu.vn"),
    ("email", "ilike", "@student.edu.vn"),
    ("name", "ilike", "Khoa"),
    ("name", "ilike", "Phòng"),
]
for partner in env["res.partner"].sudo().search(partner_domain):
    bad_fields = []
    for field_name in ["name", "email", "phone", "mobile", "street", "city"]:
        value = partner[field_name]
        if has_bad_text(value):
            bad_fields.append("%s=%r" % (field_name, value[:90]))
    if bad_fields:
        issues.append("res.partner,%s: %s" % (partner.id, "; ".join(bad_fields)))

if issues:
    log("FOUND %s bad text records" % len(issues))
    for issue in issues[:200]:
        log(issue)
else:
    log("OK: no broken text markers found")

counts = [
    ("faculties", env["univ.sms.faculty"].search_count([])),
    ("departments", env["univ.sms.department"].search_count([])),
    ("programs", env["univ.sms.program"].search_count([])),
    ("subjects", env["univ.sms.subject"].search_count([])),
    ("home_classes", env["univ.sms.home.class"].search_count([])),
    ("course_classes", env["univ.sms.class"].search_count([])),
    ("timetables", env["univ.sms.timetable"].search_count([])),
    ("attendance_sheets", env["univ.sms.attendance.sheet"].search_count([])),
    ("students", env["univ.sms.student"].search_count([])),
    ("enrollments", env["univ.sms.enrollment"].search_count([])),
    ("registrations", env["univ.sms.registration"].search_count([])),
    ("exam_results", env["univ.sms.exam.result"].search_count([])),
    ("fees", env["univ.sms.fee"].search_count([])),
    ("certificate_requests", env["univ.sms.certificate.request"].search_count([])),
    ("conduct_scores", env["univ.sms.conduct.score"].search_count([])),
    ("survey_responses", env["univ.sms.survey.response"].search_count([])),
    ("feedbacks", env["univ.sms.feedback"].search_count([])),
    ("notifications", env["univ.sms.notification"].search_count([])),
]
for label, count in counts:
    log("%s=%s" % (label, count))
