from datetime import datetime, time

from ninja import Field, Router, Schema
from ninja.errors import HttpError

from accounts.security import session_auth
from journal.entries import record_changes
from journal.models import Action
from journal.snapshots import rules_snapshot
from lunches.rule_changes import MAX_LIMIT_MINUTES, MIN_LIMIT_MINUTES, WEEKDAYS, InvalidRules, RulesDraft, save_rules
from lunches.rules import current_rules
from lunches.supervision import require_supervisor

RULES_ONLY = "Правила обеда доступны HR и администратору"

router = Router(tags=["Правила обеда"])


class RulesOut(Schema):
    limit_minutes: int
    workdays: str
    day_end: time
    window_enabled: bool
    window_start: time
    window_end: time
    updated_at: datetime
    min_limit_minutes: int
    max_limit_minutes: int


class RulesIn(Schema):
    limit_minutes: int
    workdays: str = Field(max_length=len(WEEKDAYS))
    day_end: time
    window_enabled: bool
    window_start: time
    window_end: time

    def draft(self):
        return RulesDraft(self.limit_minutes, self.workdays, self.day_end, self.window_enabled, self.window_start, self.window_end)


def describe_rules(rules):
    return RulesOut(
        limit_minutes=rules.limit_minutes,
        workdays=rules.workdays,
        day_end=rules.day_end,
        window_enabled=rules.window_enabled,
        window_start=rules.window_start,
        window_end=rules.window_end,
        updated_at=rules.updated_at,
        min_limit_minutes=MIN_LIMIT_MINUTES,
        max_limit_minutes=MAX_LIMIT_MINUTES,
    )


@router.get("", auth=session_auth, response=RulesOut)
def rules(request):
    require_supervisor(request, RULES_ONLY)
    return describe_rules(current_rules())


@router.put("", auth=session_auth, response=RulesOut)
def update_rules(request, payload: RulesIn):
    require_supervisor(request, RULES_ONLY)
    before = rules_snapshot(current_rules())
    try:
        saved = save_rules(payload.draft())
    except InvalidRules as invalid:
        raise HttpError(400, invalid.message) from invalid
    record_changes(request, Action.RULES_CHANGED, before, rules_snapshot(saved))
    return describe_rules(saved)
