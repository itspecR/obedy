import pytest
from django.db import connection, connections

from config.database import mssql_database, release_lock, seconds_since_start, try_lock

LOCK = "obedy-test-lock"


def settings_for(trust):
    return mssql_database("sql.local\\SQLEXPRESS", "", "obedy", "obedy", "secret", trust, "test_obedy")


def test_connection_uses_the_bundled_driver_and_encryption():
    database = settings_for(True)

    assert database["ENGINE"] == "mssql"
    assert database["OPTIONS"]["python_driver"] == "mssql_python"
    assert database["OPTIONS"]["extra_params"] == "Encrypt=yes;TrustServerCertificate=yes"
    assert settings_for(False)["OPTIONS"]["extra_params"] == "Encrypt=yes;TrustServerCertificate=no"


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
