from datetime import datetime, time

from django.conf import settings
from django.utils import timezone
from ninja import Router, Schema

from lunches.rules import current_rules

router = Router(tags=["Часы"])


class LunchWindowOut(Schema):
    start: time
    end: time


class ClockOut(Schema):
    server_time: datetime
    time_zone: str
    lunch_window: LunchWindowOut | None


def lunch_window_of(rules):
    if not rules.window_enabled:
        return None
    return LunchWindowOut(start=rules.window_start, end=rules.window_end)


@router.get("", auth=None, response=ClockOut)
def clock(request):
    return ClockOut(server_time=timezone.now(), time_zone=settings.TIME_ZONE, lunch_window=lunch_window_of(current_rules()))
