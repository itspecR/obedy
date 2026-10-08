from django.contrib.auth.hashers import make_password

from accounts.models import Source
from accounts.passwords import verify_password
from accounts.throttle import password_check_slot

_DUMMY_HASH = make_password("dummy-password-for-equal-timing")


def spend_equal_time(password):
    with password_check_slot():
        verify_password(password, _DUMMY_HASH)


def verify_local(account, password):
    if not account.password_hash:
        spend_equal_time(password)
        return False
    with password_check_slot():
        return verify_password(password, account.password_hash)


VERIFIERS = {
    Source.LOCAL: verify_local,
}


def verify_secret(account, password):
    verifier = VERIFIERS.get(account.source)
    if verifier is None:
        spend_equal_time(password)
        return False
    return verifier(account, password)
