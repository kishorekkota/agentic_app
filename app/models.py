# models.py
from pydantic import BaseModel
from typing import List

class ChatMessage(BaseModel):
    message_id: str
    sender: str
    content: str
    timestamp: str

class ChatHistory(BaseModel):
    username: str
    thread_id: str
    messages: List[ChatMessage]

class ChatRequest(BaseModel):
    message: str
    new_chat: bool = False
    thread_id: str 
    scope: str = "all"
    username: str = None

class ChatHistoryRequest(BaseModel):
    username: str
    thread_id: str

class AdditionalInfoRequest(BaseModel):
    username: str
    thread_id: str
    info_needed: str

class ChatFeedbackRequest(BaseModel):
    username: str
    thread_id: str
    message_id: str
    feedback: str