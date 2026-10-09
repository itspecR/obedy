#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

main() {
    local branch="${1:-main}"
    local root previous status
    root="$(project_root)"
    cd "$root"

    require_root "./scripts/deploy.sh ${branch}"
    require_env_file
    protect_env_file "$root"
    drop_legacy_env "$root"
    if [[ -d .git ]]; then
        previous="${DEPLOY_PREVIOUS_COMMIT:-$(git rev-parse HEAD)}"
        if [[ -z "${DEPLOY_PREVIOUS_COMMIT:-}" ]]; then
            step "1/7" "Получаем ветку ${branch}"
            sync_branch "$branch"
            continue_with_fetched_script "$root" "$previous" "$branch"
        fi
        trap 'roll_back "$previous"' ERR
    else
        step "1/7" "Установка из архива: берём файлы из $root как есть"
        trap 'archive_failed' ERR
    fi
    step "2/7" "Собираем контейнеры"
    prepare_state_dir
    export APP_RELEASE
    APP_RELEASE="$(release_label "$root")"
    docker compose build
    step "3/7" "Применяем миграции базы (если база подключена)"
    docker compose run --rm --no-deps app python manage.py prepare_database
    step "4/7" "Запускаем новую версию"
    docker compose up -d --remove-orphans
    step "5/7" "Проверяем, что сайт отвечает"
    status="$(wait_for_health)"
    echo "$status"
    trap - ERR
    step "6/7" "Включаем синхронизацию с доменом раз в час и ежедневную очистку журнала и сессий"
    enable_directory_sync "$root"
    enable_journal_clean "$root"
    disable_old_backups
    step "7/7" "Убираем MariaDB: база теперь на SQL Server"
    retire_mariadb "$status"
    echo "Готово: новая версия развёрнута. Обновите страницу в браузере."
}

step() {
    echo
    echo "[$1] $2"
}

require_env_file() {
    if [[ ! -f .env ]]; then
        echo "Нет файла .env. Создайте его по образцу .env.example." >&2
        exit 1
    fi
}

sync_branch() {
    git fetch origin "$1"
    git checkout -B "$1" "origin/$1"
    git reset --hard "origin/$1"
}

continue_with_fetched_script() {
    export DEPLOY_PREVIOUS_COMMIT="$2"
    exec bash "$1/scripts/deploy.sh" "$3"
}

enable_directory_sync() {
    "$1/scripts/directory-sync-timer.sh" install \
        || echo "Не удалось включить таймер синхронизации. Повторите: sudo ./scripts/directory-sync-timer.sh install" >&2
}

disable_old_backups() {
    [[ -f /etc/systemd/system/obedy-backup.timer ]] || return 0
    systemctl disable --now obedy-backup.timer 2>/dev/null || true
    rm -f /etc/systemd/system/obedy-backup.service /etc/systemd/system/obedy-backup.timer
    systemctl daemon-reload
    echo "Старый таймер копий через mysqldump отключён: копии теперь делает SQL Server."
}

enable_journal_clean() {
    "$1/scripts/journal-clean-timer.sh" install \
        || echo "Не удалось включить очистку журнала. Повторите: sudo ./scripts/journal-clean-timer.sh install" >&2
}

health() {
    curl -fsSLk --max-redirs 1 http://127.0.0.1/api/health
}

wait_for_health() {
    local body
    for _ in $(seq 1 30); do
        if body="$(health 2>/dev/null)"; then
            echo "$body"; return 0
        fi
        sleep 2
    done
    echo "Сайт не ответил за 60 секунд. Логи: docker compose logs --tail=50" >&2
    return 1
}

roll_back() {
    trap - ERR
    echo >&2
    echo "Ошибка развёртывания. Возвращаем прошлую версию кода ($(git rev-parse --short "$1"))." >&2
    git reset --hard "$1"
    docker compose up -d --build --remove-orphans || true
    echo "Прошлая версия запущена. Если миграции успели примениться и сайт работает с ошибками," >&2
    echo "восстановите базу из последней копии на SQL Server." >&2
    exit 1
}

archive_failed() {
    trap - ERR
    echo >&2
    echo "Ошибка развёртывания. Верните прошлую папку системы (из которой скопирован .env) и запустите deploy.sh в ней." >&2
    echo "Если миграции успели примениться, восстановите базу из последней копии на SQL Server." >&2
    exit 1
}

main "$@"; exit
