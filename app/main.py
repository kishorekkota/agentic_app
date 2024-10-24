# main.py
from fastapi import FastAPI,Request, status,Depends
from contextlib import asynccontextmanager
from startup import Startup
from routes import router
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging
from jwt_utils import verify_jwt_token

logger = logging.getLogger(__name__)

app = FastAPI()

startup = Startup()

# Lifespan context manager for startup and shutdown tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    startup.connect_to_mongodb()
    startup.configure_environment()
    yield
    # Shutdown tasks
    startup.close_mongodb_connection()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Request validation error: {exc}")
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    
    # Get the request body
    body = await request.body()
    body_str = body.decode('utf-8')
    logger.error(f"Request body: {body_str}")
    
    content = {'status_code': 10422, 'message': exc_str, 'data': None}
    return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


app = FastAPI(lifespan=lifespan)

# Include the router
app.include_router(router, dependencies=[Depends(verify_jwt_token)])
app.add_exception_handler(RequestValidationError, validation_exception_handler)