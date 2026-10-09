from dataclasses import dataclass

from django.db import DEFAULT_DB_ALIAS, DatabaseError
from django.db.utils import ConnectionHandler

from config.database import mssql_database

MIGRATIONS_TABLE = "django_migrations"
PROBLEMS = (
    ("Login failed", "SQL Server не пустил: проверьте логин и пароль, имя базы и что у логина есть доступ к этой базе"),
    ("Cannot open database", "SQL Server не пустил: проверьте логин и пароль, имя базы и что у логина есть доступ к этой базе"),
    ("certificate", "Сертификат SQL Server не прошёл проверку. Включите «Доверять сертификату сервера»"),
    ("SSL", "Сертификат SQL Server не прошёл проверку. Включите «Доверять сертификату сервера»"),
)
UNREACHABLE = "SQL Server не отвечает по этому адресу. Проверьте IP, имя экземпляра, порт, TCP/IP и брандмауэр"


@dataclass(frozen=True)
class ProbeResult:
    ok: bool
    message: str
    has_data: bool = False


def explain(error):
    text = str(error)
    return next((message for marker, message in PROBLEMS if marker in text), UNREACHABLE)


def probe(connection):
    handler = ConnectionHandler({DEFAULT_DB_ALIAS: mssql_database(connection, connection.name)})
    database = handler[DEFAULT_DB_ALIAS]
    try:
        with database.cursor() as cursor:
            cursor.execute("SELECT 1")
        has_data = MIGRATIONS_TABLE in database.introspection.table_names()
    except DatabaseError as error:
        return ProbeResult(False, explain(error))
    finally:
        database.close()
    return ProbeResult(True, "Подключение работает", has_data)
