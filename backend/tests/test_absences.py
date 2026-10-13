import json
from datetime import date

import pytest

from accounts.models import Account, Role, Source
from journal.models import Action, JournalEntry
from lunches.absences import absence_on, absences_by_account
from lunches.models import Absence
from tests.test_stats import JSON, frozen, person, signed_in  # noqa: F401

pytestmark = pytest.mark.django_db

ABSENCES = "/api/absences"
NOVEMBER = "?date_from=2026-11-01&date_to=2026-11-30"


def body(first, last, kind="vacation", note="", **extra):
    return json.dumps({"first": first, "last": last, "kind": kind, "note": note, **extra})


def add(client, account, first="2026-11-02", last="2026-11-13", kind="vacation", note=""):
    return client.post(ABSENCES, body(first, last, kind, note, account_id=account.pk), content_type=JSON)


@pytest.fixture
def hr():
    return signed_in("hr", Role.HR)


@pytest.fixture
def ivanov():
    return person("ivanov", "Иванов Иван")


def test_hr_marks_an_absence_and_sees_it_in_the_period(hr, ivanov):
    created = add(hr, ivanov, note="  приказ № 45 ")

    assert created.status_code == 201
    assert created.json() == {
        "id": created.json()["id"],
        "person_id": ivanov.pk,
        "name": "Иванов Иван",
        "login": "ivanov",
        "first": "2026-11-02",
        "last": "2026-11-13",
        "kind": "vacation",
        "note": "приказ № 45",
    }
    assert [item["name"] for item in hr.get(f"{ABSENCES}{NOVEMBER}").json()] == ["Иванов Иван"]
    assert hr.get(f"{ABSENCES}?date_from=2026-12-01&date_to=2026-12-31").json() == []


def test_absences_are_listed_by_start_then_name(hr, ivanov):
    petrova = person("petrova", "Петрова Анна")
    add(hr, petrova, "2026-11-10", "2026-11-12", "sick")
    add(hr, ivanov, "2026-10-28", "2026-11-03")
    add(hr, person("abramov", "Абрамов Антон"), "2026-11-10", "2026-11-10", "other")

    listed = hr.get(f"{ABSENCES}{NOVEMBER}").json()

    assert [(item["name"], item["kind"]) for item in listed] == [("Иванов Иван", "vacation"), ("Абрамов Антон", "other"), ("Петрова Анна", "sick")]


@pytest.mark.parametrize(
    ("first", "last", "message"),
    [
        ("2026-11-10", "2026-11-09", "Дата «по» не может быть раньше даты «с»"),
        ("2026-01-01", "2027-01-02", "Отсутствие — не дольше года. Разбейте его на части"),
    ],
)
def test_bad_dates_are_explained(hr, ivanov, first, last, message):
    response = add(hr, ivanov, first, last)

    assert (response.status_code, response.json()["detail"]) == (400, message)


def test_overlapping_absence_of_the_same_person_is_refused(hr, ivanov):
    add(hr, ivanov)

    clash = add(hr, ivanov, "2026-11-13", "2026-11-20", "sick")
    other_person = add(hr, person("petrova", "Петрова Анна"), "2026-11-13", "2026-11-20")
    next_day = add(hr, ivanov, "2026-11-14", "2026-11-20", "sick")

    assert (clash.status_code, clash.json()["detail"]) == (400, "В эти даты уже есть отсутствие: Отпуск 02.11.2026 — 13.11.2026. Исправьте его")
    assert (other_person.status_code, next_day.status_code) == (201, 201)


def test_change_keeps_its_own_dates_but_not_others(hr, ivanov):
    first = add(hr, ivanov).json()
    add(hr, ivanov, "2026-11-20", "2026-11-25", "sick")

    longer = hr.put(f"{ABSENCES}/{first['id']}", body("2026-11-02", "2026-11-16", "vacation", "продлён"), content_type=JSON)
    clash = hr.put(f"{ABSENCES}/{first['id']}", body("2026-11-02", "2026-11-21"), content_type=JSON)

    assert (longer.status_code, longer.json()["last"], longer.json()["note"]) == (200, "2026-11-16", "продлён")
    assert clash.status_code == 400


def test_delete_and_missing_absence(hr, ivanov):
    created = add(hr, ivanov).json()

    assert hr.delete(f"{ABSENCES}/{created['id']}").status_code == 204
    assert hr.delete(f"{ABSENCES}/{created['id']}").json()["detail"] == "Отсутствие не найдено. Обновите страницу"
    assert hr.put(f"{ABSENCES}/{created['id']}", body("2026-11-02", "2026-11-03"), content_type=JSON).status_code == 404


def test_untracked_or_unknown_person_cannot_get_an_absence(hr):
    untracked = Account.objects.create(login="kadry", full_name="Кадрова Ольга", role=Role.HR, track_lunch=False)
    departed = Account.objects.create(login="left", full_name="Ушедший", source=Source.DOMAIN, in_directory=False)

    assert add(hr, untracked).json()["detail"] == "Обеды этого сотрудника не учитываются"
    assert add(hr, departed).status_code == 404


def test_absence_changes_go_to_the_journal_with_the_person(hr, ivanov):
    created = add(hr, ivanov, note="приказ").json()
    hr.put(f"{ABSENCES}/{created['id']}", body("2026-11-02", "2026-11-14", "vacation", "приказ"), content_type=JSON)
    hr.delete(f"{ABSENCES}/{created['id']}")

    entries = list(JournalEntry.objects.filter(action__startswith="absence").order_by("created_at", "pk"))
    assert [entry.action for entry in entries] == [Action.ABSENCE_ADDED, Action.ABSENCE_CHANGED, Action.ABSENCE_REMOVED]
    assert {entry.target_id for entry in entries} == {ivanov.pk}
    assert entries[1].details == [{"label": "По", "before": "13.11.2026", "after": "14.11.2026"}]
    assert entries[0].details[0] == {"label": "Вид", "before": None, "after": "Отпуск"}


@pytest.mark.parametrize("role", [Role.EMPLOYEE])
def test_employee_has_no_access(role, ivanov):
    client = signed_in("worker", role)

    assert client.get(f"{ABSENCES}{NOVEMBER}").status_code == 403
    assert add(client, ivanov).status_code == 403


def test_absence_is_found_by_day_for_each_person(ivanov):
    vacation = Absence.objects.create(account=ivanov, first=date(2026, 11, 2), last=date(2026, 11, 13), kind="vacation")
    own = absences_by_account(date(2026, 11, 1), date(2026, 11, 30))[ivanov.pk]

    assert [absence_on(own, date(2026, 11, day)) for day in (1, 2, 13, 14)] == [None, vacation, vacation, None]
