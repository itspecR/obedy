from django.db import transaction
from django.db.models import Q

from accounts.lunch_policy import can_have_lunch, tracks_lunch_by_default
from accounts.models import Account, Role, Source
from accounts.sessions import revoke_all_sessions

OWN_ROLE = "Нельзя снять роль администратора с себя. Попросите об этом другого администратора"
OWN_BLOCK = "Нельзя заблокировать себя"
ADMIN_LUNCH = "Администратор обеды не отмечает. Чтобы учитывать обеды, назначьте другую роль"
LAST_ADMIN = "Нельзя: это последний активный администратор. Сначала назначьте администратором кого-то ещё"


class ChangeRefused(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def active_admins():
    working = Q(source=Source.LOCAL) | Q(in_directory=True)
    return Account.objects.select_for_update().filter(working, role=Role.ADMIN, is_active=True)


def ensure_other_admin_remains(account):
    if not active_admins().exclude(pk=account.pk).exists():
        raise ChangeRefused(LAST_ADMIN)


def leaves_admins(account):
    return account.role == Role.ADMIN and account.is_active


@transaction.atomic
def change_role(actor, account, role):
    if account.role == role:
        return account
    if account.pk == actor.pk:
        raise ChangeRefused(OWN_ROLE)
    if leaves_admins(account):
        ensure_other_admin_remains(account)
    account.role = role
    account.track_lunch = tracks_lunch_by_default(role)
    account.save(update_fields=["role", "track_lunch"])
    return account


def set_track_lunch(account, track_lunch):
    if track_lunch and not can_have_lunch(account.role):
        raise ChangeRefused(ADMIN_LUNCH)
    account.track_lunch = track_lunch
    account.save(update_fields=["track_lunch"])
    return account


@transaction.atomic
def set_blocked(actor, account, blocked):
    if blocked and account.pk == actor.pk:
        raise ChangeRefused(OWN_BLOCK)
    if blocked and leaves_admins(account):
        ensure_other_admin_remains(account)
    account.is_active = not blocked
    account.save(update_fields=["is_active"])
    if blocked:
        revoke_all_sessions(account)
    return account
