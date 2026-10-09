#!/usr/bin/env bash
set -Euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

REGISTRY_HOST=registry-1.docker.io
CHECK_TIMEOUT_SECONDS=15

main() {
    local root image
    root="$(project_root)"
    require_root "./scripts/registry-check.sh"
    show "Версия Docker" docker version --format '{{.Server.Version}}'
    show "Хранилище образов" docker info --format '{{.Driver}}'
    show "Прокси Docker" docker info --format '{{if .HTTPSProxy}}{{.HTTPSProxy}}{{else}}не задан{{end}}'
    check "Имя ${REGISTRY_HOST} находится в DNS" getent hosts "$REGISTRY_HOST"
    check "Docker Hub отвечает по IPv4" reach -4
    check "Docker Hub отвечает по IPv6 (без IPv6 в сети это нормально)" reach -6
    for image in $(base_images "$root"); do
        check "Docker Hub отдаёт образ $image" timeout "$PULL_TIMEOUT_SECONDS" docker pull -q "$image"
    done
}

reach() {
    curl "$1" -sS -o /dev/null --max-time "$CHECK_TIMEOUT_SECONDS" "https://${REGISTRY_HOST}/v2/"
}

show() {
    local label="$1"
    shift
    echo "  ${label}: $("$@" 2>/dev/null || echo 'нет данных')"
}

check() {
    local label="$1"
    shift
    if "$@" >/dev/null 2>&1; then
        echo "  ок   ${label}"
    else
        echo "  НЕТ  ${label}"
    fi
}

main "$@"
