from mssql.base import DatabaseWrapper as MssqlDatabaseWrapper

from sqlserver.browser import with_instance_port


class DatabaseWrapper(MssqlDatabaseWrapper):
    def get_connection_params(self):
        return with_instance_port(super().get_connection_params())
