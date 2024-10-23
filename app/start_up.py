# startup.py
from model.mongodb import SingletonMongoDB
import config
import logging
import os

class Startup:
    def __init__(self):
        self.logger = self.configure_logging()

    def configure_logging(self):
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(level=log_level)
        logger = logging.getLogger(__name__)
        return logger

    def connect_to_mongodb(self):
        SingletonMongoDB.get_db();
        self.logger.info("Connected to MongoDB")

    def close_mongodb_connection(self):
        SingletonMongoDB.get_db().client.close()
        self.logger.info("Closed MongoDB connection")