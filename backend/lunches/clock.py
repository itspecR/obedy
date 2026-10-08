from datetime import datetime

from django.utils import timezone


def local(moment):
    return timezone.localtime(moment)


def today(now):
    return local(now).date()


def moment_of(day, clock_time):
    return timezone.make_aware(datetime.combine(day, clock_time))


def clock_text(clock_time):
    return clock_time.strftime("%H:%M")
