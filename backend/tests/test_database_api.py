import json

import pytest
from django.test import Client, override_settings

from accounts.models import Role
from config import database_api, restart
from config.connection_store import Connection, load_connection
from config.probe import ProbeResult
from journal.models import Action, JournalEntry
from tests.factories import DEFAULT_PASSWORD, make_account

pytestmark = pytest.mark.django_db

JSON = "application/json"
SECRET = "secret-key"
CURRENT = Connection("192.168.1.10\\SQLEXPRESS", "", "obedy", "obedy", "Old-Pa55", True)
NEXT = {"host": "192.168.1.20", "port": "1433", "name": "obedy_prod", "user": "site", "password": "New-Pa55", "trust_certificate": False}


@pytest.fixture
def state(tmp_path):
    with override_settings(DATABASE_CONNECTION=CURRENT, DB_CONFIG_FILE=str(tmp_path / "database.bin"), SECRET_KEY=SECRET):
        yield tmp_path


@pytest.fixture
def restarts(monkeypatch):
    calls = []
    monkeypatch.setattr(restart, "schedule_restart", lambda: calls.append(True))
    return calls


def signed_in(role=Role.ADMIN):
    make_account(login="boss", role=role, must_change_password=False)
    guest = Client()
    guest.post("/api/auth/login", json.dumps({"login": "boss", "password": DEFAULT_PASSWORD}), content_type=JSON)
    return guest


def probe_returns(monkeypatch, result):
    monkeypatch.setattr(database_api, "probe", lambda connection: result)


def test_only_the_admin_sees_the_connection(state):
    assert Client().get("/api/database").status_code == 401
    assert signed_in(Role.HR).get("/api/database").status_code == 403


def test_admin_sees_the_connection_without_the_password(state):
    body = signed_in().get("/api/database").json()

    assert body == {"host": "192.168.1.10\\SQLEXPRESS", "port": "", "name": "obedy", "user": "obedy", "trust_certificate": True}


def test_admin_checks_another_connection(state, monkeypatch):
    probe_returns(monkeypatch, ProbeResult(False, "SQL Server не пустил"))

    response = signed_in().post("/api/database/check", json.dumps(NEXT), content_type=JSON)

    assert response.json() == {"ok": False, "message": "SQL Server не пустил", "has_data": False}


def test_working_connection_is_saved_logged_and_the_site_restarts(state, monkeypatch, restarts):
    probe_returns(monkeypatch, ProbeResult(True, "ok", has_data=True))

    response = signed_in().put("/api/database", json.dumps(NEXT), content_type=JSON)

    assert response.status_code == 200
    assert load_connection(str(state / "database.bin"), SECRET) == Connection("192.168.1.20", "1433", "obedy_prod", "site", "New-Pa55", False)
    assert restarts == [True]
    entry = JournalEntry.objects.get(action=Action.DATABASE_CHANGED)
    changed = {row["label"]: (row["before"], row["after"]) for row in entry.details}
    assert changed["Сервер"] == ("192.168.1.10\\SQLEXPRESS", "192.168.1.20")
    assert changed["База"] == ("obedy", "obedy_prod")
    assert changed["Пароль"] == (None, "задан заново")
    assert "New-Pa55" not in json.dumps(entry.details)


def test_broken_connection_is_refused(state, monkeypatch, restarts):
    probe_returns(monkeypatch, ProbeResult(False, "SQL Server не отвечает"))

    response = signed_in().put("/api/database", json.dumps(NEXT), content_type=JSON)

    assert response.status_code == 400
    assert response.json()["detail"] == "SQL Server не отвечает"
    assert not (state / "database.bin").exists()
    assert restarts == []
    assert not JournalEntry.objects.filter(action=Action.DATABASE_CHANGED).exists()


def test_hr_cannot_change_the_connection(state, monkeypatch, restarts):
    probe_returns(monkeypatch, ProbeResult(True, "ok"))

    assert signed_in(Role.HR).put("/api/database", json.dumps(NEXT), content_type=JSON).status_code == 403
    assert restarts == []
