#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

main() {
    local root
    root="$(project_root)"
    require_root "./scripts/setup-code.sh"
    cd "$root"
    docker compose exec -T app python manage.py setup_code
    echo "Введите этот код на сайте, в окне «Подключение базы данных». Код действует, пока база не подключена."
}

main "$@"
