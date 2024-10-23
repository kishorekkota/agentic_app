# startup.py
import logging
import config
from pymongo import MongoClient

class Startup:
    def __init__(self):
        self.logger = self.configure_logging()
        self.db_client = None

    def configure_logging(self):
        logging.basicConfig(level=config.LOG_LEVEL)
        logger = logging.getLogger(__name__)
        return logger

    def connect_to_mongodb(self):
        self.db_client = MongoClient(config.MONGODB_URI)
        self.logger.info("Connected to MongoDB")

    def close_mongodb_connection(self):
        if self.db_client:
            self.db_client.close()
            self.logger.info("Closed MongoDB connection")