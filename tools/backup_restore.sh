#!/usr/bin/env bash
# Backup / restore database Odoo.
#   tools/backup_restore.sh backup  <db>                 -> backups/<db>_<time>.dump (+ filestore nếu có)
#   tools/backup_restore.sh restore <file.dump> <db_moi> -> tạo DB mới từ file dump (không ghi đè DB cũ)
#   Cloud (Neon/Render): pg_dump/pg_restore với chuỗi kết nối:
#     pg_dump  -Fc --no-owner --no-acl "$DATABASE_URL" > backup.dump
#     pg_restore --no-owner --no-acl -d "$DATABASE_URL" backup.dump
set -euo pipefail
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")/.."
mkdir -p backups
case "${1:-}" in
  backup)
    DB="${2:?db}"; TS=$(date +%Y%m%d_%H%M%S)
    docker compose exec -T db pg_dump -U odoo -Fc --no-owner --no-acl "$DB" > "backups/${DB}_${TS}.dump"
    docker compose run --rm -T --entrypoint sh odoo -c "cd /var/lib/odoo/filestore 2>/dev/null && tar czf - $DB 2>/dev/null || true" > "backups/${DB}_${TS}_filestore.tgz"
    ls -la backups/${DB}_${TS}*
    ;;
  restore)
    FILE="${2:?dump file}"; DB="${3:?new db name}"
    if docker compose exec -T db psql -U odoo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB'" | grep -q 1; then
      echo "Database $DB đã tồn tại. Chọn tên khác (không ghi đè dữ liệu)."; exit 2
    fi
    docker compose exec -T db createdb -U odoo "$DB"
    docker compose exec -T db pg_restore -U odoo --no-owner --no-acl -d "$DB" < "$FILE"
    echo "Đã khôi phục vào $DB"
    ;;
  *) echo "Dùng: $0 backup <db> | restore <file.dump> <db_moi>"; exit 1;;
esac
