from datetime import date

from ninja import Field, Router, Schema, Status
from ninja.errors import HttpError

from accounts.names import display_name
from accounts.security import session_auth
from journal.entries import differences, record, removed
from journal.models import Action
from journal.snapshots import absence_snapshot
from lunches.absences import AbsenceDraft, AbsenceRefused, absences_between, add_absence, change_absence, remove_absence
from lunches.models import NOTE_LIMIT, Absence, AbsenceKind
from lunches.statistics import BadPeriod, checked_period
from lunches.supervision import require_supervisor
from staff.status import present_accounts

ABSENCES_ONLY = "Отсутствия доступны HR и администратору"
NOT_FOUND = "Отсутствие не найдено. Обновите страницу"
PERSON_NOT_FOUND = "Сотрудник не найден. Обновите страницу"

router = Router(tags=["Отсутствия"])


class AbsenceOut(Schema):
    id: int
    person_id: int
    name: str
    login: str
    first: date
    last: date
    kind: AbsenceKind
    note: str


class AbsenceIn(Schema):
    first: date
    last: date
    kind: AbsenceKind
    note: str = Field("", max_length=NOTE_LIMIT)

    def draft(self):
        return AbsenceDraft(self.first, self.last, self.kind, self.note)


class NewAbsenceIn(AbsenceIn):
    account_id: int


def describe_absence(absence):
    account = absence.account
    return AbsenceOut(
        id=absence.pk,
        person_id=account.pk,
        name=display_name(account),
        login=account.login,
        first=absence.first,
        last=absence.last,
        kind=absence.kind,
        note=absence.note,
    )


def refused_as_bad_request(action):
    try:
        return action()
    except AbsenceRefused as refused:
        raise HttpError(400, refused.message) from refused


def found_or_404(action):
    try:
        return refused_as_bad_request(action)
    except Absence.DoesNotExist as missing:
        raise HttpError(404, NOT_FOUND) from missing


@router.get("", auth=session_auth, response=list[AbsenceOut])
def absences(request, date_from: date, date_to: date):
    require_supervisor(request, ABSENCES_ONLY)
    try:
        period = checked_period(date_from, date_to)
    except BadPeriod as bad:
        raise HttpError(400, bad.message) from bad
    found = absences_between(period.first, period.last).order_by("first", "account__full_name", "account__login")
    return [describe_absence(absence) for absence in found]


@router.post("", auth=session_auth, response={201: AbsenceOut})
def add(request, payload: NewAbsenceIn):
    require_supervisor(request, ABSENCES_ONLY)
    account = present_accounts().filter(pk=payload.account_id).first()
    if account is None:
        raise HttpError(404, PERSON_NOT_FOUND)
    absence = refused_as_bad_request(lambda: add_absence(account, payload.draft()))
    record(request, Action.ABSENCE_ADDED, account, differences({}, absence_snapshot(absence)))
    return Status(201, describe_absence(absence))


@router.put("/{absence_id}", auth=session_auth, response=AbsenceOut)
def change(request, absence_id: int, payload: AbsenceIn):
    require_supervisor(request, ABSENCES_ONLY)
    before = Absence.objects.filter(pk=absence_id).first()
    snapshot = absence_snapshot(before) if before else {}
    absence = found_or_404(lambda: change_absence(absence_id, payload.draft()))
    record(request, Action.ABSENCE_CHANGED, absence.account, differences(snapshot, absence_snapshot(absence)))
    return describe_absence(absence)


@router.delete("/{absence_id}", auth=session_auth, response={204: None})
def delete(request, absence_id: int):
    require_supervisor(request, ABSENCES_ONLY)
    absence = found_or_404(lambda: remove_absence(absence_id))
    record(request, Action.ABSENCE_REMOVED, absence.account, removed(absence_snapshot(absence)))
    return Status(204, None)
