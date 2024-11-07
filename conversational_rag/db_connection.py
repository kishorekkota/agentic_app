# db_connection.py

import logging
import urllib.parse
from psycopg_pool import ConnectionPool  # psycopg is a PostgreSQL adapter
from environment_variables import EnvironmentVariables

logger = logging.getLogger(__name__)

# Instantiate EnvironmentVariables
# Set use_key_vault=True and provide key_vault_name if you want to load variables from Azure Key Vault
env_vars = EnvironmentVariables()

def get_connection_uri():
    # Retrieve database connection parameters from EnvironmentVariables instance
    dbhost = env_vars.db_host
    dbname = env_vars.db_name
    dbuser = urllib.parse.quote(env_vars.db_user)
    password = urllib.parse.quote(env_vars.password)
    sslmode = env_vars.sslmode

    # Construct the connection URI
    db_uri = f"host={dbhost} dbname={dbname} user={dbuser} password={password} sslmode={sslmode}"
    return db_uri

# Get the connection URI
DB_URI = get_connection_uri()

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

# Create a connection pool
pool = ConnectionPool(
    conninfo=DB_URI,  # conninfo is the connection information string
    max_size=20,
    kwargs=connection_kwargs,
)

logger.info("Database connection pool created")