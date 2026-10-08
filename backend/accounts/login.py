from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.db.models import F

from accounts.devices import find_known_device, remember_device
from accounts.models import Account, KnownDevice
from accounts.names import normalize_login
from accounts.sessions import create_session
from accounts.verification import admit_newcomer, spend_equal_time, verify_secret

MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION = timedelta(minutes=15)


class LoginFailed(Exception):
    pass


class InvalidCredentials(LoginFailed):
    pass


class AccountLocked(LoginFailed):
    pass


@dataclass
class LoginResult:
    account: Account
    session_token: str
    device_token: str | None


def authenticate(raw_login, password, device_token, now):
    login = normalize_login(raw_login)
    account = Account.objects.filter(login=login).first()
    if account is None:
        return _admit(login, password, now)
    if not account.is_active:
        spend_equal_time(password)
        raise InvalidCredentials
    device = find_known_device(account, device_token, now) if device_token else None
    if device is None and is_locked(account, now):
        spend_equal_time(password)
        raise InvalidCredentials
    if not verify_secret(account, password):
        _register_failure(account, device, now)
    return _complete_login(account, device, now)


def _admit(login, password, now):
    account = admit_newcomer(login, password)
    if account is None:
        raise InvalidCredentials
    return _complete_login(account, None, now)


def is_locked(account, now):
    return account.locked_until is not None and account.locked_until > now


def _register_failure(account, device, now):
    if device is not None:
        _register_device_failure(device)
        raise InvalidCredentials
    register_account_failure(account, now)
    raise InvalidCredentials


def _register_device_failure(device):
    KnownDevice.objects.filter(pk=device.pk).update(failed_count=F("failed_count") + 1)
    device.refresh_from_db(fields=["failed_count"])
    if device.failed_count >= MAX_FAILED_ATTEMPTS:
        device.delete()


@transaction.atomic
def register_account_failure(account, now):
    current = Account.objects.select_for_update().get(pk=account.pk)
    current.failed_count += 1
    if current.failed_count >= MAX_FAILED_ATTEMPTS:
        current.failed_count = 0
        current.locked_until = now + LOCK_DURATION
    current.save(update_fields=["failed_count", "locked_until"])
    return current.locked_until is not None and current.locked_until > now


def _complete_login(account, device, now):
    Account.objects.filter(pk=account.pk).update(failed_count=0, locked_until=None, last_login_at=now)
    session_token = create_session(account, now)
    if device is not None:
        KnownDevice.objects.filter(pk=device.pk).update(failed_count=0)
        return LoginResult(account, session_token, None)
    return LoginResult(account, session_token, remember_device(account, now))
