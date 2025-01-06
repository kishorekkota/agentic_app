import os
import sys
import logging
import json
from dotenv import load_dotenv
from typing import Dict, TypedDict, Optional, List, Annotated
from pydantic import BaseModel, Field
from operator import add
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import AzureChatOpenAI
from azure.identity import DefaultAzureCredential
from azure.identity import ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient
from io import StringIO
from azure.keyvault.secrets import SecretClient
from libs.hrbot import hrbot
from libs.retriever import CustomRetriever
from prompts.prompt_templates import general_hr_prompt
from api.environment_variables import EnvironmentVariables
from langchain.globals import set_debug, set_verbose
from libs.answer import Answer, Sources
import pprint
import uuid
from langsmith import traceable
from langchain_core.tracers.context import tracing_v2_enabled
from langsmith import Client
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from libs.models import GraphState,User_Input

# set_debug(True)
# set_verbose(True)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Load environment variables
load_dotenv()
env = EnvironmentVariables.get_instance()

memory = MemorySaver()

class Client_graph():



        
    def __init__(self):

        load_dotenv()


        credential = ManagedIdentityCredential()
        key_vault = os.getenv("AZURE_KEY_VAULT_ENDPOINT")
        keyvault_client = SecretClient(vault_url=key_vault, credential=credential)
        openai_gpt_4o_model_name=os.getenv("AZURE_OPENAI_GPT4_MODEL_NAME")
        openai_api_endpoint = os.getenv("OPENAI_ENDPOINT")
        openai_api_key = keyvault_client.get_secret("OPENAI-API-KEY").value
        self.llm = AzureChatOpenAI(temperature=0.0, deployment_name=openai_gpt_4o_model_name, azure_endpoint=openai_api_endpoint,api_key=openai_api_key)
        self.account_url = os.getenv('AZURE_STORAGEBLOB_RESOURCEENDPOINT')
        self.container_name = os.getenv('CLIENT_DEMOGRAPHICS_CONTAINER_NAME')
        self.blob_path = os.getenv('CLIENT_DEMOGRAPHICS_BLOB_PATH')
        self.config_path=str(os.getenv('CONFIG_PATH'))
        with open(self.config_path) as f:
            config_file = json.load(f)
        self.categories_list=config_file['knowledge_categories']
        self.categories = ', '.join(self.categories_list)
        blob_service_client = BlobServiceClient(account_url=self.account_url, credential=credential)
        blob_client = blob_service_client.get_blob_client(container=self.container_name, blob=self.blob_path)
        blob_data = blob_client.download_blob().readall().decode('utf-8')
        self.client_demographics = pd.read_csv(StringIO(blob_data))
        
       
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


    

    
    def verify_client_id(self,state):
        client_id = state.get('client_id', '').strip()
        if client_id in (self.client_demographics.CltNbr.to_list()) :
            client_id=client_id
        else:
            client_id='Not Found'
        return  {"client_id": client_id}
    

    def get_client_id(self, *args, **kwargs):
        return {"human_ask": "Hello! The client id you provided can not be found. Can you double check and input the correct client id?"}
    



    

    def classify(self,question):
        response = self.llm("classify intent of given input question in specific to one of the following categories: "+self.categories+". Output just the category it fits or None if it fits none of the categories.Input:{}".format(question))
        return response.content.strip()
    

      

      
    def extract_client_dem(self,state):
        question = state.get('question', '').strip()
        client_id = state.get('client_id', '').strip()
        client_state = self.client_demographics[self.client_demographics['CltNbr']==client_id]['LegalState'].iloc[0]
        client_industry = self.client_demographics[self.client_demographics['CltNbr']==client_id]['NAICSLevel01'].iloc[0]
        return {"client_state": client_state, "client_industry": client_industry}


        



    def classify_input_node(self,state):
        question = state.get('question', '').strip()
        classification = self.classify(question) 
        return {"classification": classification}
    



      
    def initial_greeting(self, *args, **kwargs):
      response= "Hello! I am an HR AI Assistant. I can only answer questions about: " +self.categories+" for now but I am still learning."
      return {"response": response}





    def handle_RAG_human_input(self,state):

        query = state.get('question', '').strip()+ " Client State: "+ state.get('client_state', '').strip()+ " Client Industry: "+ state.get('client_industry', '').strip()
        Search_Retriever= CustomRetriever(nr_top_docs=3,retrieval_type='all')
        retriever=Search_Retriever.get_retriever()
        hr_general_prompt=general_hr_prompt()
        hrcoplilot=hrbot(hr_general_prompt)

        response=hrcoplilot.get_answer(query,retriever)[0]
        return  {"response": response}


    def decide_next_node(self,state):
        return "extract_client_dem" if state.get('classification')  in self.categories_list else "initial_greeting"
    
    def check_client_id_validity(self,state):
        return "get_client_id" if state.get('client_id') =='Not Found' else "classify_input"
    

    def build_graph(self):



        
        workflow = StateGraph(GraphState)
        workflow.add_node("classify_input", self.classify_input_node)
        workflow.add_node("extract_client_dem", self.extract_client_dem)
        workflow.add_node("verify_client_id", self.verify_client_id)
        workflow.add_node("get_client_id", self.get_client_id)
        workflow.add_node("initial_greeting", self.initial_greeting)
        workflow.add_node("handle_RAG_human_input", self.handle_RAG_human_input)
        workflow.set_entry_point("verify_client_id")
        workflow.add_edge("extract_client_dem", 'handle_RAG_human_input')
        workflow.add_edge('handle_RAG_human_input', END)
        workflow.add_conditional_edges(
            "classify_input",
            self.decide_next_node,
            {
                "extract_client_dem": "extract_client_dem",
                "initial_greeting": "initial_greeting"
            }
        )



        workflow.add_conditional_edges(
            "verify_client_id",
            self.check_client_id_validity,
            {
                "get_client_id": "get_client_id",
                "classify_input": "classify_input"
            }
        )
        
        return workflow
    

    def initiate_graph(self):
        memory = MemorySaver()
        workflow=self.build_graph()
        app = workflow.compile(checkpointer=memory)
        return app

