from dataclasses import asdict
from datetime import date, datetime, time, timedelta

from django.db.models import Q
from ninja import Router, Schema
from ninja.errors import HttpError

from accounts.permissions import require_admin
from accounts.security import session_auth
from journal.models import CATEGORY_ACTIONS, Action, Category, JournalEntry
from journal.system import system_info
from lunches.board_api import PersonOut, describe_person
from lunches.clock import moment_of
from lunches.statistics import BAD_ORDER
from staff.status import present_accounts

PAGE_SIZE = 50

router = Router(tags=["Журнал"])


class RowOut(Schema):
    label: str
    before: str | None = None
    after: str | None = None


class EntryOut(Schema):
    id: int
    created_at: datetime
    action: Action
    actor: PersonOut | None
    target: PersonOut | None
    address: str
    details: list[RowOut]


class SystemOut(Schema):
    release: str
    site_started_at: datetime | None
    db_started_at: datetime | None
    last_backup_at: datetime | None
    os_name: str
    os_source: str
    memory_total: int | None
    memory_used: int | None
    app_memory_used: int | None
    app_memory_limit: int | None


class JournalOut(Schema):
    entries: list[EntryOut]
    has_more: bool


def describe_optional(account):
    return describe_person(account) if account else None


def describe_entry(entry):
    return EntryOut(
        id=entry.pk,
        created_at=entry.created_at,
        action=entry.action,
        actor=describe_optional(entry.actor),
        target=describe_optional(entry.target),
        address=entry.address,
        details=entry.details,
    )


def start_of(day):
    return moment_of(day, time.min)


def period_entries(date_from, date_to):
    if date_from > date_to:
        raise HttpError(400, BAD_ORDER)
    return JournalEntry.objects.filter(created_at__gte=start_of(date_from), created_at__lt=start_of(date_to + timedelta(days=1)))


def filtered(entries, person, category, before):
    if person is not None:
        entries = entries.filter(Q(actor_id=person) | Q(target_id=person))
    if category is not None:
        entries = entries.filter(action__in=CATEGORY_ACTIONS[category])
    if before is not None:
        entries = entries.filter(pk__lt=before)
    return entries


@router.get("", auth=session_auth, response=JournalOut)
def journal(request, date_from: date, date_to: date, person: int | None = None, category: Category | None = None, before: int | None = None):
    require_admin(request)
    entries = filtered(period_entries(date_from, date_to), person, category, before)
    page = list(entries.select_related("actor", "target").order_by("-pk")[: PAGE_SIZE + 1])
    return JournalOut(entries=[describe_entry(entry) for entry in page[:PAGE_SIZE]], has_more=len(page) > PAGE_SIZE)


@router.get("/people", auth=session_auth, response=list[PersonOut])
def people(request):
    require_admin(request)
    return [describe_person(account) for account in present_accounts().order_by("full_name", "login")]


@router.get("/system", auth=session_auth, response=SystemOut)
def system(request):
    require_admin(request)
    return SystemOut(**asdict(system_info()))
