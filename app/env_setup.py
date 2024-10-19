import os
import getpass
import logging

logger = logging.getLogger(__name__)

def set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

def setup_environment():
    logger.info("Setting up environment variables")
    set_env("OPENCAGE_API_KEY")
    set_env("OPENAI_API_KEY")
    set_env("LANGCHAIN_OPENAI_API_KEY")
    set_env("TAVILY_API_KEY")
    set_env("DB_URI")
    set_env("LOG_LEVEL")