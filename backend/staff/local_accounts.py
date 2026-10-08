import re
from dataclasses import dataclass

from django.db import transaction

from accounts.credentials import set_temporary_password
from accounts.lunch_policy import tracks_lunch_by_default
from accounts.models import Account, Source
from accounts.names import normalize_login
from accounts.passwords import hash_password
from accounts.temporary import temporary_password
from staff.changes import ChangeRefused

LOGIN_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{1,63}")

BAD_LOGIN = "Логин: от 2 до 64 символов — латинские буквы, цифры, точка, дефис или подчёркивание, первый символ — буква или цифра"
LOGIN_TAKEN = "Логин {login} уже занят"
NO_NAME = "Укажите ФИО"
DOMAIN_ACCOUNT = "Это доменная учётная запись: её данные и пароль меняются в Active Directory"
OWN_PASSWORD = "Свой пароль меняйте в профиле"


class InvalidProfile(ChangeRefused):
    pass


@dataclass(frozen=True)
class Issued:
    account: Account
    password: str


@dataclass(frozen=True)
class Profile:
    full_name: str

    def cleaned(self):
        cleaned = Profile(self.full_name.strip())
        if not cleaned.full_name:
            raise InvalidProfile(NO_NAME)
        return cleaned


def checked_login(raw_login):
    login = normalize_login(raw_login)
    if not LOGIN_PATTERN.fullmatch(login):
        raise InvalidProfile(BAD_LOGIN)
    if Account.objects.filter(login=login).exists():
        raise ChangeRefused(LOGIN_TAKEN.format(login=login))
    return login


def require_local(account):
    if account.source != Source.LOCAL:
        raise ChangeRefused(DOMAIN_ACCOUNT)


@transaction.atomic
def create_local_account(raw_login, profile, role):
    login = checked_login(raw_login)
    details = profile.cleaned()
    password = temporary_password()
    account = Account.objects.create(
        login=login,
        full_name=details.full_name,
        source=Source.LOCAL,
        role=role,
        track_lunch=tracks_lunch_by_default(role),
        password_hash=hash_password(password),
        must_change_password=True,
    )
    return Issued(account, password)


def update_local_profile(account, profile):
    require_local(account)
    details = profile.cleaned()
    account.full_name = details.full_name
    account.save(update_fields=["full_name"])
    return account


def reset_local_password(actor, account):
    if account.pk == actor.pk:
        raise ChangeRefused(OWN_PASSWORD)
    require_local(account)
    password = temporary_password()
    set_temporary_password(account, password)
    return Issued(account, password)
