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

if [ "${ODOO_AUTO_INIT:-true}" = "true" ] && [ -n "${ODOO_DB_NAME:-}" ]; then
    install_modules="${ODOO_INSTALL_MODULES:-base}"
    exec /entrypoint.sh odoo -d "$ODOO_DB_NAME" -i "$install_modules" --without-demo=all
fi

exec /entrypoint.sh "$@"
