# startup.py
import logging
import config
import os
from pymongo import MongoClient
import getpass

class Startup:
    def __init__(self):
        self.logger = self.configure_logging()
        self.db_client = None

    def set_env(self, var: str):
        if not os.environ.get(var):
            os.environ[var] = getpass.getpass(f"{var}: ")

    def configure_logging(self):
        logging.basicConfig(level=config.LOG_LEVEL)
        logger = logging.getLogger(__name__)
        return logger

    def connect_to_mongodb(self):
        try:
            self.db_client = MongoClient(config.MONGODB_URI)
            self.logger.info("Connected to MongoDB")
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")

    def close_mongodb_connection(self):
        if self.db_client:
            self.db_client.close()
            self.logger.info("Closed MongoDB connection")

    def configure_environment(self):
        self.logger.info("Setting up environment variables")
        self.set_env("OPENCAGE_API_KEY")
        self.set_env("OPENAI_API_KEY")
        self.set_env("LANGCHAIN_OPENAI_API_KEY")
        self.set_env("TAVILY_API_KEY")
        self.set_env("DB_URI")
        self.set_env("LOG_LEVEL")
        self.set_env("MONGODB_URI")