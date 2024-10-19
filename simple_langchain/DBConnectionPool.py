from psycopg_pool import ConnectionPool  # psycopg is a PostgreSQL adapter


import os

# Use environment variables for sensitive information
DB_URI = os.getenv("DB_URI")


connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}


pool = ConnectionPool(
    # Example configuration
    conninfo=DB_URI,  # conninfo is the connection information string
    max_size=20,
    kwargs=connection_kwargs,
)