#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

DEFAULT_LOGIN=admin

main() {
    local root
    root="$(project_root)"
    require_root "./scripts/change-password.sh [логин]"
    cd "$root"
    docker compose exec -T app python manage.py reset_password "${1:-$DEFAULT_LOGIN}"
}

main "$@"
