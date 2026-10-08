from datetime import timedelta

from django.db import IntegrityError, transaction

from lunches.clock import clock_text, local, moment_of, today
from lunches.models import Lunch
from lunches.rules import current_rules, inside_window, is_workday

UNDO_MINUTES = 5
UNDO_WINDOW = timedelta(minutes=UNDO_MINUTES)
WARNING_MINUTES = 5

NOT_TRACKED = "Ваши обеды не учитываются — отмечать их не нужно"
DAY_OFF = "Сегодня нерабочий день"
DAY_OVER = "Рабочий день закончился в {end}"
OUTSIDE_WINDOW = "Уйти на обед можно с {start} до {end}"
ALREADY_ON_LUNCH = "Вы уже на обеде"
ALREADY_HAD_LUNCH = "Сегодня обед уже был"
NOT_ON_LUNCH = "Вы сейчас не на обеде"
UNDO_EXPIRED = f"Отменить можно только в первые {UNDO_MINUTES} мин. Если ушли по ошибке — нажмите «Вернулся» и сообщите HR"


class LunchRefused(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def close_overdue(now):
    rules = current_rules()
    for lunch in Lunch.objects.filter(ended_at__isnull=True):
        closing = moment_of(lunch.day, rules.day_end)
        if closing <= now:
            Lunch.objects.filter(pk=lunch.pk, ended_at__isnull=True).update(ended_at=max(closing, lunch.started_at), auto_closed=True)


def todays_lunch(account, now):
    return Lunch.objects.filter(account=account, day=today(now)).first()


def start_refusal(account, rules, lunch, now):
    clock = local(now).time()
    if not account.track_lunch:
        return NOT_TRACKED
    if lunch is not None:
        return ALREADY_ON_LUNCH if lunch.ended_at is None else ALREADY_HAD_LUNCH
    if not is_workday(rules, today(now)):
        return DAY_OFF
    if clock >= rules.day_end:
        return DAY_OVER.format(end=clock_text(rules.day_end))
    if not inside_window(rules, clock):
        return OUTSIDE_WINDOW.format(start=clock_text(rules.window_start), end=clock_text(rules.window_end))
    return ""


def start_lunch(account, now):
    close_overdue(now)
    rules = current_rules()
    refusal = start_refusal(account, rules, todays_lunch(account, now), now)
    if refusal:
        raise LunchRefused(refusal)
    try:
        with transaction.atomic():
            return Lunch.objects.create(account=account, day=today(now), started_at=now, limit_minutes=rules.limit_minutes)
    except IntegrityError as error:
        raise LunchRefused(ALREADY_HAD_LUNCH) from error


def ongoing_lunch(account, now):
    close_overdue(now)
    lunch = Lunch.objects.select_for_update().filter(account=account, ended_at__isnull=True).first()
    if lunch is None:
        raise LunchRefused(NOT_ON_LUNCH)
    return lunch


@transaction.atomic
def finish_lunch(account, now):
    lunch = ongoing_lunch(account, now)
    lunch.ended_at = now
    lunch.save(update_fields=["ended_at"])
    return lunch


def undo_deadline(lunch):
    return lunch.started_at + UNDO_WINDOW


@transaction.atomic
def undo_lunch(account, now):
    lunch = ongoing_lunch(account, now)
    if now > undo_deadline(lunch):
        raise LunchRefused(UNDO_EXPIRED)
    lunch.delete()
