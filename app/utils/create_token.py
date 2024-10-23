# Example usage of create_jwt_token
from jwt_utils import create_jwt_token

user_data = {"sub": "user_id", "name": "John Doe"}
token = create_jwt_token(user_data)
print(token)