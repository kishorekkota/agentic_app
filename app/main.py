# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from startup import Startup
from routes import router

app = FastAPI()

startup = Startup()

# Lifespan context manager for startup and shutdown tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    startup.connect_to_mongodb()
    yield
    # Shutdown tasks
    startup.close_mongodb_connection()

app = FastAPI(lifespan=lifespan)

# Include the router
app.include_router(router)