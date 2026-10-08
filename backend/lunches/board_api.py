from datetime import date, datetime, time

from django.utils import timezone
from ninja import Field, Router, Schema
from ninja.errors import HttpError

from accounts.models import Role
from accounts.names import display_name
from accounts.permissions import require_roles
from accounts.security import session_auth
from lunches.clock import today
from lunches.corrections import Correction, CorrectionRefused, correct_lunch
from lunches.models import REASON_LIMIT, Lunch
from lunches.schemas import LunchOut, describe_lunch
from lunches.service import WARNING_MINUTES, close_overdue

BOARD_ROLES = (Role.HR, Role.ADMIN)
BOARD_ONLY = "Табло доступно HR и администратору"
NOT_FOUND = "Обед не найден. Обновите страницу"

router = Router(tags=["Табло"])


class PersonOut(Schema):
    id: int
    name: str
    login: str
    department: str
    position: str


class BoardEntryOut(Schema):
    person: PersonOut
    lunch: LunchOut
    can_correct: bool


class BoardOut(Schema):
    server_time: datetime
    day: date
    today: date
    warning_minutes: int
    entries: list[BoardEntryOut]


class CorrectionIn(Schema):
    started_at: time
    ended_at: time
    reason: str = Field(max_length=REASON_LIMIT)

    def correction(self):
        return Correction(self.started_at, self.ended_at, self.reason)


def describe_person(account):
    return PersonOut(id=account.pk, name=display_name(account), login=account.login, department=account.department, position=account.position)


def describe_entry(lunch, actor, now):
    return BoardEntryOut(person=describe_person(lunch.account), lunch=describe_lunch(lunch, now), can_correct=lunch.account_id != actor.pk)


def lunches_of_day(day):
    return Lunch.objects.filter(day=day).select_related("account", "corrected_by").order_by("started_at")


@router.get("", auth=session_auth, response=BoardOut)
def board(request, day: date | None = None):
    actor = require_roles(request, BOARD_ROLES, BOARD_ONLY).account
    now = timezone.now()
    close_overdue(now)
    shown = day or today(now)
    return BoardOut(
        server_time=now,
        day=shown,
        today=today(now),
        warning_minutes=WARNING_MINUTES,
        entries=[describe_entry(lunch, actor, now) for lunch in lunches_of_day(shown)],
    )


@router.put("/{lunch_id}/correction", auth=session_auth, response=BoardEntryOut)
def correct(request, lunch_id: int, payload: CorrectionIn):
    actor = require_roles(request, BOARD_ROLES, BOARD_ONLY).account
    now = timezone.now()
    try:
        lunch = correct_lunch(actor, lunch_id, payload.correction(), now)
    except Lunch.DoesNotExist as missing:
        raise HttpError(404, NOT_FOUND) from missing
    except CorrectionRefused as refused:
        raise HttpError(400, refused.message) from refused
    return describe_entry(lunch, actor, now)
