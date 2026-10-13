from dataclasses import dataclass, field

from lunches.absences import absence_on, absences_by_account
from lunches.clock import local
from lunches.models import Lunch
from lunches.statistics import Period, days_of
from lunches.tracking import spans_by_account, tracked_on
from lunches.work_calendar import work_calendar
from staff.status import present_accounts


@dataclass
class Attendance:
    account: object
    missing: list = field(default_factory=list)
    absent: dict = field(default_factory=dict)

    def __bool__(self):
        return bool(self.missing or self.absent)


def closing_time(rules):
    return rules.window_end if rules.window_enabled else rules.day_end


def settled(rules, day, now):
    moment = local(now)
    return day < moment.date() or (day == moment.date() and moment.time() >= closing_time(rules))


def counted_period(rules, period):
    if not rules.missing_enabled or rules.missing_since is None or rules.missing_since > period.last:
        return None
    return Period(max(period.first, rules.missing_since), period.last)


def lunch_days(accounts, period):
    found = Lunch.objects.filter(account__in=accounts, day__gte=period.first, day__lte=period.last)
    return set(found.values_list("account_id", "day"))


def attendance_of(account, days, spans, absences, had_lunch):
    attendance = Attendance(account)
    for day in days:
        if not tracked_on(spans, day) or (account.pk, day) in had_lunch:
            continue
        absence = absence_on(absences, day)
        if absence is None:
            attendance.missing.append(day)
        else:
            attendance.absent[day] = absence.get_kind_display()
    return attendance


def settled_workdays(rules, period, now):
    calendar = work_calendar(rules, period.first, period.last)
    return [day for day in days_of(period) if calendar.is_workday(day) and settled(rules, day, now)]


def attendance_in(rules, period, now, people=()):
    counted = counted_period(rules, period)
    if counted is None:
        return {}
    spans = spans_by_account(counted.first, counted.last)
    accounts = present_accounts().filter(pk__in=[pk for pk in spans if not people or pk in people])
    days = settled_workdays(rules, counted, now)
    had_lunch = lunch_days(accounts, counted)
    absences = absences_by_account(counted.first, counted.last)
    found = (attendance_of(account, days, spans[account.pk], absences.get(account.pk, []), had_lunch) for account in accounts)
    return {attendance.account.pk: attendance for attendance in found if attendance}
