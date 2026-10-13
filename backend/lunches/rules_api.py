from datetime import date, datetime, time

from ninja import Field, Query, Router, Schema, Status
from ninja.errors import HttpError

from accounts.security import session_auth
from journal.entries import differences, record, record_changes, removed
from journal.models import Action
from journal.snapshots import calendar_day_snapshot, rules_snapshot
from lunches.calendar_changes import DAY_NOT_FOUND, CalendarDayMissing, CalendarRefused, add_day, remove_day, year_days
from lunches.rule_changes import MAX_LIMIT_MINUTES, MIN_LIMIT_MINUTES, WEEKDAYS, InvalidRules, RulesDraft, save_rules
from lunches.rules import current_rules
from lunches.supervision import require_supervisor

RULES_ONLY = "Правила обеда доступны HR и администратору"
MIN_YEAR = 2000
MAX_YEAR = 2100

router = Router(tags=["Правила обеда"])


class RulesOut(Schema):
    limit_minutes: int
    workdays: str
    day_end: time
    window_enabled: bool
    window_start: time
    window_end: time
    updated_at: datetime
    min_limit_minutes: int
    max_limit_minutes: int


class RulesIn(Schema):
    limit_minutes: int
    workdays: str = Field(max_length=len(WEEKDAYS))
    day_end: time
    window_enabled: bool
    window_start: time
    window_end: time

    def draft(self):
        return RulesDraft(self.limit_minutes, self.workdays, self.day_end, self.window_enabled, self.window_start, self.window_end)


def describe_rules(rules):
    return RulesOut(
        limit_minutes=rules.limit_minutes,
        workdays=rules.workdays,
        day_end=rules.day_end,
        window_enabled=rules.window_enabled,
        window_start=rules.window_start,
        window_end=rules.window_end,
        updated_at=rules.updated_at,
        min_limit_minutes=MIN_LIMIT_MINUTES,
        max_limit_minutes=MAX_LIMIT_MINUTES,
    )


@router.get("", auth=session_auth, response=RulesOut)
def rules(request):
    require_supervisor(request, RULES_ONLY)
    return describe_rules(current_rules())


@router.put("", auth=session_auth, response=RulesOut)
def update_rules(request, payload: RulesIn):
    require_supervisor(request, RULES_ONLY)
    before = rules_snapshot(current_rules())
    try:
        saved = save_rules(payload.draft())
    except InvalidRules as invalid:
        raise HttpError(400, invalid.message) from invalid
    record_changes(request, Action.RULES_CHANGED, before, rules_snapshot(saved))
    return describe_rules(saved)


class CalendarDayOut(Schema):
    day: date
    working: bool


class CalendarDayIn(Schema):
    day: date
    working: bool


def year_calendar(year):
    return [CalendarDayOut(day=item.day, working=item.working) for item in year_days(year)]


@router.get("/calendar", auth=session_auth, response=list[CalendarDayOut])
def calendar(request, year: int = Query(..., ge=MIN_YEAR, le=MAX_YEAR)):
    require_supervisor(request, RULES_ONLY)
    return year_calendar(year)


@router.post("/calendar", auth=session_auth, response={201: list[CalendarDayOut]})
def add_calendar_day(request, payload: CalendarDayIn):
    require_supervisor(request, RULES_ONLY)
    try:
        added = add_day(payload.day, payload.working)
    except CalendarRefused as refused:
        raise HttpError(400, refused.message) from refused
    record(request, Action.CALENDAR_DAY_ADDED, rows=differences({}, calendar_day_snapshot(added)))
    return Status(201, year_calendar(added.day.year))


@router.delete("/calendar/{day}", auth=session_auth, response=list[CalendarDayOut])
def remove_calendar_day(request, day: date):
    require_supervisor(request, RULES_ONLY)
    try:
        gone_day = remove_day(day)
    except CalendarDayMissing as missing:
        raise HttpError(404, DAY_NOT_FOUND) from missing
    record(request, Action.CALENDAR_DAY_REMOVED, rows=removed(calendar_day_snapshot(gone_day)))
    return year_calendar(day.year)
