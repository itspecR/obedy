import io

import pytest
from django.core.management import CommandError, call_command
from django.utils import timezone

from accounts.devices import find_known_device, remember_device
from accounts.models import Account, Role, Source
from accounts.passwords import verify_password
from tests.factories import make_account

pytestmark = pytest.mark.django_db


def run(*args):
    out = io.StringIO()
    call_command(*args, stdout=out)
    return out.getvalue()


def password_from(text):
    return next(line.split(": ", 1)[1] for line in text.splitlines() if line.startswith("Временный пароль"))


def test_create_admin_makes_local_admin_once():
    text = run("create_admin")
    account = Account.objects.get(login="admin")

    assert account.role == Role.ADMIN and account.source == Source.LOCAL
    assert account.must_change_password and verify_password(password_from(text), account.password_hash)
    with pytest.raises(CommandError, match="Администратор уже есть"):
        run("create_admin")


def test_create_admin_refuses_taken_login():
    make_account(login="admin")

    with pytest.raises(CommandError, match="уже занят"):
        run("create_admin")


def test_reset_password_issues_new_temporary_password_and_ends_sessions():
    account = make_account(login="orlov.oo", must_change_password=False)
    device = remember_device(account, timezone.now())

    text = run("reset_password", " Orlov.OO ")
    account.refresh_from_db()

    assert account.must_change_password and verify_password(password_from(text), account.password_hash)
    assert find_known_device(account, device, timezone.now()) is None


def test_reset_password_rejects_unknown_and_domain_accounts():
    make_account(login="domain.user")
    Account.objects.filter(login="domain.user").update(source=Source.DOMAIN)

    with pytest.raises(CommandError, match="не найдена"):
        run("reset_password", "nobody")
    with pytest.raises(CommandError, match="Active Directory"):
        run("reset_password", "domain.user")
