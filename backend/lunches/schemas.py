from datetime import date, datetime

from ninja import Schema

from accounts.names import display_name
from lunches.models import AbsenceKind
from lunches.status import LunchStatus, duration_of, status_of


class CorrectionOut(Schema):
    by: str
    at: datetime
    reason: str
    added: bool


class LunchOut(Schema):
    id: int
    day: date
    started_at: datetime
    ended_at: datetime | None
    limit_minutes: int
    status: LunchStatus
    duration_seconds: int
    auto_closed: bool
    correction: CorrectionOut | None


def correction_of(lunch):
    if lunch.corrected_at is None:
        return None
    author = display_name(lunch.corrected_by) if lunch.corrected_by else "—"
    return CorrectionOut(by=author, at=lunch.corrected_at, reason=lunch.correction_reason, added=lunch.added_by_hand)


def describe_lunch(lunch, now):
    return LunchOut(
        id=lunch.pk,
        day=lunch.day,
        started_at=lunch.started_at,
        ended_at=lunch.ended_at,
        limit_minutes=lunch.limit_minutes,
        status=status_of(lunch, now),
        duration_seconds=int(duration_of(lunch, now).total_seconds()),
        auto_closed=lunch.auto_closed,
        correction=correction_of(lunch),
    )


class AbsenceOut(Schema):
    id: int
    person_id: int
    name: str
    login: str
    first: date
    last: date
    kind: AbsenceKind
    note: str


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
