from django.conf import settings
from ninja import Router, Schema
from ninja.errors import HttpError

from accounts.permissions import require_admin
from accounts.security import session_auth
from config import restart
from config.connection_form import ConnectionFields, ProbeOut, connection_of, probe_out
from config.connection_store import save_connection
from config.probe import probe
from journal.entries import Row, record_changes
from journal.models import Action
from journal.snapshots import database_snapshot

PASSWORD_ROW = Row("Пароль", after="задан заново")
RESTARTING = "Подключение сохранено. Сайт перезапускается и переходит на эту базу"

router = Router(tags=["База данных"])


class DatabaseOut(Schema):
    host: str
    port: str
    name: str
    user: str
    trust_certificate: bool


@router.get("", auth=session_auth, response=DatabaseOut)
def show(request):
    require_admin(request)
    current = settings.DATABASE_CONNECTION
    return DatabaseOut(host=current.host, port=current.port, name=current.name, user=current.user, trust_certificate=current.trust_certificate)


@router.post("/check", auth=session_auth, response=ProbeOut)
def check(request, payload: ConnectionFields):
    require_admin(request)
    return probe_out(probe(connection_of(payload)))


@router.put("", auth=session_auth, response=ProbeOut)
def change(request, payload: ConnectionFields):
    require_admin(request)
    connection = connection_of(payload)
    result = probe(connection)
    if not result.ok:
        raise HttpError(400, result.message)
    record_changes(request, Action.DATABASE_CHANGED, database_snapshot(settings.DATABASE_CONNECTION), database_snapshot(connection), extra=[PASSWORD_ROW])
    save_connection(settings.DB_CONFIG_FILE, settings.SECRET_KEY, connection)
    restart.schedule_restart()
    return ProbeOut(ok=True, message=RESTARTING, has_data=result.has_data)
