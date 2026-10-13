from datetime import date

from django.db import IntegrityError, transaction

from lunches.models import CalendarDay
from lunches.rules import current_rules
from lunches.work_calendar import WorkCalendar

ALREADY_OFF = "Этот день и так выходной по правилам"
ALREADY_WORKING = "Этот день и так рабочий по правилам"
DUPLICATE_DAY = "Этот день уже есть в календаре"
DAY_NOT_FOUND = "Дня нет в календаре. Обновите страницу"


class CalendarRefused(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class CalendarDayMissing(Exception):
    pass


def year_days(year):
    return CalendarDay.objects.filter(day__gte=date(year, 1, 1), day__lte=date(year, 12, 31)).order_by("day")


def ensure_changes_the_week(day, working):
    usual = WorkCalendar(current_rules().workdays, {}).by_week(day)
    if usual == working:
        raise CalendarRefused(ALREADY_WORKING if working else ALREADY_OFF)


def add_day(day, working):
    ensure_changes_the_week(day, working)
    try:
        with transaction.atomic():
            return CalendarDay.objects.create(day=day, working=working)
    except IntegrityError as error:
        raise CalendarRefused(DUPLICATE_DAY) from error


def remove_day(day):
    found = CalendarDay.objects.filter(day=day).first()
    if found is None:
        raise CalendarDayMissing
    found.delete()
    return found
