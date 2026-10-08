import json

import pytest
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client

from accounts.models import Account, Role, Source
from staff.changes import ChangeRefused, change_role, set_blocked
from tests.factories import DEFAULT_PASSWORD, make_account

pytestmark = pytest.mark.django_db

BEFORE_TRACK_LUNCH = [("accounts", "0003_account_in_directory")]
WITH_TRACK_LUNCH = [("accounts", "0004_account_track_lunch")]


def signed_in(login, role):
    make_account(login=login, role=role, must_change_password=False)
    client = Client()
    client.post("/api/auth/login", json.dumps({"login": login, "password": DEFAULT_PASSWORD}), content_type="application/json")
    return client


def domain_account(login, full_name, **fields):
    return Account.objects.create(login=login, full_name=full_name, source=Source.DOMAIN, department="Склад", position="Кладовщик", **fields)


def test_admin_sees_everyone_with_status_sorted_by_name():
    client = signed_in("boss", Role.ADMIN)
    domain_account("petrov", "Петров Пётр")
    domain_account("ivanov", "Иванов Иван")
    domain_account("sidorov", "Сидоров Сидор", in_directory=False)
    domain_account("blocked", "Блоков Борис", is_active=False, in_directory=False)

    people = client.get("/api/staff").json()

    assert [(person["login"], person["status"]) for person in people] == [
        ("boss", "active"),
        ("blocked", "blocked"),
        ("ivanov", "active"),
        ("petrov", "active"),
        ("sidorov", "gone"),
    ]
    ivanov = people[2]
    assert (ivanov["department"], ivanov["position"], ivanov["role"], ivanov["source"], ivanov["track_lunch"]) == (
        "Склад",
        "Кладовщик",
        "employee",
        "domain",
        True,
    )


@pytest.mark.parametrize("role", [Role.EMPLOYEE, Role.HR])
def test_only_admin_sees_staff(role):
    assert signed_in("worker", role).get("/api/staff").status_code == 403


def test_anonymous_must_sign_in():
    assert Client().get("/api/staff").status_code == 401


def test_new_admin_does_not_track_lunch(capsys):
    call_command("create_admin")

    assert Account.objects.get(login="admin").track_lunch is False


@pytest.mark.django_db(transaction=True)
def test_upgrade_stops_tracking_lunch_of_existing_hr_and_admins():
    executor = MigrationExecutor(connection)
    executor.migrate(BEFORE_TRACK_LUNCH)
    old_account = executor.loader.project_state(BEFORE_TRACK_LUNCH).apps.get_model("accounts", "Account")
    for login, role in [("worker", "employee"), ("hr", "hr"), ("chief", "admin")]:
        old_account.objects.create(login=login, role=role)

    executor = MigrationExecutor(connection)
    executor.migrate(WITH_TRACK_LUNCH)
    executor.loader.build_graph()
    executor.migrate(executor.loader.graph.leaf_nodes())

    tracked = dict(Account.objects.values_list("login", "track_lunch"))
    assert tracked == {"worker": True, "hr": False, "chief": False}


def put(client, account, action, payload):
    return client.put(f"/api/staff/{account.pk}/{action}", json.dumps(payload), content_type="application/json")


def employee(login="ivanov"):
    return domain_account(login, "Иванов Иван", in_directory=True)


def test_promotion_switches_lunch_tracking_by_role():
    client = signed_in("boss", Role.ADMIN)
    worker = employee()

    promoted = put(client, worker, "role", {"role": "hr"}).json()
    demoted = put(client, worker, "role", {"role": "employee"}).json()

    assert (promoted["role"], promoted["track_lunch"]) == ("hr", False)
    assert (demoted["role"], demoted["track_lunch"]) == ("employee", True)


def test_lunch_tracking_can_be_switched_by_hand():
    client = signed_in("boss", Role.ADMIN)
    worker = employee()

    assert put(client, worker, "track-lunch", {"track_lunch": False}).json()["track_lunch"] is False
    assert Account.objects.get(pk=worker.pk).track_lunch is False


def test_admin_lunch_tracking_cannot_be_switched_on():
    client = signed_in("boss", Role.ADMIN)
    other = domain_account("second", "Второй Админ", in_directory=True, role=Role.ADMIN, track_lunch=False)

    response = put(client, other, "track-lunch", {"track_lunch": True})
    people = {person["login"]: person["can_track_lunch"] for person in client.get("/api/staff").json()}

    assert (response.status_code, response.json()["detail"]) == (409, "Администратор обеды не отмечает. Чтобы учитывать обеды, назначьте другую роль")
    assert Account.objects.get(pk=other.pk).track_lunch is False
    assert people == {"boss": False, "second": False}


def test_new_role_applies_without_signing_in_again():
    client = signed_in("boss", Role.ADMIN)
    other = signed_in("deputy", Role.ADMIN)
    deputy = Account.objects.get(login="deputy")

    assert put(client, deputy, "role", {"role": "employee"}).status_code == 200
    assert other.get("/api/staff").status_code == 403


@pytest.mark.parametrize(
    ("action", "payload", "message"),
    [
        ("role", {"role": "employee"}, "Нельзя снять роль администратора с себя"),
        ("blocked", {"blocked": True}, "Нельзя заблокировать себя"),
    ],
)
def test_admin_cannot_lock_themselves_out(action, payload, message):
    client = signed_in("boss", Role.ADMIN)
    boss = Account.objects.get(login="boss")

    response = put(client, boss, action, payload)

    assert response.status_code == 409
    assert response.json()["detail"].startswith(message)
    assert Account.objects.get(pk=boss.pk).role == Role.ADMIN


def test_last_active_admin_is_kept():
    outsider = employee("outsider")
    only_admin = make_account(login="chief", role=Role.ADMIN)
    make_account(login="gone_admin", role=Role.ADMIN)
    Account.objects.filter(login="gone_admin").update(source=Source.DOMAIN, in_directory=False)

    for change in (lambda: change_role(outsider, only_admin, Role.EMPLOYEE), lambda: set_blocked(outsider, only_admin, True)):
        with pytest.raises(ChangeRefused, match="последний активный администратор"):
            change()


def test_blocking_closes_sessions_and_unblocking_lets_back_in():
    client = signed_in("boss", Role.ADMIN)
    worker_client = signed_in("worker", Role.EMPLOYEE)
    worker = Account.objects.get(login="worker")

    blocked = put(client, worker, "blocked", {"blocked": True}).json()

    assert blocked["status"] == "blocked"
    assert worker_client.get("/api/auth/me").status_code == 401
    relogin = Client().post("/api/auth/login", json.dumps({"login": "worker", "password": DEFAULT_PASSWORD}), content_type="application/json")
    assert relogin.status_code == 401

    assert put(client, worker, "blocked", {"blocked": False}).json()["status"] == "active"
    again = Client().post("/api/auth/login", json.dumps({"login": "worker", "password": DEFAULT_PASSWORD}), content_type="application/json")
    assert again.status_code == 200


def test_unknown_employee_is_reported():
    client = signed_in("boss", Role.ADMIN)

    response = client.put("/api/staff/999999/role", json.dumps({"role": "hr"}), content_type="application/json")

    assert response.status_code == 404


@pytest.mark.parametrize("role", [Role.EMPLOYEE, Role.HR])
def test_only_admin_changes_people(role):
    client = signed_in("worker", role)
    worker = employee("someone")

    for action, payload in [("role", {"role": "admin"}), ("track-lunch", {"track_lunch": False}), ("blocked", {"blocked": True})]:
        assert put(client, worker, action, payload).status_code == 403
    assert Account.objects.get(pk=worker.pk).role == Role.EMPLOYEE


def create(client, **fields):
    payload = {"login": "kassa", "full_name": "Кассир Касса", "department": "Магазин", "position": "Кассир", "role": "employee", **fields}
    return client.post("/api/staff", json.dumps(payload), content_type="application/json")


def sign_in_as(login, password):
    client = Client()
    response = client.post("/api/auth/login", json.dumps({"login": login, "password": password}), content_type="application/json")
    return client, response


def test_admin_creates_local_account_with_one_time_password():
    client = signed_in("boss", Role.ADMIN)

    response = create(client, login="  Kassa ")

    body = response.json()
    assert response.status_code == 201
    assert (body["member"]["login"], body["member"]["source"], body["member"]["track_lunch"]) == ("kassa", "local", True)
    account = Account.objects.get(login="kassa")
    assert body["temporary_password"] not in account.password_hash
    _, first_login = sign_in_as("kassa", body["temporary_password"])
    assert first_login.json()["must_change_password"] is True


def test_new_hr_account_does_not_track_lunch():
    client = signed_in("boss", Role.ADMIN)

    assert create(client, role="hr").json()["member"]["track_lunch"] is False


@pytest.mark.parametrize(
    ("fields", "status", "message"),
    [
        ({"login": "кассир"}, 400, "Логин: от 2 до 64 символов"),
        ({"login": "a"}, 400, "Логин: от 2 до 64 символов"),
        ({"login": ".kassa"}, 400, "Логин: от 2 до 64 символов"),
        ({"full_name": "   "}, 400, "Укажите ФИО"),
        ({"login": "boss"}, 409, "Логин boss уже занят"),
        ({"login": "ivanov"}, 409, "Логин ivanov уже занят"),
    ],
)
def test_local_account_is_checked(fields, status, message):
    client = signed_in("boss", Role.ADMIN)
    employee()

    response = create(client, **fields)

    assert response.status_code == status
    assert response.json()["detail"].startswith(message)


def test_local_profile_is_edited_and_domain_profile_is_not():
    client = signed_in("boss", Role.ADMIN)
    local = Account.objects.get(login=create(client).json()["member"]["login"])
    domain = employee()
    changes = {"full_name": " Кассирова Анна ", "department": "Магазин 2", "position": "Старший кассир"}

    edited = put(client, local, "profile", changes)
    refused = put(client, domain, "profile", changes)

    assert (edited.json()["full_name"], edited.json()["department"]) == ("Кассирова Анна", "Магазин 2")
    assert refused.status_code == 409
    assert refused.json()["detail"].startswith("Это доменная учётная запись")


def test_password_reset_issues_new_password_and_signs_out():
    client = signed_in("boss", Role.ADMIN)
    worker_client = signed_in("worker", Role.EMPLOYEE)
    worker = Account.objects.get(login="worker")

    response = client.post(f"/api/staff/{worker.pk}/password", content_type="application/json")

    password = response.json()["temporary_password"]
    assert response.status_code == 200
    assert worker_client.get("/api/auth/me").status_code == 401
    assert sign_in_as("worker", DEFAULT_PASSWORD)[1].status_code == 401
    assert sign_in_as("worker", password)[1].json()["must_change_password"] is True


@pytest.mark.parametrize(("login", "message"), [("boss", "Свой пароль меняйте в профиле"), ("ivanov", "Это доменная учётная запись")])
def test_password_reset_is_refused_for_self_and_domain(login, message):
    client = signed_in("boss", Role.ADMIN)
    employee()
    account = Account.objects.get(login=login)

    response = client.post(f"/api/staff/{account.pk}/password", content_type="application/json")

    assert response.status_code == 409
    assert response.json()["detail"].startswith(message)


@pytest.mark.parametrize("role", [Role.EMPLOYEE, Role.HR])
def test_only_admin_manages_local_accounts(role):
    client = signed_in("worker", role)
    worker = Account.objects.get(login="worker")

    assert create(client).status_code == 403
    assert put(client, worker, "profile", {"full_name": "Новое имя"}).status_code == 403
    assert client.post(f"/api/staff/{worker.pk}/password", content_type="application/json").status_code == 403
    assert not Account.objects.filter(login="kassa").exists()
