# ui_utils.py
import requests
from jwt_utils import create_jwt_token

def generate_jwt_token(user_data):
    return create_jwt_token(user_data)

def make_authenticated_request(url, method="GET", data=None, user_data=None):
    token = generate_jwt_token(user_data)
    headers = {"Authorization": f"Bearer {token}"}
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, json=data, headers=headers)
    else:
        raise ValueError("Unsupported HTTP method")
    return response.json()