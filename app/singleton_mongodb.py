# singleton_mongodb.py
from pymongo import MongoClient
import config

class SingletonMongoDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SingletonMongoDB, cls).__new__(cls)
            cls._instance.client = MongoClient(
                config.MONGODB_URI,
                maxPoolSize=50,  # Maximum number of connections in the pool
                minPoolSize=10,  # Minimum number of connections in the pool
                serverSelectionTimeoutMS=5000  # Timeout for server selection
            )
            cls._instance.db = cls._instance.client[config.DATABASE_NAME]
        return cls._instance

    @classmethod
    def get_db(cls):
        return cls._instance.db