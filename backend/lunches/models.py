from datetime import time

from django.db import models

from accounts.models import Account

RULES_ID = 1
DEFAULT_LIMIT_MINUTES = 45
DEFAULT_WORKDAYS = "12345"
DEFAULT_DAY_END = time(18, 0)
DEFAULT_WINDOW_START = time(12, 0)
DEFAULT_WINDOW_END = time(15, 0)
REASON_LIMIT = 500
NOTE_LIMIT = 200


class LunchRules(models.Model):
    limit_minutes = models.PositiveSmallIntegerField(default=DEFAULT_LIMIT_MINUTES)
    workdays = models.CharField(max_length=7, default=DEFAULT_WORKDAYS)
    day_end = models.TimeField(default=DEFAULT_DAY_END)
    window_enabled = models.BooleanField(default=False)
    window_start = models.TimeField(default=DEFAULT_WINDOW_START)
    window_end = models.TimeField(default=DEFAULT_WINDOW_END)
    rabbit_enabled = models.BooleanField(default=False)
    missing_enabled = models.BooleanField(default=False)
    missing_since = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class Lunch(models.Model):
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="lunches")
    day = models.DateField()
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    limit_minutes = models.PositiveSmallIntegerField()
    auto_closed = models.BooleanField(default=False)
    corrected_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    corrected_at = models.DateTimeField(null=True, blank=True)
    correction_reason = models.CharField(max_length=REASON_LIMIT, blank=True)
    added_by_hand = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["account", "day"], name="one_lunch_per_day")]
        indexes = [models.Index(fields=["day"])]


class TrackingSpan(models.Model):
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="tracking_spans")
    started_on = models.DateField()
    ended_on = models.DateField(null=True, blank=True)


class CalendarDay(models.Model):
    day = models.DateField(unique=True)
    working = models.BooleanField()


class AbsenceKind(models.TextChoices):
    VACATION = "vacation", "Отпуск"
    SICK = "sick", "Больничный"
    OTHER = "other", "Другое"


class Absence(models.Model):
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="absences")
    first = models.DateField()
    last = models.DateField()
    kind = models.CharField(max_length=16, choices=AbsenceKind.choices)
    note = models.CharField(max_length=NOTE_LIMIT, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["first", "last"])]
