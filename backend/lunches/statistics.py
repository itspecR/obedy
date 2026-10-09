from dataclasses import dataclass
from datetime import date

from accounts.names import display_name
from lunches.history import summary_of
from lunches.models import Lunch
from lunches.status import LunchStatus, duration_of, is_overrun, limit_of, status_of
from staff.status import gone

MAX_PERIOD_DAYS = 366
SECONDS_IN_MINUTE = 60
PERCENT = 100
BAD_ORDER = "Начало периода позже конца"
TOO_LONG = "Период — не больше года"


class BadPeriod(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class Period:
    first: date
    last: date


@dataclass(frozen=True)
class PersonStats:
    account: object
    count: int
    overruns: int
    unreturned: int
    violations: int
    average_minutes: int | None
    overrun_minutes: int


@dataclass(frozen=True)
class Overview:
    count: int
    violations: int
    average_minutes: int | None
    on_time_percent: int | None
    people: int


def checked_period(first, last):
    if first > last:
        raise BadPeriod(BAD_ORDER)
    if (last - first).days >= MAX_PERIOD_DAYS:
        raise BadPeriod(TOO_LONG)
    return Period(first, last)


def period_query(period):
    return Lunch.objects.filter(day__gte=period.first, day__lte=period.last).exclude(gone("account__"))


def lunches_in(period):
    return list(period_query(period).select_related("account", "corrected_by").order_by("day", "started_at", "account__full_name"))


def chosen(lunches, people):
    wanted = set(people)
    return [lunch for lunch in lunches if lunch.account_id in wanted] if wanted else lunches


def is_unreturned(lunch, now):
    return status_of(lunch, now) == LunchStatus.UNRETURNED


def counts_as_overrun(lunch, now):
    return not is_unreturned(lunch, now) and is_overrun(lunch, now)


def excess_seconds(lunch, now):
    return max(0, (duration_of(lunch, now) - limit_of(lunch)).total_seconds())


def person_stats(account, lunches, now):
    summary = summary_of(lunches, now)
    overruns = [lunch for lunch in lunches if counts_as_overrun(lunch, now)]
    return PersonStats(
        account=account,
        count=summary.count,
        overruns=len(overruns),
        unreturned=sum(1 for lunch in lunches if is_unreturned(lunch, now)),
        violations=summary.violations,
        average_minutes=summary.average_minutes,
        overrun_minutes=round(sum(excess_seconds(lunch, now) for lunch in overruns) / SECONDS_IN_MINUTE),
    )


def by_account(lunches):
    groups = {}
    for lunch in lunches:
        groups.setdefault(lunch.account_id, (lunch.account, []))[1].append(lunch)
    return groups.values()


def worst_first(stats):
    return (-stats.violations, -stats.overrun_minutes, display_name(stats.account).lower())


def people_stats(lunches, now):
    return sorted((person_stats(account, own, now) for account, own in by_account(lunches)), key=worst_first)


def on_time_percent(lunches, now):
    finished = [lunch for lunch in lunches if status_of(lunch, now) != LunchStatus.ONGOING]
    if not finished:
        return None
    on_time = sum(1 for lunch in finished if status_of(lunch, now) == LunchStatus.ON_TIME)
    return round(on_time * PERCENT / len(finished))


def overview_of(lunches, now):
    summary = summary_of(lunches, now)
    return Overview(
        count=summary.count,
        violations=summary.violations,
        average_minutes=summary.average_minutes,
        on_time_percent=on_time_percent(lunches, now),
        people=len({lunch.account_id for lunch in lunches}),
    )
