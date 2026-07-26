#!/bin/bash
set -e

if [ -n "${DATABASE_URL:-}" ]; then
    eval "$(
        python3 - <<'PY'
import os
import shlex
from urllib.parse import unquote, urlparse

parsed = urlparse(os.environ["DATABASE_URL"])
values = {
    "HOST": parsed.hostname or "",
    "PORT": str(parsed.port or 5432),
    "USER": unquote(parsed.username or ""),
    "PASSWORD": unquote(parsed.password or ""),
}

db_name = (parsed.path or "").lstrip("/")
if db_name and not os.environ.get("ODOO_DB_NAME"):
    values["ODOO_DB_NAME"] = unquote(db_name)

for key, value in values.items():
    if value:
        print(f"export {key}={shlex.quote(value)}")
PY
    )"
fi

if [ -n "${ODOO_MASTER_PASSWORD:-}" ]; then
    python3 - "$ODOO_RC" "$ODOO_MASTER_PASSWORD" <<'PY'
import configparser
import sys

conf_path, password = sys.argv[1], sys.argv[2]
config = configparser.ConfigParser()
config.read(conf_path)
config["options"]["admin_passwd"] = password
with open(conf_path, "w") as f:
    config.write(f)
PY
fi

if [ -n "${ODOO_DB_NAME:-}" ]; then
    python3 - <<'PY'
# Render's free web service has no persistent disk, so /var/lib/odoo (filestore)
# is wiped on every restart while ir_attachment rows in Postgres survive.
# Stale rows pointing at compiled JS/CSS bundles then 500 on load; delete them
# so Odoo recompiles fresh bundles against the current filestore.
import os
import psycopg2

try:
    conn = psycopg2.connect(
        host=os.environ.get("HOST"),
        port=os.environ.get("PORT", "5432"),
        user=os.environ.get("USER"),
        password=os.environ.get("PASSWORD"),
        dbname=os.environ.get("ODOO_DB_NAME"),
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM ir_attachment WHERE res_model = 'ir.ui.view' AND name ILIKE %s",
            ('%assets%',),
        )
    conn.close()
except Exception:
    pass
PY
fi

if [ "${ODOO_AUTO_INIT:-true}" = "true" ] && [ -n "${ODOO_DB_NAME:-}" ]; then
    install_modules="${ODOO_INSTALL_MODULES:-base}"
    exec /entrypoint.sh odoo -d "$ODOO_DB_NAME" -i "$install_modules" --without-demo=all
fi

exec /entrypoint.sh "$@"
