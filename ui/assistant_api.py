import requests
import os
import env_loader
import logging
from ui_utils import make_authenticated_request
import pprint
import json

env_loader.load_dotenv()

CHATBOT_API_URL = os.getenv('CHATBOT_API_URL')

logger = logging.getLogger(__name__)

def chatbot_request(user_input, new_chat, thread_id: str, scope: str, username: str,additional_info_needed: bool = False):
    """
    Sends a user's input to the chatbot API and retrieves the response.

    Parameters:
    user_input (str): The message from the user to be sent to the chatbot.

    Returns:
    str: The response from the chatbot.

    Raises:
    requests.exceptions.RequestException: If there is an error with the HTTP request.
    """
    logger.info("Sending user input to chatbot API")

    json_str = {
        "message": "" if additional_info_needed else user_input,
        "new_chat": new_chat,
        "thread_id": thread_id,
        "scope": scope,
        "username": username,
        "user_answer": user_input if additional_info_needed else ""
    }



    # json_str = json.dumps({
    #     "message": user_input,
    #     "new_chat": new_chat,
    #     "thread_id": thread_id,
    #     "scope": scope,
    #     "username": username
    # })
    logger.debug(f"Request payload: {json_str}")

    pprint.pprint(json_str)

    response = make_authenticated_request(CHATBOT_API_URL, "POST", json_str, {"scope": scope, "username": username})

    logger.debug(f"Response: {response.json()}")

    response.raise_for_status()
    
    return response.json().get('response')