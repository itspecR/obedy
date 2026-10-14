from django.contrib.auth.hashers import make_password

from accounts.models import Source
from accounts.passwords import verify_password
from accounts.throttle import password_check_slot

_DUMMY_HASH = make_password("dummy-password-for-equal-timing")


class VerifierUnavailable(Exception):
    pass


def spend_equal_time(password):
    with password_check_slot():
        verify_password(password, _DUMMY_HASH)


def verify_local(account, password):
    if not account.password_hash:
        spend_equal_time(password)
        return False
    with password_check_slot():
        return verify_password(password, account.password_hash)


_verifiers = {Source.LOCAL: verify_local}
_newcomer_admitters = []


def register_verifier(source, verifier):
    _verifiers[source] = verifier


def register_newcomer_admitter(admitter):
    if admitter not in _newcomer_admitters:
        _newcomer_admitters.append(admitter)


def verify_secret(account, password):
    verifier = _verifiers.get(account.source)
    if verifier is None:
        spend_equal_time(password)
        return False
    return verifier(account, password)


def admit_newcomer(login, password):
    for admitter in _newcomer_admitters:
        account = admitter(login, password)
        if account is not None:
            return account
    if not _newcomer_admitters:
        spend_equal_time(password)
    return None
