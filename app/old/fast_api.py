# fast_api.py
from fastapi import FastAPI, Request, HTTPException, Depends
from pydantic import BaseModel
from env_setup import setup_environment
import logging
import os
import json
from contextlib import asynccontextmanager

from ai_assistant import AIAssistant
from start_up import Startup

app = FastAPI()

startup = Startup()

setup_environment()

# Lifespan context manager for startup and shutdown tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    startup.connect_to_mongodb()
    yield
    # Shutdown tasks
    startup.close_mongodb_connection()

app = FastAPI(lifespan=lifespan)

# Pydantic models to define the structure of incoming requests
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

def get_ai_assistant(thread_id: str, new_chat: bool):
    return AIAssistant(thread_id, new_chat)

@app.post("/chat")
async def chat(request: ChatRequest, assistant: AIAssistant = Depends(get_ai_assistant)):
    try:
        user_message = request.message
        startup.logger.info("Received request: %s", request)
        startup.logger.debug("user_message: %s new_chat: %s thread_id: %s", user_message, request.new_chat, request.thread_id)

        if request.new_chat:
            assistant.new_conversation = True
        else:
            assistant.thread_id = request.thread_id

        bot_response = assistant.run(user_message)
        startup.logger.info("Responding back to client for thread_id: %s", bot_response.thread_id)
        startup.logger.debug("Sending response: %s", bot_response)

        return {"response": bot_response}
    except Exception as e:
        startup.logger.error("Error processing chat request: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/chat/history")
async def chat_history(request: ChatHistoryRequest, assistant: AIAssistant = Depends(get_ai_assistant)):
    try:
        username = request.username
        thread_id = request.thread_id
        startup.logger.info("Received history request for username: %s, thread_id: %s", username, thread_id)

        history = assistant.get_history(username, thread_id)
        startup.logger.info("Returning chat history for username: %s, thread_id: %s", username, thread_id)

        return {"history": history}
    except Exception as e:
        startup.logger.error("Error processing chat history request: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/chat/additional_info")
async def additional_info(request: AdditionalInfoRequest, assistant: AIAssistant = Depends(get_ai_assistant)):
    try:
        username = request.username
        thread_id = request.thread_id
        info_needed = request.info_needed
        startup.logger.info("Received additional info request for username: %s, thread_id: %s, info_needed: %s", username, thread_id, info_needed)

        additional_info_response = assistant.request_additional_info(username, thread_id, info_needed)
        startup.logger.info("Returning additional info response for username: %s, thread_id: %s", username, thread_id)

        return {"additional_info_response": additional_info_response}
    except Exception as e:
        startup.logger.error("Error processing additional info request: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/chat/feedback")
async def chat_feedback(request: ChatFeedbackRequest, assistant: AIAssistant = Depends(get_ai_assistant)):
    try:
        username = request.username
        thread_id = request.thread_id
        message_id = request.message_id
        feedback = request.feedback
        startup.logger.info("Received feedback for username: %s, thread_id: %s, message_id: %s", username, thread_id, message_id)

        feedback_response = assistant.submit_feedback(username, thread_id, message_id, feedback)
        startup.logger.info("Returning feedback response for username: %s, thread_id: %s, message_id: %s", username, thread_id, message_id)

        return {"feedback_response": feedback_response}
    except Exception as e:
        startup.logger.error("Error processing feedback request: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")