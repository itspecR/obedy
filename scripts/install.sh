#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

PACKAGES=(docker.io docker-compose-v2 git curl openssl)

main() {
    local root mode
    root="$(project_root)"
    if [[ $EUID -ne 0 ]]; then
        echo "Запустите через sudo: sudo ./scripts/install.sh [--https [имя-или-IP ...] | --http]" >&2
        exit 1
    fi
    mode="$(choose_mode "${1:-}")"
    [[ $# -gt 0 ]] && shift
    step "1/6" "Устанавливаем пакеты: ${PACKAGES[*]}"
    install_packages
    step "2/6" "Готовим файл .env"
    prepare_env "$root"
    step "3/6" "Собираем и запускаем систему"
    prepare_state_dir
    export APP_RELEASE
    APP_RELEASE="$(release_label "$root")"
    (cd "$root" && docker compose up -d --build --remove-orphans && wait_for_app "$root")
    step "4/6" "Включаем синхронизацию с доменом раз в час и ежедневную очистку журнала и сессий"
    "$root/scripts/directory-sync-timer.sh" install
    "$root/scripts/journal-clean-timer.sh" install
    step "5/6" "Режим работы: ${mode^^}"
    enable_mode "$root" "$mode" "$@"
    step "6/6" "Код для подключения базы на сайте"
    (cd "$root" && docker compose exec -T app python manage.py setup_code)
    echo
    echo "Готово. Откройте ${mode}://$(server_ip)/ — сайт попросит подключить базу SQL Server."
    echo "Введите код выше, данные SQL Server и создайте первого администратора. Новый код: sudo ./scripts/setup-code.sh"
}

choose_mode() {
    case "$1" in
        --https) echo https ;;
        --http) echo http ;;
        "") ask_mode ;;
        *) echo "Неизвестный параметр: $1. Допустимо: --https [имя-или-IP ...] или --http" >&2; exit 1 ;;
    esac
}

ask_mode() {
    local answer
    if [[ ! -t 0 ]]; then
        echo https
        return
    fi
    read -r -p "Включить HTTPS? Самоподписанный сертификат, браузер один раз предупредит. [Y/n]: " answer
    case "$answer" in
        [Nn]* | Н* | н*) echo http ;;
        *) echo https ;;
    esac
}

enable_mode() {
    local root="$1" mode="$2"
    shift 2
    if [[ "$mode" == "https" ]]; then
        "$root/scripts/setup-https.sh" "$@"
    else
        warn_plain_http
    fi
}

warn_plain_http() {
    echo "ВНИМАНИЕ: система работает по HTTP. Пароли и cookie входа передаются по сети открытым текстом."
    echo "Включить HTTPS: sudo ./scripts/setup-https.sh"
}

step() {
    echo
    echo "[$1] $2"
}

install_packages() {
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -q
    apt-get install -y -q "${PACKAGES[@]}"
    systemctl enable --now docker
}

prepare_env() {
    local root="$1" file="$1/.env"
    if [[ -f "$file" ]]; then
        echo "Файл .env уже есть — оставляем его как есть."
        drop_legacy_env "$root"
        return
    fi
    umask 077
    cat > "$file" <<ENV_FILE
DJANGO_SECRET_KEY=$(openssl rand -hex 32)
DJANGO_DEBUG=0
COOKIE_SECURE=0
DJANGO_ALLOWED_HOSTS=$(server_ip),localhost,127.0.0.1
ENV_FILE
    protect_env_file "$root"
    echo "Создан $file (доступен только root)."
}

server_ip() {
    hostname -I | awk '{print $1}'
}

wait_for_app() {
    for _ in $(seq 1 30); do
        if (cd "$1" && docker compose exec -T app python -c "print('ok')" >/dev/null 2>&1); then
            return 0
        fi
        sleep 2
    done
    echo "Контейнер app не запустился. Логи: docker compose logs --tail=50 app" >&2
    return 1
}

main "$@"
