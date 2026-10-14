from datetime import date, time

import pytest

from accounts.models import Account
from lunches.models import Absence, TrackingSpan
from lunches.rules import current_rules
from tests.test_lunches import JSON, at, frozen, signed_in  # noqa: F401

pytestmark = pytest.mark.django_db


def enable():
    rules = current_rules()
    rules.missing_enabled = True
    rules.missing_since = date(2026, 10, 1)
    rules.save()


def test_employee_sees_own_days_without_lunch_and_absences_newest_first(frozen):  # noqa: F811
    client = signed_in()
    worker = Account.objects.get(login="worker")
    TrackingSpan.objects.create(account=worker, started_on=date(2026, 9, 1))
    Absence.objects.create(account=worker, first=date(2026, 10, 2), last=date(2026, 10, 2), kind="sick")
    enable()
    frozen.moment = at(time(12, 0), date(2026, 10, 7))
    client.post("/api/lunch/start", content_type=JSON)
    frozen.moment = at(time(12, 30), date(2026, 10, 7))
    client.post("/api/lunch/finish", content_type=JSON)
    frozen.moment = at(time(19, 0), date(2026, 10, 8))

    history = client.get("/api/lunch/history?month=2026-10").json()

    assert history["attendance_enabled"] is True
    assert history["marks"] == [
        {"day": "2026-10-08", "label": "Без обеда"},
        {"day": "2026-10-06", "label": "Без обеда"},
        {"day": "2026-10-05", "label": "Без обеда"},
        {"day": "2026-10-02", "label": "Больничный"},
        {"day": "2026-10-01", "label": "Без обеда"},
    ]
    assert history["summary"]["missing"] == 4


def test_nothing_is_marked_while_the_rule_is_off(frozen):  # noqa: F811
    client = signed_in()
    TrackingSpan.objects.create(account=Account.objects.get(login="worker"), started_on=date(2026, 9, 1))

    history = client.get("/api/lunch/history?month=2026-10").json()

    assert (history["attendance_enabled"], history["marks"], history["summary"]["missing"]) == (False, [], 0)
