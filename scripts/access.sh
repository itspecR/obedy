#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

usage() {
    echo "Использование:"
    echo "  sudo ./scripts/access.sh show                     показать, с каких адресов открыт сайт"
    echo "  sudo ./scripts/access.sh add <адрес> [пометка]    разрешить адрес или подсеть (192.168.1.10, 192.168.1.0/24)"
    echo "  sudo ./scripts/access.sh remove <адрес>           убрать адрес из списка"
    echo "  sudo ./scripts/access.sh lan on|off               открыть или закрыть всю локальную сеть"
    echo "Изменения вступают в силу в течение 5 секунд."
}

main() {
    local root
    root="$(project_root)"
    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi
    require_root "./scripts/access.sh $*"
    cd "$root"
    docker compose exec -T app python manage.py access "$@"
}

main "$@"
