import logging
from dataclasses import dataclass

from ldap3.core.exceptions import LDAPException

from directory.authentication import ServiceAccountRejected, service_connection
from directory.connection import DirectoryUnavailable
from directory.users import count_users, group_exists

USER_SAMPLE_LIMIT = 1000

INCOMPLETE = "Сначала заполните и сохраните серверы, сервисную учётную запись, её пароль и базу поиска"
UNREACHABLE = "Контроллер домена не отвечает или не принимает соединение. Проверьте адрес, порт, режим и сертификат"
SERVICE_REJECTED = "Контроллер отклонил сервисную учётную запись: проверьте её логин и пароль"
NO_USERS = "Подключение есть, но в базе поиска нет учётных записей. Проверьте поле «База поиска»"
NO_GROUP = "Подключение есть, но группа не найдена. Проверьте поле «Группа доступа»"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    message: str


def success(found):
    more = "+" if found >= USER_SAMPLE_LIMIT else ""
    return CheckResult(True, f"Подключение работает. Найдено учётных записей: {found}{more}")


def inspect(connection, config):
    found = count_users(connection, config.base_dn, USER_SAMPLE_LIMIT)
    if found == 0:
        return CheckResult(False, NO_USERS)
    if config.group_dn and not group_exists(connection, config.group_dn):
        return CheckResult(False, NO_GROUP)
    return success(found)


def check_connection(config):
    if not config.complete:
        return CheckResult(False, INCOMPLETE)
    try:
        connection = service_connection(config)
    except ServiceAccountRejected:
        return CheckResult(False, SERVICE_REJECTED)
    except DirectoryUnavailable as error:
        logger.warning("Проверка подключения к домену не удалась: %r", error.__cause__ or error)
        return CheckResult(False, UNREACHABLE)
    try:
        return inspect(connection, config)
    except LDAPException as error:
        logger.warning("Ошибка запроса к домену при проверке: %r", error)
        return CheckResult(False, UNREACHABLE)
    finally:
        connection.unbind()
