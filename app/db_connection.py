from psycopg_pool import ConnectionPool  # psycopg is a PostgreSQL adapter
import logging
import os

logger = logging.getLogger(__name__)

# Use environment variables for sensitive information
DB_URI = os.getenv("DB_URI", "postgresql://simple_langchain:simple_langchain@localhost:5432/simple_langchain?sslmode=disable")


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

logger.info("Database connection pool created")