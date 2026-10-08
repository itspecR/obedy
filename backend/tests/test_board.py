import json
from datetime import date, time, timedelta
from types import SimpleNamespace

import pytest
from django.test import Client

import lunches.api
import lunches.board_api
from accounts.models import Account, Role
from lunches.clock import moment_of
from lunches.models import Lunch
from lunches.service import close_overdue, finish_lunch, start_lunch
from tests.factories import DEFAULT_PASSWORD, make_account

pytestmark = pytest.mark.django_db

THURSDAY = date(2026, 10, 8)
JSON = "application/json"


def at(clock, day=THURSDAY):
    return moment_of(day, clock)


NOW = at(time(14, 0))


@pytest.fixture(autouse=True)
def frozen(monkeypatch):
    clock = SimpleNamespace(moment=NOW)
    fake = SimpleNamespace(now=lambda: clock.moment)
    monkeypatch.setattr(lunches.api, "timezone", fake)
    monkeypatch.setattr(lunches.board_api, "timezone", fake)
    return clock


def signed_in(login, role):
    make_account(login=login, role=role, must_change_password=False)
    client = Client()
    client.post("/api/auth/login", json.dumps({"login": login, "password": DEFAULT_PASSWORD}), content_type=JSON)
    return client


def employee(login, full_name="", department=""):
    return Account.objects.create(login=login, full_name=full_name, department=department, position="Кассир")


def lunch_of(account, start, minutes=None, day=THURSDAY):
    lunch = start_lunch(account, at(start, day))
    if minutes is not None:
        lunch = finish_lunch(account, at(start, day) + timedelta(minutes=minutes))
    return lunch


def correct(client, lunch_id, **changes):
    body = {"started_at": "12:00", "ended_at": "12:40", "reason": "Забыл нажать «Вернулся»", **changes}
    return client.put(f"/api/lunch/board/{lunch_id}/correction", json.dumps(body), content_type=JSON)


@pytest.mark.parametrize("role", [Role.HR, Role.ADMIN])
def test_board_shows_todays_lunches_with_people(role):
    ivanov = employee("ivanov", "Иванов Иван", "Склад")
    lunch_of(ivanov, time(12, 0), 30)
    lunch_of(employee("petrov"), time(13, 0))
    lunch_of(employee("old"), time(12, 0), 20, day=date(2026, 10, 7))

    board = signed_in("hr", role).get("/api/lunch/board").json()

    assert (board["day"], board["today"], board["warning_minutes"]) == ("2026-10-08", "2026-10-08", 5)
    assert [(entry["person"]["name"], entry["lunch"]["status"]) for entry in board["entries"]] == [("Иванов Иван", "on_time"), ("petrov", "ongoing")]
    assert board["entries"][0]["person"] == {"id": ivanov.pk, "name": "Иванов Иван", "login": "ivanov", "department": "Склад", "position": "Кассир"}
    assert board["entries"][1]["lunch"]["duration_seconds"] == 3600


def test_board_shows_past_day_with_unreturned_closed():
    lunch_of(employee("ivanov"), time(12, 0), day=date(2026, 10, 7))

    board = signed_in("hr", Role.HR).get("/api/lunch/board?day=2026-10-07").json()

    assert board["day"] == "2026-10-07"
    assert [entry["lunch"]["status"] for entry in board["entries"]] == ["unreturned"]


def test_employee_cannot_see_board():
    response = signed_in("worker", Role.EMPLOYEE).get("/api/lunch/board")

    assert (response.status_code, response.json()["detail"]) == (403, "Табло доступно HR и администратору")


def test_hr_corrects_forgotten_return_with_reason():
    ivanov = employee("ivanov", "Иванов Иван")
    lunch = lunch_of(ivanov, time(12, 0), day=date(2026, 10, 7))
    close_overdue(NOW)
    hr = signed_in("hr", Role.HR)

    entry = correct(hr, lunch.pk, started_at="12:05", ended_at="12:55").json()

    assert entry["lunch"]["status"] == "overrun"
    assert entry["lunch"]["duration_seconds"] == 50 * 60
    assert entry["lunch"]["correction"]["reason"] == "Забыл нажать «Вернулся»"
    stored = Lunch.objects.get()
    assert (stored.started_at, stored.ended_at, stored.corrected_by.login) == (at(time(12, 5), date(2026, 10, 7)), at(time(12, 55), date(2026, 10, 7)), "hr")


def test_correction_is_visible_to_the_employee():
    ivanov = make_account(login="ivanov", must_change_password=False)
    lunch = lunch_of(ivanov, time(12, 0), day=date(2026, 10, 7))
    correct(signed_in("hr", Role.HR), lunch.pk, started_at="12:00", ended_at="12:30")
    client = Client()
    client.post("/api/auth/login", json.dumps({"login": "ivanov", "password": DEFAULT_PASSWORD}), content_type=JSON)

    history = client.get("/api/lunch/history").json()

    assert history["lunches"][0]["status"] == "on_time"
    assert history["lunches"][0]["correction"]["by"] == "hr"


def test_correction_closes_ongoing_lunch():
    lunch = lunch_of(employee("ivanov"), time(12, 0))

    entry = correct(signed_in("hr", Role.HR), lunch.pk, started_at="12:00", ended_at="13:00").json()

    assert entry["lunch"]["status"] == "overrun"
    assert entry["lunch"]["ended_at"] is not None


def test_nobody_corrects_own_lunch():
    hr = signed_in("hr", Role.HR)
    own = lunch_of(Account.objects.get(login="hr"), time(12, 0), 30)

    response = correct(hr, own.pk)
    board = hr.get("/api/lunch/board").json()

    assert (response.status_code, response.json()["detail"]) == (400, "Свой обед исправить нельзя — попросите коллегу")
    assert board["entries"][0]["can_correct"] is False


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"reason": "   "}, "Укажите причину исправления"),
        ({"started_at": "13:00", "ended_at": "12:00"}, "Время возврата должно быть позже времени ухода"),
        ({"started_at": "13:00", "ended_at": "13:00"}, "Время возврата должно быть позже времени ухода"),
        ({"ended_at": "14:30"}, "Время возврата ещё не наступило"),
    ],
)
def test_bad_correction_is_explained(changes, message):
    lunch = lunch_of(employee("ivanov"), time(12, 0), 30)

    response = correct(signed_in("hr", Role.HR), lunch.pk, **changes)

    assert (response.status_code, response.json()["detail"]) == (400, message)
    assert Lunch.objects.get().corrected_at is None


def test_employee_cannot_correct():
    lunch = lunch_of(employee("ivanov"), time(12, 0), 30)

    assert correct(signed_in("worker", Role.EMPLOYEE), lunch.pk).status_code == 403


def test_correcting_missing_lunch_is_not_found():
    response = correct(signed_in("hr", Role.HR), 999)

    assert (response.status_code, response.json()["detail"]) == (404, "Обед не найден. Обновите страницу")
