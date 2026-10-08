import json
import uuid
from datetime import timedelta

import pytest
from django.test import Client, override_settings
from django.utils import timezone
from ldap3 import MOCK_SYNC, Connection, Server
from ldap3.core.exceptions import LDAPSocketOpenError, LDAPStartTLSError

import directory.connection as connection_module
from accounts.models import Account, Role, Source
from directory.config import current_config, stored_settings
from directory.connection import DirectoryUnavailable
from directory.settings_store import save_settings
from directory.vault import seal, unseal
from tests.factories import DEFAULT_PASSWORD, make_account

pytestmark = pytest.mark.django_db

SERVICE_DN = "CN=svc-obedy,OU=Service,DC=co,DC=local"
SERVICE_PASSWORD = "service-secret-1"
BASE_DN = "OU=Staff,DC=co,DC=local"
GROUP_DN = "CN=Obedy,OU=Groups,DC=co,DC=local"
INNER_GROUP_DN = "CN=Kitchen,OU=Groups,DC=co,DC=local"
USER_PASSWORD = "windows-password-1"
IVANOV_GUID = uuid.UUID("11111111-2222-3333-4444-555555555555")

SETTINGS = {
    "enabled": True,
    "servers": "dc1.co.local, dc2.co.local",
    "mode": "plain",
    "port": None,
    "ca_certificate": "",
    "bind_user": SERVICE_DN,
    "bind_password": SERVICE_PASSWORD,
    "base_dn": BASE_DN,
    "group_dn": GROUP_DN,
    "session_days": 30,
}


def person(login, full_name, groups, guid=None, flags=512, department="Бухгалтерия", title="Бухгалтер"):
    return {
        "objectClass": ["top", "person", "user"],
        "sAMAccountName": login,
        "displayName": full_name,
        "department": department,
        "title": title,
        "userAccountControl": flags,
        "memberOf": groups,
        "objectGUID": (guid or uuid.uuid4()).bytes_le,
        "userPassword": USER_PASSWORD,
    }


@pytest.fixture
def domain(monkeypatch):
    server = Server("mock-dc")
    seed = Connection(server, user=SERVICE_DN, password=SERVICE_PASSWORD, client_strategy=MOCK_SYNC)
    seed.strategy.add_entry(SERVICE_DN, {"objectClass": ["user"], "userPassword": SERVICE_PASSWORD})
    seed.strategy.add_entry(GROUP_DN, {"objectClass": ["group"], "cn": "Obedy"})
    seed.strategy.add_entry(INNER_GROUP_DN, {"objectClass": ["group"], "cn": "Kitchen", "memberOf": [GROUP_DN]})
    seed.strategy.add_entry(f"CN=Ivanov,{BASE_DN}", person("Ivanov", "Иванов Иван", [GROUP_DN], guid=IVANOV_GUID))
    seed.strategy.add_entry(f"CN=Petrov,{BASE_DN}", person("petrov", "Петров Пётр", [INNER_GROUP_DN]))
    seed.strategy.add_entry(f"CN=Sidorov,{BASE_DN}", person("sidorov", "Сидоров Сидор", []))
    seed.strategy.add_entry(f"CN=Blocked,{BASE_DN}", person("blocked", "Отключённый", [GROUP_DN], flags=514))
    monkeypatch.setattr(connection_module, "STRATEGY", MOCK_SYNC)
    monkeypatch.setattr(connection_module, "server_for", lambda config: server)
    save_settings(SETTINGS)
    return seed


def login(client, name, password=USER_PASSWORD):
    return client.post("/api/auth/login", json.dumps({"login": name, "password": password}), content_type="application/json")


def admin_client():
    make_account(login="boss", role=Role.ADMIN, must_change_password=False)
    client = Client()
    login(client, "boss", DEFAULT_PASSWORD)
    return client


def put_settings(client, **changes):
    return client.put("/api/directory", json.dumps({**SETTINGS, **changes}), content_type="application/json")


def test_first_login_creates_domain_employee(domain):
    response = login(Client(), "ivanov")

    account = Account.objects.get(login="ivanov")
    assert response.status_code == 200
    assert response.json()["display_name"] == "Иванов Иван"
    assert response.json()["source"] == Source.DOMAIN
    assert (account.role, account.department, account.position) == (Role.EMPLOYEE, "Бухгалтерия", "Бухгалтер")
    assert account.external_id == str(IVANOV_GUID)
    assert account.password_hash == ""


@pytest.mark.parametrize("name", ["ivanov", "IVANOV", "CO\\ivanov", "ivanov@co.local", "  Ivanov@CO.local "])
def test_any_login_form_reaches_the_same_employee(domain, name):
    assert login(Client(), name).status_code == 200
    assert Account.objects.filter(source=Source.DOMAIN).count() == 1


def test_nested_group_member_can_log_in(domain):
    assert login(Client(), "petrov").status_code == 200


@pytest.mark.parametrize(
    ("name", "password"),
    [("ivanov", "wrong-password-1"), ("sidorov", USER_PASSWORD), ("blocked", USER_PASSWORD), ("nobody", USER_PASSWORD), ("*", USER_PASSWORD), ("ivanov", "")],
)
def test_rejected_logins_look_the_same_and_create_nothing(domain, name, password):
    response = login(Client(), name, password)

    assert response.status_code == 401
    assert response.json()["detail"].startswith("Неверный логин или пароль")
    assert not Account.objects.filter(source=Source.DOMAIN).exists()


def test_domain_session_lasts_configured_days(domain):
    save_settings({**SETTINGS, "session_days": 7})

    login(Client(), "ivanov")

    expires = Account.objects.get(login="ivanov").sessions.get().expires_at
    assert timezone.now() + timedelta(days=6, hours=23) < expires < timezone.now() + timedelta(days=7, minutes=1)


def test_second_login_refreshes_profile_from_directory(domain):
    login(Client(), "ivanov")
    Account.objects.filter(login="ivanov").update(full_name="Старое имя", department="")

    login(Client(), "ivanov")

    account = Account.objects.get(login="ivanov")
    assert (account.full_name, account.department) == ("Иванов Иван", "Бухгалтерия")


def test_wrong_domain_passwords_lock_known_account(domain):
    login(Client(), "ivanov")
    statuses = [login(Client(), "ivanov", "wrong-password-1").status_code for _ in range(6)]

    assert statuses == [401] * 6
    assert Account.objects.get(login="ivanov").locked_until is not None


def test_unreachable_directory_reports_it_and_keeps_local_admin_working(domain, monkeypatch):
    def unreachable(*args, **kwargs):
        raise DirectoryUnavailable

    monkeypatch.setattr("directory.authentication.open_connection", unreachable)
    make_account(login="admin", role=Role.ADMIN, must_change_password=False)

    newcomer = login(Client(), "ivanov")
    local = login(Client(), "admin", DEFAULT_PASSWORD)

    assert newcomer.status_code == 503
    assert newcomer.json()["detail"].startswith("Домен сейчас недоступен")
    assert local.status_code == 200


def test_disabled_directory_login_is_ignored(domain):
    save_settings({**SETTINGS, "enabled": False})

    assert login(Client(), "ivanov").status_code == 401


def test_local_account_wins_over_domain_namesake(domain):
    make_account(login="ivanov", must_change_password=False)

    assert login(Client(), "ivanov", USER_PASSWORD).status_code == 401
    assert login(Client(), "ivanov", DEFAULT_PASSWORD).json()["source"] == Source.LOCAL


def test_bind_password_is_encrypted_and_tied_to_secret_key():
    token = seal("service-secret-1")

    assert "service-secret-1" not in token
    assert unseal(token) == "service-secret-1"
    with override_settings(SECRET_KEY="another-key"):
        assert unseal(token) == ""


def test_admin_reads_settings_without_password(domain):
    body = admin_client().get("/api/directory").json()

    assert body["has_bind_password"] is True
    assert "bind_password" not in body
    assert body["servers"] == "dc1.co.local dc2.co.local"
    assert body["mode"] == "plain"


def test_blank_password_keeps_the_stored_one(domain):
    client = admin_client()

    response = put_settings(client, bind_password="", session_days=14)

    assert response.status_code == 200
    assert current_config().bind_password == SERVICE_PASSWORD
    assert current_config().session_days == 14


def test_enabling_requires_essential_fields():
    response = put_settings(admin_client(), servers=" ", base_dn="", bind_password="")

    assert response.status_code == 400
    assert response.json()["detail"] == "Чтобы включить вход через домен, заполните: серверы, пароль сервисной учётной записи, база поиска"


def test_incomplete_settings_can_be_saved_while_disabled():
    response = put_settings(admin_client(), enabled=False, servers="", base_dn="", bind_password="")

    assert response.status_code == 200
    assert stored_settings().enabled is False


def test_invalid_certificate_is_rejected(domain):
    response = put_settings(admin_client(), ca_certificate="-----BEGIN CERTIFICATE-----\nnot-a-cert\n-----END CERTIFICATE-----")

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Сертификат не распознан")


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({}, "Подключение работает. Найдено учётных записей: 4"),
        ({"base_dn": "OU=Empty,DC=co,DC=local"}, "Подключение есть, но в базе поиска нет учётных записей. Проверьте поле «База поиска»"),
        ({"group_dn": "CN=Missing,DC=co,DC=local"}, "Подключение есть, но группа не найдена. Проверьте поле «Группа доступа»"),
        ({"bind_password": "wrong-service-password"}, "Контроллер отклонил сервисную учётную запись: проверьте её логин и пароль"),
    ],
)
def test_connection_check_explains_the_result(domain, changes, message):
    client = admin_client()
    put_settings(client, **changes)

    body = client.post("/api/directory/check", content_type="application/json").json()

    assert body["message"] == message
    assert body["ok"] is (not changes)


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        (
            LDAPSocketOpenError("socket ssl wrapping error: certificate doesn't match any name in ['192.168.0.252']"),
            "Контроллер ответил, но его сертификат не подошёл. Укажите контроллеры полными именами, как в их сертификатах "
            "(не IP), и вставьте корневой сертификат вашего центра сертификации",
        ),
        (
            LDAPStartTLSError("wrap socket error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed"),
            "Контроллер ответил, но его сертификат не подошёл. Укажите контроллеры полными именами, как в их сертификатах "
            "(не IP), и вставьте корневой сертификат вашего центра сертификации",
        ),
        (
            LDAPSocketOpenError("unable to open socket"),
            "Контроллер домена не отвечает или не принимает соединение. Проверьте адрес, порт, режим и сертификат",
        ),
    ],
)
def test_connection_check_tells_certificate_problems_apart(domain, monkeypatch, failure, message):
    def failing(connection):
        raise failure

    monkeypatch.setattr(connection_module, "bind", failing)

    body = admin_client().post("/api/directory/check", content_type="application/json").json()

    assert body == {"ok": False, "message": message}


def test_certificate_problem_on_login_is_reported_as_unavailable_domain(domain, monkeypatch):
    def failing(connection):
        raise LDAPSocketOpenError("socket ssl wrapping error: certificate verify failed")

    monkeypatch.setattr(connection_module, "bind", failing)

    response = login(Client(), "ivanov")

    assert response.status_code == 503
    assert response.json()["detail"].startswith("Домен сейчас недоступен")


@pytest.mark.parametrize("role", [Role.EMPLOYEE, Role.HR])
def test_only_admin_manages_directory(role):
    make_account(login="worker", role=role, must_change_password=False)
    client = Client()
    login(client, "worker", DEFAULT_PASSWORD)

    assert client.get("/api/directory").status_code == 403
    assert put_settings(client).status_code == 403
    assert client.post("/api/directory/check", content_type="application/json").status_code == 403


def test_public_status_tells_login_page_whether_domain_is_on(domain):
    assert Client().get("/api/directory/public").json() == {"enabled": True}
    save_settings({**SETTINGS, "enabled": False})
    assert Client().get("/api/directory/public").json() == {"enabled": False}
