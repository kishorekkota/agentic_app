# routes.py
from fastapi import APIRouter, HTTPException, Depends
from models import  ChatHistoryRequest, AdditionalInfoRequest, ChatFeedbackRequest, ChatRequest
from ai_assistant import AIAssistant
from startup import Startup
from jwt_utils import get_current_user

router = APIRouter()
startup = Startup()


def get_ai_assistant(thread_id: str, new_chat: bool):
    return AIAssistant(thread_id, new_chat)


#, current_user: dict = Depends(get_current_user), assistant: AIAssistant = Depends(get_ai_assistant)
@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        assistant = get_ai_assistant(request.thread_id, request.new_chat)
        startup.logger.info("Received chat request: %s", request)
        startup.logger.debug("user_message: %s new_chat: %s thread_id: %s", request.message, request.new_chat, request.thread_id)

        if request.new_chat:
            assistant.new_conversation = True
        else:
            assistant.thread_id = request.thread_id

        bot_response = assistant.run(request.message)
        startup.logger.info("Responding back to client for thread_id: %s", bot_response.thread_id)
        startup.logger.debug("Sending response: %s", bot_response)

        return {"response": bot_response}
    except Exception as e:
        startup.logger.error("Error processing chat request: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/chat/history")
async def chat_history(request: ChatHistoryRequest):
    try:
        assistant = get_ai_assistant(request.thread_id, request.new_chat)

        startup.logger.info("Received history request for username: %s, thread_id: %s", request.username, request.thread_id)

        history = assistant.get_history(request.username, request.thread_id)
        startup.logger.info("Returning chat history for username: %s, thread_id: %s", request.username, request.thread_id)

        return {"history": history}
    except Exception as e:
        startup.logger.error("Error processing chat history request: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/chat/additional_info")
async def additional_info(request: AdditionalInfoRequest):
    try:
        assistant = get_ai_assistant(request.thread_id, request.new_chat)

        startup.logger.info("Received additional info request for username: %s, thread_id: %s, info_needed: %s", request.username, request.thread_id, request.info_needed)

        additional_info_response = assistant.request_additional_info(request.username, request.thread_id, request.info_needed)
        startup.logger.info("Returning additional info response for username: %s, thread_id: %s", request.username, request.thread_id)

        return {"additional_info_response": additional_info_response}
    except Exception as e:
        startup.logger.error("Error processing additional info request: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/chat/feedback")
async def chat_feedback(request: ChatFeedbackRequest):
    try:
        startup.logger.info("Received feedback for username: %s, thread_id: %s, message_id: %s", request.username, request.thread_id, request.message_id)

        feedback_response = assistant.submit_feedback(request.username, request.thread_id, request.message_id, request.feedback)
        startup.logger.info("Returning feedback response for username: %s, thread_id: %s, message_id: %s", request.username, request.thread_id, request.message_id)

        return {"feedback_response": feedback_response}
    except Exception as e:
        startup.logger.error("Error processing feedback request: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")