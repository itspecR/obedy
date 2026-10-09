#!/usr/bin/env bash
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"

ROOT="$(project_root)"
BASE_IMAGES="nginx:1.30.5 node:24.21.0 python:3.12.15"
failures=0

setup() {
    sandbox="$(mktemp -d)"
    mkdir "$sandbox/bin"
    cp "$ROOT/scripts/tests/fake-docker" "$sandbox/bin/docker"
    export PATH="$sandbox/bin:$PATH" FAKE_LOG="$sandbox/calls" FAKE_LOCAL="" FAKE_PULL=ok FAKE_BUILD=ok
    touch "$FAKE_LOG"
    PULL_TIMEOUT_SECONDS=1
    PULL_ATTEMPTS=2
    PULL_RETRY_PAUSE_SECONDS=0
    BUILD_TIMEOUT_SECONDS=1
}

expect() {
    if [[ "$2" == "$3" ]]; then
        echo "ок   $1"
    else
        echo "FAIL $1: ждали «$3», получили «$2»"
        failures=$((failures + 1))
    fi
}

calls() {
    grep -c "^$1" "$FAKE_LOG"
}

test_reads_base_images_from_dockerfiles() {
    expect "базовые образы берутся из Dockerfile" "$(base_images "$ROOT" | xargs)" "$BASE_IMAGES"
}

test_skips_images_already_on_server() {
    FAKE_LOCAL="$BASE_IMAGES"
    ensure_base_images "$ROOT" >/dev/null
    expect "скачанные образы не тянутся из сети" "$(calls pull)" 0
}

test_pulls_missing_images() {
    FAKE_LOCAL="node:24.21.0"
    ensure_base_images "$ROOT" >/dev/null
    expect "недостающие образы скачиваются" "$(grep '^pull' "$FAKE_LOG" | xargs)" "pull -q nginx:1.30.5 pull -q python:3.12.15"
}

test_hanging_pull_stops_after_attempts() {
    local status=0 message
    FAKE_PULL=hang
    message="$(ensure_base_images "$ROOT" 2>&1)" || status=$?
    expect "зависшее скачивание прерывается с ошибкой" "$status" 1
    expect "попыток столько, сколько задано" "$(calls pull)" "$PULL_ATTEMPTS"
    expect "подсказка про проверку сети" "$(grep -c registry-check.sh <<<"$message")" 1
}

test_hanging_build_stops_with_message() {
    local status=0 message
    FAKE_LOCAL="$BASE_IMAGES"
    FAKE_BUILD=hang
    message="$(build_images "$ROOT" 2>&1)" || status=$?
    expect "зависшая сборка прерывается по времени" "$status" 124
    expect "сообщение о зависшей сборке" "$(grep -c "Сборка не закончилась" <<<"$message")" 1
}

test_build_runs_after_base_images() {
    FAKE_LOCAL="$BASE_IMAGES"
    build_images "$ROOT" >/dev/null
    expect "сборка запускается" "$(calls "compose build")" 1
}

for test in $(declare -F | awk '$3 ~ /^test_/ { print $3 }'); do
    setup
    "$test"
    rm -rf "$sandbox"
done
exit "$((failures > 0))"
