from ninja import Schema
from pydantic import Field

from config.connection_store import Connection

FIELD_LIMIT = 200
PORT_PATTERN = r"^\d{0,5}$"


class ConnectionFields(Schema):
    host: str = Field(min_length=1, max_length=FIELD_LIMIT)
    port: str = Field("", pattern=PORT_PATTERN)
    name: str = Field(min_length=1, max_length=FIELD_LIMIT)
    user: str = Field(min_length=1, max_length=FIELD_LIMIT)
    password: str = Field(min_length=1, max_length=FIELD_LIMIT)
    trust_certificate: bool = True


class ProbeOut(Schema):
    ok: bool
    message: str
    has_data: bool


def connection_of(payload):
    return Connection(
        host=payload.host.strip(),
        port=payload.port,
        name=payload.name.strip(),
        user=payload.user.strip(),
        password=payload.password,
        trust_certificate=payload.trust_certificate,
    )


def probe_out(result):
    return ProbeOut(ok=result.ok, message=result.message, has_data=result.has_data)
