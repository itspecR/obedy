import json
from datetime import date, time, timedelta
from io import BytesIO
from types import SimpleNamespace

import pytest
from django.test import Client
from openpyxl import load_workbook

import lunches.api
import lunches.board_api
import lunches.stats_api
from accounts.models import Account, Role, Source
from lunches.clock import moment_of
from lunches.models import Lunch
from tests.factories import DEFAULT_PASSWORD, make_account

pytestmark = pytest.mark.django_db

JSON = "application/json"
DAY = date(2026, 10, 7)
NOW = moment_of(date(2026, 10, 8), time(14, 0))
OCTOBER = "?date_from=2026-10-01&date_to=2026-10-31"


@pytest.fixture(autouse=True)
def frozen(monkeypatch):
    fake = SimpleNamespace(now=lambda: NOW)
    for module in (lunches.api, lunches.board_api, lunches.stats_api):
        monkeypatch.setattr(module, "timezone", fake)


def signed_in(login, role):
    make_account(login=login, role=role, must_change_password=False)
    client = Client()
    client.post("/api/auth/login", json.dumps({"login": login, "password": DEFAULT_PASSWORD}), content_type=JSON)
    return client


def domain_person(login, in_directory=True, is_active=True):
    return Account.objects.create(login=login, full_name=login.title(), source=Source.DOMAIN, in_directory=in_directory, is_active=is_active)


def lunch_of(account, minutes=30, day=DAY):
    started = moment_of(day, time(12, 0))
    return Lunch.objects.create(account=account, day=day, started_at=started, ended_at=started + timedelta(minutes=minutes), limit_minutes=45)


@pytest.fixture
def people():
    staying = domain_person("staying")
    departed = domain_person("departed", in_directory=False)
    blocked = domain_person("blocked", is_active=False)
    for account in (staying, departed, blocked):
        lunch_of(account)
    return staying, departed, blocked


def logins(rows, key="login"):
    return sorted(row[key] for row in rows)


def test_staff_list_hides_departed_but_shows_blocked(people):
    rows = signed_in("boss", Role.ADMIN).get("/api/staff").json()

    assert logins(rows) == ["blocked", "boss", "staying"]


@pytest.mark.parametrize(("action", "payload"), [("role", {"role": "hr"}), ("track-lunch", {"track_lunch": False}), ("blocked", {"blocked": True})])
def test_departed_person_cannot_be_changed(people, action, payload):
    departed = people[1]

    response = signed_in("boss", Role.ADMIN).put(f"/api/staff/{departed.pk}/{action}", json.dumps(payload), content_type=JSON)

    assert response.status_code == 404


def test_board_archive_hides_departed(people):
    board = signed_in("hr", Role.HR).get(f"/api/lunch/board?day={DAY}").json()

    assert logins([entry["person"] for entry in board["entries"]]) == ["blocked", "staying"]


def test_departed_lunch_cannot_be_corrected(people):
    lunch = Lunch.objects.get(account=people[1])
    body = {"started_at": "12:00", "ended_at": "12:20", "reason": "Проверка"}

    response = signed_in("hr", Role.HR).put(f"/api/lunch/board/{lunch.pk}/correction", json.dumps(body), content_type=JSON)

    assert response.status_code == 404


def test_departed_person_is_not_offered_and_cannot_get_a_lunch(people):
    hr = signed_in("hr", Role.HR)
    body = {"account_id": people[1].pk, "day": "2026-10-08", "started_at": "12:00", "ended_at": "12:30", "reason": "Проверка"}

    offered = hr.get("/api/lunch/board/people").json()
    response = hr.post("/api/lunch/board/lunches", json.dumps(body), content_type=JSON)

    assert "departed" not in logins(offered)
    assert (response.status_code, response.json()["detail"]) == (404, "Сотрудник не найден. Обновите страницу")


def test_statistics_and_excel_hide_departed(people):
    hr = signed_in("hr", Role.HR)

    stats = hr.get(f"/api/lunch/stats{OCTOBER}").json()
    book = load_workbook(BytesIO(hr.get(f"/api/lunch/stats/export{OCTOBER}").content))

    assert logins(stats["people"]) == ["blocked", "staying"]
    assert stats["overview"]["count"] == 2
    assert sorted(row[1] for row in list(book["Сводка"].values)[1:]) == ["blocked", "staying"]
    assert "departed" not in [cell for row in book["Отчёт"].values for cell in row]


def test_returned_person_appears_again_with_history(people):
    Account.objects.filter(login="departed").update(in_directory=True)
    hr = signed_in("hr", Role.HR)

    stats = hr.get(f"/api/lunch/stats{OCTOBER}").json()
    board = hr.get(f"/api/lunch/board?day={DAY}").json()

    assert "departed" in logins(stats["people"])
    assert "departed" in logins([entry["person"] for entry in board["entries"]])
    assert Lunch.objects.filter(account__login="departed").count() == 1
