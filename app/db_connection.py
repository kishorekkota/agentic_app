import logging
import os
import urllib
from typing import Optional

from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

def get_connection_uri():
    dbhost = os.getenv("DBHOST")
    dbname = os.getenv("DBNAME")
    dbuser = os.getenv("DBUSER")
    password = os.getenv("DBPASSWORD")
    sslmode = os.getenv("SSLMODE", "require")

    if not all([dbhost, dbname, dbuser, password]):
        logger.warning("Postgres environment variables are not fully configured.")
        return None

    encoded_user = urllib.parse.quote(dbuser)
    db_uri = f"host={dbhost} dbname={dbname} user={encoded_user} password={password} sslmode={sslmode}"
    return db_uri

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}


def create_connection_pool() -> Optional[ConnectionPool]:
    db_uri = get_connection_uri()
    if not db_uri:
        return None

    return ConnectionPool(
        conninfo=db_uri,
        max_size=20,
        kwargs=connection_kwargs,
    )


pool = create_connection_pool()
if pool is None:
    logger.warning("Database connection pool not created.")
else:
    logger.info("Database connection pool created")