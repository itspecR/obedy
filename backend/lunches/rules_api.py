from datetime import datetime, time

from ninja import Field, Router, Schema
from ninja.errors import HttpError

from accounts.permissions import require_admin
from accounts.security import session_auth
from lunches.rule_changes import MAX_LIMIT_MINUTES, MIN_LIMIT_MINUTES, WEEKDAYS, InvalidRules, RulesDraft, save_rules
from lunches.rules import current_rules

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
    require_admin(request)
    return describe_rules(current_rules())


@router.put("", auth=session_auth, response=RulesOut)
def update_rules(request, payload: RulesIn):
    require_admin(request)
    try:
        return describe_rules(save_rules(payload.draft()))
    except InvalidRules as invalid:
        raise HttpError(400, invalid.message) from invalid
