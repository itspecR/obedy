from django.db.models import Q, TextChoices

from accounts.models import Account, Source


class StaffStatus(TextChoices):
    ACTIVE = "active", "Активен"
    BLOCKED = "blocked", "Заблокирован"
    GONE = "gone", "Нет в домене"


def gone(prefix=""):
    return Q(**{f"{prefix}source": Source.DOMAIN, f"{prefix}in_directory": False})


def present_accounts():
    return Account.objects.exclude(gone())


def status_of(account):
    if not account.is_active:
        return StaffStatus.BLOCKED
    if account.source == Source.DOMAIN and not account.in_directory:
        return StaffStatus.GONE
    return StaffStatus.ACTIVE
