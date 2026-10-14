#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
source "$(dirname "${BASH_SOURCE[0]}")/certs.sh"

PFX_MIN_LENGTH=8

usage() {
    cat >&2 <<'EOF'
Свой центр сертификации для сайта и контроллеров домена:
  sudo ./scripts/ca.sh init <домен>              создать центр, например: init company.local
  sudo ./scripts/ca.sh root                      показать корневой сертификат (для GPO и раздела «Домен»)
  sudo ./scripts/ca.sh dc <полное имя контроллера>  выпустить сертификат LDAPS, например: dc srv-ad16.company.local
EOF
    exit 1
}

main() {
    require_root "./scripts/ca.sh ${1:-}"
    umask 077
    case "${1:-}:$#" in
        init:2) init_ca "$2" ;;
        root:1) show_root ;;
        dc:2) issue_dc "$2" ;;
        *) usage ;;
    esac
}

require_ca() {
    ca_exists || fail "Центр сертификации ещё не создан. Сначала: sudo ./scripts/ca.sh init <домен>"
}

init_ca() {
    local domain="${1,,}"
    valid_domain "$domain" || fail "Неверное имя домена: $1. Пример: company.local"
    if ca_exists; then
        fail "Центр сертификации уже создан для $(ca_domain). Пересоздавать нельзя: разосланный корневой сертификат перестанет подходить"
    fi
    create_ca "$domain"
    echo "Центр сертификации создан для $domain и всех имён внутри него. Ключ: $CA_KEY (доступ только у root)."
    show_root
}

show_root() {
    require_ca
    echo
    echo "Корневой сертификат ($CA_CERT), срок до $(openssl x509 -in "$CA_CERT" -noout -enddate | cut -d= -f2):"
    echo
    cat "$CA_CERT"
    echo
    echo "1. Сохраните текст выше в файл obedy-root.cer и импортируйте его через групповую политику:"
    echo "   Конфигурация компьютера → Политики → Конфигурация Windows → Параметры безопасности →"
    echo "   Политики открытого ключа → Доверенные корневые центры сертификации."
    echo "2. Вставьте тот же текст в поле «Корневой сертификат» в разделе «Домен» на сайте."
}

read_pfx_password() {
    local first second
    while true; do
        read -r -s -p "Пароль на файл .pfx (не короче $PFX_MIN_LENGTH символов): " first; echo >&2
        read -r -s -p "Повторите пароль: " second; echo >&2
        if [[ "$first" != "$second" ]]; then echo "Пароли не совпадают" >&2; continue; fi
        if (( ${#first} < PFX_MIN_LENGTH )); then echo "Слишком короткий пароль" >&2; continue; fi
        printf '%s' "$first"
        return
    done
}

issue_dc() {
    local name="${1,,}" domain base password
    require_ca
    domain="$(ca_domain)"
    if ! valid_domain "$name" || [[ "$name" == "$domain" ]] || ! in_domain "$name" "$domain"; then
        fail "Укажите полное имя контроллера в домене $domain, например: srv-ad16.$domain"
    fi
    base="$ISSUED_DIR/$name"
    issue_cert "$name" "DNS:$name,DNS:$domain" "$base.key" "$base.pem"
    password="$(read_pfx_password)"
    printf '%s' "$password" | openssl pkcs12 -export -inkey "$base.key" -in "$base.pem" -certfile "$CA_CERT" \
        -name "$name" -certpbe PBE-SHA1-3DES -keypbe PBE-SHA1-3DES -macalg sha1 -passout stdin -out "$base.pfx" \
        || fail "Не удалось собрать файл .pfx"
    rm -f "$base.key"
    echo
    echo "Готово: $base.pfx (срок $LEAF_DAYS дней)."
    echo "Перенесите файл на $name и выполните там в PowerShell от администратора:"
    echo "  Import-PfxCertificate -FilePath C:\\$name.pfx -CertStoreLocation Cert:\\LocalMachine\\My -Password (Read-Host -AsSecureString)"
    echo "Подробно, включая применение без перезагрузки, — README, раздел «Свой центр сертификации»."
}

main "$@"
