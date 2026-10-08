import ssl

from ldap3 import FIRST, NONE, SYNC, Connection, Server, ServerPool, Tls
from ldap3.core.exceptions import LDAPException

from directory.models import Mode

CONNECT_TIMEOUT_SECONDS = 5
RECEIVE_TIMEOUT_SECONDS = 10
INVALID_CREDENTIALS = 49

STRATEGY = SYNC


class DirectoryUnavailable(Exception):
    pass


class BindRejected(Exception):
    pass


def tls_for(config):
    if config.mode == Mode.PLAIN:
        return None
    return Tls(validate=ssl.CERT_REQUIRED, ca_certs_data=config.ca_certificate or None)


def server_for(config):
    tls = tls_for(config)
    servers = [
        Server(host, port=config.port, use_ssl=config.mode == Mode.LDAPS, tls=tls, connect_timeout=CONNECT_TIMEOUT_SECONDS, get_info=NONE)
        for host in config.servers
    ]
    return ServerPool(servers, FIRST, active=1, exhaust=True)


def open_connection(config, user, password):
    connection = Connection(
        server_for(config),
        user=user,
        password=password,
        client_strategy=STRATEGY,
        receive_timeout=RECEIVE_TIMEOUT_SECONDS,
        auto_referrals=False,
        raise_exceptions=False,
    )
    try:
        start_tls_if_needed(connection, config)
        bind(connection)
    except LDAPException as error:
        raise DirectoryUnavailable from error
    return connection


def start_tls_if_needed(connection, config):
    if config.mode != Mode.STARTTLS:
        return
    connection.open()
    if not connection.start_tls():
        raise DirectoryUnavailable


def bind(connection):
    if connection.bind():
        return
    if (connection.result or {}).get("result") == INVALID_CREDENTIALS:
        raise BindRejected
    raise DirectoryUnavailable
