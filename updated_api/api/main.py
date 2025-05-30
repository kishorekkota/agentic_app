# main.py
import os
from fastapi import FastAPI, Request, status, Depends
from api.environment_variables import EnvironmentVariables

hosted = os.getenv("HOSTED")
profile = os.getenv("PROFILE")
env = EnvironmentVariables.create_instance()

from contextlib import asynccontextmanager
from api.routes import router
# from api.health_router import router_health
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging
from api.jwt_utils import verify_jwt_token

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)



logger.info("Hosted: %s, Profile: %s", hosted, profile)



app = FastAPI()

# Lifespan context manager for startup and shutdown tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    logger.info("Starting up the application...")
    yield
    logger.info("Shutting down the application...")
    # Shutdown tasks

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("Request validation error: %s", exc)
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    
    # Get the request body
    body = await request.body()
    body_str = body.decode('utf-8')
    logger.error("Request body: %s", body_str)
    
    content = {'status_code': 10422, 'message': exc_str, 'data': None}
    return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

app = FastAPI(lifespan=lifespan)

# Include the router
app.include_router(router, dependencies=[Depends(verify_jwt_token)])
# app.include_router(router_health)
app.add_exception_handler(RequestValidationError, validation_exception_handler)