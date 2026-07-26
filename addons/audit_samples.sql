SELECT code, name::text AS name
FROM univ_sms_faculty
ORDER BY code;

SELECT code, name AS name
FROM univ_sms_home_class
ORDER BY code;

SELECT c.name::text AS class_name, t.day_of_week, t.start_time, t.end_time, t.room, t.building
FROM univ_sms_timetable t
JOIN univ_sms_class c ON c.id = t.class_id
ORDER BY c.name::text
LIMIT 30;

SELECT s.name AS sheet_name, c.name::text AS class_name, s.attendance_date, p.name AS lecturer,
       COUNT(l.id) FILTER (WHERE l.state = 'present') AS present_count,
       COUNT(l.id) FILTER (WHERE l.state = 'absent') AS absent_count
FROM univ_sms_attendance_sheet s
JOIN univ_sms_class c ON c.id = s.class_id
LEFT JOIN res_partner p ON p.id = s.lecturer_id
LEFT JOIN univ_sms_attendance_line l ON l.sheet_id = s.id
GROUP BY s.id, s.name, c.name, s.attendance_date, p.name
ORDER BY s.attendance_date DESC, s.name
LIMIT 30;
