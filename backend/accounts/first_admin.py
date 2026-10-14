from django.db import transaction

from accounts.lunch_policy import tracks_lunch_by_default
from accounts.models import Account, Role, Source
from accounts.names import normalize_login
from accounts.passwords import hash_password
from accounts.temporary import temporary_password
from journal.entries import differences, record_server
from journal.models import Action
from journal.snapshots import created_account_snapshot

ADMIN_NAME = "Администратор"
DEFAULT_LOGIN = "admin"


class AdminExists(Exception):
    def __init__(self, login):
        super().__init__(login)
        self.login = login


class LoginTaken(Exception):
    pass


def existing_admin():
    return Account.objects.filter(source=Source.LOCAL, role=Role.ADMIN).first()


@transaction.atomic
def create_first_admin(raw_login=DEFAULT_LOGIN):
    existing = existing_admin()
    if existing is not None:
        raise AdminExists(existing.login)
    login = normalize_login(raw_login)
    if Account.objects.filter(login=login).exists():
        raise LoginTaken(login)
    password = temporary_password()
    account = Account.objects.create(
        login=login,
        full_name=ADMIN_NAME,
        source=Source.LOCAL,
        role=Role.ADMIN,
        password_hash=hash_password(password),
        must_change_password=True,
        track_lunch=tracks_lunch_by_default(Role.ADMIN),
    )
    record_server(Action.ACCOUNT_CREATED, account, differences({}, created_account_snapshot(account)))
    return account, password
