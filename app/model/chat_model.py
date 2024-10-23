# chat_model.py
from pydantic import BaseModel
from typing import List
from bson import ObjectId
from model.mongodb import SingletonMongoDB

class ChatMessage(BaseModel):
    message_id: str
    sender: str
    content: str
    timestamp: str

class ChatHistory(BaseModel):
    username: str
    thread_id: str
    messages: List[ChatMessage]

class MongoDB:
    def __init__(self):
        self.db = SingletonMongoDB.get_db()

    def save_chat_history(self, chat_history: ChatHistory):
        result = self.db.chat_history.insert_one(chat_history.dict())
        return str(result.inserted_id)

    def get_chat_history(self, username: str, thread_id: str):
        result = self.db.chat_history.find_one({"username": username, "thread_id": thread_id})
        if result:
            return ChatHistory(**result)
        return None

    def update_chat_history(self, username: str, thread_id: str, chat_message: ChatMessage):
        result = self.db.chat_history.update_one(
            {"username": username, "thread_id": thread_id},
            {"$push": {"messages": chat_message.dict()}}
        )
        return result.modified_count

    def delete_chat_history(self, username: str, thread_id: str):
        result = self.db.chat_history.delete_one({"username": username, "thread_id": thread_id})
        return result.deleted_count