from django.db.models import F

from accounts.devices import forget_all_devices
from accounts.login import AccountLocked, is_locked, register_account_failure
from accounts.models import Account, Source
from accounts.password_policy import check_password_rules, password_problem, personal_words
from accounts.passwords import hash_password, verify_password
from accounts.sessions import revoke_all_sessions, revoke_other_sessions
from accounts.throttle import password_check_slot


class SamePassword(Exception):
    pass


class WrongCurrentPassword(Exception):
    pass


class DomainPassword(Exception):
    pass


def set_temporary_password(account, raw_password):
    account.password_hash = hash_password(raw_password)
    account.must_change_password = True
    account.weak_password = False
    account.failed_count = 0
    account.locked_until = None
    account.save(update_fields=["password_hash", "must_change_password", "weak_password", "failed_count", "locked_until"])
    bump_version(account)
    revoke_all_sessions(account)
    forget_all_devices(account)


def change_own_password(account, new_password, keep_session_token, current_password, now):
    if account.source != Source.LOCAL:
        raise DomainPassword
    if not issued_temporarily(account):
        confirm_current_password(account, current_password, now)
    check_password_rules(new_password, personal_words(account))
    with password_check_slot():
        if verify_password(new_password, account.password_hash):
            raise SamePassword
    account.password_hash = hash_password(new_password)
    account.must_change_password = False
    account.weak_password = False
    account.failed_count = 0
    account.locked_until = None
    account.save(update_fields=["password_hash", "must_change_password", "weak_password", "failed_count", "locked_until"])
    revoke_other_sessions(account, keep_session_token)
    forget_all_devices(account)


def issued_temporarily(account):
    return account.must_change_password and not account.weak_password


def bump_version(account):
    Account.objects.filter(pk=account.pk).update(version=F("version") + 1)
    account.refresh_from_db(fields=["version"])


def confirm_current_password(account, current_password, now):
    if is_locked(account, now):
        raise AccountLocked
    with password_check_slot():
        matches = verify_password(current_password or "", account.password_hash)
    if matches:
        Account.objects.filter(pk=account.pk).update(failed_count=0)
        return
    if register_account_failure(account, now):
        raise AccountLocked
    raise WrongCurrentPassword


def flag_weak_password(account, raw_password):
    if account.source != Source.LOCAL or account.must_change_password:
        return
    if password_problem(raw_password, personal_words(account)) is None:
        return
    Account.objects.filter(pk=account.pk).update(must_change_password=True, weak_password=True)
    account.must_change_password = True
    account.weak_password = True
