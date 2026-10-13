import json
from datetime import date, time
from types import SimpleNamespace

import pytest

import lunches.rule_changes
from accounts.models import Account, Source
from journal.models import Action, JournalEntry
from lunches.attendance import attendance_in, settled
from lunches.clock import moment_of
from lunches.models import Absence, CalendarDay, TrackingSpan
from lunches.rules import current_rules
from lunches.statistics import Period
from tests.test_stats import JSON, NOW, frozen, lunch, person, report_rows, row_starting, signed_in, workbook_of  # noqa: F401

pytestmark = pytest.mark.django_db

OCTOBER = Period(date(2026, 10, 1), date(2026, 10, 31))
STATS = "/api/lunch/stats?date_from=2026-10-01&date_to=2026-10-31"
EXPORT = "/api/lunch/stats/export?date_from=2026-10-01&date_to=2026-10-31"


def enabled(since=date(2026, 10, 1), **fields):
    rules = current_rules()
    rules.missing_enabled = True
    rules.missing_since = since
    for name, value in fields.items():
        setattr(rules, name, value)
    rules.save()
    return rules


def tracked(login, full_name, since=date(2026, 9, 1), until=None, **fields):
    account = person(login, full_name) if not fields else Account.objects.create(login=login, full_name=full_name, **fields)
    TrackingSpan.objects.create(account=account, started_on=since, ended_on=until)
    return account


def missing_days(attendance, account):
    return [day.day for day in attendance[account.pk].missing] if account.pk in attendance else []


def test_workdays_without_lunch_until_the_last_settled_day_are_missing():
    rules = enabled()
    ivanov = tracked("ivanov", "Иванов Иван")
    lunch(ivanov, date(2026, 10, 1), 30)
    lunch(ivanov, date(2026, 10, 5), 40)

    attendance = attendance_in(rules, OCTOBER, NOW)

    assert missing_days(attendance, ivanov) == [2, 6, 7]


def test_calendar_and_counting_start_decide_which_days_count():
    rules = enabled(since=date(2026, 10, 2))
    CalendarDay.objects.create(day=date(2026, 10, 6), working=False)
    CalendarDay.objects.create(day=date(2026, 10, 3), working=True)
    ivanov = tracked("ivanov", "Иванов Иван")

    assert missing_days(attendance_in(rules, OCTOBER, NOW), ivanov) == [2, 3, 5, 7]


def test_only_days_inside_tracking_spans_count():
    rules = enabled()
    newcomer = tracked("novikov", "Новиков Никита", since=date(2026, 10, 6))
    leaver = tracked("staroy", "Старый Сергей", until=date(2026, 10, 5))

    attendance = attendance_in(rules, OCTOBER, NOW)

    assert missing_days(attendance, newcomer) == [6, 7]
    assert missing_days(attendance, leaver) == [1, 2]


def test_absence_days_are_named_instead_of_missing():
    rules = enabled()
    ivanov = tracked("ivanov", "Иванов Иван")
    Absence.objects.create(account=ivanov, first=date(2026, 10, 5), last=date(2026, 10, 9), kind="sick")

    attendance = attendance_in(rules, OCTOBER, NOW)[ivanov.pk]

    assert [day.day for day in attendance.missing] == [1, 2]
    assert attendance.absent == {date(2026, 10, 5): "Больничный", date(2026, 10, 6): "Больничный", date(2026, 10, 7): "Больничный"}


@pytest.mark.parametrize(
    ("window", "clock", "expected"),
    [
        (False, time(17, 59), False),
        (False, time(18, 0), True),
        (True, time(14, 59), False),
        (True, time(15, 0), True),
    ],
)
def test_today_settles_after_the_lunch_window_or_the_end_of_the_day(window, clock, expected):
    rules = enabled(window_enabled=window)

    assert settled(rules, date(2026, 10, 8), moment_of(date(2026, 10, 8), clock)) is expected


def test_nothing_is_counted_while_switched_off_or_for_departed_people():
    ivanov = tracked("ivanov", "Иванов Иван")
    gone = tracked("left", "Ушедший", source=Source.DOMAIN, in_directory=False)

    assert attendance_in(current_rules(), OCTOBER, NOW) == {}
    attendance = attendance_in(enabled(), OCTOBER, NOW)
    assert ivanov.pk in attendance and gone.pk not in attendance


def test_statistics_list_people_without_lunches_and_count_their_days():
    enabled()
    ivanov = tracked("ivanov", "Иванов Иван")
    petrova = tracked("petrova", "Петрова Анна")
    lunch(petrova, date(2026, 10, 1), 30)
    Absence.objects.create(account=petrova, first=date(2026, 10, 2), last=date(2026, 10, 2), kind="vacation")

    body = signed_in().get(STATS).json()
    people = {item["login"]: (item["count"], item["missing"], item["absent"]) for item in body["people"]}

    assert body["attendance_enabled"] is True
    assert people == {"ivanov": (0, 5, 0), "petrova": (1, 3, 1)}
    assert (body["overview"]["missing"], body["overview"]["absent"], body["overview"]["people"]) == (8, 1, 2)
    selected = signed_in("hr2").get(f"{STATS}&person={ivanov.pk}").json()["overview"]
    assert (selected["missing"], selected["people"]) == (5, 1)


def test_statistics_stay_as_before_while_switched_off():
    tracked("ivanov", "Иванов Иван")

    body = signed_in().get(STATS).json()

    assert (body["attendance_enabled"], body["people"], body["overview"]["missing"]) == (False, [], 0)


def test_export_names_missing_and_absent_days():
    enabled()
    ivanov = tracked("ivanov", "Иванов Иван")
    lunch(ivanov, date(2026, 10, 1), 30)
    Absence.objects.create(account=ivanov, first=date(2026, 10, 5), last=date(2026, 10, 5), kind="vacation")

    book = workbook_of(signed_in().get(EXPORT))
    rows = report_rows(book)
    block = row_starting(rows, "Иванов Иван")
    days = rows[block + 2 : block + 33]

    assert days[1][6] == "Без обеда"
    assert days[2][6] == "Выходной"
    assert days[4][6] == "Отпуск"
    assert days[8][6] == "—"
    assert rows[block + 34][0] == "Дней рабочих: 22 · выходных: 9 · обедов: 1 · без обеда: 3 · отсутствий: 1"
    summary = list(book["Сводка"].values)
    assert summary[0][-2:] == ("Без обеда", "Отсутствий")
    assert summary[1][-2:] == (3, 1)


def rules_body(client, **changes):
    current = client.get("/api/lunch/rules").json()
    kept = {key: current[key] for key in ("limit_minutes", "workdays", "day_end", "window_enabled", "window_start", "window_end")}
    return json.dumps({**kept, **changes})


def test_switching_on_starts_counting_today_unless_a_date_is_given(monkeypatch):
    monkeypatch.setattr(lunches.rule_changes, "timezone", SimpleNamespace(now=lambda: NOW))
    hr = signed_in()

    switched = hr.put("/api/lunch/rules", rules_body(hr, missing_enabled=True), content_type=JSON).json()
    dated = hr.put("/api/lunch/rules", rules_body(hr, missing_enabled=True, missing_since="2026-09-15"), content_type=JSON).json()
    untouched = hr.put("/api/lunch/rules", rules_body(hr, limit_minutes=50), content_type=JSON).json()

    assert (switched["missing_enabled"], switched["missing_since"]) == (True, "2026-10-08")
    assert dated["missing_since"] == "2026-09-15"
    assert (untouched["missing_enabled"], untouched["missing_since"]) == (True, "2026-09-15")
    first = JournalEntry.objects.filter(action=Action.RULES_CHANGED).order_by("created_at", "pk").first()
    assert {"label": "Дни без обеда", "before": "выключено", "after": "включено"} in first.details
    assert {"label": "Считать с", "before": "—", "after": "08.10.2026"} in first.details
