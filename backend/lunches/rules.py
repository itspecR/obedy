from lunches.models import RULES_ID, LunchRules


def current_rules():
    return LunchRules.objects.get_or_create(pk=RULES_ID)[0]


def is_workday(rules, day):
    return str(day.isoweekday()) in rules.workdays


def inside_window(rules, clock_time):
    return not rules.window_enabled or rules.window_start <= clock_time < rules.window_end
