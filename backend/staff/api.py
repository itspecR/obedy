from datetime import datetime

from ninja import Field, Router, Schema, Status
from ninja.errors import HttpError

from accounts.lunch_policy import can_have_lunch
from accounts.models import Role, Source
from accounts.permissions import require_admin
from accounts.security import session_auth
from staff.changes import ChangeRefused, change_role, set_blocked, set_track_lunch
from staff.local_accounts import InvalidProfile, Profile, create_local_account, reset_local_password, update_local_profile
from staff.status import StaffStatus, present_accounts, status_of

NOT_FOUND = "Сотрудник не найден. Обновите страницу"
LOGIN_LIMIT = 150
TEXT_LIMIT = 255

router = Router(tags=["Сотрудники"])


class StaffOut(Schema):
    id: int
    login: str
    full_name: str
    role: Role
    source: Source
    status: StaffStatus
    track_lunch: bool
    can_track_lunch: bool
    last_login_at: datetime | None


class RoleIn(Schema):
    role: Role


class TrackLunchIn(Schema):
    track_lunch: bool


class BlockedIn(Schema):
    blocked: bool


class ProfileIn(Schema):
    full_name: str = Field(max_length=TEXT_LIMIT)

    def profile(self):
        return Profile(self.full_name)


class LocalAccountIn(ProfileIn):
    login: str = Field(max_length=LOGIN_LIMIT)
    role: Role = Role.EMPLOYEE


class IssuedOut(Schema):
    member: StaffOut
    temporary_password: str


def describe(account):
    return StaffOut(
        id=account.pk,
        login=account.login,
        full_name=account.full_name,
        role=account.role,
        source=account.source,
        status=status_of(account),
        track_lunch=account.track_lunch,
        can_track_lunch=can_have_lunch(account.role),
        last_login_at=account.last_login_at,
    )


@router.get("", auth=session_auth, response=list[StaffOut])
def staff(request):
    require_admin(request)
    return [describe(account) for account in present_accounts().order_by("full_name", "login")]


def target(account_id):
    account = present_accounts().filter(pk=account_id).first()
    if account is None:
        raise HttpError(404, NOT_FOUND)
    return account


def guarded(change):
    try:
        return change()
    except InvalidProfile as invalid:
        raise HttpError(400, invalid.message) from invalid
    except ChangeRefused as refused:
        raise HttpError(409, refused.message) from refused


def applied(change):
    return describe(guarded(change))


def issued(change):
    result = guarded(change)
    return IssuedOut(member=describe(result.account), temporary_password=result.password)


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


@router.post("", auth=session_auth, response={201: IssuedOut})
def create(request, payload: LocalAccountIn):
    require_admin(request)
    return Status(201, issued(lambda: create_local_account(payload.login, payload.profile(), payload.role)))


@router.put("/{account_id}/profile", auth=session_auth, response=StaffOut)
def update_profile(request, account_id: int, payload: ProfileIn):
    require_admin(request)
    return applied(lambda: update_local_profile(target(account_id), payload.profile()))


@router.post("/{account_id}/password", auth=session_auth, response=IssuedOut)
def reset_password(request, account_id: int):
    actor = require_admin(request).account
    return issued(lambda: reset_local_password(actor, target(account_id)))
