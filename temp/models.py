from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    message: str
    new_chat: bool = False
    thread_id: str
    scope: str
    username: str 
    user_answer: str
    client_state: str
    client_industry: str
    client_id: str


class ChatMessage(BaseModel):
    message_id: str
    sender: str
    content: str
    timestamp: str

class ChatHistory(BaseModel):
    username: str
    thread_id: str
    messages: List[ChatMessage]


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