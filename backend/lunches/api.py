from datetime import datetime

from django.utils import timezone
from ninja import Router, Schema
from ninja.errors import HttpError

from accounts.lunch_policy import LUNCH_ROLES
from accounts.permissions import require_roles
from accounts.security import session_auth
from lunches.board_api import router as board_router
from lunches.history import BadMonth, lunches_of_month, month_start, summary_of
from lunches.rules import current_rules
from lunches.rules_api import router as rules_router
from lunches.schemas import LunchOut, describe_lunch
from lunches.service import (
    UNDO_WINDOW,
    WARNING_MINUTES,
    LunchRefused,
    close_overdue,
    finish_lunch,
    start_lunch,
    start_refusal,
    todays_lunch,
    undo_deadline,
    undo_lunch,
)

MONTH_FORMAT = "%Y-%m"
NO_LUNCH_FOR_ROLE = "Администратор обеды не отмечает"

router = Router(tags=["Обед"])
router.add_router("/rules", rules_router)
router.add_router("/board", board_router)


class StateOut(Schema):
    server_time: datetime
    tracked: bool
    limit_minutes: int
    warning_minutes: int
    undo_seconds: int
    today: LunchOut | None
    can_start: bool
    refusal: str
    undo_until: datetime | None


class SummaryOut(Schema):
    count: int
    violations: int
    average_minutes: int | None


class HistoryOut(Schema):
    month: str
    lunches: list[LunchOut]
    summary: SummaryOut


def undo_until_of(lunch, now):
    if lunch is None or lunch.ended_at is not None or now > undo_deadline(lunch):
        return None
    return undo_deadline(lunch)


def state_of(account, now):
    close_overdue(now)
    rules = current_rules()
    lunch = todays_lunch(account, now)
    refusal = start_refusal(account, rules, lunch, now)
    return StateOut(
        server_time=now,
        tracked=account.track_lunch,
        limit_minutes=lunch.limit_minutes if lunch else rules.limit_minutes,
        warning_minutes=WARNING_MINUTES,
        undo_seconds=int(UNDO_WINDOW.total_seconds()),
        today=describe_lunch(lunch, now) if lunch else None,
        can_start=not refusal,
        refusal=refusal,
        undo_until=undo_until_of(lunch, now),
    )


def lunch_taker(request):
    return require_roles(request, LUNCH_ROLES, NO_LUNCH_FOR_ROLE).account


def acted(request, action):
    account = lunch_taker(request)
    try:
        action(account, timezone.now())
    except LunchRefused as refused:
        raise HttpError(409, refused.message) from refused
    return state_of(account, timezone.now())


@router.get("/me", auth=session_auth, response=StateOut)
def my_state(request):
    return state_of(lunch_taker(request), timezone.now())


@router.post("/start", auth=session_auth, response=StateOut)
def start(request):
    return acted(request, start_lunch)


@router.post("/finish", auth=session_auth, response=StateOut)
def finish(request):
    return acted(request, finish_lunch)


@router.post("/undo", auth=session_auth, response=StateOut)
def undo(request):
    return acted(request, undo_lunch)


@router.get("/history", auth=session_auth, response=HistoryOut)
def history(request, month: str = ""):
    account = lunch_taker(request)
    now = timezone.now()
    try:
        first = month_start(month, now)
    except BadMonth as bad:
        raise HttpError(400, str(bad)) from bad
    lunches = lunches_of_month(account, first)
    summary = summary_of(lunches, now)
    return HistoryOut(
        month=first.strftime(MONTH_FORMAT),
        lunches=[describe_lunch(lunch, now) for lunch in lunches],
        summary=SummaryOut(count=summary.count, violations=summary.violations, average_minutes=summary.average_minutes),
    )
