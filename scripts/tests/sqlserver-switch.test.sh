#!/usr/bin/env bash
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"

failures=0

expect() {
    if [[ "$2" == "$3" ]]; then
        echo "ок   $1"
    else
        echo "FAIL $1: ждали «$3», получили «$2»"
        failures=$((failures + 1))
    fi
}

test_legacy_database_settings_leave_env() {
    local root
    root="$(mktemp -d)"
    printf 'DJANGO_SECRET_KEY=k\nDB_HOST=127.0.0.1\nDB_PASSWORD=p\nBACKUP_KEEP=40\nBACKUP_DIR=/var/backups/obedy\nCOOKIE_SECURE=0\n' > "$root/.env"
    drop_legacy_env "$root" >/dev/null
    expect "в .env остаются только настройки сайта" "$(tr '\n' ' ' < "$root/.env")" "DJANGO_SECRET_KEY=k COOKIE_SECURE=0 "
    expect "прежний .env сохранён" "$(grep -c '^DB_' "$root/.env.before-sqlserver")" 2
    drop_legacy_env "$root" >/dev/null
    expect "повторный запуск ничего не меняет" "$(grep -c '^DB_' "$root/.env.before-sqlserver")" 2
}

test_mariadb_is_removed_only_after_sql_server_works() {
    removed=0
    mariadb_installed() { return 0; }
    remove_mariadb() { removed=$((removed + 1)); }
    retire_mariadb '{"status": "setup", "database": "not_configured"}' >/dev/null
    expect "пока база не подключена, MariaDB остаётся" "$removed" 0
    retire_mariadb '{"status": "error", "database": "unavailable"}' >/dev/null
    expect "если SQL Server недоступен, MariaDB остаётся" "$removed" 0
    retire_mariadb '{"status": "ok", "database": "ok"}' >/dev/null
    expect "после подключения SQL Server MariaDB удаляется" "$removed" 1
}

test_nothing_to_remove_without_mariadb() {
    removed=0
    mariadb_installed() { return 1; }
    remove_mariadb() { removed=$((removed + 1)); }
    retire_mariadb '{"status": "ok", "database": "ok"}' >/dev/null
    expect "без MariaDB удалять нечего" "$removed" 0
}

for test in $(declare -F | awk '$3 ~ /^test_/ { print $3 }'); do
    "$test"
done
exit "$((failures > 0))"
