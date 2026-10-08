#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

main() {
    local root file
    root="$(project_root)"
    require_root "./scripts/restore.sh <файл копии>"
    load_env "$root"
    file="${1:-}"
    if [[ -z "$file" ]]; then
        echo "Использование: sudo ./scripts/restore.sh <файл копии> [--yes]"
        echo "Доступные копии (новые сверху):"
        ls -1t "$BACKUP_DIR"/obedy-*.sql.gz 2>/dev/null | head -n 10 || echo "  копий нет"
        exit 1
    fi
    [[ -f "$file" ]] || { echo "Файл не найден: $file" >&2; exit 1; }
    gzip -t "$file" || { echo "Файл повреждён: $file" >&2; exit 1; }
    confirm "${2:-}"
    WORK="$(mktemp)"
    trap 'rm -f "$WORK"' EXIT
    cp "$file" "$WORK"
    echo "[1/4] Сохраняем текущую базу на всякий случай"
    "$root/scripts/backup.sh"
    echo "[2/4] Останавливаем приложение"
    (cd "$root" && docker compose stop app)
    trap 'on_failure "$root"' ERR
    echo "[3/4] Восстанавливаем базу из $file"
    drop_tables
    gunzip -c "$WORK" | db
    trap - ERR
    echo "[4/4] Запускаем приложение и применяем миграции"
    (cd "$root" && docker compose start app && docker compose exec -T app python manage.py migrate --noinput)
    echo "Готово: база восстановлена из $(basename "$file")."
}

db() {
    MYSQL_PWD="$DB_PASSWORD" mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" "$DB_NAME" "$@"
}

drop_tables() {
    local tables
    tables="$(db -N -e "SET SESSION group_concat_max_len = 1000000; SELECT GROUP_CONCAT(CONCAT('\`', table_name, '\`')) FROM information_schema.tables WHERE table_schema = DATABASE()")"
    if [[ -n "$tables" && "$tables" != "NULL" ]]; then
        db -e "SET FOREIGN_KEY_CHECKS = 0; DROP TABLE $tables; SET FOREIGN_KEY_CHECKS = 1;"
    fi
}

on_failure() {
    echo "Ошибка восстановления. Запускаем приложение обратно; копия текущей базы сделана на шаге 1." >&2
    (cd "$1" && docker compose start app) || true
}

confirm() {
    if [[ "$1" == "--yes" ]]; then
        return
    fi
    echo "Текущие данные системы будут заменены данными из копии."
    read -r -p "Чтобы продолжить, введите ВОССТАНОВИТЬ: " answer
    [[ "$answer" == "ВОССТАНОВИТЬ" ]] || { echo "Отменено."; exit 1; }
}

main "$@"
