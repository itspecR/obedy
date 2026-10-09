import hashlib

from accounts.models import Role
from directory.models import Mode
from lunches.clock import clock_text, local

ON = "включено"
OFF = "выключено"
OPEN = "открыт"
CLOSED = "заблокирован"
EMPTY = "—"
DEFAULT_PORT = "по умолчанию"
FINGERPRINT_LENGTH = 12
WEEKDAY_NAMES = {"1": "Пн", "2": "Вт", "3": "Ср", "4": "Чт", "5": "Пт", "6": "Сб", "7": "Вс"}
DAY_FORMAT = "%d.%m.%Y"


def switch(value):
    return ON if value else OFF


def text(value):
    return value or EMPTY


def day_text(day):
    return day.strftime(DAY_FORMAT)


def moment_text(moment):
    return clock_text(local(moment)) if moment else EMPTY


def fingerprint(certificate):
    return hashlib.sha256(certificate.encode()).hexdigest()[:FINGERPRINT_LENGTH] if certificate else EMPTY


def account_snapshot(account):
    return {
        "ФИО": text(account.full_name),
        "Роль": Role(account.role).label,
        "Учёт обеда": switch(account.track_lunch),
        "Доступ": OPEN if account.is_active else CLOSED,
    }


def created_account_snapshot(account):
    return {"Логин": account.login, **account_snapshot(account)}


def lunch_snapshot(lunch):
    return {"Ушёл": moment_text(lunch.started_at), "Вернулся": moment_text(lunch.ended_at)}


def rules_snapshot(rules):
    return {
        "Лимит обеда": f"{rules.limit_minutes} мин",
        "Рабочие дни": ", ".join(WEEKDAY_NAMES[day] for day in rules.workdays),
        "Конец рабочего дня": clock_text(rules.day_end),
        "Окно обеда": switch(rules.window_enabled),
        "Окно с": clock_text(rules.window_start),
        "Окно до": clock_text(rules.window_end),
    }


def directory_snapshot(stored):
    return {
        "Вход через домен": switch(stored.enabled),
        "Серверы": text(stored.servers),
        "Подключение": Mode(stored.mode).label,
        "Порт": str(stored.port) if stored.port else DEFAULT_PORT,
        "Сертификат домена": fingerprint(stored.ca_certificate),
        "Учётная запись для чтения": text(stored.bind_user),
        "Где искать": text(stored.base_dn),
        "Группа сотрудников": text(stored.group_dn),
        "Срок входа": f"{stored.session_days} дн.",
    }


def network_snapshot(network):
    snapshot = {"Адрес": network.network}
    return {**snapshot, "Заметка": network.note} if network.note else snapshot


def private_snapshot(enabled):
    return {"Вся локальная сеть": switch(enabled)}
