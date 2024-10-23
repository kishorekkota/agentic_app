# config.py
import os

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "chat_db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()