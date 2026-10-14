from datetime import datetime

from django.utils import timezone
from ninja import Field, Router, Schema
from ninja.errors import HttpError

from accounts.permissions import require_admin
from accounts.security import session_auth
from directory.certificates import InvalidCertificate
from directory.config import config_from, current_config, stored_settings
from directory.diagnostics import check_connection
from directory.models import DEFAULT_SESSION_DAYS, Mode
from directory.settings_store import IncompleteSettings, save_settings
from directory.sync import SyncBusy, latest_report, run_sync
from journal.entries import Row, record, record_changes
from journal.models import Action
from journal.snapshots import directory_snapshot

TEXT_LIMIT = 500
SECRET_LIMIT = 255
CERTIFICATE_LIMIT = 20000
MIN_SESSION_DAYS = 1
MAX_SESSION_DAYS = 90
MAX_PORT = 65535

SYNC_BUSY = "Синхронизация уже идёт. Подождите минуту и обновите страницу"
PASSWORD_CHANGED = Row("Пароль учётной записи для чтения", after="изменён")
RESULT_LABEL = "Итог"
INVALID_CERTIFICATE = "Сертификат не распознан. Вставьте корневой сертификат домена в формате PEM (-----BEGIN CERTIFICATE-----)"

router = Router(tags=["Active Directory"])


class DirectoryOut(Schema):
    enabled: bool
    servers: str
    mode: Mode
    port: int | None
    ca_certificate: str
    bind_user: str
    has_bind_password: bool
    base_dn: str
    group_dn: str
    session_days: int


class DirectoryIn(Schema):
    enabled: bool
    servers: str = Field("", max_length=TEXT_LIMIT)
    mode: Mode = Mode.LDAPS
    port: int | None = Field(None, ge=1, le=MAX_PORT)
    ca_certificate: str = Field("", max_length=CERTIFICATE_LIMIT)
    bind_user: str = Field("", max_length=SECRET_LIMIT)
    bind_password: str = Field("", max_length=SECRET_LIMIT)
    base_dn: str = Field("", max_length=TEXT_LIMIT)
    group_dn: str = Field("", max_length=TEXT_LIMIT)
    session_days: int = Field(DEFAULT_SESSION_DAYS, ge=MIN_SESSION_DAYS, le=MAX_SESSION_DAYS)


class CheckOut(Schema):
    ok: bool
    message: str


class PublicOut(Schema):
    enabled: bool


class SyncOut(Schema):
    finished_at: datetime | None = None
    status: str | None = None
    message: str = ""
    created: int = 0
    updated: int = 0
    deactivated: int = 0
    skipped: int = 0


def describe(stored):
    return DirectoryOut(
        enabled=stored.enabled,
        servers=stored.servers,
        mode=stored.mode,
        port=stored.port,
        ca_certificate=stored.ca_certificate,
        bind_user=stored.bind_user,
        has_bind_password=bool(stored.bind_password),
        base_dn=stored.base_dn,
        group_dn=stored.group_dn,
        session_days=stored.session_days,
    )


@router.get("/public", auth=None, response=PublicOut)
def public(request):
    return PublicOut(enabled=current_config().ready)


@router.get("", auth=session_auth, response=DirectoryOut)
def show(request):
    require_admin(request)
    return describe(stored_settings())


@router.put("", auth=session_auth, response=DirectoryOut)
def update(request, payload: DirectoryIn):
    require_admin(request)
    before = directory_snapshot(stored_settings())
    try:
        stored = save_settings(payload.dict())
    except InvalidCertificate as error:
        raise HttpError(400, INVALID_CERTIFICATE) from error
    except IncompleteSettings as error:
        raise HttpError(400, f"Чтобы включить вход через домен, заполните: {', '.join(error.missing)}") from error
    password_rows = [PASSWORD_CHANGED] if payload.bind_password else []
    record_changes(request, Action.DIRECTORY_CHANGED, before, directory_snapshot(stored), extra=password_rows)
    return describe(stored)


@router.post("/check", auth=session_auth, response=CheckOut)
def check(request):
    require_admin(request)
    result = check_connection(config_from(stored_settings()))
    record(request, Action.DIRECTORY_CHECKED, rows=[Row(RESULT_LABEL, after=result.message)])
    return CheckOut(ok=result.ok, message=result.message)


def sync_report():
    report = latest_report()
    if report is None:
        return SyncOut()
    return SyncOut(
        finished_at=report.finished_at,
        status=report.status,
        message=report.message,
        created=report.created,
        updated=report.updated,
        deactivated=report.deactivated,
        skipped=report.skipped,
    )


@router.get("/sync", auth=session_auth, response=SyncOut)
def sync_status(request):
    require_admin(request)
    return sync_report()


@router.post("/sync", auth=session_auth, response=SyncOut)
def sync_now(request):
    require_admin(request)
    try:
        run_sync(timezone.now())
    except SyncBusy as error:
        raise HttpError(409, SYNC_BUSY) from error
    report = sync_report()
    record(request, Action.DIRECTORY_SYNCED, rows=[Row(RESULT_LABEL, after=report.message)])
    return report
