from dataclasses import dataclass
from datetime import time

from django.db import IntegrityError, transaction

from accounts.lunch_policy import can_have_lunch
from lunches.clock import moment_of, today
from lunches.models import Lunch
from lunches.rules import current_rules
from staff.status import StaffStatus, gone, status_of

OWN_LUNCH = "Свой обед исправить нельзя — попросите коллегу"
REASON_REQUIRED = "Укажите причину исправления"
TIME_ORDER = "Время возврата должно быть позже времени ухода"
FUTURE_RETURN = "Время возврата ещё не наступило"
OWN_ADD = "Себе обед добавить нельзя — попросите коллегу"
UNTRACKED_PERSON = "Обеды этого сотрудника не учитываются"
FUTURE_DAY = "Нельзя добавить обед на будущий день"
ALREADY_HAS_LUNCH = "У сотрудника уже есть обед в этот день — исправьте его время через «⋯»"


class CorrectionRefused(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class Correction:
    started: time
    ended: time
    reason: str


def checked_moments(day, correction, now):
    started_at = moment_of(day, correction.started)
    ended_at = moment_of(day, correction.ended)
    if ended_at <= started_at:
        raise CorrectionRefused(TIME_ORDER)
    if ended_at > now:
        raise CorrectionRefused(FUTURE_RETURN)
    return started_at, ended_at


def required_reason(correction):
    reason = correction.reason.strip()
    if not reason:
        raise CorrectionRefused(REASON_REQUIRED)
    return reason


def refuse_own(actor, account_id, message):
    if account_id == actor.pk:
        raise CorrectionRefused(message)


def can_receive_lunch(account):
    return account.track_lunch and can_have_lunch(account.role) and status_of(account) == StaffStatus.ACTIVE


@transaction.atomic
def correct_lunch(actor, lunch_id, correction, now):
    lunch = Lunch.objects.select_for_update().exclude(gone("account__")).get(pk=lunch_id)
    refuse_own(actor, lunch.account_id, OWN_LUNCH)
    reason = required_reason(correction)
    lunch.started_at, lunch.ended_at = checked_moments(lunch.day, correction, now)
    lunch.corrected_by = actor
    lunch.corrected_at = now
    lunch.correction_reason = reason
    lunch.save(update_fields=["started_at", "ended_at", "corrected_by", "corrected_at", "correction_reason"])
    return lunch


def check_addable(actor, account, day, now):
    refuse_own(actor, account.pk, OWN_ADD)
    if not can_receive_lunch(account):
        raise CorrectionRefused(UNTRACKED_PERSON)
    if day > today(now):
        raise CorrectionRefused(FUTURE_DAY)
    if Lunch.objects.filter(account=account, day=day).exists():
        raise CorrectionRefused(ALREADY_HAS_LUNCH)


def add_lunch(actor, account, day, correction, now):
    check_addable(actor, account, day, now)
    reason = required_reason(correction)
    started_at, ended_at = checked_moments(day, correction, now)
    try:
        with transaction.atomic():
            return Lunch.objects.create(
                account=account,
                day=day,
                started_at=started_at,
                ended_at=ended_at,
                limit_minutes=current_rules().limit_minutes,
                corrected_by=actor,
                corrected_at=now,
                correction_reason=reason,
                added_by_hand=True,
            )
    except IntegrityError as error:
        raise CorrectionRefused(ALREADY_HAS_LUNCH) from error
