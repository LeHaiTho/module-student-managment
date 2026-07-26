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

if [ "${ODOO_AUTO_INIT:-true}" = "true" ] && [ -n "${ODOO_DB_NAME:-}" ]; then
    install_modules="${ODOO_INSTALL_MODULES:-base}"
    odoo_args=(odoo -d "$ODOO_DB_NAME" -i "$install_modules" --without-demo=all)

    if [ -n "${ODOO_MASTER_PASSWORD:-}" ]; then
        odoo_args+=(--admin-passwd "$ODOO_MASTER_PASSWORD")
    fi

    exec /entrypoint.sh "${odoo_args[@]}"
fi

exec /entrypoint.sh "$@"
