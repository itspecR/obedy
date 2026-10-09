from dataclasses import asdict, dataclass

from access.client import client_address
from journal.models import ADDRESS_LIMIT, JournalEntry

SERVER_ADDRESS = "сервер"


@dataclass(frozen=True)
class Row:
    label: str
    before: str | None = None
    after: str | None = None


def differences(before, after):
    return [Row(label, before.get(label), value) for label, value in after.items() if before.get(label) != value]


def removed(snapshot):
    return [Row(label, before=value) for label, value in snapshot.items()]


def write(action, actor, address, target=None, rows=()):
    return JournalEntry.objects.create(
        action=action,
        actor=actor,
        target=target,
        address=address[:ADDRESS_LIMIT],
        details=[asdict(row) for row in rows],
    )


def record(request, action, target=None, rows=()):
    return write(action, request.auth.account, client_address(request), target, rows)


def record_server(action, target=None, rows=()):
    return write(action, None, SERVER_ADDRESS, target, rows)


def record_server_changes(action, before, after, target=None):
    rows = differences(before, after)
    if rows:
        record_server(action, target, rows)
    return rows


def record_changes(request, action, before, after, target=None, extra=()):
    rows = [*differences(before, after), *extra]
    if rows:
        record(request, action, target, rows)
    return rows
