import requests
import logging
from ui_utils import make_authenticated_request
import pprint
from environment_variables import EnvironmentVariables

env = EnvironmentVariables.get_instance()
CHATBOT_API_URL = env.chatbot_api_url

logger = logging.getLogger(__name__)

def chatbot_request(user_input, new_chat, thread_id: str, scope: str, username: str, additional_info: bool, client_state: str, client_industry: str, client_id: str):
    logger.info("Sending user input to chatbot API")

    json_str = {
        "message": "" if additional_info else user_input,
        "new_chat": new_chat,
        "thread_id": thread_id,
        "scope": scope,
        "username": username,
        "user_answer": user_input if additional_info else "",
        "client_state": client_state,
        "client_industry": client_industry,
        "client_id": client_id if client_id else ""
    }

    logger.debug(f"Request payload: {json_str}")
    pprint.pprint(json_str)

    if client_id:
        response = make_authenticated_request(f"{CHATBOT_API_URL}/chat_with_client_id", "POST", json_str, {"scope": scope, "username": username})
    else:
        response = make_authenticated_request(f"{CHATBOT_API_URL}/chat", "POST", json_str, {"scope": scope, "username": username})

    logger.debug(f"Response: {response.json()}")
    pprint.pprint(response.json())

    response.raise_for_status()
    return response.json().get('response')

def validate_client_id(client_id, scope, username):
    logger.info("Sending client ID to chatbot API for validation")

    json_str = {
        "message": "",
        "new_chat": False,
        "thread_id": "",
        "scope": "",
        "username": "",
        "user_answer": "",
        "client_state": "",
        "client_industry": "",
        "client_id": client_id
    }

    logger.debug(f"Request payload: {json_str}")
    pprint.pprint(json_str)

    response = make_authenticated_request(f"{CHATBOT_API_URL}/verify_clientid", "POST", json_str, {"scope": scope, "username": username})

    logger.debug(f"Response: {response.json()}")
    pprint.pprint(response.json())

    response.raise_for_status()
    return response.json().get('response')