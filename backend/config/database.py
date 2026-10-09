MSSQL_ENGINE = "mssql"
DEFAULT_PORT = "1433"
LOCK_ACQUIRED = 0


def connection_string_extras(trust_certificate):
    return f"Encrypt=yes;TrustServerCertificate={'yes' if trust_certificate else 'no'}"


def mssql_database(host, port, name, user, password, trust_certificate, test_name):
    return {
        "ENGINE": MSSQL_ENGINE,
        "HOST": host,
        "PORT": port,
        "NAME": name,
        "USER": user,
        "PASSWORD": password,
        "OPTIONS": {"python_driver": "mssql_python", "extra_params": connection_string_extras(trust_certificate)},
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
