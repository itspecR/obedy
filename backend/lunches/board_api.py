from datetime import date, datetime, time

from django.utils import timezone
from ninja import Field, Router, Schema, Status
from ninja.errors import HttpError

from accounts.names import display_name
from accounts.security import session_auth
from journal.entries import Row, differences, record, removed
from journal.models import Action
from journal.snapshots import day_text, lunch_snapshot
from lunches.clock import today
from lunches.corrections import Correction, CorrectionRefused, add_lunch, can_receive_lunch, correct_lunch, delete_lunch
from lunches.models import REASON_LIMIT, Lunch
from lunches.schemas import LunchOut, describe_lunch
from lunches.service import WARNING_MINUTES, close_overdue
from lunches.supervision import require_supervisor
from staff.status import gone, present_accounts

BOARD_ONLY = "Табло доступно HR и администратору"
NOT_FOUND = "Обед не найден. Обновите страницу"
PERSON_NOT_FOUND = "Сотрудник не найден. Обновите страницу"

router = Router(tags=["Табло"])


class PersonOut(Schema):
    id: int
    name: str
    login: str


class BoardEntryOut(Schema):
    person: PersonOut
    lunch: LunchOut


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


class DeleteIn(Schema):
    reason: str = Field(max_length=REASON_LIMIT)


class AddLunchIn(CorrectionIn):
    account_id: int
    day: date


def describe_person(account):
    return PersonOut(id=account.pk, name=display_name(account), login=account.login)


def describe_entry(lunch, now):
    return BoardEntryOut(person=describe_person(lunch.account), lunch=describe_lunch(lunch, now))


def lunches_of_day(day):
    return Lunch.objects.filter(day=day).exclude(gone("account__")).select_related("account", "corrected_by").order_by("started_at")


def board_actor(request):
    return require_supervisor(request, BOARD_ONLY)


def day_row(lunch):
    return Row("День", after=day_text(lunch.day))


def reason_row(reason):
    return Row("Причина", after=reason)


def lunch_rows(before, lunch):
    return [day_row(lunch), *differences(before, lunch_snapshot(lunch)), reason_row(lunch.correction_reason)]


def deleted_rows(lunch, reason):
    return [day_row(lunch), *removed(lunch_snapshot(lunch)), reason_row(reason)]


def refused_as_bad_request(action):
    try:
        return action()
    except CorrectionRefused as refused:
        raise HttpError(400, refused.message) from refused


@router.get("", auth=session_auth, response=BoardOut)
def board(request, day: date | None = None):
    board_actor(request)
    now = timezone.now()
    close_overdue(now)
    shown = day or today(now)
    return BoardOut(
        server_time=now,
        day=shown,
        today=today(now),
        warning_minutes=WARNING_MINUTES,
        entries=[describe_entry(lunch, now) for lunch in lunches_of_day(shown)],
    )


@router.get("/people", auth=session_auth, response=list[PersonOut])
def people(request):
    board_actor(request)
    candidates = present_accounts().filter(is_active=True, track_lunch=True).order_by("full_name", "login")
    return [describe_person(account) for account in candidates if can_receive_lunch(account)]


@router.post("/lunches", auth=session_auth, response={201: BoardEntryOut})
def add(request, payload: AddLunchIn):
    actor = board_actor(request)
    account = present_accounts().filter(pk=payload.account_id).first()
    if account is None:
        raise HttpError(404, PERSON_NOT_FOUND)
    now = timezone.now()
    lunch = refused_as_bad_request(lambda: add_lunch(actor, account, payload.day, payload.correction(), now))
    record(request, Action.LUNCH_ADDED, account, lunch_rows({}, lunch))
    return Status(201, describe_entry(lunch, now))


@router.put("/{lunch_id}/correction", auth=session_auth, response=BoardEntryOut)
def correct(request, lunch_id: int, payload: CorrectionIn):
    actor = board_actor(request)
    now = timezone.now()
    before = Lunch.objects.filter(pk=lunch_id).first()
    try:
        lunch = refused_as_bad_request(lambda: correct_lunch(actor, lunch_id, payload.correction(), now))
    except Lunch.DoesNotExist as missing:
        raise HttpError(404, NOT_FOUND) from missing
    record(request, Action.LUNCH_CORRECTED, lunch.account, lunch_rows(lunch_snapshot(before), lunch))
    return describe_entry(lunch, now)


@router.delete("/{lunch_id}", auth=session_auth, response={204: None})
def delete(request, lunch_id: int, payload: DeleteIn):
    board_actor(request)
    try:
        lunch, reason = refused_as_bad_request(lambda: delete_lunch(lunch_id, payload.reason))
    except Lunch.DoesNotExist as missing:
        raise HttpError(404, NOT_FOUND) from missing
    record(request, Action.LUNCH_DELETED, lunch.account, deleted_rows(lunch, reason))
    return Status(204, None)
