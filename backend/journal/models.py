from django.db import models
from django.utils import timezone

from accounts.models import Account

ADDRESS_LIMIT = 45


class Action(models.TextChoices):
    LOGIN = "login", "Вход"
    LOGIN_FAILED = "login_failed", "Неудачный вход"
    LOGOUT = "logout", "Выход"
    PASSWORD_CHANGED = "password_changed", "Сменил свой пароль"
    ROLE_CHANGED = "role_changed", "Изменена роль"
    TRACK_LUNCH_CHANGED = "track_lunch_changed", "Изменён учёт обеда"
    BLOCKED = "blocked", "Заблокирован"
    UNBLOCKED = "unblocked", "Разблокирован"
    ACCOUNT_CREATED = "account_created", "Создана учётная запись"
    PROFILE_CHANGED = "profile_changed", "Изменено ФИО"
    PASSWORD_ISSUED = "password_issued", "Выдан временный пароль"
    LUNCH_CORRECTED = "lunch_corrected", "Исправлен обед"
    LUNCH_ADDED = "lunch_added", "Добавлен обед"
    LUNCH_DELETED = "lunch_deleted", "Удалён обед"
    LUNCHES_RESET = "lunches_reset", "Обеды сброшены"
    RULES_CHANGED = "rules_changed", "Изменены правила обеда"
    NETWORK_ADDED = "network_added", "Добавлен адрес доступа"
    NETWORK_REMOVED = "network_removed", "Удалён адрес доступа"
    PRIVATE_NETWORKS_CHANGED = "private_networks_changed", "Изменён доступ из локальной сети"
    DIRECTORY_CHANGED = "directory_changed", "Изменены настройки домена"
    DIRECTORY_CHECKED = "directory_checked", "Проверка связи с доменом"
    DIRECTORY_SYNCED = "directory_synced", "Синхронизация с доменом"


class Category(models.TextChoices):
    LOGINS = "logins", "Входы"
    STAFF = "staff", "Сотрудники"
    LUNCHES = "lunches", "Обеды"
    SETTINGS = "settings", "Настройки"


CATEGORY_ACTIONS = {
    Category.LOGINS: (Action.LOGIN, Action.LOGIN_FAILED, Action.LOGOUT, Action.PASSWORD_CHANGED),
    Category.STAFF: (
        Action.ROLE_CHANGED,
        Action.TRACK_LUNCH_CHANGED,
        Action.BLOCKED,
        Action.UNBLOCKED,
        Action.ACCOUNT_CREATED,
        Action.PROFILE_CHANGED,
        Action.PASSWORD_ISSUED,
    ),
    Category.LUNCHES: (Action.LUNCH_CORRECTED, Action.LUNCH_ADDED, Action.LUNCH_DELETED, Action.LUNCHES_RESET),
    Category.SETTINGS: (
        Action.RULES_CHANGED,
        Action.NETWORK_ADDED,
        Action.NETWORK_REMOVED,
        Action.PRIVATE_NETWORKS_CHANGED,
        Action.DIRECTORY_CHANGED,
        Action.DIRECTORY_CHECKED,
        Action.DIRECTORY_SYNCED,
    ),
}


class JournalEntry(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    action = models.CharField(max_length=32, choices=Action.choices)
    actor = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    target = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    address = models.CharField(max_length=ADDRESS_LIMIT, blank=True)
    details = models.JSONField(default=list)

    class Meta:
        indexes = [models.Index(fields=["created_at"]), models.Index(fields=["action", "created_at"])]
