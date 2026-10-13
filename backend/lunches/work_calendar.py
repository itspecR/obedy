from dataclasses import dataclass

from lunches.models import CalendarDay


@dataclass(frozen=True)
class WorkCalendar:
    workdays: str
    exceptions: dict

    def by_week(self, day):
        return str(day.isoweekday()) in self.workdays

    def is_workday(self, day):
        return self.exceptions.get(day, self.by_week(day))


def work_calendar(rules, first, last):
    exceptions = dict(CalendarDay.objects.filter(day__gte=first, day__lte=last).values_list("day", "working"))
    return WorkCalendar(rules.workdays, exceptions)


def is_workday(rules, day):
    return work_calendar(rules, day, day).is_workday(day)
