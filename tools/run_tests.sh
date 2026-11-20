#!/usr/bin/env bash
# Chạy automated test Odoo trong Docker trên một database test riêng.
# Cách dùng: tools/run_tests.sh <db_name> <module1,module2,...> [test_tags]
#   - Tạo mới DB (xóa DB test cũ cùng tên), cài các module, chạy test có tag.
#   - Log lưu tại test-results/<db_name>.log
# KHÔNG dùng tên DB univ_sms_db (DB dữ liệu thật).
set -euo pipefail
export MSYS_NO_PATHCONV=1
DB="${1:?db name}"; MODS="${2:?modules}"; TAGS="${3:-univ_sms}"
if [ "$DB" = "univ_sms_db" ]; then echo "Refusing to use univ_sms_db"; exit 2; fi
cd "$(dirname "$0")/.."
mkdir -p test-results
docker compose up -d db >/dev/null
for i in $(seq 1 30); do docker compose exec -T db pg_isready -U odoo >/dev/null 2>&1 && break; sleep 1; done
docker compose exec -T db psql -U odoo -d postgres -q -c "DROP DATABASE IF EXISTS \"$DB\"" >/dev/null
LOG="test-results/$DB.log"
set +e
docker compose run --rm -T odoo odoo -c /etc/odoo/odoo.conf -d "$DB" -i "$MODS" \
  --without-demo=all --test-enable --test-tags "$TAGS" --stop-after-init \
  --log-level=test --http-port=8169 > "$LOG" 2>&1
RC=$?
set -e
echo "exit=$RC log=$LOG"
grep -E "Ran [0-9]+ tests|FAIL|ERROR|failed|errors" "$LOG" | grep -v "fa class" | tail -40 || true
grep -E "tests? (passed|failed)|[0-9]+ failed, [0-9]+ error" "$LOG" | tail -3 || true
exit $RC
