from datetime import timedelta

from django.db.models import TextChoices


class LunchStatus(TextChoices):
    ONGOING = "ongoing", "На обеде"
    ON_TIME = "on_time", "В пределах лимита"
    OVERRUN = "overrun", "Превышение"
    UNRETURNED = "unreturned", "Возврат не отмечен"


VIOLATIONS = (LunchStatus.OVERRUN, LunchStatus.UNRETURNED)


def limit_of(lunch):
    return timedelta(minutes=lunch.limit_minutes)


def duration_of(lunch, now):
    return (lunch.ended_at or now) - lunch.started_at


def is_overrun(lunch, now):
    return duration_of(lunch, now) > limit_of(lunch)


def status_of(lunch, now):
    if lunch.ended_at is None:
        return LunchStatus.ONGOING
    if lunch.auto_closed and lunch.corrected_at is None:
        return LunchStatus.UNRETURNED
    return LunchStatus.OVERRUN if is_overrun(lunch, now) else LunchStatus.ON_TIME


def is_violation(lunch, now):
    return status_of(lunch, now) in VIOLATIONS or is_overrun(lunch, now)
