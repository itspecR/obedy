from datetime import datetime, time, timedelta

import pytest
from django.test import Client
from django.utils import timezone

from lunches.rules import current_rules

pytestmark = pytest.mark.django_db

CLOCK_TOLERANCE = timedelta(seconds=5)


def test_clock_tells_server_time_and_zone_without_login():
    response = Client().get("/api/clock")
    body = response.json()

    assert response.status_code == 200
    assert abs(datetime.fromisoformat(body["server_time"]) - timezone.now()) < CLOCK_TOLERANCE
    assert body["time_zone"] == "Europe/Moscow"
    assert body["lunch_window"] is None


def test_clock_shows_the_lunch_window_only_when_it_is_enabled():
    rules = current_rules()
    rules.window_enabled = True
    rules.window_start = time(12, 30)
    rules.window_end = time(14, 0)
    rules.save()

    assert Client().get("/api/clock").json()["lunch_window"] == {"start": "12:30:00", "end": "14:00:00"}

    rules.window_enabled = False
    rules.save()

    assert Client().get("/api/clock").json()["lunch_window"] is None


def test_clock_does_not_reveal_anything_about_people():
    assert set(Client().get("/api/clock").json()) == {"server_time", "time_zone", "lunch_window"}
