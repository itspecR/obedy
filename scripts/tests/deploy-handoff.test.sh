#!/usr/bin/env bash
set -uo pipefail

failures=0
scripts="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

expect() {
    if [[ "$2" == "$3" ]]; then
        echo "ок   $1"
    else
        echo "FAIL $1: ждали «$3», получили «$2»"
        failures=$((failures + 1))
    fi
}

commit_all() {
    git -C "$1" add -A
    git -C "$1" -c user.name=test -c user.email=test@example.invalid commit -qm "$2"
}

site_with_origin() {
    local work="$1"
    git init -q --bare "$work/origin.git"
    git clone -q "$work/origin.git" "$work/site" 2>/dev/null
    cp -r "$scripts" "$work/site/scripts"
    echo "DJANGO_SECRET_KEY=k" > "$work/site/.env"
    printf '.env\n' > "$work/site/.gitignore"
    git -C "$work/site" checkout -qb release-test
    commit_all "$work/site" "old"
    git -C "$work/site" push -q origin release-test 2>/dev/null
}

publish_new_deploy() {
    local work="$1"
    git clone -q -b release-test "$work/origin.git" "$work/next" 2>/dev/null
    printf '#!/usr/bin/env bash\necho "новый deploy.sh $1 ${DEPLOY_PREVIOUS_COMMIT}"\n' > "$work/next/scripts/deploy.sh"
    commit_all "$work/next" "new"
    git -C "$work/next" push -q origin release-test 2>/dev/null
}

test_fetched_deploy_script_finishes_the_update() {
    local work old output
    work="$(mktemp -d)"
    site_with_origin "$work"
    old="$(git -C "$work/site" rev-parse HEAD)"
    publish_new_deploy "$work"

    output="$("$work/site/scripts/deploy.sh" release-test 2>&1 | tail -n 1)"

    expect "после получения ветки работает уже новый deploy.sh и знает прежнюю версию" "$output" "новый deploy.sh release-test $old"
    rm -rf "$work"
}

test_continued_run_does_not_fetch_again_and_rolls_back_to_the_first_version() {
    local work old output
    work="$(mktemp -d)"
    site_with_origin "$work"
    old="$(git -C "$work/site" rev-parse HEAD)"
    echo "next" > "$work/site/marker"
    commit_all "$work/site" "next"
    rm -rf "$work/origin.git"
    mkdir "$work/bin"
    printf '#!/usr/bin/env bash\n[[ "$*" == "compose build" ]] && exit 1\nexit 0\n' > "$work/bin/docker"
    chmod +x "$work/bin/docker"

    output="$(PATH="$work/bin:$PATH" DEPLOY_PREVIOUS_COMMIT="$old" "$work/site/scripts/deploy.sh" release-test 2>&1)"

    expect "повторно ветка не скачивается" "$(grep -c 'Получаем ветку' <<<"$output")" 0
    expect "сборка идёт сразу" "$(grep -c 'Собираем контейнеры' <<<"$output")" 1
    expect "откат к версии до обновления" "$(git -C "$work/site" rev-parse HEAD)" "$old"
    rm -rf "$work"
}

if [[ $EUID -ne 0 ]]; then
    echo "Запустите через sudo: deploy.sh работает только от root" >&2
    exit 1
fi
for test in $(declare -F | awk '$3 ~ /^test_/ { print $3 }'); do
    "$test"
done
exit "$((failures > 0))"
