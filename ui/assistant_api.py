import requests
import os
import env_loader

env_loader.load_dotenv()

CHATBOT_API_URL = os.getenv('CHATBOT_API_URL')

def chatbot_response(user_input,new_chat):
    """
    Sends a user's input to the chatbot API and retrieves the response.

    Parameters:
    user_input (str): The message from the user to be sent to the chatbot.

    Returns:
    str: The response from the chatbot.

    Raises:
    requests.exceptions.RequestException: If there is an error with the HTTP request.
    """
    response = requests.post(CHATBOT_API_URL, json={"message": user_input, "new_chat": new_chat})
    response.raise_for_status()
    return response.json()["response"]