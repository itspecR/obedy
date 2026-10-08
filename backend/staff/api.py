from datetime import datetime

from ninja import Router, Schema

from accounts.models import Account, Role, Source
from accounts.permissions import require_admin
from accounts.security import session_auth
from staff.status import StaffStatus, status_of

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
