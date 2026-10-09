import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.utils import timezone

from config.database import seconds_since_start
from journal.models import Action, JournalEntry

OS_RELEASES = ((Path("/host/os-release"), "server"), (Path("/etc/os-release"), "container"))
MEMINFO = Path("/proc/meminfo")
PROC_STAT = Path("/proc/stat")
INIT_STAT = Path("/proc/1/stat")
CGROUP_LIMITS = (
    (Path("/sys/fs/cgroup/memory.current"), Path("/sys/fs/cgroup/memory.max")),
    (Path("/sys/fs/cgroup/memory/memory.usage_in_bytes"), Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")),
)
UNLIMITED_FROM = 1 << 60
START_TIME_FIELD = 19
KIBIBYTE = 1024


@dataclass(frozen=True)
class SystemInfo:
    release: str
    site_started_at: datetime | None
    db_started_at: datetime | None
    last_backup_at: datetime | None
    os_name: str
    os_source: str
    memory_total: int | None
    memory_used: int | None
    app_memory_used: int | None
    app_memory_limit: int | None


def read(path):
    try:
        return path.read_text()
    except OSError:
        return ""


def pretty_name(text):
    for line in text.splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.split("=", 1)[1].strip().strip('"')
    return ""


def os_release():
    for path, source in OS_RELEASES:
        name = pretty_name(read(path))
        if name:
            return name, source
    return "", ""


def meminfo(text):
    values = {}
    for line in text.splitlines():
        key, _, rest = line.partition(":")
        parts = rest.split()
        if parts and parts[0].isdigit():
            values[key] = int(parts[0]) * KIBIBYTE
    return values


def memory():
    values = meminfo(read(MEMINFO))
    total, available = values.get("MemTotal"), values.get("MemAvailable")
    return (total, total - available) if total and available is not None else (None, None)


def number(text):
    value = text.strip()
    return int(value) if value.isdigit() else None


def app_memory():
    for used_path, limit_path in CGROUP_LIMITS:
        used = number(read(used_path))
        if used is not None:
            limit = number(read(limit_path))
            return used, limit if limit and limit < UNLIMITED_FROM else None
    return None, None


def boot_time(text):
    for line in text.splitlines():
        if line.startswith("btime "):
            return int(line.split()[1])
    return None


def process_started_at(stat_text, boot, ticks_per_second):
    fields = stat_text.rpartition(")")[2].split()
    if boot is None or len(fields) <= START_TIME_FIELD:
        return None
    seconds = boot + int(fields[START_TIME_FIELD]) / ticks_per_second
    return datetime.fromtimestamp(seconds, tz=timezone.get_current_timezone())


def site_started_at():
    return process_started_at(read(INIT_STAT), boot_time(read(PROC_STAT)), os.sysconf("SC_CLK_TCK"))


def db_started_at():
    seconds = seconds_since_start(connection)
    return timezone.now() - timedelta(seconds=seconds) if seconds is not None else None


def last_backup_at():
    latest = JournalEntry.objects.filter(action=Action.BACKUP_DONE).order_by("-pk").first()
    return latest.created_at if latest else None


def system_info():
    name, source = os_release()
    total, used = memory()
    app_used, app_limit = app_memory()
    return SystemInfo(settings.APP_RELEASE, site_started_at(), db_started_at(), last_backup_at(), name, source, total, used, app_used, app_limit)
