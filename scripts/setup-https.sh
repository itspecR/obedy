#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
source "$(dirname "${BASH_SOURCE[0]}")/certs.sh"

TLS_DIR=/etc/obedy/tls

main() {
    local root
    root="$(project_root)"
    if [[ $EUID -ne 0 ]]; then
        echo "Запустите через sudo: sudo ./scripts/setup-https.sh [имя-или-IP ...]" >&2
        exit 1
    fi
    require_env_file "$root"
    prepare_tls_dir
    if ca_exists; then make_ca_cert "$@"; else make_self_signed_cert "$@"; fi
    set_env_flag "$root/.env" COOKIE_SECURE 1
    allow_hosts "$root/.env" "$@"
    step "Перезапускаем"
    (cd "$root" && docker compose up -d --force-recreate app web)
    wait_for_https
    echo
    if ca_exists; then report_ca_cert "$1"; else report_self_signed_cert; fi
    echo "Обновить сертификат позже: снова запустите этот скрипт."
}

report_self_signed_cert() {
    echo "Готово. HTTPS включён. Откройте https://$(server_ip)/"
    echo "Самоподписанный сертификат: браузер один раз предупредит — примите его (Дополнительно → Перейти)."
}

report_ca_cert() {
    echo "Готово. HTTPS включён. Откройте https://${1,,}/"
    echo "Сертификат выпущен вашим центром сертификации: на компьютерах, получивших корневой сертификат"
    echo "через групповую политику, браузер не будет предупреждать. Срок — $LEAF_DAYS дней."
}

step() { echo; echo "== $1"; }

require_env_file() {
    [[ -f "$1/.env" ]] || { echo "Нет файла .env. Сначала установите систему." >&2; exit 1; }
}

server_ip() { hostname -I | awk '{print $1}'; }

prepare_tls_dir() {
    mkdir -p "$TLS_DIR"
    chmod 700 "$TLS_DIR"
}

make_ca_cert() {
    local domain san="" name ip
    domain="$(ca_domain)"
    [[ $# -gt 0 ]] || fail "Укажите имя сайта в домене $domain, например: sudo ./scripts/setup-https.sh obedy.$domain"
    step "Выпускаем сертификат сайта от центра сертификации $domain"
    for name in "$@"; do
        name="${name,,}"
        if is_private_ipv4 "$name"; then san+=",IP:$name"; continue; fi
        if ! valid_domain "$name" || ! in_domain "$name" "$domain"; then
            fail "Имя $name не входит в домен $domain — такой сертификат браузеры не примут"
        fi
        san+=",DNS:$name"
    done
    for ip in $(private_ipv4_addresses); do san+=",IP:$ip"; done
    san="${san#,}"
    issue_cert "${1,,}" "$san" "$TLS_DIR/privkey.pem" "$TLS_DIR/fullchain.pem"
    chmod 644 "$TLS_DIR/fullchain.pem"
    echo "Адреса в сертификате: $san"
}

make_self_signed_cert() {
    step "Создаём самоподписанный сертификат в $TLS_DIR"
    local san="DNS:localhost,IP:127.0.0.1" name host
    host="$(hostname)"
    [[ -n "$host" ]] && san="$san,DNS:$host"
    for ip in $(hostname -I); do san="$san,IP:$ip"; done
    for name in "$@"; do
        if [[ "$name" =~ ^[0-9.]+$ ]]; then san="$san,IP:$name"; else san="$san,DNS:$name"; fi
    done
    openssl req -x509 -utf8 -newkey rsa:2048 -nodes \
        -keyout "$TLS_DIR/privkey.pem" -out "$TLS_DIR/fullchain.pem" \
        -days "$LEAF_DAYS" -subj "/CN=Обеды" \
        -addext "subjectAltName=$san" \
        -addext "keyUsage=digitalSignature,keyEncipherment" \
        -addext "extendedKeyUsage=serverAuth" 2>/dev/null
    chmod 600 "$TLS_DIR/privkey.pem"
    chmod 644 "$TLS_DIR/fullchain.pem"
    echo "Адреса в сертификате: $san"
}

set_env_flag() {
    local file="$1" key="$2" value="$3"
    if grep -qE "^$key=" "$file"; then
        sed -i "s|^$key=.*|$key=$value|" "$file"
    else
        printf '%s=%s\n' "$key" "$value" >> "$file"
    fi
    echo "$key=$value в .env"
}

allow_hosts() {
    local file="$1" hosts name
    shift
    hosts="$(env_value "$file" DJANGO_ALLOWED_HOSTS "localhost,127.0.0.1")"
    for name in "${@,,}"; do
        [[ ",$hosts," == *",$name,"* ]] || hosts="$hosts,$name"
    done
    set_env_flag "$file" DJANGO_ALLOWED_HOSTS "$hosts"
}

wait_for_https() {
    step "Проверяем HTTPS"
    for _ in $(seq 1 30); do
        if curl -fsSk https://127.0.0.1/api/health >/dev/null 2>&1; then
            curl -fsSk https://127.0.0.1/api/health; echo; return 0
        fi
        sleep 2
    done
    echo "HTTPS не ответил за 60 секунд. Логи: docker compose logs --tail=50 web" >&2
    return 1
}

main "$@"
