# routes.py
from fastapi import APIRouter, HTTPException, Depends
from api.models import ChatHistoryRequest, AdditionalInfoRequest, ChatFeedbackRequest, ChatRequest
from api.jwt_utils import get_current_user
from libs.hrbot import hrbot
from prompts.prompt_templates import general_hr_prompt
import logging
from libs.retriever import CustomRetriever
from libs.input_graph import InputGraph
from libs.client_graph import ClientGraph
from api.chat_response import ChatBot
from api.environment_variables import EnvironmentVariables
import uuid

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_ai_assistant(thread_id: str, new_chat: bool):
    logger.debug("Initializing AI assistant with thread_id: %s, new_chat: %s", thread_id, new_chat)
    hr_general_prompt = general_hr_prompt()
    hrcoplilot = hrbot(hr_general_prompt)
    return hrcoplilot

hrbot = get_ai_assistant("", True)

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        logger.info("Received chat request: %s", request)
        logger.debug("user_message: %s, new_chat: %s, thread_id: %s", request.message, request.new_chat, request.thread_id)
        
        workflow = InputGraph.get_instance()
        
        if request.new_chat:
            request.thread_id = str(uuid.uuid4())
            logger.debug("Generated new thread_id: %s", request.thread_id)
        
        logger.debug("Running workflow.get_answer with message: %s, user_answer: %s, thread_id: %s, client_state: %s, client_industry: %s, client_id: %s", request.message, request.user_answer, request.thread_id,request.client_state,request.client_industry,request.client_id)
        answer = workflow.get_answer(request.message, request.user_answer, request.thread_id,)
        logger.debug("Received response from workflow: %s", answer)

        logger.info("Responding back to client for thread_id: %s", request.thread_id)
        logger.debug("Sending response: %s", answer)

        return {"response": answer}
    except Exception as e:
        logger.error("Error processing chat request: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.post("/chat_with_client_id")
async def chat(request: ChatRequest):
    try:
        logger.info("Received chat request: %s", request)
        logger.debug("user_message: %s, new_chat: %s, thread_id: %s", request.message, request.new_chat, request.thread_id)
        
        workflow = ClientGraph.get_instance()
        
        if request.new_chat:
            request.thread_id = str(uuid.uuid4())
            logger.debug("Generated new thread_id: %s", request.thread_id)
        
        logger.debug("Running workflow.get_answer with message: %s, user_answer: %s, thread_id: %s, client_state: %s, client_industry: %s, client_id: %s", request.message, request.user_answer, request.thread_id,request.client_state,request.client_industry,request.client_id)
        answer = workflow.get_answer(request.message, request.user_answer, request.thread_id,request.client_state,request.client_industry,request.client_id)
        logger.debug("Received response from workflow: %s", answer)

        logger.info("Responding back to client for thread_id: %s", request.thread_id)
        logger.debug("Sending response: %s", answer)

        return {"response": answer}
    except Exception as e:
        logger.error("Error processing chat request: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/verify_clientid")
async def verify_clientid(request: ChatRequest):
    try:
        logger.debug("validating client id for %s",request)
        workflow = InputGraph.get_instance()

        answer = workflow.validate_clientid(request.client_id)
        logger.debug("Received response from workflow: %s", answer)

        logger.info("Responding back to client for thread_id: %s", request.thread_id)
        logger.debug("Sending response: %s", answer)

        return {"response": answer}
    except Exception as e:
        logger.error("Error processing chat request: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")