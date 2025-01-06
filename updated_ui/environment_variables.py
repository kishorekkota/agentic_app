import os
from typing import Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class EnvironmentVariables:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EnvironmentVariables, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, hosted: bool = False, profile: Optional[str] = None):
        if not self._initialized:
            logger.debug(" hosted %s", hosted)
            logger.debug(" profile %s", profile)

            if hosted:
                logger.debug("Not loading from ENV as the environment variables are sourced via Vault into the App.")
                self._load_variables_from_env()
            else:
                logger.debug("Loading Environment variables from profile...if profile is empty then loading .env %s", profile)
                env_file = f".env.{profile}" if profile else ".env"
                logger.debug("loading env file ******", env_file)
                load_dotenv(env_file, override=True)
                self._load_variables_from_env()

            self._validate_variables()
            self._initialized = True

    def _load_variables_from_env(self):
        self.chatbot_api_url = os.getenv("CHATBOT_API_URL")
        self.secret = os.getenv("SECRET_KEY")
        self.langchain_project = os.getenv("LANGCHAIN_PROJECT")
        self.langchain_tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2")
        self.langchain_endpoint = os.getenv("LANGCHAIN_ENDPOINT")
        self.langchain_hub_api_url = os.getenv("LANGCHAIN_HUB_API_URL")
        self.langchain_api_key = os.getenv("LANGCHAIN_API_KEY")

        logger.debug(f"Loaded variables: {self.chatbot_api_url}, {self.secret}, {self.langchain_project}")

    def _validate_variables(self):
        missing_vars = []
        required_attrs = [
            'chatbot_api_url',
            'secret',
            'langchain_project',
            'langchain_tracing_v2',
            'langchain_endpoint',
            'langchain_hub_api_url',
            'langchain_api_key'
        ]
        for var in required_attrs:
            if getattr(self, var) is None:
                missing_vars.append(var.upper())
        if missing_vars:
            logger.debug(f"Missing required variables: {', '.join(missing_vars)}")

    @classmethod
    def create_instance(cls, hosted: bool = False, profile: Optional[str] = None):
        if cls._instance is None:
            cls._instance = cls(hosted, profile)
        return cls._instance

    @classmethod
    def get_instance(cls):
        hosted = os.getenv("HOSTED")
        profile = os.getenv("PROFILE")

        if cls._instance is None:
            cls._instance = cls(hosted, profile)
        return cls._instance