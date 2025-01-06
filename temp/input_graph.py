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
from libs.uitls import map_response, map_client_id_response, data_sources_mapping, create_dataset
from langgraph.checkpoint.postgres import PostgresSaver
from libs.db_connections import pool
from docx import Document
from io import BytesIO

# set_debug(True)
# set_verbose(True)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Load environment variables
load_dotenv()
env = EnvironmentVariables.get_instance()

memory = PostgresSaver(pool)
memory.setup()
class InputGraph:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(InputGraph, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            logger.debug("Initializing InputGraph instance")
            self.credential = DefaultAzureCredential()
            key_vault = env.key_vault
            openai_gpt_4o_model_name = env.openai_gpt_4o_model_name
            openai_api_endpoint = env.openai_api_endpoint
            openai_api_key = env.openai_api_key


            self.account_url = env.account_url
            print("account_url",self.account_url)
            self.container_name = env.container_name
            print("container_name",self.container_name)
            self.blob_path = env.industry_categories_blob_path
            print("blob_path",self.blob_path)
            self.job_description_sample_blob_path=env.job_description_sample_blob_path
            print("job_description_sample_blob_path",self.job_description_sample_blob_path)
            self.load_industry_codes()
            self.llm = AzureChatOpenAI(temperature=0.0, deployment_name=openai_gpt_4o_model_name, azure_endpoint=openai_api_endpoint, api_key=openai_api_key)
            config_path = "configs/hrbot_config.json"
            with open(config_path) as f:
                config_file = json.load(f)
            self.categories_list=config_file['knowledge_categories']
            self.tools_list=config_file['tools']
            self.categories = ', '.join(self.categories_list+self.tools_list)
            self._initialized = True
            



    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


    def load_industry_codes(self):
        logger.debug("Loading industry categories")
        blob_service_client = BlobServiceClient(account_url=self.account_url, credential=self.credential)
        blob_client = blob_service_client.get_blob_client(container=self.container_name, blob=self.blob_path)
        blob_data = blob_client.download_blob().readall().decode('utf-8')
        df = pd.read_csv(StringIO(blob_data))
        self.industry_codes = df[~df['NAICSLevel01'].isin(['Not Specified', 'Unclassified'])]['NAICSLevel01'].to_list()
        #print(self.client_demographics.CltNbr.to_list())
        logger.debug("Industry codes loaded")

    def classify(self, question):
        logger.debug(f"Classifying question: {question}")
        response = self.llm.invoke(f"classify intent of given input question in specific to one of the following categories: {self.categories}.Classify questions about salary in the 'wage' category. Output just the category it fits or None if it fits none of the categories. Input: {question}")
        logger.debug(f"Classification result: {response.content.strip()}")
        return response.content.strip()

    def extract_client_state(self, question):
        logger.debug(f"Extracting client state from question: {question}")
        response = self.llm.invoke(f"classify if the state of the client is specified in the question. Extract the state independent whether lower case  or upper case letters are used in the input. Also extract the state even if state abbreviations are used. If you find the state, extract and output that state. If not, output only 'No state'. Output just the class. Input: {question}")
        logger.debug(f"Extracted client state: {response.content.strip()}")
        return response.content.strip()

    def extract_client_industry(self,question):
        response = self.llm.invoke(f"classify if the industry of the client is specified in the question. Classify to  one of the following industry categories: {self.industry_codes} . Classify to one of the industry categories even if the client mentions a job title or profession. If so extract and output only that that industry category. If not output only 'No industry'. Output just the class. Input:{question}")
        logger.debug(f"Extracted client industry: {response.content.strip()}")
        return response.content.strip()
    
    def read_job_description_sample(self):
        blob_service_client = BlobServiceClient(account_url=self.account_url, credential=self.credential)
        blob_client = blob_service_client.get_blob_client(container=self.container_name, blob=self.job_description_sample_blob_path)
        blob_data = blob_client.download_blob().readall()
        doc = Document(BytesIO(blob_data))
        example=[]
        for paragraph in doc.paragraphs:
            example.append(paragraph.text)
        return example
        

    
    def produce_job_description(self,state):
        if state.get('job_title', '').strip()!='':
            input=state.get('question', '').strip() + " " + state.get('job_title', '').strip()
        else:
            input=state.get('question', '').strip()

        if state.get('client_state', '').strip()!='':
            input=input+ " in state  " + state.get('client_state', '').strip()
        if state.get('client_industry', '').strip()!='':
            input=input+ " for industry " + state.get('client_industry', '').strip()
        print(input)
      
        example=self.read_job_description_sample()
        response = self.llm.invoke(f"Produce a detailed job description using the job title and primary duties and client demographics provided in the input. Produce the job description if valid job titles or positions are found in the input. if not ask for the job title or position. Use the format and structure of the example: {example} ,Input:{input}")
        return {"response": response.content.strip()}
         
    

    def extract_client_dem(self,state):
        
        question = state.get('question', '').strip()
        client_state = self.extract_client_state(question)
        if self.extract_client_state(question)!="No state" or state.get('client_state', '').strip()=='':
            client_state = self.extract_client_state(question)
        else:
            logger.debug(" client_state %s ", state.get('client_state'))
            client_state=state.get('client_state', '').strip()
        if self.extract_client_industry(question)!="No industry" or state.get('client_industry', '').strip()=='':
            client_industry = self.extract_client_industry(question)
        else:
            logger.debug(" client_industry %s ", state.get('client_industry'))
            client_industry=state.get('client_industry', '').strip()
        return {"client_state": client_state, "client_industry": client_industry}
    

    def verify_user_input(self, state):
        human_input = state.get('human_input', '').strip()
        state=self.extract_client_state(human_input)
        industry=self.extract_client_industry(human_input)
        return state, industry


    def classify_input_node(self, state):
        question = state.get('question', '').strip()
        classification = self.classify(question)
        return {"classification": classification}

    def get_client_dem(self, *args, **kwargs):
        return {"human_ask": "Hello! Could you please provide your state and industry?"}

    def initial_greeting(self, *args, **kwargs):
        response = f"Hello! I am an HR AI Assistant. I can only answer questions about: {self.categories} for now but I am still learning."
        return {"response": response}

    def check_user_input(self, state):
        client_state, client_industry = self.verify_user_input(state)
        return {"client_state": client_state, "client_industry": client_industry}


    def handle_RAG_human_input(self, state):
        query = state.get('question', '').strip() +" " +state.get('human_input', '').strip() + " Client State: " + state.get('client_state', '').strip() + " Client Industry: " + state.get('client_industry', '').strip()
        logger.debug(f"Handling RAG with human input for query: {query}")
        retriever = CustomRetriever(nr_top_docs=3, retrieval_type='all').get_retriever()
        hr_general_prompt = general_hr_prompt()
        hrcoplilot = hrbot(hr_general_prompt)
        response = hrcoplilot.get_answer(query, retriever)
        sources = data_sources_mapping(response[1])
        state['source_title'] = [source.title for source in sources]
        state['source_metadata_id'] = [source.reference_id for source in sources]
        state['source_url'] = [source.url for source in sources]
        logger.debug(f"RAG response with human input sources: {response[1]}")
        return {"response": response[0],"sources":response[1],"source_title":state['source_title'],"source_url":state['source_url']}

    def decide_next_node(self, state):
        logger.debug(f"Deciding next node for state: {state}")
        if state.get('classification') in self.categories_list:
            next_node = "extract_client_dem"
        elif state.get('classification') in self.tools_list:
            next_node = "produce_job_description"
        else:
            next_node = "initial_greeting"
        logger.debug(f"Next node: {next_node}")
        return next_node

    def get_client_data(self, state):
        logger.debug(f"Getting client data for state: {state}")
        next_node = "get_client_dem" if state.get('client_state') == "No state" or state.get('client_industry') == "No industry" else "handle_RAG_human_input"
        logger.debug(f"Next node: {next_node}")
        return next_node

    def reply_human_state(self, state):
        logger.debug(f"Replying human state for state: {state}")
        next_node = "get_client_dem" if state.get('client_state') == "No state" or state.get('client_industry') == "No industry" else "handle_RAG_human_input"
        logger.debug(f"Next node: {next_node}")
        return next_node

    def build_graph(self):
        logger.debug("Building graph")
        workflow = StateGraph(GraphState)
        workflow.add_node("classify_input", self.classify_input_node)
        workflow.add_node("extract_client_dem", self.extract_client_dem)
        workflow.add_node("get_client_dem", self.get_client_dem)
        workflow.add_node("initial_greeting", self.initial_greeting)
        workflow.add_node("check_user_input", self.check_user_input)
        workflow.add_node("handle_RAG_human_input", self.handle_RAG_human_input)
        workflow.add_node("produce_job_description", self.produce_job_description)
        workflow.set_entry_point("classify_input")
        workflow.add_edge('handle_RAG_human_input', END)
        workflow.add_edge('get_client_dem', 'check_user_input')
        workflow.add_conditional_edges(
            "classify_input",
            self.decide_next_node,
            {
                "extract_client_dem": "extract_client_dem",
                "initial_greeting": "initial_greeting",
                "produce_job_description": "produce_job_description"
            }
        )
        workflow.add_conditional_edges(
            "extract_client_dem",
            self.get_client_data,
            {
                "get_client_dem": "get_client_dem",
                "handle_RAG_human_input": "handle_RAG_human_input"
            }
        )
        workflow.add_conditional_edges(
            "check_user_input",
            self.reply_human_state,
            {
                "get_client_dem": "get_client_dem",
                "handle_RAG_human_input": "handle_RAG_human_input"
            }
        )
        logger.debug("Graph built successfully")
        return workflow

    def initiate_graph(self):
        logger.debug("Initiating graph")
        workflow = self.build_graph()
        app = workflow.compile(checkpointer=memory)
        logger.debug("Graph initiated successfully")
        return app



   
    def get_answer(self, query, user_answer, thread_id,client_state=None,client_industry=None):
        logger.info("Getting answer for query: %s", query)

        run_id = uuid.uuid4()

        app = self.initiate_graph()

        config = {"configurable": {"thread_id": thread_id}, "run_id": run_id, "metadata": {"user_id": "user name"}}
        logger.debug("Config: %s", config)
        
        try:
            breakpoint = "check_user_input"
            if user_answer == "":
                current_state = app.get_state(config)
                logger.debug("client_state: %s", client_state)
                logger.debug("client_industry: %s", client_industry)
                if(current_state.metadata):
                    logger.debug("Update state to clear response from previous interation")
                    app.update_state(config=config, values={"response": None,"source_title":None,"source_metadata_id":None,"source_url":None})
                with tracing_v2_enabled():
                    if(client_state and client_state !=""):
                        response = app.invoke({"question": query, 'length': 0,'client_state':client_state,'client_industry':client_industry}, config=config, interrupt_before=[breakpoint])
                    else:
                        logger.debug("Asking bot to get responses for the question %s",query)
                        response = app.invoke({"question": query, 'length': 0}, config=config, interrupt_before=[breakpoint])


            else:
                with tracing_v2_enabled():
                    breakpoint = "check_user_input"
                    logger.debug("Updating state to process human input %s",user_answer)
                    app.update_state(config=config, values={"human_input": user_answer})
                    logger.debug("Getting answer to the question")
                    response = app.invoke(None, config=config,interrupt_before=[breakpoint])

            logger.debug("Response: %s", response)
            
            state = app.get_state(config)
            logger.debug("state: %s", state)

            answer = map_response(response, query, thread_id, run_id)
            logger.debug("Answer: %s", answer)

            logger.debug("Writing to dataset: %s", answer)
            create_dataset(answer)

            return answer
        except Exception as e:
            logger.error("Error getting answer: %s", e)
            return {"error": str(e)}
    
    def validate_clientid(self,client_id):
        
        logger.info("Validating client_id: %s", client_id)

        input_graph = InputGraph.get_instance()
        app = input_graph.initiate_graph()
        run_id = uuid.uuid4()
        thread_id = uuid.uuid4()

        config = {"configurable": {"thread_id": thread_id}, "run_id": run_id, "metadata": {"user_id": "user name"}}
        logger.debug("Config: %s", config)
        
        try:
            breakpoint = "check_client_id_validity"
            app.update_state(config, {"client_id": client_id})
            query="Should I pay OT to my employee ?"
            response = app.invoke({'question':query,'length':0}, config=config,interrupt_before=[breakpoint])

            logger.debug("Response: %s", response)

            answer = map_client_id_response(response, client_id, thread_id, run_id)
            logger.debug("Answer: %s", answer)

            return answer
        except Exception as e:
            logger.error("Error getting answer: %s", e)
            return {"error": str(e)}