import json
from datetime import date, time, timedelta
from types import SimpleNamespace

import pytest
from django.db import IntegrityError, transaction
from django.test import Client

import lunches.api
from accounts.models import Account, Role
from lunches.clock import moment_of
from lunches.history import BadMonth, lunches_of_month, month_start, summary_of
from lunches.models import Lunch
from lunches.rules import current_rules
from lunches.service import (
    ALREADY_HAD_LUNCH,
    ALREADY_ON_LUNCH,
    DAY_OFF,
    NOT_ON_LUNCH,
    NOT_TRACKED,
    UNDO_EXPIRED,
    LunchRefused,
    close_overdue,
    finish_lunch,
    start_lunch,
    undo_lunch,
)
from lunches.status import LunchStatus, is_violation, status_of
from tests.factories import DEFAULT_PASSWORD, make_account

pytestmark = pytest.mark.django_db

THURSDAY = date(2026, 10, 8)
SATURDAY = date(2026, 10, 10)
NOON = moment_of(THURSDAY, time(12, 0))
JSON = "application/json"


def at(clock, day=THURSDAY):
    return moment_of(day, clock)


def worker(login="worker"):
    return make_account(login=login, must_change_password=False)


def refusal_of(action):
    with pytest.raises(LunchRefused) as refused:
        action()
    return refused.value.message


def change_rules(**fields):
    rules = current_rules()
    for name, value in fields.items():
        setattr(rules, name, value)
    rules.save()


def test_start_saves_todays_lunch_with_current_limit():
    lunch = start_lunch(worker(), NOON)

    assert (lunch.day, lunch.started_at, lunch.ended_at, lunch.limit_minutes) == (THURSDAY, NOON, None, 45)
    assert status_of(lunch, NOON) == LunchStatus.ONGOING


def test_rule_changes_do_not_touch_started_lunch():
    account = worker()
    start_lunch(account, NOON)
    change_rules(limit_minutes=30)

    lunch = finish_lunch(account, NOON + timedelta(minutes=40))

    assert lunch.limit_minutes == 45
    assert status_of(lunch, NOON + timedelta(minutes=40)) == LunchStatus.ON_TIME


def test_untracked_employee_cannot_start():
    account = worker()
    account.track_lunch = False
    account.save()

    assert refusal_of(lambda: start_lunch(account, NOON)) == NOT_TRACKED


def test_lunch_is_refused_on_day_off():
    assert refusal_of(lambda: start_lunch(worker(), at(time(12, 0), SATURDAY))) == DAY_OFF


def test_workdays_are_configurable():
    change_rules(workdays="123456")

    assert start_lunch(worker(), at(time(12, 0), SATURDAY)).day == SATURDAY


def test_lunch_is_refused_after_day_end():
    assert refusal_of(lambda: start_lunch(worker(), at(time(18, 0)))) == "Рабочий день закончился в 18:00"


def test_window_limits_start_when_enabled():
    change_rules(window_enabled=True, window_start=time(12, 0), window_end=time(15, 0))
    account = worker()

    assert refusal_of(lambda: start_lunch(account, at(time(11, 59)))) == "Уйти на обед можно с 12:00 до 15:00"
    assert refusal_of(lambda: start_lunch(account, at(time(15, 0)))) == "Уйти на обед можно с 12:00 до 15:00"
    assert start_lunch(account, at(time(14, 59))).started_at == at(time(14, 59))


def test_window_is_ignored_when_disabled():
    assert start_lunch(worker(), at(time(9, 0))).started_at == at(time(9, 0))


def test_second_start_while_on_lunch_is_refused():
    account = worker()
    start_lunch(account, NOON)

    assert refusal_of(lambda: start_lunch(account, NOON + timedelta(minutes=1))) == ALREADY_ON_LUNCH


def test_only_one_lunch_per_day():
    account = worker()
    start_lunch(account, NOON)
    finish_lunch(account, NOON + timedelta(minutes=30))

    assert refusal_of(lambda: start_lunch(account, NOON + timedelta(hours=1))) == ALREADY_HAD_LUNCH


def test_database_keeps_one_lunch_per_day():
    account = worker()
    start_lunch(account, NOON)

    with pytest.raises(IntegrityError), transaction.atomic():
        Lunch.objects.create(account=account, day=THURSDAY, started_at=NOON, limit_minutes=45)


def test_finish_over_limit_is_overrun():
    account = worker()
    start_lunch(account, NOON)

    lunch = finish_lunch(account, NOON + timedelta(minutes=46))

    assert status_of(lunch, NOON + timedelta(minutes=46)) == LunchStatus.OVERRUN
    assert is_violation(lunch, NOON + timedelta(minutes=46))


def test_finish_without_lunch_is_refused():
    assert refusal_of(lambda: finish_lunch(worker(), NOON)) == NOT_ON_LUNCH


def test_undo_within_five_minutes_removes_lunch():
    account = worker()
    start_lunch(account, NOON)

    undo_lunch(account, NOON + timedelta(minutes=5))

    assert not Lunch.objects.exists()
    assert start_lunch(account, NOON + timedelta(minutes=6)).started_at == NOON + timedelta(minutes=6)


def test_undo_after_five_minutes_is_refused():
    account = worker()
    start_lunch(account, NOON)

    assert refusal_of(lambda: undo_lunch(account, NOON + timedelta(minutes=5, seconds=1))) == UNDO_EXPIRED
    assert Lunch.objects.count() == 1


def test_forgotten_lunch_closes_at_day_end_as_unreturned():
    account = worker()
    start_lunch(account, NOON)

    close_overdue(at(time(18, 0)))

    lunch = Lunch.objects.get()
    assert (lunch.ended_at, lunch.auto_closed) == (at(time(18, 0)), True)
    assert status_of(lunch, at(time(18, 0))) == LunchStatus.UNRETURNED
    assert is_violation(lunch, at(time(18, 0)))


def test_open_lunch_stays_open_before_day_end():
    start_lunch(worker(), NOON)

    close_overdue(at(time(17, 59)))

    assert Lunch.objects.get().ended_at is None


def test_yesterdays_forgotten_lunch_does_not_block_today():
    account = worker()
    start_lunch(account, at(time(12, 0), date(2026, 10, 7)))

    lunch = start_lunch(account, NOON)

    assert lunch.day == THURSDAY
    assert Lunch.objects.get(day=date(2026, 10, 7)).auto_closed


def test_month_start_reads_month_or_defaults_to_current():
    assert month_start("2026-09", NOON) == date(2026, 9, 1)
    assert month_start("", NOON) == date(2026, 10, 1)


@pytest.mark.parametrize("text", ["2026-13", "2026-00", "сентябрь", "2026-9", "2026-09-01"])
def test_month_start_rejects_bad_month(text):
    with pytest.raises(BadMonth):
        month_start(text, NOON)


def finished(account, day, minutes):
    start = at(time(12, 0), day)
    start_lunch(account, start)
    return finish_lunch(account, start + timedelta(minutes=minutes))


def test_month_history_is_newest_first_with_summary():
    account = worker()
    finished(account, date(2026, 9, 30), 20)
    finished(account, date(2026, 10, 1), 30)
    finished(account, date(2026, 10, 2), 50)
    start_lunch(account, at(time(12, 0), date(2026, 10, 5)))
    close_overdue(at(time(18, 0), date(2026, 10, 5)))
    finished(worker("other"), date(2026, 10, 1), 90)

    lunches = lunches_of_month(account, date(2026, 10, 1))
    summary = summary_of(lunches, NOON)

    assert [lunch.day for lunch in lunches] == [date(2026, 10, 5), date(2026, 10, 2), date(2026, 10, 1)]
    assert (summary.count, summary.violations, summary.average_minutes) == (3, 2, 40)


def test_empty_month_has_no_average():
    summary = summary_of([], NOON)

    assert (summary.count, summary.violations, summary.average_minutes) == (0, 0, None)


@pytest.fixture
def frozen(monkeypatch):
    clock = SimpleNamespace(moment=NOON)
    monkeypatch.setattr(lunches.api, "timezone", SimpleNamespace(now=lambda: clock.moment))
    return clock


def signed_in(login="worker", role=Role.EMPLOYEE):
    make_account(login=login, role=role, must_change_password=False)
    client = Client()
    client.post("/api/auth/login", json.dumps({"login": login, "password": DEFAULT_PASSWORD}), content_type=JSON)
    return client


def test_lunch_api_requires_login():
    assert Client().get("/api/lunch/me").status_code == 401


def test_state_before_lunch_allows_start(frozen):
    state = signed_in().get("/api/lunch/me").json()

    assert (state["tracked"], state["can_start"], state["refusal"], state["today"], state["undo_until"]) == (True, True, "", None, None)
    assert (state["limit_minutes"], state["warning_minutes"], state["undo_seconds"]) == (45, 5, 300)


def test_untracked_state_explains_why(frozen):
    client = signed_in("hr", Role.HR)
    Account.objects.filter(login="hr").update(track_lunch=False)

    state = client.get("/api/lunch/me").json()

    assert (state["tracked"], state["can_start"], state["refusal"]) == (False, False, NOT_TRACKED)


def test_start_via_api_returns_ongoing_state_with_undo(frozen):
    state = signed_in().post("/api/lunch/start", content_type=JSON).json()

    assert state["today"]["status"] == "ongoing"
    assert state["can_start"] is False
    assert state["refusal"] == ALREADY_ON_LUNCH
    assert state["undo_until"] is not None


def test_undo_deadline_disappears_after_five_minutes(frozen):
    client = signed_in()
    client.post("/api/lunch/start", content_type=JSON)
    frozen.moment = NOON + timedelta(minutes=6)

    state = client.get("/api/lunch/me").json()

    assert state["undo_until"] is None
    assert state["today"]["duration_seconds"] == 360


def test_finish_via_api_returns_finished_lunch(frozen):
    client = signed_in()
    client.post("/api/lunch/start", content_type=JSON)
    frozen.moment = NOON + timedelta(minutes=30)

    state = client.post("/api/lunch/finish", content_type=JSON).json()

    assert (state["today"]["status"], state["today"]["duration_seconds"]) == ("on_time", 1800)
    assert state["refusal"] == ALREADY_HAD_LUNCH


def test_undo_via_api_clears_today(frozen):
    client = signed_in()
    client.post("/api/lunch/start", content_type=JSON)

    state = client.post("/api/lunch/undo", content_type=JSON).json()

    assert (state["today"], state["can_start"]) == (None, True)


def test_refusal_via_api_is_conflict_with_message(frozen):
    response = signed_in().post("/api/lunch/finish", content_type=JSON)

    assert (response.status_code, response.json()["detail"]) == (409, NOT_ON_LUNCH)


def test_history_via_api_returns_own_month(frozen):
    client = signed_in()
    frozen.moment = at(time(12, 0), date(2026, 9, 30))
    client.post("/api/lunch/start", content_type=JSON)
    frozen.moment = at(time(12, 50), date(2026, 9, 30))
    client.post("/api/lunch/finish", content_type=JSON)
    frozen.moment = NOON

    september = client.get("/api/lunch/history?month=2026-09").json()
    october = client.get("/api/lunch/history").json()

    assert (september["month"], len(september["lunches"]), september["summary"]) == (
        "2026-09",
        1,
        {"count": 1, "violations": 1, "average_minutes": 50},
    )
    assert september["lunches"][0]["status"] == "overrun"
    assert (october["month"], october["lunches"]) == ("2026-10", [])


def test_history_rejects_bad_month(frozen):
    response = signed_in().get("/api/lunch/history?month=2026-13")

    assert (response.status_code, response.json()["detail"]) == (400, "Месяц указывается так: 2026-10")


RULES = {"limit_minutes": 30, "workdays": "6123", "day_end": "17:00", "window_enabled": True, "window_start": "11:30", "window_end": "15:00"}


def put_rules(client, **changes):
    return client.put("/api/lunch/rules", json.dumps({**RULES, **changes}), content_type=JSON)


def test_admin_reads_default_rules():
    rules = signed_in("boss", Role.ADMIN).get("/api/lunch/rules").json()

    assert (rules["limit_minutes"], rules["workdays"], rules["day_end"], rules["window_enabled"]) == (45, "12345", "18:00:00", False)
    assert (rules["min_limit_minutes"], rules["max_limit_minutes"]) == (5, 240)


@pytest.mark.parametrize("role", [Role.EMPLOYEE, Role.HR])
def test_only_admin_manages_rules(role):
    client = signed_in("worker", role)

    assert client.get("/api/lunch/rules").status_code == 403
    assert put_rules(client).status_code == 403


def test_admin_saves_rules_with_sorted_workdays():
    rules = put_rules(signed_in("boss", Role.ADMIN)).json()

    assert (rules["limit_minutes"], rules["workdays"], rules["day_end"]) == (30, "1236", "17:00:00")
    assert (rules["window_start"], rules["window_end"]) == ("11:30:00", "15:00:00")
    assert current_rules().limit_minutes == 30


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"limit_minutes": 4}, "Лимит обеда — от 5 до 240 минут"),
        ({"limit_minutes": 241}, "Лимит обеда — от 5 до 240 минут"),
        ({"workdays": ""}, "Отметьте хотя бы один рабочий день"),
        ({"workdays": "18"}, "Дни недели указываются цифрами от 1 (понедельник) до 7 (воскресенье)"),
        ({"window_start": "15:00"}, "Окно обеда должно начинаться раньше, чем заканчиваться"),
        ({"window_end": "17:30"}, "Окно обеда должно закончиться не позже конца рабочего дня (17:00)"),
    ],
)
def test_invalid_rules_are_explained(changes, message):
    response = put_rules(signed_in("boss", Role.ADMIN), **changes)

    assert (response.status_code, response.json()["detail"]) == (400, message)
    assert current_rules().limit_minutes == 45


def test_disabled_window_times_are_not_checked():
    response = put_rules(signed_in("boss", Role.ADMIN), window_enabled=False, window_start="16:00", window_end="10:00")

    assert response.status_code == 200


def test_new_rules_apply_to_next_lunch_only(frozen):
    employee = signed_in()
    employee.post("/api/lunch/start", content_type=JSON)
    put_rules(signed_in("boss", Role.ADMIN), limit_minutes=20, workdays="12345", window_enabled=False)

    state = employee.get("/api/lunch/me").json()

    assert (state["limit_minutes"], state["today"]["limit_minutes"]) == (45, 45)
    assert start_lunch(worker("next"), NOON).limit_minutes == 20


@pytest.mark.parametrize(("method", "path"), [("get", "/api/lunch/me"), ("post", "/api/lunch/start"), ("get", "/api/lunch/history")])
def test_admin_has_no_lunch(method, path):
    client = signed_in("boss", Role.ADMIN)

    response = getattr(client, method)(path, content_type=JSON)

    assert (response.status_code, response.json()["detail"]) == (403, "Администратор обеды не отмечает")
    assert not Lunch.objects.exists()


def test_hr_can_mark_lunch(frozen):
    client = signed_in("hr", Role.HR)

    assert client.post("/api/lunch/start", content_type=JSON).json()["today"]["status"] == "ongoing"
