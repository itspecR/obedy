from django.db.models import TextChoices

from accounts.models import Source


class StaffStatus(TextChoices):
    ACTIVE = "active", "Активен"
    BLOCKED = "blocked", "Заблокирован"
    GONE = "gone", "Нет в домене"


def status_of(account):
    if not account.is_active:
        return StaffStatus.BLOCKED
    if account.source == Source.DOMAIN and not account.in_directory:
        return StaffStatus.GONE
    return StaffStatus.ACTIVE
