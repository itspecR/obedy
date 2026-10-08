import uuid

import pytest
from django.core.management import CommandError, call_command
from django.db import connections
from django.test import Client
from django.utils import timezone
from ldap3 import MODIFY_REPLACE

import directory.authentication as authentication_module
from accounts.models import Account, Role, Session, Source
from directory.connection import DirectoryUnavailable
from directory.models import SyncStatus
from directory.settings_store import save_settings
from directory.sync import LOCK_NAME, SyncBusy, run_sync
from tests.factories import DEFAULT_PASSWORD, make_account
from tests.test_directory import BASE_DN, GROUP_DN, SETTINGS, admin_client, domain, login  # noqa: F401

pytestmark = pytest.mark.django_db

IVANOV_DN = f"CN=Ivanov,{BASE_DN}"
PETROV_DN = f"CN=Petrov,{BASE_DN}"


@pytest.fixture
def directory(domain):  # noqa: F811
    domain.bind()
    return domain


def unreachable_connection(*args, **kwargs):
    raise DirectoryUnavailable


@pytest.fixture
def unreachable(monkeypatch):
    monkeypatch.setattr(authentication_module, "open_connection", unreachable_connection)


@pytest.fixture
def held_lock():
    other = connections.create_connection("default")
    with other.cursor() as cursor:
        cursor.execute("SELECT GET_LOCK(%s, 0)", [LOCK_NAME])
    yield
    with other.cursor() as cursor:
        cursor.execute("SELECT RELEASE_LOCK(%s)", [LOCK_NAME])
    other.close()


def sync():
    return run_sync(timezone.now())


def change(directory, dn, attribute, value):
    directory.modify(dn, {attribute: [(MODIFY_REPLACE, value)]})


def domain_logins():
    return sorted(Account.objects.filter(source=Source.DOMAIN, in_directory=True).values_list("login", flat=True))


def make_domain_account(login):
    return Account.objects.create(login=login, source=Source.DOMAIN, role=Role.EMPLOYEE, external_id=str(uuid.uuid4()))


def test_sync_adds_group_members_including_nested_groups_before_first_login(directory):
    result = sync()

    assert result.status == SyncStatus.DONE
    assert result.message == "Добавлено 2, обновлено 0, отключено 0"
    assert domain_logins() == ["ivanov", "petrov"]
    assert Account.objects.get(login="ivanov").full_name == "Иванов Иван"


def test_repeated_sync_changes_nothing(directory):
    sync()

    assert sync().message == "Добавлено 0, обновлено 0, отключено 0"


def test_sync_updates_changed_profile_and_renamed_login(directory):
    sync()
    change(directory, IVANOV_DN, "displayName", ["Иванов Иван Петрович"])
    change(directory, IVANOV_DN, "sAMAccountName", ["ivanov.ip"])

    result = sync()

    assert result.updated == 1
    assert domain_logins() == ["ivanov.ip", "petrov"]
    assert Account.objects.get(login="ivanov.ip").full_name == "Иванов Иван Петрович"


@pytest.mark.parametrize(("attribute", "value"), [("memberOf", []), ("userAccountControl", [514])])
def test_sync_deactivates_removed_or_disabled_employee_and_closes_sessions(directory, attribute, value):
    assert login(Client(), "petrov").status_code == 200
    change(directory, PETROV_DN, attribute, value)

    result = sync()

    petrov = Account.objects.get(login="petrov")
    assert result.deactivated == 1
    assert petrov.in_directory is False
    assert not Session.objects.filter(account=petrov).exists()
    assert login(Client(), "petrov").status_code == 401


def test_employee_returned_to_group_is_restored(directory):
    sync()
    change(directory, PETROV_DN, "memberOf", [])
    sync()
    change(directory, PETROV_DN, "memberOf", [GROUP_DN])

    result = sync()

    assert result.updated == 1
    assert domain_logins() == ["ivanov", "petrov"]


def test_local_namesake_is_skipped_and_left_untouched(directory):
    make_account(login="ivanov", must_change_password=False)

    result = sync()

    assert result.message == "Добавлено 1, обновлено 0, отключено 0. Пропущено 1: ivanov — логин занят локальной учётной записью"
    assert Account.objects.get(login="ivanov").source == Source.LOCAL


def test_computer_accounts_are_ignored(directory):
    directory.strategy.add_entry(
        f"CN=PC01,{BASE_DN}",
        {
            "objectClass": ["top", "person", "user", "computer"],
            "objectCategory": "computer",
            "sAMAccountName": "PC01$",
            "memberOf": [GROUP_DN],
            "objectGUID": uuid.uuid4().bytes_le,
        },
    )

    sync()

    assert domain_logins() == ["ivanov", "petrov"]


def test_mass_deactivation_is_stopped_and_nothing_changes(directory):
    sync()
    for index in range(6):
        make_domain_account(f"old{index}")
    change(directory, IVANOV_DN, "displayName", ["Новое имя"])

    result = sync()

    assert result.status == SyncStatus.GUARDED
    assert result.message.startswith("Синхронизация отключила бы 6 из 8 сотрудников домена — ничего не изменено")
    assert len(domain_logins()) == 8
    assert Account.objects.get(login="ivanov").full_name == "Иванов Иван"


def test_few_deactivations_pass_the_guard(directory):
    sync()
    for index in range(4):
        make_domain_account(f"old{index}")

    result = sync()

    assert (result.status, result.deactivated) == (SyncStatus.DONE, 4)
    assert domain_logins() == ["ivanov", "petrov"]


def test_disabled_domain_login_skips_sync(directory):
    save_settings({**SETTINGS, "enabled": False})

    result = sync()

    assert result.status == SyncStatus.SKIPPED
    assert result.message == "Вход через домен выключен — синхронизация не выполняется"
    assert domain_logins() == []


def test_unreachable_directory_changes_nothing(directory, monkeypatch):
    sync()
    monkeypatch.setattr(authentication_module, "open_connection", unreachable_connection)

    result = sync()

    assert result.status == SyncStatus.FAILED
    assert result.message.startswith("Контроллер домена не отвечает")
    assert domain_logins() == ["ivanov", "petrov"]


def test_second_sync_waits_for_the_running_one(directory, held_lock):
    with pytest.raises(SyncBusy):
        sync()


def test_admin_runs_sync_and_sees_the_last_report(directory):
    client = admin_client()

    before = client.get("/api/directory/sync").json()
    after = client.post("/api/directory/sync", content_type="application/json").json()

    assert before["status"] is None
    assert (after["status"], after["created"]) == (SyncStatus.DONE, 2)
    assert client.get("/api/directory/sync").json()["message"] == "Добавлено 2, обновлено 0, отключено 0"


def test_busy_sync_is_reported_to_admin(directory, held_lock):
    response = admin_client().post("/api/directory/sync", content_type="application/json")

    assert response.status_code == 409
    assert response.json()["detail"].startswith("Синхронизация уже идёт")


@pytest.mark.parametrize("role", [Role.EMPLOYEE, Role.HR])
def test_only_admin_runs_sync(directory, role):
    make_account(login="worker", role=role, must_change_password=False)
    client = Client()
    login(client, "worker", DEFAULT_PASSWORD)

    assert client.get("/api/directory/sync").status_code == 403
    assert client.post("/api/directory/sync", content_type="application/json").status_code == 403


def test_command_prints_result(directory, capsys):
    call_command("sync_directory")

    assert "Добавлено 2" in capsys.readouterr().out


def test_command_fails_loudly_when_directory_is_down(directory, unreachable):
    with pytest.raises(CommandError, match="Контроллер домена не отвечает"):
        call_command("sync_directory")


def test_sync_keeps_manual_block(directory):
    sync()
    Account.objects.filter(login="ivanov").update(is_active=False)

    sync()

    assert Account.objects.get(login="ivanov").is_active is False
