# environment_variables.py

import os
from typing import Optional
from dotenv import load_dotenv
import logging

class EnvironmentVariables:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EnvironmentVariables, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, hosted: bool = False, profile: Optional[str] = None):
        if not self._initialized:
            self._initialized = True
            if hosted:
                logging.info("Not loading from ENV as the environment variables are sourced via Vault into the App.")
                self._load_variables_from_env()
            else:
                logging.info("Loading Environment variables from profile...if profile is empty then loading .env")
                env_file = f".env.{profile}" if profile else ".env"
                load_dotenv(env_file,override=True)
                self._load_variables_from_env()

            # Validate that all required variables are set
            self._validate_variables()

    def _load_variables_from_env(self):
        self.key_vault = os.getenv("AZURE_KEY_VAULT_ENDPOINT")
        self.config_path=str(os.getenv('CONFIG_PATH'))
        self.openai_api_version = os.getenv("OPENAI_API_VERSION")
        self.openai_api_endpoint = os.getenv("OPENAI_ENDPOINT")
        self.embedding_model = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_SMALL")
        self.azure_search_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
        self.openai_gpt_4o_model_name = os.getenv("AZURE_OPENAI_GPT4_MODEL_NAME")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.secret = os.getenv("SECRET_KEY")
        self.internal_guidelines_index_name = os.getenv("INTERNAL_GUIDELINES_INDEX_NAME")
        self.external_regulations_index_name = os.getenv("EXTERNAL_REGULATIONS_INDEX_NAME")
        self.azure_hrcopilot_search_api_key = os.getenv("AZURE_SEARCH_HRCOPILOT_API_KEY")
        self.account_url = os.getenv('AZURE_STORAGEBLOB_RESOURCEENDPOINT')
        self.container_name = os.getenv('CLIENT_DEMOGRAPHICS_CONTAINER_NAME')
        self.industry_categories_blob_path = os.getenv('INDUSTRY_CATEGORIES_BLOB_PATH')
        self.client_demographics_blob_path = os.getenv('CLIENT_DEMOGRAPHICS_BLOB_PATH')
        self.job_description_sample_blob_path = os.getenv('JOB_DESCRIPTION_SAMPLE_BLOB_PATH')

        self.db_host = os.getenv("DB_HOST")
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self.db_sslmode = os.getenv("DB_SSLMODE")
        print(os.getenv('LANGCHAIN_TRACING_V2'))
        print(os.getenv('LANGCHAIN_ENDPOINT'))
        print(os.getenv('LANGCHAIN_PROJECT'))
        print("self.key_vault",self.key_vault)
        


    def _validate_variables(self):
        missing_vars = []
        required_attrs = [
            'key_vault',
            'openai_api_version',
            'openai_api_endpoint',
            'embedding_model',
            'azure_search_endpoint',
            'openai_gpt_4o_model_name',
            'openai_api_key',
            'internal_guidelines_index_name',
            'external_regulations_index_name',
            'azure_hrcopilot_search_api_key',
            'db_host',
            'db_name',
            'db_user',
            'db_password',
            'db_sslmode',
            'account_url',
            'container_name',
            'industry_categories_blob_path',
            'client_demographics_blob_path'

        ]
        for var in required_attrs:
            if getattr(self, var) is None:
                missing_vars.append(var.upper())
        if missing_vars:
            logging.error(f"Missing required variables: {', '.join(missing_vars)}")

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