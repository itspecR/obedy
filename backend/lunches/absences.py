from dataclasses import dataclass
from datetime import date

from django.db import transaction

from lunches.corrections import UNTRACKED_PERSON, can_receive_lunch
from lunches.models import Absence
from staff.status import gone

MAX_ABSENCE_DAYS = 366
DATE_FORMAT = "%d.%m.%Y"
BAD_ORDER = "Дата «по» не может быть раньше даты «с»"
TOO_LONG = "Отсутствие — не дольше года. Разбейте его на части"
OVERLAP = "В эти даты уже есть отсутствие: {kind} {first} — {last}. Исправьте его"


class AbsenceRefused(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class AbsenceDraft:
    first: date
    last: date
    kind: str
    note: str


def checked_dates(draft):
    if draft.last < draft.first:
        raise AbsenceRefused(BAD_ORDER)
    if (draft.last - draft.first).days >= MAX_ABSENCE_DAYS:
        raise AbsenceRefused(TOO_LONG)


def overlap_text(absence):
    return OVERLAP.format(kind=absence.get_kind_display(), first=absence.first.strftime(DATE_FORMAT), last=absence.last.strftime(DATE_FORMAT))


def ensure_no_overlap(account, draft, keep=None):
    clash = Absence.objects.select_for_update().filter(account=account, first__lte=draft.last, last__gte=draft.first).exclude(pk=keep).first()
    if clash is not None:
        raise AbsenceRefused(overlap_text(clash))


def filled(absence, draft):
    absence.first, absence.last, absence.kind, absence.note = draft.first, draft.last, draft.kind, draft.note.strip()
    absence.save()
    return absence


@transaction.atomic
def add_absence(account, draft):
    if not can_receive_lunch(account):
        raise AbsenceRefused(UNTRACKED_PERSON)
    checked_dates(draft)
    ensure_no_overlap(account, draft)
    return filled(Absence(account=account), draft)


@transaction.atomic
def change_absence(absence_id, draft):
    absence = Absence.objects.select_for_update().exclude(gone("account__")).select_related("account").get(pk=absence_id)
    checked_dates(draft)
    ensure_no_overlap(absence.account, draft, keep=absence.pk)
    return filled(absence, draft)


def remove_absence(absence_id):
    absence = Absence.objects.exclude(gone("account__")).select_related("account").get(pk=absence_id)
    absence.delete()
    return absence


def absences_between(first, last):
    return Absence.objects.filter(first__lte=last, last__gte=first).exclude(gone("account__")).select_related("account")


def absences_by_account(first, last):
    groups = {}
    for absence in absences_between(first, last):
        groups.setdefault(absence.account_id, []).append(absence)
    return groups


def absence_on(absences, day):
    return next((absence for absence in absences if absence.first <= day <= absence.last), None)
