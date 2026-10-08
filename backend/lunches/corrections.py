from dataclasses import dataclass
from datetime import time

from django.db import transaction

from lunches.clock import moment_of
from lunches.models import Lunch

OWN_LUNCH = "Свой обед исправить нельзя — попросите коллегу"
REASON_REQUIRED = "Укажите причину исправления"
TIME_ORDER = "Время возврата должно быть позже времени ухода"
FUTURE_RETURN = "Время возврата ещё не наступило"


class CorrectionRefused(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class Correction:
    started: time
    ended: time
    reason: str


def corrected_moments(lunch, correction, now):
    started_at = moment_of(lunch.day, correction.started)
    ended_at = moment_of(lunch.day, correction.ended)
    if ended_at <= started_at:
        raise CorrectionRefused(TIME_ORDER)
    if ended_at > now:
        raise CorrectionRefused(FUTURE_RETURN)
    return started_at, ended_at


def checked_reason(actor, lunch, correction):
    if lunch.account_id == actor.pk:
        raise CorrectionRefused(OWN_LUNCH)
    reason = correction.reason.strip()
    if not reason:
        raise CorrectionRefused(REASON_REQUIRED)
    return reason


@transaction.atomic
def correct_lunch(actor, lunch_id, correction, now):
    lunch = Lunch.objects.select_for_update().get(pk=lunch_id)
    reason = checked_reason(actor, lunch, correction)
    lunch.started_at, lunch.ended_at = corrected_moments(lunch, correction, now)
    lunch.corrected_by = actor
    lunch.corrected_at = now
    lunch.correction_reason = reason
    lunch.save(update_fields=["started_at", "ended_at", "corrected_by", "corrected_at", "correction_reason"])
    return lunch
