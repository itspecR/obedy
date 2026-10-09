#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

UNIT=obedy-journal-clean

main() {
    local root
    root="$(project_root)"
    require_root "./scripts/journal-clean-timer.sh ${1:-install}"
    case "${1:-install}" in
        install) install_timer "$root" ;;
        remove) remove_timer ;;
        status) systemctl list-timers "$UNIT.timer" --no-pager ;;
        run) systemctl start "$UNIT.service" && journalctl -u "$UNIT.service" -n 5 --no-pager ;;
        *) fail "Использование: sudo ./scripts/journal-clean-timer.sh [install|remove|status|run]" ;;
    esac
}

install_timer() {
    local docker
    docker="$(command -v docker)" || fail "Не найден docker. Сначала установите систему: sudo ./scripts/install.sh"
    cat > "/etc/systemd/system/$UNIT.service" <<UNIT_FILE
[Unit]
Description=Очистка «Обеды»: записи журнала старше трёх лет и истёкшие сессии

[Service]
Type=oneshot
WorkingDirectory=$1
ExecStart=$docker compose exec -T app python manage.py clean_journal
ExecStart=-$1/scripts/clean-sessions.sh
PrivateTmp=true
ProtectHome=read-only
NoNewPrivileges=true
UNIT_FILE
    cat > "/etc/systemd/system/$UNIT.timer" <<UNIT_FILE
[Unit]
Description=Ежедневная очистка журнала и сессий «Обеды» в 00:30 по Москве

[Timer]
OnCalendar=*-*-* 00:30:00 Europe/Moscow
Persistent=true

[Install]
WantedBy=timers.target
UNIT_FILE
    systemctl daemon-reload
    systemctl enable --now "$UNIT.timer"
    echo "Таймер включён: каждый день в 00:30 по Москве удаляются записи журнала старше трёх лет."
}

remove_timer() {
    systemctl disable --now "$UNIT.timer" 2>/dev/null || true
    rm -f "/etc/systemd/system/$UNIT.service" "/etc/systemd/system/$UNIT.timer"
    systemctl daemon-reload
    echo "Таймер очистки журнала отключён."
}

main "$@"
