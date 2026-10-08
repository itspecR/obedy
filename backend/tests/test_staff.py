import json

import pytest
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client

from accounts.models import Account, Role, Source
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
