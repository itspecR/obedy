#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

main() {
    local root answer
    root="$(project_root)"
    require_root "./scripts/reset-database.sh"
    cd "$root"
    echo "Сайт забудет подключение к SQL Server и откроет окно «Подключение базы данных»."
    echo "Данные в SQL Server не удаляются: эту же базу можно подключить снова."
    read -r -p "Продолжить? [y/N] " answer
    [[ "$answer" == [yYдД] ]] || fail "Отменено: подключение не тронуто."
    docker compose run --rm -T --no-deps app python manage.py forget_database
    docker compose restart app >/dev/null
    echo "Откройте сайт и подключите базу этим кодом."
}

main "$@"
