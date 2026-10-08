#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

UNIT=obedy-backup

main() {
    local root
    root="$(project_root)"
    if [[ $EUID -ne 0 ]]; then
        echo "Запустите через sudo: sudo ./scripts/backup-timer.sh ${1:-install}" >&2
        exit 1
    fi
    case "${1:-install}" in
        install) install_timer "$root" ;;
        remove) remove_timer ;;
        status) systemctl list-timers "$UNIT.timer" --no-pager ;;
        *) echo "Использование: sudo ./scripts/backup-timer.sh [install|remove|status]" >&2; exit 1 ;;
    esac
}

install_timer() {
    cat > "/etc/systemd/system/$UNIT.service" <<UNIT_FILE
[Unit]
Description=Резервная копия базы «Обеды» и очистка истёкших сессий

[Service]
Type=oneshot
ExecStart=$1/scripts/backup.sh
ExecStart=-$1/scripts/clean-sessions.sh
PrivateTmp=true
ProtectHome=read-only
NoNewPrivileges=true
UNIT_FILE
    cat > "/etc/systemd/system/$UNIT.timer" <<UNIT_FILE
[Unit]
Description=Ежедневная резервная копия «Обеды» в 00:00 по Москве

[Timer]
OnCalendar=*-*-* 00:00:00 Europe/Moscow
Persistent=true

[Install]
WantedBy=timers.target
UNIT_FILE
    systemctl daemon-reload
    systemctl enable --now "$UNIT.timer"
    echo "Таймер включён: копия каждый день в 00:00 по Москве, хранятся последние ${BACKUP_KEEP:-40}."
    systemctl list-timers "$UNIT.timer" --no-pager
}

remove_timer() {
    systemctl disable --now "$UNIT.timer" 2>/dev/null || true
    rm -f "/etc/systemd/system/$UNIT.service" "/etc/systemd/system/$UNIT.timer"
    systemctl daemon-reload
    echo "Таймер резервного копирования отключён."
}

main "$@"
