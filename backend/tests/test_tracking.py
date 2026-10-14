from datetime import date, datetime, timedelta

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from accounts.models import Account, Role
from directory.sync import run_sync
from lunches.models import TrackingSpan
from lunches.tracking import follow_tracking, spans_by_account, tracked_on
from staff.changes import change_role, set_blocked, set_track_lunch
from staff.local_accounts import Profile, create_local_account
from tests.factories import make_account
from tests.test_directory import BASE_DN, domain  # noqa: F401
from tests.test_directory_sync import change

pytestmark = pytest.mark.django_db

BEFORE_SPANS = [("accounts", "0005_remove_department_position"), ("lunches", "0003_lunchrules_rabbit_enabled")]
PETROV_DN = f"CN=Petrov,{BASE_DN}"
MONDAY = date(2026, 3, 2)


def moment(day):
    return timezone.make_aware(datetime.combine(day, datetime.min.time().replace(hour=10)))


def spans(account):
    return list(TrackingSpan.objects.filter(account=account).order_by("started_on").values_list("started_on", "ended_on"))


def today():
    return timezone.localdate()


def tracked_since(day, login="worker", role=Role.EMPLOYEE):
    account = make_account(login=login, role=role)
    follow_tracking(account, moment(day))
    return account


def test_tracked_person_gets_a_span_from_the_day_tracking_starts():
    account = tracked_since(MONDAY)

    assert spans(account) == [(MONDAY, None)]


def test_following_twice_keeps_one_span():
    account = tracked_since(MONDAY)

    follow_tracking(account, moment(MONDAY + timedelta(days=3)))

    assert spans(account) == [(MONDAY, None)]


def test_blocking_ends_the_span_on_that_day():
    account = tracked_since(MONDAY)
    account.is_active = False

    follow_tracking(account, moment(MONDAY + timedelta(days=4)))

    assert spans(account) == [(MONDAY, MONDAY + timedelta(days=4))]


def test_returning_later_opens_a_new_span():
    account = tracked_since(MONDAY)
    account.is_active = False
    follow_tracking(account, moment(MONDAY + timedelta(days=1)))
    account.is_active = True

    follow_tracking(account, moment(MONDAY + timedelta(days=7)))

    assert spans(account) == [(MONDAY, MONDAY + timedelta(days=1)), (MONDAY + timedelta(days=7), None)]


def test_returning_the_same_day_continues_the_span():
    account = tracked_since(MONDAY)
    account.track_lunch = False
    follow_tracking(account, moment(MONDAY + timedelta(days=2)))
    account.track_lunch = True

    follow_tracking(account, moment(MONDAY + timedelta(days=2)))

    assert spans(account) == [(MONDAY, None)]


def test_tracking_stopped_on_its_first_day_leaves_no_span():
    account = tracked_since(MONDAY)
    account.track_lunch = False

    follow_tracking(account, moment(MONDAY))

    assert spans(account) == []


@pytest.mark.parametrize("role", [Role.ADMIN])
def test_people_who_cannot_have_lunch_get_no_span(role):
    account = tracked_since(MONDAY, role=role)

    assert spans(account) == []


def test_span_covers_its_days_and_not_the_end_day():
    account = tracked_since(MONDAY)
    account.is_active = False
    follow_tracking(account, moment(MONDAY + timedelta(days=3)))
    own = spans_by_account(MONDAY, MONDAY + timedelta(days=10))[account.pk]

    assert [tracked_on(own, MONDAY + timedelta(days=shift)) for shift in range(-1, 5)] == [False, True, True, True, False, False]


def test_spans_outside_the_period_are_left_out():
    early = tracked_since(MONDAY, login="early")
    early.is_active = False
    follow_tracking(early, moment(MONDAY + timedelta(days=2)))
    late = tracked_since(MONDAY + timedelta(days=20), login="late")

    assert set(spans_by_account(MONDAY + timedelta(days=2), MONDAY + timedelta(days=10))) == set()
    assert set(spans_by_account(MONDAY, MONDAY + timedelta(days=30))) == {early.pk, late.pk}


def test_staff_changes_follow_tracking():
    boss = make_account(login="boss", role=Role.ADMIN)
    worker = tracked_since(MONDAY)

    set_blocked(boss, worker, True)
    assert spans(worker) == [(MONDAY, today())]
    set_blocked(boss, worker, False)
    assert spans(worker) == [(MONDAY, None)]
    set_track_lunch(worker, False)
    assert spans(worker) == [(MONDAY, today())]
    set_track_lunch(worker, True)
    change_role(boss, worker, Role.HR)
    assert spans(worker) == [(MONDAY, today())]


def test_new_local_account_is_tracked_from_today():
    issued = create_local_account("novikov", Profile("Новиков Никита"), Role.EMPLOYEE)

    assert spans(issued.account) == [(today(), None)]


def test_directory_sync_opens_and_closes_spans(domain):  # noqa: F811
    domain.bind()
    run_sync(timezone.now())
    petrov = Account.objects.get(login="petrov")
    assert spans(petrov) == [(today(), None)]

    change(domain, PETROV_DN, "memberOf", [])
    run_sync(timezone.now())

    assert spans(petrov) == []


@pytest.mark.django_db(transaction=True)
def test_upgrade_opens_spans_for_people_tracked_now_from_their_creation_day():
    executor = MigrationExecutor(connection)
    executor.migrate(BEFORE_SPANS)
    old_account = executor.loader.project_state(BEFORE_SPANS).apps.get_model("accounts", "Account")
    created = timezone.make_aware(datetime(2026, 1, 15, 9, 0))
    people = {
        "worker": {},
        "blocked": {"is_active": False},
        "untracked": {"track_lunch": False},
        "chief": {"role": "admin"},
        "gone": {"source": "domain", "in_directory": False},
        "present": {"source": "domain"},
    }
    for login_name, fields in people.items():
        old_account.objects.create(login=login_name, **fields)
    old_account.objects.update(created_at=created)

    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate(executor.loader.graph.leaf_nodes())

    opened = {span.account.login: (span.started_on, span.ended_on) for span in TrackingSpan.objects.select_related("account")}
    assert opened == {"worker": (date(2026, 1, 15), None), "present": (date(2026, 1, 15), None)}
