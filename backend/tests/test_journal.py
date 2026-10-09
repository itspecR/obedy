import json
from datetime import date, time, timedelta

import pytest
from django.core.management import CommandError, call_command
from django.db import DatabaseError
from django.test import Client, override_settings
from django.utils import timezone

import directory.api
import journal.system
from accounts.models import Account, Role, Source
from journal.models import Action, JournalEntry
from journal.retention import RETENTION_DAYS
from journal.system import meminfo, pretty_name, process_started_at
from lunches.clock import moment_of
from lunches.models import Lunch
from tests.factories import DEFAULT_PASSWORD, make_account

pytestmark = pytest.mark.django_db

JSON = "application/json"
ADDRESS = "10.0.0.7"
TODAY = timezone.localdate()
PERIOD = f"?date_from={TODAY - timedelta(days=1)}&date_to={TODAY}"
FORGOTTEN_SECRET = "Пароль-в-поле-логина-1"


def client():
    return Client(HTTP_X_REAL_IP=ADDRESS)


def sign_in(guest, login):
    return guest.post("/api/auth/login", json.dumps({"login": login, "password": DEFAULT_PASSWORD}), content_type=JSON)


def signed_in(login="admin", role=Role.ADMIN):
    account = make_account(login=login, role=role, must_change_password=False)
    guest = client()
    sign_in(guest, login)
    return guest, account


def entries(action):
    return list(JournalEntry.objects.filter(action=action).order_by("pk"))


def rows(entry):
    return [(row["label"], row["before"], row["after"]) for row in entry.details]


def put(guest, path, payload):
    return guest.put(path, json.dumps(payload), content_type=JSON)


def post(guest, path, payload=None):
    return guest.post(path, json.dumps(payload or {}), content_type=JSON)


def test_successful_login_and_logout_are_recorded_with_address():
    guest, account = signed_in("ivanov", Role.EMPLOYEE)
    post(guest, "/api/auth/logout")

    login, logout = entries(Action.LOGIN)[0], entries(Action.LOGOUT)[0]
    assert (login.actor, login.address) == (account, ADDRESS)
    assert logout.actor == account


def test_failed_login_names_the_account_but_never_the_typed_text():
    account = make_account(login="ivanov", must_change_password=False)
    guest = client()
    guest.post("/api/auth/login", json.dumps({"login": "IVANOV", "password": "wrong-password"}), content_type=JSON)
    guest.post("/api/auth/login", json.dumps({"login": FORGOTTEN_SECRET, "password": "x"}), content_type=JSON)

    known, unknown = entries(Action.LOGIN_FAILED)
    assert (known.actor, known.target, known.address) == (None, account, ADDRESS)
    assert (unknown.actor, unknown.target, unknown.details) == (None, None, [])
    assert FORGOTTEN_SECRET not in json.dumps(list(JournalEntry.objects.values()), default=str)


def test_blocked_account_attempt_is_a_failed_login():
    account = make_account(login="ivanov", must_change_password=False)
    Account.objects.filter(pk=account.pk).update(is_active=False)

    sign_in(client(), "ivanov")

    assert [entry.target for entry in entries(Action.LOGIN_FAILED)] == [account]
    assert entries(Action.LOGIN) == []


def test_own_password_change_is_recorded_without_the_password():
    guest, account = signed_in("ivanov", Role.EMPLOYEE)
    new_password = "Новый-пароль-2026!"

    post(guest, "/api/auth/change-password", {"current_password": DEFAULT_PASSWORD, "new_password": new_password})

    assert [entry.actor for entry in entries(Action.PASSWORD_CHANGED)] == [account]
    assert new_password not in json.dumps(list(JournalEntry.objects.values()), default=str)


def test_role_change_keeps_before_and_after():
    guest, admin = signed_in()
    member = make_account(login="petrova", full_name="Петрова Анна")

    put(guest, f"/api/staff/{member.pk}/role", {"role": "hr"})

    entry = entries(Action.ROLE_CHANGED)[0]
    assert (entry.actor, entry.target, entry.address) == (admin, member, ADDRESS)
    assert ("Роль", "Сотрудник", "HR") in rows(entry)


def test_unchanged_or_refused_change_leaves_no_entry():
    guest, admin = signed_in()
    member = make_account(login="petrova")

    put(guest, f"/api/staff/{member.pk}/role", {"role": "employee"})
    put(guest, f"/api/staff/{admin.pk}/blocked", {"blocked": True})

    assert JournalEntry.objects.exclude(action=Action.LOGIN).count() == 0


def test_blocking_and_unblocking_are_separate_actions():
    guest, _ = signed_in()
    member = make_account(login="petrova")

    put(guest, f"/api/staff/{member.pk}/blocked", {"blocked": True})
    put(guest, f"/api/staff/{member.pk}/blocked", {"blocked": False})

    assert rows(entries(Action.BLOCKED)[0]) == [("Доступ", "открыт", "заблокирован")]
    assert rows(entries(Action.UNBLOCKED)[0]) == [("Доступ", "заблокирован", "открыт")]


def test_created_account_and_issued_password_never_store_the_password():
    guest, _ = signed_in()

    created = post(guest, "/api/staff", {"login": "sidorov", "full_name": "Сидоров Сидор", "role": "employee"}).json()
    issued = post(guest, f"/api/staff/{created['member']['id']}/password").json()

    creation = entries(Action.ACCOUNT_CREATED)[0]
    assert ("Логин", None, "sidorov") in rows(creation)
    assert ("ФИО", None, "Сидоров Сидор") in rows(creation)
    assert entries(Action.PASSWORD_ISSUED)[0].target.login == "sidorov"
    stored = json.dumps(list(JournalEntry.objects.values()), default=str)
    assert created["temporary_password"] not in stored
    assert issued["temporary_password"] not in stored


def test_lunch_correction_and_addition_keep_times_and_reason():
    guest, hr = signed_in("kadry", Role.HR)
    member = make_account(login="petrova", must_change_password=False)
    yesterday = TODAY - timedelta(days=1)
    lunch = Lunch.objects.create(account=member, day=yesterday, started_at=moment_of(yesterday, time(12, 0)), limit_minutes=45)

    put(guest, f"/api/lunch/board/{lunch.pk}/correction", {"started_at": "12:00", "ended_at": "12:40", "reason": "забыла нажать"})
    earlier = str(yesterday - timedelta(days=1))
    post(guest, "/api/lunch/board/lunches", {"account_id": member.pk, "day": earlier, "started_at": "13:00", "ended_at": "13:30", "reason": "был на обеде"})

    corrected, added = entries(Action.LUNCH_CORRECTED)[0], entries(Action.LUNCH_ADDED)[0]
    assert (corrected.actor, corrected.target) == (hr, member)
    assert rows(corrected) == [("День", None, yesterday.strftime("%d.%m.%Y")), ("Вернулся", "—", "12:40"), ("Причина", None, "забыла нажать")]
    assert ("Ушёл", None, "13:00") in rows(added)
    assert ("Причина", None, "был на обеде") in rows(added)


def test_lunch_deletion_keeps_what_was_deleted_and_why():
    guest, hr = signed_in("kadry", Role.HR)
    member = make_account(login="petrova", must_change_password=False)
    yesterday = TODAY - timedelta(days=1)
    started, ended = moment_of(yesterday, time(12, 0)), moment_of(yesterday, time(12, 40))
    lunch = Lunch.objects.create(account=member, day=yesterday, started_at=started, ended_at=ended, limit_minutes=45)

    guest.delete(f"/api/lunch/board/{lunch.pk}", json.dumps({"reason": "добавлен по ошибке"}), content_type=JSON)

    entry = entries(Action.LUNCH_DELETED)[0]
    assert (entry.actor, entry.target) == (hr, member)
    assert rows(entry) == [
        ("День", None, yesterday.strftime("%d.%m.%Y")),
        ("Ушёл", "12:00", None),
        ("Вернулся", "12:40", None),
        ("Причина", None, "добавлен по ошибке"),
    ]


def test_rules_change_lists_only_changed_fields():
    guest, _ = signed_in()
    rules = guest.get("/api/lunch/rules").json()

    kept = {key: rules[key] for key in ("workdays", "day_end", "window_enabled", "window_start", "window_end")}
    put(guest, "/api/lunch/rules", {**kept, "limit_minutes": 50})

    assert rows(entries(Action.RULES_CHANGED)[0]) == [("Лимит обеда", "45 мин", "50 мин")]


def test_access_changes_are_recorded():
    guest, _ = signed_in()

    network_id = post(guest, "/api/access/networks", {"network": "10.0.0.0/24", "note": "офис"}).json()["networks"][0]["id"]
    guest.delete(f"/api/access/networks/{network_id}")

    assert rows(entries(Action.NETWORK_ADDED)[0]) == [("Адрес", None, "10.0.0.0/24"), ("Заметка", None, "офис")]
    assert rows(entries(Action.NETWORK_REMOVED)[0]) == [("Адрес", "10.0.0.0/24", None), ("Заметка", "офис", None)]


def test_directory_change_marks_password_without_storing_it(monkeypatch):
    guest, _ = signed_in()
    secret = "service-secret-9"
    settings = {
        "enabled": False,
        "servers": "dc1.co.local",
        "mode": "ldaps",
        "port": None,
        "ca_certificate": "",
        "bind_user": "svc",
        "bind_password": secret,
        "base_dn": "",
        "group_dn": "",
        "session_days": 30,
    }

    put(guest, "/api/directory", settings)
    monkeypatch.setattr(directory.api, "check_connection", lambda config: type("Result", (), {"ok": False, "message": "Нет связи"})())
    post(guest, "/api/directory/check")

    changed = rows(entries(Action.DIRECTORY_CHANGED)[0])
    assert ("Серверы", "—", "dc1.co.local") in changed
    assert ("Пароль учётной записи для чтения", None, "изменён") in changed
    assert rows(entries(Action.DIRECTORY_CHECKED)[0]) == [("Итог", None, "Нет связи")]
    assert secret not in json.dumps(list(JournalEntry.objects.values()), default=str)


@pytest.mark.parametrize("role", [Role.EMPLOYEE, Role.HR])
def test_only_admin_reads_the_journal(role):
    guest, _ = signed_in("someone", role)

    assert guest.get(f"/api/journal{PERIOD}").status_code == 403
    assert guest.get("/api/journal/people").status_code == 403


def test_journal_lists_newest_first_with_people_and_details():
    guest, admin = signed_in()
    member = make_account(login="petrova", full_name="Петрова Анна")
    put(guest, f"/api/staff/{member.pk}/track-lunch", {"track_lunch": False})

    body = guest.get(f"/api/journal{PERIOD}").json()

    newest = body["entries"][0]
    assert newest["action"] == "track_lunch_changed"
    assert newest["actor"] == {"id": admin.pk, "name": "admin", "login": "admin"}
    assert newest["target"]["name"] == "Петрова Анна"
    assert newest["details"] == [{"label": "Учёт обеда", "before": "включено", "after": "выключено"}]
    assert body["entries"][1]["action"] == "login"
    assert body["has_more"] is False


def test_journal_filters_by_person_category_and_period():
    guest, admin = signed_in()
    member = make_account(login="petrova")
    put(guest, f"/api/staff/{member.pk}/blocked", {"blocked": True})
    sign_in(client(), "petrova")
    old = JournalEntry.objects.create(action=Action.LOGOUT, actor=member)
    JournalEntry.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=10))

    def actions(query):
        return [entry["action"] for entry in guest.get(f"/api/journal{PERIOD}{query}").json()["entries"]]

    assert actions(f"&person={member.pk}") == ["login_failed", "blocked"]
    assert actions("&category=logins") == ["login_failed", "login"]
    assert actions("&category=staff") == ["blocked"]
    assert guest.get(f"/api/journal?date_from={TODAY}&date_to={TODAY - timedelta(days=1)}").status_code == 400


def test_journal_pages_with_cursor():
    guest, admin = signed_in()
    JournalEntry.objects.bulk_create([JournalEntry(action=Action.LOGOUT, actor=admin) for _ in range(60)])

    first = guest.get(f"/api/journal{PERIOD}").json()
    second = guest.get(f"/api/journal{PERIOD}&before={first['entries'][-1]['id']}").json()

    assert (len(first["entries"]), first["has_more"]) == (50, True)
    assert (len(second["entries"]), second["has_more"]) == (11, False)


def test_departed_person_stays_in_history_but_not_in_filter_list():
    guest, _ = signed_in()
    departed = Account.objects.create(login="ushel", source=Source.DOMAIN, in_directory=False)
    JournalEntry.objects.create(action=Action.LOGIN, actor=departed)

    logins = [entry["actor"]["login"] for entry in guest.get(f"/api/journal{PERIOD}&category=logins").json()["entries"]]
    people = [person["login"] for person in guest.get("/api/journal/people").json()]

    assert "ushel" in logins
    assert "ushel" not in people


def test_entries_older_than_retention_are_deleted():
    account = make_account(login="ivanov")
    kept = JournalEntry.objects.create(action=Action.LOGIN, actor=account)
    expired = JournalEntry.objects.create(action=Action.LOGIN, actor=account)
    JournalEntry.objects.filter(pk=kept.pk).update(created_at=timezone.now() - timedelta(days=RETENTION_DAYS - 1))
    JournalEntry.objects.filter(pk=expired.pk).update(created_at=timezone.now() - timedelta(days=RETENTION_DAYS + 1))

    call_command("clean_journal")

    assert list(JournalEntry.objects.values_list("pk", flat=True)) == [kept.pk]


def test_empty_period_returns_nothing():
    guest, _ = signed_in()

    assert guest.get(f"/api/journal?date_from={date(2020, 1, 1)}&date_to={date(2020, 1, 1)}").json() == {"entries": [], "has_more": False}


def test_reset_needs_confirmation_and_keeps_everything_else():
    account = make_account(login="ivanov")
    Lunch.objects.create(account=account, day=TODAY, started_at=moment_of(TODAY, time(12, 0)), limit_minutes=45)

    with pytest.raises(CommandError):
        call_command("reset_lunches")

    assert Lunch.objects.count() == 1
    assert not entries(Action.LUNCHES_RESET)


def test_reset_deletes_all_lunches_and_is_recorded_as_server():
    account = make_account(login="ivanov")
    for offset in range(3):
        day = TODAY - timedelta(days=offset)
        Lunch.objects.create(account=account, day=day, started_at=moment_of(day, time(12, 0)), limit_minutes=45)
    JournalEntry.objects.create(action=Action.LOGIN, actor=account)

    call_command("reset_lunches", "--yes")

    reset = entries(Action.LUNCHES_RESET)[0]
    assert Lunch.objects.count() == 0
    assert Account.objects.filter(login="ivanov").exists()
    assert entries(Action.LOGIN)
    assert (reset.actor, reset.address, rows(reset)) == (None, "сервер", [("Удалено обедов", None, "3")])


def server_entries(action):
    return [entry for entry in entries(action) if entry.actor is None and entry.address == "сервер"]


def test_server_access_commands_are_recorded():
    call_command("access", "add", "10.9.9.0/24", "офис")
    call_command("access", "lan", "off")
    call_command("access", "remove", "10.9.9.0/24")

    assert rows(server_entries(Action.NETWORK_ADDED)[0]) == [("Адрес", None, "10.9.9.0/24"), ("Заметка", None, "офис")]
    assert rows(server_entries(Action.PRIVATE_NETWORKS_CHANGED)[0]) == [("Вся локальная сеть", "включено", "выключено")]
    assert rows(server_entries(Action.NETWORK_REMOVED)[0]) == [("Адрес", "10.9.9.0/24", None), ("Заметка", "офис", None)]


def test_server_password_and_admin_commands_are_recorded_without_passwords(capsys):
    call_command("create_admin")
    call_command("reset_password", "admin")
    output = capsys.readouterr().out
    admin = Account.objects.get(login="admin")

    assert server_entries(Action.ACCOUNT_CREATED)[0].target == admin
    assert server_entries(Action.PASSWORD_ISSUED)[0].target == admin
    stored = json.dumps(list(JournalEntry.objects.values()), default=str)
    assert all(line.split(": ", 1)[1] not in stored for line in output.splitlines() if line.startswith("Временный пароль"))


def test_system_text_parsers():
    assert pretty_name('NAME="Ubuntu"\nPRETTY_NAME="Ubuntu 24.04.1 LTS"\n') == "Ubuntu 24.04.1 LTS"
    assert meminfo("MemTotal:       2048 kB\nMemAvailable:   1024 kB\n") == {"MemTotal": 2097152, "MemAvailable": 1048576}
    assert process_started_at("1 (python) S" + " 0" * 25, None, 100) is None


@override_settings(APP_RELEASE="release-0.10.08 · abc1234 · 09.10.2026 12:00")
def test_admin_sees_server_panel_with_release_and_last_backup(monkeypatch):
    guest, _ = signed_in()
    monkeypatch.setattr(journal.system, "seconds_since_backup", lambda database: 3600)

    body = guest.get("/api/journal/system").json()

    assert body["release"] == "release-0.10.08 · abc1234 · 09.10.2026 12:00"
    assert body["last_backup_at"] is not None
    assert body["db_started_at"] is not None


def test_backup_time_is_unknown_when_sql_server_hides_it(monkeypatch):
    def denied(database):
        raise DatabaseError("The SELECT permission was denied on the object 'backupset'")

    monkeypatch.setattr(journal.system, "seconds_since_backup", denied)

    assert journal.system.last_backup_at() is None


def test_only_admin_sees_server_panel():
    guest, _ = signed_in("kadry", Role.HR)

    assert guest.get("/api/journal/system").status_code == 403
