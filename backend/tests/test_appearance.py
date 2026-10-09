import json

import pytest
from django.test import Client, override_settings

from accounts.models import Role
from journal.models import Action, JournalEntry
from lunches.rules import current_rules
from tests.factories import DEFAULT_PASSWORD, make_account

pytestmark = pytest.mark.django_db

JSON = "application/json"


def signed_in(login, role):
    make_account(login=login, role=role, must_change_password=False)
    client = Client()
    client.post("/api/auth/login", json.dumps({"login": login, "password": DEFAULT_PASSWORD}), content_type=JSON)
    return client


def switch(client, enabled):
    return client.put("/api/appearance/rabbit", json.dumps({"enabled": enabled}), content_type=JSON)


def test_rabbit_is_off_by_default_and_visible_without_login():
    response = Client().get("/api/appearance")

    assert (response.status_code, response.json()) == (200, {"rabbit": False})


def test_admin_switches_the_rabbit_and_it_is_logged():
    admin = signed_in("boss", Role.ADMIN)

    response = switch(admin, True)

    assert (response.status_code, response.json()) == (200, {"rabbit": True})
    assert Client().get("/api/appearance").json() == {"rabbit": True}
    entry = JournalEntry.objects.get(action=Action.RULES_CHANGED)
    assert [(row["label"], row["before"], row["after"]) for row in entry.details] == [("Анимация с кроликом", "выключено", "включено")]


def test_switching_to_the_same_value_writes_nothing_to_the_log():
    switch(signed_in("boss", Role.ADMIN), False)

    assert not JournalEntry.objects.filter(action=Action.RULES_CHANGED).exists()


@pytest.mark.parametrize("role", [Role.HR, Role.EMPLOYEE])
def test_only_the_admin_switches_the_rabbit(role):
    response = switch(signed_in("someone", role), True)

    assert (response.status_code, response.json()["detail"]) == (403, "Раздел доступен только администратору")
    assert current_rules().rabbit_enabled is False


def test_guest_cannot_switch_the_rabbit():
    assert switch(Client(), True).status_code == 401


def test_hr_saving_lunch_rules_keeps_the_rabbit():
    switch(signed_in("boss", Role.ADMIN), True)
    rules = {"limit_minutes": 50, "workdays": "12345", "day_end": "18:00", "window_enabled": False, "window_start": "12:00", "window_end": "15:00"}

    signed_in("kadry", Role.HR).put("/api/lunch/rules", json.dumps(rules), content_type=JSON)

    assert current_rules().rabbit_enabled is True


def test_switching_the_rabbit_does_not_touch_the_lunch_rules_date():
    changed_at = current_rules().updated_at

    switch(signed_in("boss", Role.ADMIN), True)

    assert current_rules().updated_at == changed_at


@override_settings(DATABASE_CONFIGURED=False)
def test_appearance_waits_for_the_database_in_setup_mode():
    assert Client().get("/api/appearance").status_code == 503
