from datetime import datetime

from ninja import Router, Schema
from ninja.errors import HttpError

from accounts.models import Account, Role, Source
from accounts.permissions import require_admin
from accounts.security import session_auth
from staff.changes import ChangeRefused, change_role, set_blocked, set_track_lunch
from staff.status import StaffStatus, status_of

NOT_FOUND = "Сотрудник не найден. Обновите страницу"

router = Router(tags=["Сотрудники"])


class StaffOut(Schema):
    id: int
    login: str
    full_name: str
    department: str
    position: str
    role: Role
    source: Source
    status: StaffStatus
    track_lunch: bool
    last_login_at: datetime | None


class RoleIn(Schema):
    role: Role


class TrackLunchIn(Schema):
    track_lunch: bool


class BlockedIn(Schema):
    blocked: bool


def describe(account):
    return StaffOut(
        id=account.pk,
        login=account.login,
        full_name=account.full_name,
        department=account.department,
        position=account.position,
        role=account.role,
        source=account.source,
        status=status_of(account),
        track_lunch=account.track_lunch,
        last_login_at=account.last_login_at,
    )


@router.get("", auth=session_auth, response=list[StaffOut])
def staff(request):
    require_admin(request)
    return [describe(account) for account in Account.objects.order_by("full_name", "login")]


def target(account_id):
    account = Account.objects.filter(pk=account_id).first()
    if account is None:
        raise HttpError(404, NOT_FOUND)
    return account


def applied(change):
    try:
        return describe(change())
    except ChangeRefused as refused:
        raise HttpError(409, refused.message) from refused


@router.put("/{account_id}/role", auth=session_auth, response=StaffOut)
def update_role(request, account_id: int, payload: RoleIn):
    actor = require_admin(request).account
    return applied(lambda: change_role(actor, target(account_id), payload.role))


@router.put("/{account_id}/track-lunch", auth=session_auth, response=StaffOut)
def update_track_lunch(request, account_id: int, payload: TrackLunchIn):
    require_admin(request)
    return applied(lambda: set_track_lunch(target(account_id), payload.track_lunch))


@router.put("/{account_id}/blocked", auth=session_auth, response=StaffOut)
def update_blocked(request, account_id: int, payload: BlockedIn):
    actor = require_admin(request).account
    return applied(lambda: set_blocked(actor, target(account_id), payload.blocked))
