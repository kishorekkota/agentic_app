# environment_variables.py

import os
from typing import Optional
from dotenv import load_dotenv
from azure.identity import ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient

class EnvironmentVariables:
    def __init__(self, use_key_vault: bool = False, key_vault_name: Optional[str] = None):
        if use_key_vault:
            if not key_vault_name:
                raise ValueError("Key Vault name must be provided when use_key_vault is True.")
            self._load_variables_from_key_vault(key_vault_name)
        else:
            # Load environment variables from a .env file, if present
            load_dotenv()
            self._load_variables_from_env()

        # Validate that all required variables are set
        self._validate_variables()

    def _load_variables_from_env(self):
        # Azure OpenAI Service Variables
        self.azure_openai_api_key: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_endpoint: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_deployment_name: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.azure_openai_embedding_deployment: Optional[str] = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        # Azure Cognitive Search Variables
        self.azure_search_endpoint: Optional[str] = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.azure_search_key: Optional[str] = os.getenv("AZURE_SEARCH_KEY")
        self.azure_search_index_name: Optional[str] = os.getenv("AZURE_SEARCH_INDEX_NAME")

        # PostgreSQL Database Variables
        self.db_host: Optional[str] = os.getenv("DB_HOST")
        self.db_name: Optional[str] = os.getenv("DB_NAME")
        self.db_user: Optional[str] = os.getenv("DB_USER")
        self.sslmode: Optional[str] = os.getenv("SSLMODE")
        self.password: Optional[str] = os.getenv("DB_PASSWORD")

    def _load_variables_from_key_vault(self, key_vault_name: str):
        # Authenticate to Azure using Managed Identity
        credential = ManagedIdentityCredential()
        vault_url = f"https://{key_vault_name}.vault.azure.net"
        client = SecretClient(vault_url=vault_url, credential=credential)

        # Azure OpenAI Service Variables
        self.azure_openai_api_key = self._get_secret(client, "AZURE-OPENAI-API-KEY")
        self.azure_openai_endpoint = self._get_secret(client, "AZURE-OPENAI-ENDPOINT")
        self.azure_openai_deployment_name = self._get_secret(client, "AZURE-OPENAI-DEPLOYMENT-NAME")
        self.azure_openai_embedding_deployment = self._get_secret(client, "AZURE-OPENAI-EMBEDDING-DEPLOYMENT")

        # Azure Cognitive Search Variables
        self.azure_search_endpoint = self._get_secret(client, "AZURE-SEARCH-ENDPOINT")
        self.azure_search_key = self._get_secret(client, "AZURE-SEARCH-KEY")
        self.azure_search_index_name = self._get_secret(client, "AZURE-SEARCH-INDEX-NAME")

        # PostgreSQL Database Variables
        self.db_host = self._get_secret(client, "DB-HOST")
        self.db_name = self._get_secret(client, "DB-NAME")
        self.db_user = self._get_secret(client, "DB-USER")
        self.sslmode = self._get_secret(client, "SSL-MODE")
        self.password = self._get_secret(client, "DB-PASSWORD")

    def _get_secret(self, client: SecretClient, secret_name: str) -> Optional[str]:
        try:
            secret = client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            print(f"Warning: Could not retrieve '{secret_name}' from Azure Key Vault: {e}")
            return None

    def _validate_variables(self):
        missing_vars = []
        required_attrs = [
            'azure_openai_api_key',
            'azure_openai_endpoint',
            'azure_openai_deployment_name',
            'azure_openai_embedding_deployment',
            'azure_search_endpoint',
            'azure_search_key',
            'azure_search_index_name',
            'db_host',
            'db_name',
            'db_user',
            'sslmode',
            'password'
        ]
        for var in required_attrs:
            if getattr(self, var) is None:
                missing_vars.append(var.upper())
        if missing_vars:
            raise EnvironmentError(f"Missing required variables: {', '.join(missing_vars)}")