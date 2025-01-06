from azure.keyvault.secrets import SecretClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
import openai


class AISearchIndex:
    def __init__(self, index_name=None, service_name=None, azure_search_api_key=None,  
                 openai_api_key=None, openai_api_version=None, openai_api_endpoint=None,
                   openai_embedding_model=None):
        self.index_name = index_name
        self.service_name = service_name
        self.azure_search_api_key = azure_search_api_key
        self.endpoint = f"https://{self.service_name}.search.windows.net"
        self.credential = AzureKeyCredential(self.azure_search_api_key)
        self.index_client = SearchIndexClient(endpoint=self.endpoint, credential=self.credential)
        self.search_client = SearchClient(endpoint=self.endpoint, index_name=self.index_name, credential=self.credential)
        self.openai_api_key = openai_api_key
        self.openai_api_version = openai_api_version
        self.openai_api_endpoint = openai_api_endpoint
        self.embedding_model = openai_embedding_model
        self.openai_client = openai.AzureOpenAI(
                                    api_key=self.openai_api_key,
                                    api_version=self.openai_api_version,
                                    azure_endpoint=self.openai_api_endpoint,
                                            )


    #unenforced abstract method
    def create_index(self):
        pass

    #unenforced abstract method
    def populate_index(self, data):
        pass

    def generate_embeddings_oai(self, text):
        return self.openai_client.embeddings.create(input=[text], model=self.embedding_model).data[0].embedding


