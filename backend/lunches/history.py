import re
from dataclasses import dataclass
from datetime import date

from lunches.clock import today
from lunches.models import Lunch
from lunches.status import MEASURED, duration_of, is_violation, status_of

MONTH_PATTERN = re.compile(r"(\d{4})-(\d{2})")
MONTHS_IN_YEAR = 12
SECONDS_IN_MINUTE = 60
BAD_MONTH = "Месяц указывается так: 2026-10"


class BadMonth(Exception):
    pass


@dataclass(frozen=True)
class Summary:
    count: int
    violations: int
    average_minutes: int | None


def month_start(text, now):
    if not text:
        return today(now).replace(day=1)
    matched = MONTH_PATTERN.fullmatch(text)
    if not matched or not 1 <= int(matched.group(2)) <= MONTHS_IN_YEAR:
        raise BadMonth(BAD_MONTH)
    return date(int(matched.group(1)), int(matched.group(2)), 1)


def next_month(first):
    return date(first.year + first.month // MONTHS_IN_YEAR, first.month % MONTHS_IN_YEAR + 1, 1)


def lunches_of_month(account, first):
    return list(Lunch.objects.filter(account=account, day__gte=first, day__lt=next_month(first)).order_by("-day").select_related("corrected_by"))


def summary_of(lunches, now):
    measured = [lunch for lunch in lunches if status_of(lunch, now) in MEASURED]
    total_seconds = sum(duration_of(lunch, now).total_seconds() for lunch in measured)
    average = round(total_seconds / len(measured) / SECONDS_IN_MINUTE) if measured else None
    return Summary(len(lunches), sum(1 for lunch in lunches if is_violation(lunch, now)), average)
