#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

cd "$(project_root)"
docker compose exec -T app python manage.py clean_sessions
