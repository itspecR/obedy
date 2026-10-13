from datetime import date, time

import pytest

from accounts.models import Role
from lunches.models import Absence, CalendarDay, TrackingSpan
from lunches.rules import current_rules
from tests.test_board import NOW, THURSDAY, at, employee, frozen, lunch_of, signed_in  # noqa: F401

pytestmark = pytest.mark.django_db

BOARD = "/api/lunch/board"


def enabled(**fields):
    rules = current_rules()
    rules.missing_enabled = True
    rules.missing_since = date(2026, 10, 1)
    for name, value in fields.items():
        setattr(rules, name, value)
    rules.save()


def tracked(login, full_name):
    account = employee(login, full_name)
    TrackingSpan.objects.create(account=account, started_on=date(2026, 9, 1))
    return account


@pytest.fixture
def team():
    ivanov = tracked("ivanov", "Иванов Иван")
    petrova = tracked("petrova", "Петрова Анна")
    sidorov = tracked("sidorov", "Сидоров Сидор")
    lunch_of(ivanov, time(12, 0), 30)
    Absence.objects.create(account=sidorov, first=date(2026, 10, 5), last=date(2026, 10, 9), kind="vacation", note="приказ")
    return ivanov, petrova, sidorov


def names(people):
    return [person["name"] for person in people]


@pytest.mark.usefixtures("team")
def test_today_shows_who_has_not_had_lunch_yet_and_who_is_away():
    enabled()

    board = signed_in("hr", Role.HR).get(BOARD).json()

    assert board["attendance_enabled"] is True
    assert (names(board["pending"]), names(board["missing"])) == (["Петрова Анна"], [])
    assert [(item["name"], item["kind"], item["note"]) for item in board["absent"]] == [("Сидоров Сидор", "vacation", "приказ")]


@pytest.mark.usefixtures("team")
def test_after_the_lunch_window_they_are_without_lunch(frozen):  # noqa: F811
    enabled(window_enabled=True)
    frozen.moment = at(time(15, 0))

    board = signed_in("hr", Role.HR).get(BOARD).json()

    assert (names(board["pending"]), names(board["missing"])) == ([], ["Петрова Анна"])


@pytest.mark.usefixtures("team")
def test_past_day_lists_people_without_lunch():
    enabled()

    board = signed_in("hr", Role.HR).get(f"{BOARD}?day=2026-10-07").json()

    assert (names(board["pending"]), names(board["missing"])) == ([], ["Иванов Иван", "Петрова Анна"])
    assert names(board["absent"]) == ["Сидоров Сидор"]


@pytest.mark.usefixtures("team")
def test_holidays_and_switched_off_rule_show_nobody():
    CalendarDay.objects.create(day=THURSDAY, working=False)
    hr = signed_in("hr", Role.HR)

    off = hr.get(BOARD).json()
    enabled()
    holiday = hr.get(BOARD).json()

    assert (off["attendance_enabled"], off["pending"], off["missing"], off["absent"]) == (False, [], [], [])
    assert (holiday["pending"], holiday["missing"], holiday["absent"]) == ([], [], [])
