import os
import stat

import pytest
from django.core.management import call_command
from django.test import Client, override_settings

from accounts.first_admin import create_first_admin
from accounts.models import Account, Role
from config import restart, setup_api
from config.connection_store import Connection, forget_connection, load_connection, save_connection
from config.probe import ProbeResult, explain
from config.setup_code import code_matches, forget_code, issue_code

SECRET = "secret-key"
CONNECTION = Connection("192.168.1.10\\SQLEXPRESS", "", "obedy", "obedy", "Pa55-word", True)
PAYLOAD = {"host": "192.168.1.10\\SQLEXPRESS", "port": "", "name": "obedy", "user": "obedy", "password": "Pa55-word", "trust_certificate": True}


@pytest.fixture
def state(tmp_path):
    with override_settings(
        DATABASE_CONFIGURED=False,
        DB_CONFIG_FILE=str(tmp_path / "database.bin"),
        SETUP_CODE_FILE=str(tmp_path / "setup-code.sha256"),
        SECRET_KEY=SECRET,
    ):
        yield tmp_path


@pytest.fixture
def restarts(monkeypatch):
    calls = []
    monkeypatch.setattr(restart, "schedule_restart", lambda: calls.append(True))
    return calls


def probe_returns(monkeypatch, result):
    monkeypatch.setattr(setup_api, "probe", lambda connection: result)


def post(path, body):
    return Client().post(path, body, content_type="application/json")


def test_connection_is_stored_encrypted_and_private(tmp_path):
    path = str(tmp_path / "state" / "database.bin")
    save_connection(path, SECRET, CONNECTION)

    assert load_connection(path, SECRET) == CONNECTION
    assert b"Pa55-word" not in open(path, "rb").read()
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    assert load_connection(path, "other-key") is None
    assert load_connection(str(tmp_path / "missing.bin"), SECRET) is None


def test_setup_code_is_one_time_and_forgiving_to_format(tmp_path):
    path = str(tmp_path / "code")
    code = issue_code(path)

    assert code_matches(path, code)
    assert code_matches(path, code.replace("-", " ").lower())
    assert not code_matches(path, "AAAA-BBBB-CCCC")
    assert not code_matches(path, "")
    forget_code(path)
    assert not code_matches(path, code)


def test_login_failures_and_certificates_are_explained_in_russian():
    assert "логин и пароль" in explain(Exception("[Microsoft][SQL Server]Login failed for user 'obedy'."))
    assert "Доверять сертификату" in explain(Exception("SSL Provider: certificate verify failed"))
    assert "не отвечает" in explain(Exception("TCP Provider: timeout"))


def test_only_setup_and_health_work_until_the_database_is_connected(state):
    client = Client()

    assert client.get("/api/staff").status_code == 503
    assert client.get("/api/staff").json()["setup"] is True
    assert client.get("/api/access/check").status_code == 204
    assert client.get("/api/setup/status").json() == {"configured": False, "needs_admin": False}
    assert client.get("/api/health").json() == {"status": "setup", "database": "not_configured"}


def test_wrong_code_is_refused(state, monkeypatch, restarts):
    issue_code(str(state / "setup-code.sha256"))
    probe_returns(monkeypatch, ProbeResult(True, "ok"))

    response = post("/api/setup/database", {**PAYLOAD, "code": "AAAA-BBBB-CCCC"})

    assert response.status_code == 403
    assert not (state / "database.bin").exists()
    assert restarts == []


def test_check_reports_the_problem_without_saving(state, monkeypatch):
    code = issue_code(str(state / "setup-code.sha256"))
    probe_returns(monkeypatch, ProbeResult(False, "SQL Server не отвечает"))

    response = post("/api/setup/check", {**PAYLOAD, "code": code})

    assert response.json() == {"ok": False, "message": "SQL Server не отвечает", "has_data": False}
    assert not (state / "database.bin").exists()


def test_working_connection_is_saved_and_the_site_restarts(state, monkeypatch, restarts):
    code = issue_code(str(state / "setup-code.sha256"))
    probe_returns(monkeypatch, ProbeResult(True, "ok", has_data=True))

    response = post("/api/setup/database", {**PAYLOAD, "code": code})

    assert response.status_code == 200
    assert response.json()["has_data"] is True
    assert load_connection(str(state / "database.bin"), SECRET) == CONNECTION
    assert restarts == [True]


def test_broken_connection_is_not_saved(state, monkeypatch, restarts):
    code = issue_code(str(state / "setup-code.sha256"))
    probe_returns(monkeypatch, ProbeResult(False, "SQL Server не пустил"))

    response = post("/api/setup/database", {**PAYLOAD, "code": code})

    assert response.status_code == 400
    assert response.json()["detail"] == "SQL Server не пустил"
    assert restarts == []


@pytest.mark.django_db
def test_setup_is_closed_once_the_database_is_connected(state, monkeypatch, restarts):
    code = issue_code(str(state / "setup-code.sha256"))
    with override_settings(DATABASE_CONFIGURED=True):
        response = post("/api/setup/database", {**PAYLOAD, "code": code})

    assert response.status_code == 409
    assert restarts == []


def test_restart_only_stops_the_container_process(monkeypatch):
    timers = []
    monkeypatch.setattr(restart.threading, "Timer", lambda delay, action: timers.append(action) or type("T", (), {"start": lambda self: None})())
    monkeypatch.setattr(restart.os, "getppid", lambda: 4242)
    restart.schedule_restart()
    assert timers == []
    monkeypatch.setattr(restart.os, "getppid", lambda: restart.CONTAINER_MAIN_PROCESS)
    restart.schedule_restart()
    assert timers == [restart.stop_main_process]


@pytest.mark.django_db
def test_first_admin_is_created_once_with_the_setup_code(state):
    code = issue_code(str(state / "setup-code.sha256"))
    with override_settings(DATABASE_CONFIGURED=True):
        assert Client().get("/api/setup/status").json() == {"configured": True, "needs_admin": True}
        assert post("/api/setup/admin", {"code": "AAAA-BBBB-CCCC"}).status_code == 403

        response = post("/api/setup/admin", {"code": code})

        assert response.status_code == 200
        assert response.json()["login"] == "admin"
        admin = Account.objects.get(login="admin")
        assert admin.role == Role.ADMIN and admin.must_change_password
        assert Client().get("/api/setup/status").json() == {"configured": True, "needs_admin": False}
        assert post("/api/setup/admin", {"code": code}).status_code == 403


@pytest.mark.django_db
def test_first_admin_waits_for_the_database(state):
    code = issue_code(str(state / "setup-code.sha256"))

    assert post("/api/setup/admin", {"code": code}).status_code == 409


def test_forgetting_the_database_returns_the_site_to_setup_with_a_new_code(state, capsys):
    save_connection(str(state / "database.bin"), SECRET, CONNECTION)

    call_command("forget_database")

    code = capsys.readouterr().out.strip().removeprefix("Код настройки: ")
    assert load_connection(str(state / "database.bin"), SECRET) is None
    assert code_matches(str(state / "setup-code.sha256"), code)


def test_forgetting_twice_is_harmless(state):
    forget_connection(str(state / "database.bin"))
    forget_connection(str(state / "database.bin"))

    assert not os.path.exists(state / "database.bin")


@pytest.mark.django_db
def test_setup_code_is_dropped_on_start_when_the_database_already_has_an_admin(state):
    code_file = str(state / "setup-code.sha256")
    issue_code(code_file)
    with override_settings(DATABASE_CONFIGURED=True):
        call_command("prepare_database", verbosity=0)
        assert os.path.exists(code_file)

        create_first_admin()
        call_command("prepare_database", verbosity=0)

    assert not os.path.exists(code_file)
