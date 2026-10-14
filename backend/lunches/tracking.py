from django.db import transaction

from lunches.clock import today
from lunches.corrections import can_receive_lunch
from lunches.models import TrackingSpan


def open_span(account):
    return TrackingSpan.objects.filter(account=account, ended_on__isnull=True).first()


def resume(account, day):
    closed_today = TrackingSpan.objects.filter(account=account, ended_on=day).first()
    if closed_today is None:
        TrackingSpan.objects.create(account=account, started_on=day)
        return
    closed_today.ended_on = None
    closed_today.save(update_fields=["ended_on"])


def close(span, day):
    if span.started_on >= day:
        span.delete()
        return
    span.ended_on = day
    span.save(update_fields=["ended_on"])


@transaction.atomic
def follow_tracking(account, now):
    day = today(now)
    span = open_span(account)
    if can_receive_lunch(account) and span is None:
        resume(account, day)
    elif not can_receive_lunch(account) and span is not None:
        close(span, day)


def covers(span, day):
    return span.started_on <= day and (span.ended_on is None or day < span.ended_on)


def tracked_on(spans, day):
    return any(covers(span, day) for span in spans)


def spans_by_account(first, last):
    overlapping = TrackingSpan.objects.filter(started_on__lte=last).exclude(ended_on__lte=first)
    groups = {}
    for span in overlapping.order_by("started_on"):
        groups.setdefault(span.account_id, []).append(span)
    return groups
