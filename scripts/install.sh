#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

PACKAGES=(docker.io docker-compose-v2 mariadb-server mariadb-client git curl openssl)

main() {
    local root mode
    root="$(project_root)"
    if [[ $EUID -ne 0 ]]; then
        echo "Запустите через sudo: sudo ./scripts/install.sh [--https [имя-или-IP ...] | --http]" >&2
        exit 1
    fi
    mode="$(choose_mode "${1:-}")"
    [[ $# -gt 0 ]] && shift
    step "1/7" "Устанавливаем пакеты: ${PACKAGES[*]}"
    install_packages
    step "2/7" "Готовим базу данных и файл .env"
    prepare_env "$root"
    step "3/7" "Собираем и запускаем систему"
    prepare_state_dir
    export APP_RELEASE
    APP_RELEASE="$(release_label "$root")"
    (cd "$root" && docker compose up -d --build --remove-orphans && wait_for_app "$root" && docker compose exec -T app python manage.py migrate --noinput)
    step "4/7" "Создаём локального администратора"
    (cd "$root" && docker compose exec -T app python manage.py create_admin || true)
    step "5/7" "Включаем ежедневную резервную копию"
    "$root/scripts/backup-timer.sh" install
    step "6/7" "Включаем синхронизацию с доменом раз в час и ежедневную очистку журнала"
    "$root/scripts/directory-sync-timer.sh" install
    "$root/scripts/journal-clean-timer.sh" install
    step "7/7" "Режим работы: ${mode^^}"
    enable_mode "$root" "$mode" "$@"
    echo
    echo "Готово. Откройте ${mode}://$(server_ip)/ и войдите логином и временным паролем администратора выше."
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
    systemctl enable --now docker mariadb
}

prepare_env() {
    local root="$1" file="$1/.env" password
    if [[ -f "$file" ]]; then
        echo "Файл .env уже есть — оставляем его как есть."
        return
    fi
    password="$(openssl rand -hex 24)"
    mariadb -e "CREATE DATABASE IF NOT EXISTS obedy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    for host in localhost 127.0.0.1; do
        mariadb <<SQL
CREATE USER IF NOT EXISTS 'obedy'@'${host}' IDENTIFIED BY '${password}';
ALTER USER 'obedy'@'${host}' IDENTIFIED BY '${password}';
GRANT ALL PRIVILEGES ON obedy.* TO 'obedy'@'${host}';
SQL
    done
    mariadb -e "FLUSH PRIVILEGES;"
    umask 077
    cat > "$file" <<ENV_FILE
DJANGO_SECRET_KEY=$(openssl rand -hex 32)
DJANGO_DEBUG=0
COOKIE_SECURE=0
DJANGO_ALLOWED_HOSTS=$(server_ip),localhost,127.0.0.1
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=obedy
DB_USER=obedy
DB_PASSWORD=${password}
BACKUP_DIR=/var/backups/obedy
BACKUP_KEEP=40
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
