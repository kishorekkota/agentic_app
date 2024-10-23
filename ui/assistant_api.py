import requests
import os
import env_loader
import logging

env_loader.load_dotenv()

CHATBOT_API_URL = os.getenv('CHATBOT_API_URL')

logger = logging.getLogger(__name__)

def chatbot_response(user_input,new_chat,thread_id=None,scope="all",username=None):
    """
    Sends a user's input to the chatbot API and retrieves the response.

    Parameters:
    user_input (str): The message from the user to be sent to the chatbot.

    Returns:
    str: The response from the chatbot.

    Raises:
    requests.exceptions.RequestException: If there is an error with the HTTP request.
    """

    json_str = {"message": user_input, "new_chat": new_chat, "thread_id": thread_id, "scope": scope, "username": username}

    logger.debug(json_str)

    response = requests.post(CHATBOT_API_URL,json=json_str)

    logger.debug(response.json())

    print(response.json())

    response.raise_for_status()
    
    return response.json().get('response')