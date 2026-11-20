#!/usr/bin/env bash
# Dựng database demo hoàn chỉnh ở local rồi xuất file dump để nạp lên Postgres cloud.
# Cách dùng: tools/build_deploy_db.sh [db_name]   (mặc định: univ_sms_demo)
#  1. Tạo DB mới, cài 16 module univ_sms
#  2. Chạy seed demo (tools/seed_demo.py), lặp lại an toàn
#  3. Chuyển file đính kèm vào database (ir_attachment.location = db) vì host free
#     không có ổ đĩa bền
#  4. Xuất backups/<db>_<ngày>.dump (pg_dump -Fc, không kèm owner/ACL)
set -euo pipefail
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")/.."
DB="${1:-univ_sms_demo}"
[ "$DB" = "univ_sms_db" ] && { echo "Không dùng univ_sms_db"; exit 2; }
MODS="univ_sms_base,univ_sms_student,univ_sms_class,univ_sms_attendance,univ_sms_exam,univ_sms_fee,univ_sms_registration,univ_sms_portal,univ_sms_notification,univ_sms_feedback,univ_sms_student_affairs,univ_sms_conduct,univ_sms_certificate,univ_sms_survey,univ_sms_report,univ_sms_early_warning"
mkdir -p backups test-results
docker compose up -d db >/dev/null
docker compose exec -T db psql -U odoo -d postgres -q -c "DROP DATABASE IF EXISTS \"$DB\""
echo "[1/4] Cài module vào $DB"
docker compose run --rm -T odoo odoo -c /etc/odoo/odoo.conf -d "$DB" -i "$MODS" \
  --without-demo=all --stop-after-init --log-level=warn > "test-results/build_$DB.log" 2>&1
echo "[2/4] Nạp dữ liệu demo"
docker compose run --rm -T odoo odoo shell -c /etc/odoo/odoo.conf -d "$DB" --no-http \
  < tools/seed_demo.py >> "test-results/build_$DB.log" 2>&1
echo "[3/4] Lưu file đính kèm trong database"
docker compose run --rm -T odoo odoo shell -c /etc/odoo/odoo.conf -d "$DB" --no-http >> "test-results/build_$DB.log" 2>&1 <<'PY'
env['ir.config_parameter'].sudo().set_param('ir_attachment.location', 'db')
env['ir.attachment'].sudo().force_storage()
# Xóa bundle asset đã biên dịch: server mới sẽ tự biên dịch lại
env['ir.attachment'].sudo().search([('res_model', '=', 'ir.ui.view'), ('name', 'ilike', 'assets')]).unlink()
env.cr.commit()
print('attachment storage ->', env['ir.config_parameter'].sudo().get_param('ir_attachment.location'))
PY
OUT="backups/${DB}_$(date +%Y%m%d_%H%M).dump"
echo "[4/4] Xuất $OUT"
docker compose exec -T db pg_dump -U odoo -Fc --no-owner --no-acl "$DB" > "$OUT"
ls -la "$OUT"
grep -iE "traceback|error" "test-results/build_$DB.log" | grep -v "fa class\|<string>" | head -5 || true
