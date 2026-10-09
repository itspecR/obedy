#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

main() {
    local root file
    root="$(project_root)"
    require_root "./scripts/backup.sh"
    load_env "$root"
    mkdir -p "$BACKUP_DIR"
    chmod 700 "$BACKUP_DIR"
    file="$BACKUP_DIR/obedy-$(TZ=Europe/Moscow date +%Y%m%d-%H%M%S).sql.gz"
    trap 'on_failure "$file"' ERR
    dump > "$file.part"
    gzip -t "$file.part"
    mv "$file.part" "$file"
    chmod 600 "$file"
    trap - ERR
    prune
    mark_backup "$root" "$file"
    echo "Готово: $file"
}

mark_backup() {
    (cd "$1" && docker compose exec -T app python manage.py mark_backup "$(basename "$2")" >/dev/null 2>&1) || true
}

dump() {
    set -o pipefail
    MYSQL_PWD="$DB_PASSWORD" mysqldump \
        --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" \
        --single-transaction --default-character-set=utf8mb4 \
        "$DB_NAME" | gzip -9
}

prune() {
    ls -1t "$BACKUP_DIR"/obedy-*.sql.gz 2>/dev/null | tail -n +"$((BACKUP_KEEP + 1))" | xargs -r rm -f --
}

on_failure() {
    rm -f "$1.part"
    echo "Ошибка: копия не создана." >&2
}

main "$@"
