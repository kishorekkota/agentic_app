# jwt_utils.py
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer
from jwt import PyJWTError
import os
from datetime import datetime, timedelta
from environment_variables import EnvironmentVariables

env = EnvironmentVariables.get_instance()


SECRET_KEY = env.secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token expiration time

security = HTTPBearer()

def decode_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

def get_current_user(token: str = Security(security)):
    return decode_jwt(token.credentials)

def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt