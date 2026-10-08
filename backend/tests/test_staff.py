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
