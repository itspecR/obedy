MSSQL_ENGINE = "sqlserver"
NO_DATABASE = {"ENGINE": "django.db.backends.dummy"}
DEFAULT_PORT = "1433"
LOCK_ACQUIRED = 0
CONNECTION_REUSE_S = 60


def connection_string_extras(trust_certificate):
    return f"Encrypt=yes;TrustServerCertificate={'yes' if trust_certificate else 'no'}"


def mssql_database(connection, test_name):
    return {
        "ENGINE": MSSQL_ENGINE,
        "HOST": connection.host,
        "PORT": connection.port,
        "NAME": connection.name,
        "USER": connection.user,
        "PASSWORD": connection.password,
        "CONN_MAX_AGE": CONNECTION_REUSE_S,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {"python_driver": "mssql_python", "extra_params": connection_string_extras(connection.trust_certificate)},
        "TEST": {"NAME": test_name},
    }


def try_lock(database, name):
    with database.cursor() as cursor:
        cursor.execute(
            "SET NOCOUNT ON; DECLARE @result int; "
            "EXEC @result = sp_getapplock @Resource = %s, @LockMode = 'Exclusive', @LockOwner = 'Session', @LockTimeout = 0; "
            "SELECT @result",
            [name],
        )
        return cursor.fetchone()[0] >= LOCK_ACQUIRED


def release_lock(database, name):
    with database.cursor() as cursor:
        cursor.execute("EXEC sp_releaseapplock @Resource = %s, @LockOwner = 'Session'", [name])


def seconds_since_start(database):
    with database.cursor() as cursor:
        cursor.execute("SELECT DATEDIFF(SECOND, create_date, GETDATE()) FROM sys.databases WHERE name = 'tempdb'")
        row = cursor.fetchone()
    return row[0] if row else None


def seconds_since_backup(database):
    with database.cursor() as cursor:
        cursor.execute(
            "SELECT DATEDIFF(SECOND, MAX(backup_finish_date), GETDATE()) FROM msdb.dbo.backupset WHERE database_name = DB_NAME()"
        )
        row = cursor.fetchone()
    return row[0] if row else None
