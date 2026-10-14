import socket
import threading

import pytest
from django.db import DEFAULT_DB_ALIAS
from django.db.utils import ConnectionHandler

from config.connection_store import Connection
from config.database import mssql_database
from sqlserver import browser

REPLY = b"ServerName;SQL;InstanceName;SQL;IsClustered;No;Version;15.0.2000.5;tcp;50345;np;\\\\SQL\\pipe\\MSSQL$SQL\\sql\\query;;"


def framed(body):
    return b"\x05" + len(body).to_bytes(2, "little") + body


def test_instance_is_split_from_the_address():
    assert browser.split_instance("192.168.1.253\\SQL") == ("192.168.1.253", "SQL")
    assert browser.split_instance("192.168.1.253") == ("192.168.1.253", None)
    assert browser.split_instance("192.168.1.253\\") == ("192.168.1.253\\", None)


def test_port_is_read_from_the_browser_reply_case_insensitively():
    reply = framed(b"ServerName;SQL;InstanceName;OTHER;tcp;50001;;" + REPLY)

    assert browser.port_in_reply(reply, "sql") == "50345"
    assert browser.port_in_reply(reply, "missing") is None


def test_explicit_port_wins_over_the_instance_name(monkeypatch):
    monkeypatch.setattr(browser, "ask_browser", lambda server, instance: pytest.fail("Browser не должен вызываться"))

    assert browser.with_instance_port({"HOST": "10.0.0.1\\SQL", "PORT": "50345"}) == {"HOST": "10.0.0.1", "PORT": "50345"}
    assert browser.with_instance_port({"HOST": "10.0.0.1", "PORT": ""}) == {"HOST": "10.0.0.1", "PORT": ""}


def test_silent_browser_keeps_the_address_as_entered(monkeypatch):
    monkeypatch.setattr(browser, "BROWSER_TIMEOUT_S", 0.2)
    monkeypatch.setattr(browser, "BROWSER_PORT", free_udp_port())

    assert browser.with_instance_port({"HOST": "127.0.0.1\\SQL", "PORT": ""}) == {"HOST": "127.0.0.1\\SQL", "PORT": ""}


def free_udp_port():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def fake_browser(monkeypatch, settings):
    sql_port = settings.DATABASES["default"]["PORT"] or "1433"
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("127.0.0.1", 0))
    server.settimeout(5)
    queries = []

    def answer():
        try:
            data, sender = server.recvfrom(1024)
        except OSError:
            return
        queries.append(data)
        body = f"ServerName;SQL;InstanceName;SQL;IsClustered;No;Version;15.0.2000.5;tcp;{sql_port};;".encode()
        server.sendto(framed(body), sender)

    thread = threading.Thread(target=answer, daemon=True)
    thread.start()
    monkeypatch.setattr(browser, "BROWSER_PORT", server.getsockname()[1])
    yield queries
    thread.join(timeout=5)
    server.close()


@pytest.mark.django_db
def test_named_instance_connects_through_the_browser_port(fake_browser, settings):
    current = settings.DATABASES["default"]
    connection = Connection(f"{current['HOST']}\\SQL", "", "master", current["USER"], current["PASSWORD"], True)
    handler = ConnectionHandler({DEFAULT_DB_ALIAS: mssql_database(connection, "unused")})
    database = handler[DEFAULT_DB_ALIAS]
    try:
        with database.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1
    finally:
        database.close()

    assert fake_browser == [b"\x04SQL\x00"]
