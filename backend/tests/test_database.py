import pytest
from django.db import close_old_connections, connection, connections

from config.connection_store import Connection
from config.database import mssql_database, release_lock, seconds_since_backup, seconds_since_start, try_lock

LOCK = "obedy-test-lock"


def settings_for(trust):
    return mssql_database(Connection("sql.local\\SQLEXPRESS", "", "obedy", "obedy", "secret", trust), "test_obedy")


def test_connection_uses_the_bundled_driver_and_encryption():
    database = settings_for(True)

    assert database["ENGINE"] == "sqlserver"
    assert database["OPTIONS"]["python_driver"] == "mssql_python"
    assert database["OPTIONS"]["extra_params"] == "Encrypt=yes;TrustServerCertificate=yes"
    assert settings_for(False)["OPTIONS"]["extra_params"] == "Encrypt=yes;TrustServerCertificate=no"


def test_connection_is_reused_for_a_minute_and_checked_before_use():
    database = settings_for(True)

    assert database["CONN_MAX_AGE"] == 60
    assert database["CONN_HEALTH_CHECKS"] is True


@pytest.mark.django_db(transaction=True)
def test_lock_is_exclusive_between_connections_until_released():
    other = connections.create_connection("default")
    try:
        assert try_lock(connection, LOCK)
        assert not try_lock(other, LOCK)
        release_lock(connection, LOCK)
        assert try_lock(other, LOCK)
        release_lock(other, LOCK)
    finally:
        other.close()


@pytest.mark.django_db
def test_database_uptime_is_known():
    assert seconds_since_start(connection) >= 0


@pytest.mark.django_db
def test_backup_age_is_empty_for_a_database_never_backed_up():
    assert seconds_since_backup(connection) is None


def current_session(database):
    with database.cursor() as cursor:
        cursor.execute("SELECT session_id, login_time FROM sys.dm_exec_sessions WHERE session_id = @@SPID")
        return tuple(cursor.fetchone())


def kill(session):
    killer = connections.create_connection("default")
    try:
        with killer.cursor() as cursor:
            cursor.execute(f"KILL {int(session)}")
    finally:
        killer.close()


@pytest.mark.django_db(transaction=True)
def test_next_request_reuses_the_session_and_survives_a_dropped_one():
    close_old_connections()
    first = current_session(connection)
    close_old_connections()
    assert current_session(connection) == first

    kill(first[0])
    close_old_connections()

    assert current_session(connection) != first
