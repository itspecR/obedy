from dataclasses import asdict
from datetime import date
from typing import Annotated

from django.http import HttpResponse
from django.utils import timezone
from ninja import Query, Router, Schema
from ninja.errors import HttpError

from accounts.names import display_name
from accounts.security import session_auth
from lunches.excel import workbook_bytes
from lunches.service import close_overdue
from lunches.schemas import LunchOut, describe_lunch
from lunches.statistics import BadPeriod, checked_period, chosen, lunches_in, overview_of, people_stats
from lunches.supervision import require_supervisor

People = Annotated[list[int] | None, Query()]

STATS_ONLY = "Статистика доступна HR и администратору"
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
FILE_NAME = "obedy_{first}_{last}.xlsx"

router = Router(tags=["Статистика"])


class PersonStatsOut(Schema):
    id: int
    name: str
    login: str
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


class PersonLunchOut(Schema):
    person_id: int
    name: str
    lunch: LunchOut


class StatsOut(Schema):
    date_from: date
    date_to: date
    overview: OverviewOut
    people: list[PersonStatsOut]
    lunches: list[PersonLunchOut]


def describe_stats(stats):
    account = stats.account
    return PersonStatsOut(
        id=account.pk,
        name=display_name(account),
        login=account.login,
        count=stats.count,
        violations=stats.violations,
        overruns=stats.overruns,
        unreturned=stats.unreturned,
        average_minutes=stats.average_minutes,
        overrun_minutes=stats.overrun_minutes,
    )


def describe_person_lunch(lunch, now):
    return PersonLunchOut(person_id=lunch.account_id, name=display_name(lunch.account), lunch=describe_lunch(lunch, now))


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
def stats(request, date_from: date, date_to: date, person: People = None):
    period = period_for(request, date_from, date_to)
    now = fresh_now()
    lunches = lunches_in(period)
    selected = chosen(lunches, person or ())
    return StatsOut(
        date_from=period.first,
        date_to=period.last,
        overview=OverviewOut(**asdict(overview_of(selected, now))),
        people=[describe_stats(item) for item in people_stats(lunches, now)],
        lunches=[describe_person_lunch(lunch, now) for lunch in selected] if person else [],
    )


@router.get("/export", auth=session_auth)
def export(request, date_from: date, date_to: date, person: People = None):
    period = period_for(request, date_from, date_to)
    now = fresh_now()
    lunches = chosen(lunches_in(period), person or ())
    response = HttpResponse(workbook_bytes(people_stats(lunches, now), lunches, now), content_type=XLSX_TYPE)
    response["Content-Disposition"] = f'attachment; filename="{FILE_NAME.format(first=period.first, last=period.last)}"'
    return response
