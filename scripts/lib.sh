#!/usr/bin/env bash

project_root() {
    cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd
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

STATE_DIR=/var/lib/obedy
APP_UID=10001

prepare_state_dir() {
    install -d -o "$APP_UID" -g "$APP_UID" -m 700 "$STATE_DIR"
}

LEGACY_ENV_KEYS='^(DB_[A-Z_]+|BACKUP_DIR|BACKUP_KEEP)='
MARIADB_PACKAGES=(mariadb-server mariadb-client mariadb-common)
MARIADB_DATA=(/var/lib/mysql /etc/mysql)

drop_legacy_env() {
    local file="$1/.env"
    grep -Eq "$LEGACY_ENV_KEYS" "$file" || return 0
    cp -p "$file" "$file.before-sqlserver"
    grep -Ev "$LEGACY_ENV_KEYS" "$file.before-sqlserver" > "$file"
    protect_env_file "$1"
    echo "Из .env убраны настройки MariaDB и копий (прежний файл: .env.before-sqlserver)."
}

mariadb_installed() {
    dpkg -s mariadb-server >/dev/null 2>&1
}

database_connected() {
    grep -Eq '"database": *"ok"' <<<"$1"
}

remove_mariadb() {
    systemctl disable --now mariadb 2>/dev/null || true
    DEBIAN_FRONTEND=noninteractive apt-get purge -y -q "${MARIADB_PACKAGES[@]}"
    DEBIAN_FRONTEND=noninteractive apt-get autoremove -y -q
    rm -rf "${MARIADB_DATA[@]}"
    echo "MariaDB удалена вместе с данными."
}

retire_mariadb() {
    if ! mariadb_installed; then
        echo "MariaDB не установлена — пропускаем."
    elif database_connected "$1"; then
        remove_mariadb
    else
        echo "MariaDB пока оставлена: подключите базу SQL Server на сайте, она удалится при следующем обновлении."
    fi
}
