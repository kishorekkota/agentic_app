from sentence_transformers import util
from sentence_transformers import SentenceTransformer
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import torch
import os
from openai import AzureOpenAI
from api.environment_variables import EnvironmentVariables

import logging

logger = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG)

env = EnvironmentVariables.get_instance()

class EmbeddingModel():
    def __init__(self,type,model_name=None):
    
        self.openai_api_key = env.openai_api_key
        self.openai_api_version = env.openai_api_version
        self.openai_api_endpoint = env.openai_api_endpoint
        self.embedding_model =env.embedding_model
        self.client=AzureOpenAI(api_key=self.openai_api_key, api_version=self.openai_api_version, azure_endpoint=self.openai_api_endpoint)
        self.type=type

    def generate_embeddings(self,query,type='openai',model_path=None): 
            
            if type=='openai': # model = "deployment_name"
                return self.client.embeddings.create(input=[query], model=self.embedding_model).data[0].embedding
            elif type=='sentence_transformers':
                device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
                model = SentenceTransformer(model_path, device=device)
                return model.encode(query)
        
        