#!/usr/bin/env bash

PULL_TIMEOUT_SECONDS=300
PULL_ATTEMPTS=3
PULL_RETRY_PAUSE_SECONDS=10
BUILD_TIMEOUT_SECONDS=1800

project_root() {
    cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd
}

load_env() {
    local file="$1/.env"
    if [[ ! -f "$file" ]]; then
        echo "Нет файла .env в $1. Создайте его по образцу .env.example." >&2
        exit 1
    fi
    DB_HOST="$(env_value "$file" DB_HOST 127.0.0.1)"
    DB_PORT="$(env_value "$file" DB_PORT 3306)"
    DB_NAME="$(env_value "$file" DB_NAME obedy)"
    DB_USER="$(env_value "$file" DB_USER obedy)"
    DB_PASSWORD="$(env_value "$file" DB_PASSWORD "")"
    BACKUP_DIR="$(env_value "$file" BACKUP_DIR /var/backups/obedy)"
    BACKUP_KEEP="$(env_value "$file" BACKUP_KEEP 40)"
    if [[ ! "$BACKUP_KEEP" =~ ^[0-9]+$ ]]; then
        echo "BACKUP_KEEP в .env должен быть целым числом, сейчас: $BACKUP_KEEP" >&2
        exit 1
    fi
}

protect_env_file() {
    chown root:root "$1/.env"
    chmod 600 "$1/.env"
}

require_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "Запустите через sudo: sudo $1" >&2
        exit 1
    fi
}

env_value() {
    local value
    value="$(grep -E "^$2=" "$1" | tail -n 1 | cut -d= -f2- || true)"
    echo "${value:-$3}"
}

latest_backup() {
    ls -1t "${BACKUP_DIR:-/var/backups/obedy}"/obedy-*.sql.gz 2>/dev/null | head -n 1
}

fail() {
    echo "$1" >&2
    exit 1
}

release_label() {
    local commit
    if commit="$(git -C "$1" rev-parse --short HEAD 2>/dev/null)"; then
        echo "$(git -C "$1" rev-parse --abbrev-ref HEAD) · $commit · $(TZ=Europe/Moscow date '+%d.%m.%Y %H:%M')"
    else
        echo "из архива · $(TZ=Europe/Moscow date '+%d.%m.%Y %H:%M')"
    fi
}

base_images() {
    awk 'toupper($1) == "FROM" { print $2 }' "$1"/deploy/*.Dockerfile | sort -u
}

has_image() {
    docker image inspect "$1" >/dev/null 2>&1
}

pull_image() {
    local attempt
    for attempt in $(seq 1 "$PULL_ATTEMPTS"); do
        if timeout "$PULL_TIMEOUT_SECONDS" docker pull -q "$1" >/dev/null; then
            return 0
        fi
        echo "Docker Hub не отдал $1 (попытка $attempt из $PULL_ATTEMPTS)." >&2
        if [[ $attempt -lt $PULL_ATTEMPTS ]]; then
            sleep "$PULL_RETRY_PAUSE_SECONDS"
        fi
    done
    return 1
}

ensure_base_images() {
    local image
    for image in $(base_images "$1"); do
        if has_image "$image"; then
            echo "Образ $image уже есть на сервере."
        elif pull_image "$image"; then
            echo "Образ $image скачан."
        else
            echo "Не удалось скачать $image: Docker Hub не отвечает. Проверка сети: sudo ./scripts/registry-check.sh" >&2
            return 1
        fi
    done
}

build_images() {
    local status=0
    ensure_base_images "$1" || return 1
    timeout "$BUILD_TIMEOUT_SECONDS" docker compose build || status=$?
    if [[ $status -eq 124 ]]; then
        echo "Сборка не закончилась за $((BUILD_TIMEOUT_SECONDS / 60)) минут и остановлена. Проверка сети: sudo ./scripts/registry-check.sh" >&2
    fi
    return "$status"
}
