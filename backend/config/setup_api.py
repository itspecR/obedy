from django.conf import settings
from django.db import DatabaseError
from ninja import Router, Schema
from ninja.errors import HttpError
from pydantic import Field

from accounts.first_admin import AdminExists, create_first_admin, existing_admin
from config import restart
from config.connection_store import Connection, save_connection
from config.probe import probe
from config.setup_code import code_matches, forget_code

FIELD_LIMIT = 200
PORT_PATTERN = r"^\d{0,5}$"
ALREADY_CONFIGURED = "База уже подключена"
WRONG_CODE = "Неверный код настройки. Его показывает install.sh, новый: sudo ./scripts/setup-code.sh"

router = Router(tags=["Настройка"])


class StatusOut(Schema):
    configured: bool
    needs_admin: bool


class CodeIn(Schema):
    code: str = Field(max_length=FIELD_LIMIT)


class AdminOut(Schema):
    login: str
    password: str


class ConnectionIn(Schema):
    code: str = Field(max_length=FIELD_LIMIT)
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


def require_code(code):
    if not code_matches(settings.SETUP_CODE_FILE, code):
        raise HttpError(403, WRONG_CODE)


def require_setup_code(payload):
    if settings.DATABASE_CONFIGURED:
        raise HttpError(409, ALREADY_CONFIGURED)
    require_code(payload.code)


def needs_admin():
    if not settings.DATABASE_CONFIGURED:
        return False
    try:
        return existing_admin() is None
    except DatabaseError:
        return False


@router.get("/status", auth=None, response=StatusOut)
def status(request):
    return StatusOut(configured=settings.DATABASE_CONFIGURED, needs_admin=needs_admin())


@router.post("/check", auth=None, response=ProbeOut)
def check(request, payload: ConnectionIn):
    require_setup_code(payload)
    result = probe(connection_of(payload))
    return ProbeOut(ok=result.ok, message=result.message, has_data=result.has_data)


@router.post("/database", auth=None, response=ProbeOut)
def connect(request, payload: ConnectionIn):
    require_setup_code(payload)
    connection = connection_of(payload)
    result = probe(connection)
    if not result.ok:
        raise HttpError(400, result.message)
    save_connection(settings.DB_CONFIG_FILE, settings.SECRET_KEY, connection)
    restart.schedule_restart()
    return ProbeOut(ok=True, message="Подключение сохранено. Сайт перезапускается", has_data=result.has_data)


@router.post("/admin", auth=None, response=AdminOut)
def first_admin(request, payload: CodeIn):
    if not settings.DATABASE_CONFIGURED:
        raise HttpError(409, "Сначала подключите базу данных")
    require_code(payload.code)
    try:
        account, password = create_first_admin()
    except AdminExists as error:
        raise HttpError(409, "Администратор уже есть") from error
    forget_code(settings.SETUP_CODE_FILE)
    return AdminOut(login=account.login, password=password)
