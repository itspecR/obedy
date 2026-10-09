import json
from datetime import date, time, timedelta
from io import BytesIO
from types import SimpleNamespace

import pytest
from django.test import Client
from openpyxl import load_workbook

import lunches.stats_api
from accounts.models import Account, Role
from lunches.clock import moment_of
from lunches.models import Lunch
from tests.factories import DEFAULT_PASSWORD, make_account

pytestmark = pytest.mark.django_db

JSON = "application/json"
NOW = moment_of(date(2026, 10, 8), time(14, 0))
OCTOBER = "?date_from=2026-10-01&date_to=2026-10-31"


@pytest.fixture(autouse=True)
def frozen(monkeypatch):
    monkeypatch.setattr(lunches.stats_api, "timezone", SimpleNamespace(now=lambda: NOW))


def signed_in(login="hr", role=Role.HR):
    make_account(login=login, role=role, must_change_password=False)
    client = Client()
    client.post("/api/auth/login", json.dumps({"login": login, "password": DEFAULT_PASSWORD}), content_type=JSON)
    return client


def person(login, full_name):
    return Account.objects.create(login=login, full_name=full_name)


def lunch(account, day, minutes, **fields):
    started = moment_of(day, time(12, 0))
    ended = started + timedelta(minutes=minutes) if minutes is not None else None
    return Lunch.objects.create(account=account, day=day, started_at=started, ended_at=ended, limit_minutes=45, **fields)


@pytest.fixture
def october():
    ivanov = person("ivanov", "Иванов Иван")
    petrova = person("petrova", "Петрова Анна")
    sidorov = person("sidorov", "Сидоров Сидор")
    lunch(ivanov, date(2026, 10, 1), 30)
    lunch(ivanov, date(2026, 10, 2), 55)
    lunch(ivanov, date(2026, 10, 5), 360, auto_closed=True)
    lunch(petrova, date(2026, 10, 1), 40)
    lunch(petrova, date(2026, 10, 2), 47)
    lunch(sidorov, date(2026, 10, 1), 20)
    lunch(sidorov, date(2026, 9, 30), 90)
    return ivanov, petrova, sidorov


def test_period_overview_and_worst_first(october):
    body = signed_in().get(f"/api/lunch/stats{OCTOBER}").json()

    assert body["overview"] == {"count": 6, "violations": 3, "average_minutes": 38, "on_time_percent": 50, "people": 3}
    assert [(row["login"], row["violations"], row["overruns"], row["unreturned"], row["overrun_minutes"]) for row in body["people"]] == [
        ("ivanov", 2, 1, 1, 10),
        ("petrova", 1, 1, 0, 2),
        ("sidorov", 0, 0, 0, 0),
    ]
    assert (body["people"][0]["count"], body["people"][0]["average_minutes"]) == (3, 42)
    assert "departments" not in body


def test_ongoing_lunch_is_counted_but_not_measured():
    ivanov = person("ivanov", "Иванов Иван")
    lunch(ivanov, date(2026, 10, 8), None)

    body = signed_in().get(f"/api/lunch/stats{OCTOBER}").json()

    assert body["overview"] == {"count": 1, "violations": 1, "average_minutes": None, "on_time_percent": None, "people": 1}
    assert body["people"][0]["overrun_minutes"] == 75


def test_empty_period_has_no_rows():
    body = signed_in().get("/api/lunch/stats?date_from=2025-01-01&date_to=2025-01-31").json()

    assert body["overview"] == {"count": 0, "violations": 0, "average_minutes": None, "on_time_percent": None, "people": 0}
    assert body["people"] == []


@pytest.mark.parametrize(
    ("query", "message"),
    [
        ("?date_from=2026-10-31&date_to=2026-10-01", "Начало периода позже конца"),
        ("?date_from=2025-09-30&date_to=2026-10-01", "Период — не больше года"),
    ],
)
def test_bad_period_is_explained(query, message):
    response = signed_in().get(f"/api/lunch/stats{query}")

    assert (response.status_code, response.json()["detail"]) == (400, message)


def test_whole_year_is_allowed():
    assert signed_in().get("/api/lunch/stats?date_from=2025-10-02&date_to=2026-10-02").status_code == 200


@pytest.mark.parametrize("path", ["/api/lunch/stats", "/api/lunch/stats/export"])
def test_employee_cannot_see_statistics(path):
    response = signed_in("worker", Role.EMPLOYEE).get(f"{path}{OCTOBER}")

    assert (response.status_code, response.json()["detail"]) == (403, "Статистика доступна HR и администратору")


def test_admin_sees_statistics(october):
    assert signed_in("boss", Role.ADMIN).get(f"/api/lunch/stats{OCTOBER}").status_code == 200


def workbook_of(response):
    return load_workbook(BytesIO(response.content))


def test_export_has_people_and_lunch_sheets(october):
    hr = signed_in()
    ivanov = october[0]
    Lunch.objects.filter(account=ivanov, day=date(2026, 10, 1)).update(
        corrected_by=Account.objects.get(login="hr"), corrected_at=NOW, correction_reason="Забыл нажать", added_by_hand=True
    )

    response = hr.get(f"/api/lunch/stats/export{OCTOBER}")
    book = workbook_of(response)
    people = list(book["Сотрудники"].values)
    lunches = list(book["Все обеды"].values)

    assert response["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert response["Content-Disposition"] == 'attachment; filename="obedy_2026-10-01_2026-10-31.xlsx"'
    assert people[0][:4] == ("Сотрудник", "Логин", "Обедов", "Нарушений")
    assert people[1] == ("Иванов Иван", "ivanov", 3, 2, 1, 1, 42, 10)
    assert len(lunches) == 7
    assert lunches[1][1:] == ("Иванов Иван", "ivanov", "12:00", "12:30", 30, 45, "В пределах лимита", "Добавлено", "hr", "Забыл нажать")
    assert lunches[1][0].date() == date(2026, 10, 1)
    assert book["Все обеды"].freeze_panes == "A2"


def test_export_keeps_formula_like_text_as_text():
    ivanov = person("ivanov", "=HYPERLINK(\"http://evil\")")
    lunch(ivanov, date(2026, 10, 1), 30, corrected_at=NOW, correction_reason="=1+1")

    book = workbook_of(signed_in().get(f"/api/lunch/stats/export{OCTOBER}"))
    cells = [cell for row in book["Все обеды"].iter_rows(min_row=2) for cell in row]

    assert all(cell.data_type != "f" for cell in cells)
    assert "=1+1" in [cell.value for cell in cells]


def test_selected_people_narrow_overview_and_show_their_lunches(october):
    ivanov, petrova, _ = october

    body = signed_in().get(f"/api/lunch/stats{OCTOBER}&person={ivanov.pk}&person={petrova.pk}").json()

    assert body["overview"] == {"count": 5, "violations": 3, "average_minutes": 43, "on_time_percent": 40, "people": 2}
    assert len(body["people"]) == 3
    assert [(row["name"], row["lunch"]["day"]) for row in body["lunches"]][:3] == [
        ("Иванов Иван", "2026-10-01"),
        ("Петрова Анна", "2026-10-01"),
        ("Иванов Иван", "2026-10-02"),
    ]
    assert {row["person_id"] for row in body["lunches"]} == {ivanov.pk, petrova.pk}


def test_without_selection_daily_lunches_are_not_sent(october):
    assert signed_in().get(f"/api/lunch/stats{OCTOBER}").json()["lunches"] == []


def test_export_contains_only_selected_people(october):
    petrova = october[1]

    book = workbook_of(signed_in().get(f"/api/lunch/stats/export{OCTOBER}&person={petrova.pk}"))

    assert [row[1] for row in book["Сотрудники"].iter_rows(min_row=2, values_only=True)] == ["petrova"]
    assert {row[2] for row in book["Все обеды"].iter_rows(min_row=2, values_only=True)} == {"petrova"}
