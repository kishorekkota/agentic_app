from fastapi import FastAPI, Request
from pydantic import BaseModel
from env_setup import setup_environment
import logging
import os
import json

from ai_assistant import AIAssistant

app = FastAPI()

log_level = os.getenv("LOG_LEVEL", "INFO").upper()

setup_environment()

# Configure logging
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)


# Pydantic model to define the structure of incoming requests
class ChatRequest(BaseModel):
    message: str
    new_chat: bool = False
    thread_id: str 


@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message

    logger.info("Received request: %s", request)

    logger.debug("user_message: " + user_message + " new_chat: " + str(request.new_chat)+ " thread_id: " + request.thread_id)

    assistant = AIAssistant(request.thread_id, request.new_chat)

    if(request.new_chat):
        assistant.new_conversation = True
    else:
        assistant.thread_id = request.thread_id
    
    logger.debug("ai assistant: execution " + str(assistant))

    bot_response = assistant.run(user_message)
    
    logger.info("Responding back to client.for thread_id: " + bot_response.thread_id)

    logger.debug("Sending response: %s ", bot_response)

    return {bot_response}