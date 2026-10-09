import logging
from contextlib import contextmanager
from dataclasses import dataclass, field

from django.db import connection as database
from django.db import transaction
from ldap3.core.exceptions import LDAPException

from accounts.models import Account, Source
from config.database import release_lock, try_lock
from accounts.sessions import revoke_all_sessions
from directory.config import current_config
from directory.diagnostics import UNREACHABLE, ConnectionProblem, explained_connection
from directory.models import SyncReport, SyncStatus
from directory.provisioning import existing_account, is_outdated, save_account
from directory.roster import permitted_users

REPORT_ID = 1
LOCK_NAME = "obedy-directory-sync"
MAX_DEACTIVATION_SHARE = 0.5
MIN_GUARDED_DEACTIVATIONS = 5
SKIPPED_SHOWN = 3

DISABLED = "Вход через домен выключен — синхронизация не выполняется"
GUARDED = (
    "Синхронизация отключила бы {gone} из {total} сотрудников домена — ничего не изменено. "
    "Проверьте базу поиска и группу доступа"
)
LOCAL_NAMESAKE = "{login} — логин занят локальной учётной записью"
LOGIN_TAKEN = "{login} — логин уже занят другой учётной записью"

logger = logging.getLogger(__name__)


class SyncBusy(Exception):
    pass


class SyncSkipped(Exception):
    pass


@dataclass(frozen=True)
class SyncResult:
    status: str
    message: str
    created: int = 0
    updated: int = 0
    deactivated: int = 0
    skipped: int = 0


@dataclass
class SyncPlan:
    create: list = field(default_factory=list)
    update: list = field(default_factory=list)
    kept: set = field(default_factory=set)
    skipped: list = field(default_factory=list)
    gone: list = field(default_factory=list)


@contextmanager
def sync_lock():
    if not try_lock(database, LOCK_NAME):
        raise SyncBusy
    try:
        yield
    finally:
        release_lock(database, LOCK_NAME)


def collect(config):
    if not config.enabled:
        raise SyncSkipped(DISABLED)
    connection = explained_connection(config)
    try:
        return permitted_users(connection, config)
    except LDAPException as error:
        logger.warning("Ошибка запроса к домену при синхронизации: %r", error)
        raise ConnectionProblem(UNREACHABLE) from error
    finally:
        connection.unbind()


def domain_accounts():
    return Account.objects.filter(source=Source.DOMAIN, in_directory=True)


def login_conflict(user, account):
    holders = Account.objects.filter(login=user.login)
    if account is not None:
        holders = holders.exclude(pk=account.pk)
    holder = holders.first()
    if holder is None:
        return None
    template = LOCAL_NAMESAKE if holder.source == Source.LOCAL else LOGIN_TAKEN
    return template.format(login=user.login)


def plan_for(users):
    plan = SyncPlan()
    for user in users:
        account = existing_account(user)
        if account is not None:
            plan.kept.add(account.pk)
        problem = login_conflict(user, account)
        if problem:
            plan.skipped.append(problem)
        elif account is None:
            plan.create.append(user)
        elif is_outdated(account, user):
            plan.update.append((account, user))
    plan.gone = list(domain_accounts().exclude(pk__in=plan.kept))
    return plan


def too_destructive(plan, total):
    gone = len(plan.gone)
    return gone >= MIN_GUARDED_DEACTIVATIONS and gone > total * MAX_DEACTIVATION_SHARE


def deactivate(account):
    account.in_directory = False
    account.save(update_fields=["in_directory"])
    revoke_all_sessions(account)


@transaction.atomic
def apply(plan):
    for user in plan.create:
        save_account(user)
    for account, user in plan.update:
        save_account(user, account)
    for account in plan.gone:
        deactivate(account)


def summary(plan):
    text = f"Добавлено {len(plan.create)}, обновлено {len(plan.update)}, отключено {len(plan.gone)}"
    if not plan.skipped:
        return text
    shown = "; ".join(plan.skipped[:SKIPPED_SHOWN])
    more = "…" if len(plan.skipped) > SKIPPED_SHOWN else ""
    return f"{text}. Пропущено {len(plan.skipped)}: {shown}{more}"


def synchronize(config):
    try:
        users = collect(config)
    except SyncSkipped as skipped:
        return SyncResult(SyncStatus.SKIPPED, str(skipped))
    except ConnectionProblem as problem:
        return SyncResult(SyncStatus.FAILED, problem.message)
    plan = plan_for(users)
    total = domain_accounts().count()
    if too_destructive(plan, total):
        return SyncResult(SyncStatus.GUARDED, GUARDED.format(gone=len(plan.gone), total=total))
    apply(plan)
    return SyncResult(SyncStatus.DONE, summary(plan), len(plan.create), len(plan.update), len(plan.gone), len(plan.skipped))


def record(result, now):
    SyncReport.objects.update_or_create(
        pk=REPORT_ID,
        defaults={
            "finished_at": now,
            "status": result.status,
            "message": result.message,
            "created": result.created,
            "updated": result.updated,
            "deactivated": result.deactivated,
            "skipped": result.skipped,
        },
    )


def run_sync(now):
    with sync_lock():
        result = synchronize(current_config())
        record(result, now)
        return result


def latest_report():
    return SyncReport.objects.filter(pk=REPORT_ID).first()
