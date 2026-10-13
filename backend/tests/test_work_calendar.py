import json
from datetime import date, time

import pytest

from accounts.models import Role
from journal.models import Action, JournalEntry
from lunches.clock import moment_of
from lunches.models import CalendarDay
from lunches.rules import current_rules
from lunches.service import DAY_OFF, start_refusal
from lunches.work_calendar import is_workday, work_calendar
from tests.factories import make_account
from tests.test_stats import JSON, frozen, lunch, person, report_rows, row_starting, signed_in, workbook_of  # noqa: F401

pytestmark = pytest.mark.django_db

UNITY_DAY = date(2026, 11, 4)
WORKING_SATURDAY = date(2026, 11, 7)
PLAIN_THURSDAY = date(2026, 11, 5)
PLAIN_SUNDAY = date(2026, 11, 8)
CALENDAR = "/api/lunch/rules/calendar"


def holidays():
    CalendarDay.objects.create(day=UNITY_DAY, working=False)
    CalendarDay.objects.create(day=WORKING_SATURDAY, working=True)


def post(client, day, working):
    return client.post(CALENDAR, json.dumps({"day": day.isoformat(), "working": working}), content_type=JSON)


def test_calendar_days_override_the_week():
    holidays()
    calendar = work_calendar(current_rules(), date(2026, 11, 1), date(2026, 11, 30))

    assert [calendar.is_workday(day) for day in (UNITY_DAY, WORKING_SATURDAY, PLAIN_THURSDAY, PLAIN_SUNDAY)] == [False, True, True, False]


def test_lunch_button_follows_the_calendar():
    holidays()
    worker = make_account(login="worker")
    rules = current_rules()

    assert start_refusal(worker, rules, None, moment_of(UNITY_DAY, time(13, 0))) == DAY_OFF
    assert start_refusal(worker, rules, None, moment_of(WORKING_SATURDAY, time(13, 0))) == ""
    assert is_workday(rules, PLAIN_THURSDAY)


@pytest.mark.parametrize("role", [Role.HR, Role.ADMIN])
def test_supervisor_adds_and_removes_calendar_days_by_year(role):
    client = signed_in("boss", role)

    assert post(client, UNITY_DAY, False).status_code == 201
    added = post(client, WORKING_SATURDAY, True)
    post(client, date(2027, 1, 1), False)

    assert added.json() == [{"day": "2026-11-04", "working": False}, {"day": "2026-11-07", "working": True}]
    assert client.get(f"{CALENDAR}?year=2027").json() == [{"day": "2027-01-01", "working": False}]
    assert client.delete(f"{CALENDAR}/2026-11-04").json() == [{"day": "2026-11-07", "working": True}]


def test_calendar_changes_are_written_to_the_journal():
    client = signed_in("hr", Role.HR)

    post(client, UNITY_DAY, False)
    client.delete(f"{CALENDAR}/2026-11-04")

    entries = list(JournalEntry.objects.order_by("created_at", "pk").filter(action__startswith="calendar"))
    assert [entry.action for entry in entries] == [Action.CALENDAR_DAY_ADDED, Action.CALENDAR_DAY_REMOVED]
    assert entries[0].details == [{"label": "Дата", "before": None, "after": "04.11.2026"}, {"label": "День", "before": None, "after": "выходной"}]


@pytest.mark.parametrize(
    ("day", "working", "message"),
    [
        (PLAIN_SUNDAY, False, "Этот день и так выходной по правилам"),
        (PLAIN_THURSDAY, True, "Этот день и так рабочий по правилам"),
    ],
)
def test_day_that_changes_nothing_is_refused(day, working, message):
    response = post(signed_in("hr", Role.HR), day, working)

    assert (response.status_code, response.json()["detail"]) == (400, message)


def test_same_day_twice_and_missing_day_are_explained():
    client = signed_in("hr", Role.HR)
    post(client, UNITY_DAY, False)

    repeated = post(client, UNITY_DAY, False)
    missing = client.delete(f"{CALENDAR}/2026-12-31")

    assert (repeated.status_code, repeated.json()["detail"]) == (400, "Этот день уже есть в календаре")
    assert (missing.status_code, missing.json()["detail"]) == (404, "Дня нет в календаре. Обновите страницу")


def test_employee_cannot_touch_the_calendar():
    client = signed_in("worker", Role.EMPLOYEE)

    assert client.get(f"{CALENDAR}?year=2026").status_code == 403
    assert post(client, UNITY_DAY, False).status_code == 403


def test_year_outside_the_range_is_rejected():
    assert signed_in("hr", Role.HR).get(f"{CALENDAR}?year=1999").status_code == 422


def test_export_counts_days_by_the_calendar():
    CalendarDay.objects.create(day=date(2026, 10, 5), working=False)
    CalendarDay.objects.create(day=date(2026, 10, 3), working=True)
    ivanov = person("ivanov", "Иванов Иван")
    lunch(ivanov, date(2026, 10, 1), 30)

    rows = report_rows(workbook_of(signed_in().get("/api/lunch/stats/export?date_from=2026-10-01&date_to=2026-10-31")))
    block = row_starting(rows, "Иванов Иван")
    days = rows[block + 2 : block + 33]

    assert days[2][1:] == ("сб", "—", "—", None, None, "—")
    assert days[4][1:] == ("пн", "—", "—", None, None, "Выходной")
    assert rows[block + 34][0] == "Дней рабочих: 22 · выходных: 9 · обедов: 1"
