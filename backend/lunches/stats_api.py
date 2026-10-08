from dataclasses import asdict
from datetime import date

from django.http import HttpResponse
from django.utils import timezone
from ninja import Router, Schema
from ninja.errors import HttpError

from accounts.names import display_name
from accounts.security import session_auth
from lunches.excel import workbook_bytes
from lunches.service import close_overdue
from lunches.statistics import BadPeriod, checked_period, departments_in, lunches_in, overview_of, people_stats
from lunches.supervision import require_supervisor

STATS_ONLY = "Статистика доступна HR и администратору"
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
FILE_NAME = "obedy_{first}_{last}.xlsx"

router = Router(tags=["Статистика"])


class PersonStatsOut(Schema):
    id: int
    name: str
    login: str
    department: str
    position: str
    count: int
    violations: int
    overruns: int
    unreturned: int
    average_minutes: int | None
    overrun_minutes: int


class OverviewOut(Schema):
    count: int
    violations: int
    average_minutes: int | None
    on_time_percent: int | None
    people: int


class StatsOut(Schema):
    date_from: date
    date_to: date
    departments: list[str]
    overview: OverviewOut
    people: list[PersonStatsOut]


def describe_stats(stats):
    account = stats.account
    return PersonStatsOut(
        id=account.pk,
        name=display_name(account),
        login=account.login,
        department=account.department,
        position=account.position,
        count=stats.count,
        violations=stats.violations,
        overruns=stats.overruns,
        unreturned=stats.unreturned,
        average_minutes=stats.average_minutes,
        overrun_minutes=stats.overrun_minutes,
    )


def period_for(request, date_from, date_to):
    require_supervisor(request, STATS_ONLY)
    try:
        return checked_period(date_from, date_to)
    except BadPeriod as bad:
        raise HttpError(400, bad.message) from bad


def fresh_now():
    now = timezone.now()
    close_overdue(now)
    return now


@router.get("", auth=session_auth, response=StatsOut)
def stats(request, date_from: date, date_to: date, department: str = ""):
    period = period_for(request, date_from, date_to)
    now = fresh_now()
    lunches = lunches_in(period, department)
    overview = overview_of(lunches, now)
    return StatsOut(
        date_from=period.first,
        date_to=period.last,
        departments=departments_in(period),
        overview=OverviewOut(**asdict(overview)),
        people=[describe_stats(item) for item in people_stats(lunches, now)],
    )


@router.get("/export", auth=session_auth)
def export(request, date_from: date, date_to: date, department: str = ""):
    period = period_for(request, date_from, date_to)
    now = fresh_now()
    lunches = lunches_in(period, department)
    response = HttpResponse(workbook_bytes(people_stats(lunches, now), lunches, now), content_type=XLSX_TYPE)
    response["Content-Disposition"] = f'attachment; filename="{FILE_NAME.format(first=period.first, last=period.last)}"'
    return response
