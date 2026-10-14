from ninja import Router, Schema

from accounts.permissions import require_admin
from accounts.security import session_auth
from journal.entries import record_changes
from journal.models import Action
from journal.snapshots import rules_snapshot
from lunches.rule_changes import switch_rabbit
from lunches.rules import current_rules

router = Router(tags=["Оформление"])


class AppearanceOut(Schema):
    rabbit: bool


class RabbitIn(Schema):
    enabled: bool


def describe(rules):
    return AppearanceOut(rabbit=rules.rabbit_enabled)


@router.get("", auth=None, response=AppearanceOut)
def appearance(request):
    return describe(current_rules())


@router.put("/rabbit", auth=session_auth, response=AppearanceOut)
def set_rabbit(request, payload: RabbitIn):
    require_admin(request)
    before = rules_snapshot(current_rules())
    saved = switch_rabbit(payload.enabled)
    record_changes(request, Action.RULES_CHANGED, before, rules_snapshot(saved))
    return describe(saved)
