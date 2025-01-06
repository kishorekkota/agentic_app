# jwt_utils.py
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer
from jwt import PyJWTError
import os
import logging
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.environment_variables import EnvironmentVariables


env = EnvironmentVariables.get_instance()

SECRET_KEY = env.secret

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 240  # Token expiration time

security = HTTPBearer()

loggers = logging.getLogger(__name__)

def decode_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

def get_current_user(token: str = Security(security)):
    loggers.debug("Get current user")
    return decode_jwt(token.credentials)

def create_jwt_token(data: dict):
    logging.debug("Create JWT token")
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        # Replace 'your-secret-key' with your actual secret key
        print(SECRET_KEY)
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="JWT token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid JWT token")