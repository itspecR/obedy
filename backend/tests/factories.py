from accounts.models import Account, Role, Source
from accounts.passwords import hash_password

DEFAULT_PASSWORD = "correct-horse-battery"


def make_account(login="ivanov.ii", full_name="", role=Role.EMPLOYEE, password=DEFAULT_PASSWORD, must_change_password=True):
    return Account.objects.create(
        login=login,
        full_name=full_name,
        source=Source.LOCAL,
        role=role,
        password_hash=hash_password(password),
        must_change_password=must_change_password,
    )
