#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

CONFIRM_WORD="СБРОС"

main() {
    local root answer
    root="$(project_root)"
    require_root "./scripts/reset-stats.sh"
    cd "$root"
    echo "Будут удалены ВСЕ обеды за всё время: статистика и табло начнутся с нуля."
    echo "Сотрудники, роли, правила, настройки и журнал действий останутся."
    read -r -p "Чтобы продолжить, напечатайте ${CONFIRM_WORD}: " answer
    [[ "$answer" == "$CONFIRM_WORD" ]] || fail "Отменено: обеды не тронуты."
    echo "Делаем резервную копию базы перед удалением…"
    "$root/scripts/backup.sh"
    docker compose exec -T app python manage.py reset_lunches --yes
    echo "Готово. Вернуть всё как было: sudo ./scripts/restore.sh (последняя копия сделана только что)."
}

main "$@"
