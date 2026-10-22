from sqlalchemy import event
from sqlalchemy.engine import Engine


def configure_sqlite_foreign_keys(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record):
        previous_autocommit= dbapi_connection.autocommit
        dbapi_connection.autocommit = True

        try:
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()
        finally:
            dbapi_connection.autocommit = previous_autocommit