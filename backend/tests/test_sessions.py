import io
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from accounts.devices import find_known_device, remember_device
from accounts.lifetimes import LOCAL_SESSION_LIFETIME
from accounts.models import Account, KnownDevice, Session
from accounts.sessions import (
    create_session,
    find_active_session,
    revoke_all_sessions,
    revoke_other_sessions,
    revoke_session,
)
from accounts.tokens import hash_token
from tests.factories import make_account

pytestmark = pytest.mark.django_db


@pytest.fixture
def now():
    return timezone.now()


@pytest.fixture
def account():
    return make_account()


def test_only_token_hash_is_stored(account, now):
    token = create_session(account, now)

    assert Session.objects.get().token_hash == hash_token(token)
    assert not Session.objects.filter(token_hash=token).exists()


def test_session_expires_after_its_lifetime(account, now):
    token = create_session(account, now)

    assert find_active_session(token, now + LOCAL_SESSION_LIFETIME - timedelta(seconds=1)) is not None
    assert find_active_session(token, now + LOCAL_SESSION_LIFETIME) is None


def test_unknown_token_finds_nothing(account, now):
    create_session(account, now)

    assert find_active_session("unknown-token", now) is None


def test_version_bump_invalidates_session(account, now):
    token = create_session(account, now)
    Account.objects.update(version=account.version + 1)

    assert find_active_session(token, now) is None


def test_revoke_variants(account, now):
    first = create_session(account, now)
    second = create_session(account, now)
    third = create_session(account, now)

    revoke_session(first)
    assert find_active_session(first, now) is None
    revoke_other_sessions(account, second)
    assert find_active_session(second, now) is not None
    assert find_active_session(third, now) is None
    revoke_all_sessions(account)
    assert Session.objects.count() == 0


def test_device_token_is_stored_only_as_hash_and_tied_to_account(account, now):
    other = make_account(login="petrov.pp")
    token = remember_device(account, now)

    assert KnownDevice.objects.get().token_hash == hash_token(token)
    assert find_known_device(account, token, now) is not None
    assert find_known_device(other, token, now) is None


def test_device_expires_after_a_year(account, now):
    token = remember_device(account, now)

    assert find_known_device(account, token, now + timedelta(days=364)) is not None
    assert find_known_device(account, token, now + timedelta(days=365)) is None


def test_clean_sessions_removes_only_expired(account, now):
    create_session(account, now)
    Session.objects.create(token_hash="old", account=account, account_version=1, expires_at=now - timedelta(minutes=1))
    KnownDevice.objects.create(token_hash="old", account=account, expires_at=now - timedelta(minutes=1))
    out = io.StringIO()

    call_command("clean_sessions", stdout=out)

    assert Session.objects.count() == 1
    assert KnownDevice.objects.count() == 0
    assert "Удалено сессий: 1, устройств: 1" in out.getvalue()
