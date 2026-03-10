# db_connection.py

import logging
import urllib.parse
from typing import Optional

from psycopg_pool import ConnectionPool  # psycopg is a PostgreSQL adapter
from environment_variables import EnvironmentVariables

logger = logging.getLogger(__name__)

# Instantiate EnvironmentVariables in non-strict mode to avoid import-time failures.
env_vars = EnvironmentVariables(strict=False)

def get_connection_uri():
    # Retrieve database connection parameters from EnvironmentVariables instance
    dbhost = env_vars.db_host
    dbname = env_vars.db_name
    dbuser = env_vars.db_user
    password = env_vars.password
    sslmode = env_vars.sslmode

    if not all([dbhost, dbname, dbuser, password]):
        logger.warning("Postgres settings are incomplete; checkpointer persistence is disabled.")
        return None

    encoded_user = urllib.parse.quote(dbuser)
    encoded_password = urllib.parse.quote(password)

    # Construct the connection URI
    db_uri = f"host={dbhost} dbname={dbname} user={encoded_user} password={encoded_password} sslmode={sslmode or 'require'}"
    return db_uri

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

def create_connection_pool() -> Optional[ConnectionPool]:
    db_uri = get_connection_uri()
    if db_uri is None:
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