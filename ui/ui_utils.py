# ui_utils.py
import requests
from jwt_utils import create_jwt_token
import logging
import pprint

logger = logging.getLogger(__name__)

def generate_jwt_token(user_data):
    return create_jwt_token(user_data)

def make_authenticated_request(url, method, json_data, user_data):
    logger.info("Making authenticated request to API")

    token = generate_jwt_token(user_data)
    headers = {"Authorization": f"Bearer {token}"}

    logger.debug(f"Token: {token}")
    logger.debug(f"Headers: {headers}")
    logger.debug(f"json_data: {json_data}")

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=json_data, headers=headers)
        else:
            raise ValueError("Unsupported HTTP method")

        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        return response

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        logger.error(f"Response content: {response.content}")
        pprint.pprint(response.json())
        raise
    except Exception as err:
        logger.error(f"An error occurred: {err}")
        raise