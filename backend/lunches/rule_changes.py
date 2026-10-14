from dataclasses import dataclass
from datetime import date, time

from django.utils import timezone

from lunches.clock import clock_text, today
from lunches.rules import current_rules

MIN_LIMIT_MINUTES = 5
MAX_LIMIT_MINUTES = 240
WEEKDAYS = "1234567"

BAD_LIMIT = f"Лимит обеда — от {MIN_LIMIT_MINUTES} до {MAX_LIMIT_MINUTES} минут"
NO_WORKDAYS = "Отметьте хотя бы один рабочий день"
BAD_WORKDAYS = "Дни недели указываются цифрами от 1 (понедельник) до 7 (воскресенье)"
WINDOW_ORDER = "Окно обеда должно начинаться раньше, чем заканчиваться"
WINDOW_AFTER_DAY = "Окно обеда должно закончиться не позже конца рабочего дня ({end})"


class InvalidRules(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class RulesDraft:
    limit_minutes: int
    workdays: str
    day_end: time
    window_enabled: bool
    window_start: time
    window_end: time
    missing_enabled: bool | None = None
    missing_since: date | None = None


def normalized_workdays(text):
    if set(text) - set(WEEKDAYS):
        raise InvalidRules(BAD_WORKDAYS)
    if not text:
        raise InvalidRules(NO_WORKDAYS)
    return "".join(sorted(set(text)))


def check_limit(minutes):
    if not MIN_LIMIT_MINUTES <= minutes <= MAX_LIMIT_MINUTES:
        raise InvalidRules(BAD_LIMIT)


def check_window(draft):
    if not draft.window_enabled:
        return
    if draft.window_start >= draft.window_end:
        raise InvalidRules(WINDOW_ORDER)
    if draft.window_end > draft.day_end:
        raise InvalidRules(WINDOW_AFTER_DAY.format(end=clock_text(draft.day_end)))


def apply_missing(rules, draft):
    if draft.missing_enabled is None:
        return
    rules.missing_enabled = draft.missing_enabled
    if draft.missing_since is not None:
        rules.missing_since = draft.missing_since
    elif draft.missing_enabled and rules.missing_since is None:
        rules.missing_since = today(timezone.now())


def save_rules(draft):
    check_limit(draft.limit_minutes)
    check_window(draft)
    rules = current_rules()
    rules.limit_minutes = draft.limit_minutes
    rules.workdays = normalized_workdays(draft.workdays)
    rules.day_end = draft.day_end
    rules.window_enabled = draft.window_enabled
    rules.window_start = draft.window_start
    rules.window_end = draft.window_end
    apply_missing(rules, draft)
    rules.save()
    return rules


def switch_rabbit(enabled):
    rules = current_rules()
    rules.rabbit_enabled = enabled
    rules.save(update_fields=["rabbit_enabled"])
    return rules
