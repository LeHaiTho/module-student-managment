#!/bin/bash
# Entrypoint cho môi trường demo (Render / Railway / bất kỳ Docker host nào).
#
# Biến môi trường:
#   DATABASE_URL          postgres://user:pass@host:port/dbname[?sslmode=require]  (bắt buộc)
#   ODOO_MASTER_PASSWORD  mật khẩu master của Odoo (bắt buộc ở production)
#   ODOO_INIT_MODULES     module cài khi database CHƯA được khởi tạo (mặc định: toàn bộ univ_sms)
#   ODOO_UPDATE_MODULES   nếu đặt (vd "all" hoặc "univ_sms_portal"), chạy -u trước khi phục vụ
#   PORT                  cổng HTTP (Render tự đặt)
set -e

ODOO_RC="${ODOO_RC:-/etc/odoo/odoo.conf}"
DEFAULT_MODULES="univ_sms_base,univ_sms_student,univ_sms_class,univ_sms_attendance,univ_sms_exam,univ_sms_fee,univ_sms_registration,univ_sms_portal,univ_sms_notification,univ_sms_feedback,univ_sms_student_affairs,univ_sms_conduct,univ_sms_certificate,univ_sms_survey,univ_sms_report,univ_sms_early_warning"

if [ -z "${DATABASE_URL:-}" ]; then
    echo "DATABASE_URL is required" >&2
    exit 1
fi

# Tách DATABASE_URL thành biến HOST/PORT/USER/PASSWORD/ODOO_DB_NAME/PGSSLMODE
eval "$(
    python3 - <<'PY'
import os
import shlex
from urllib.parse import parse_qs, unquote, urlparse

parsed = urlparse(os.environ["DATABASE_URL"])
query = parse_qs(parsed.query)
values = {
    "DB_HOST": parsed.hostname or "",
    "DB_PORT": str(parsed.port or 5432),
    "DB_USER": unquote(parsed.username or ""),
    "DB_PASSWORD": unquote(parsed.password or ""),
    "ODOO_DB_NAME": os.environ.get("ODOO_DB_NAME") or unquote((parsed.path or "").lstrip("/")),
}
sslmode = (query.get("sslmode") or [""])[0]
if sslmode:
    values["PGSSLMODE"] = sslmode
for key, value in values.items():
    print(f"export {key}={shlex.quote(value)}")
PY
)"

if [ -z "${ODOO_MASTER_PASSWORD:-}" ]; then
    echo "WARNING: ODOO_MASTER_PASSWORD is not set; generating a random master password for this run." >&2
    ODOO_MASTER_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
fi

# Ghi thông tin kết nối và mật khẩu master vào file cấu hình (không lộ ra dòng lệnh / log)
python3 - "$ODOO_RC" <<'PY'
import configparser
import os
import sys

conf_path = sys.argv[1]
config = configparser.ConfigParser()
config.read(conf_path)
opts = config["options"]
opts["db_host"] = os.environ["DB_HOST"]
opts["db_port"] = os.environ["DB_PORT"]
opts["db_user"] = os.environ["DB_USER"]
opts["db_password"] = os.environ["DB_PASSWORD"]
opts["db_name"] = os.environ["ODOO_DB_NAME"]
opts["dbfilter"] = "^%s$" % os.environ["ODOO_DB_NAME"]
opts["admin_passwd"] = os.environ["ODOO_MASTER_PASSWORD"]
opts["http_port"] = os.environ.get("PORT", "8069")
with open(conf_path, "w") as f:
    config.write(f)
PY

# Database đã được khởi tạo chưa?
DB_READY="$(python3 - <<'PY'
import os
import psycopg2
try:
    conn = psycopg2.connect(host=os.environ["DB_HOST"], port=os.environ["DB_PORT"],
                            user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
                            dbname=os.environ["ODOO_DB_NAME"], connect_timeout=20)
    cur = conn.cursor()
    cur.execute("SELECT to_regclass('public.ir_module_module') IS NOT NULL")
    print("yes" if cur.fetchone()[0] else "no")
    conn.close()
except Exception as exc:  # database chưa tồn tại / chưa kết nối được
    print("no")
PY
)"

if [ "$DB_READY" = "no" ]; then
    echo "Database ${ODOO_DB_NAME} is empty: installing ${ODOO_INIT_MODULES:-$DEFAULT_MODULES}" >&2
    odoo -c "$ODOO_RC" -d "$ODOO_DB_NAME" -i "${ODOO_INIT_MODULES:-$DEFAULT_MODULES}" \
        --without-demo=all --stop-after-init
elif [ -n "${ODOO_UPDATE_MODULES:-}" ]; then
    echo "Updating modules: ${ODOO_UPDATE_MODULES}" >&2
    odoo -c "$ODOO_RC" -d "$ODOO_DB_NAME" -u "$ODOO_UPDATE_MODULES" --stop-after-init
fi

exec odoo -c "$ODOO_RC" -d "$ODOO_DB_NAME" "$@"
