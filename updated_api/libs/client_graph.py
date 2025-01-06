import os
import logging
import json
from dotenv import load_dotenv
from typing import Dict, TypedDict, Optional, List
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import AzureChatOpenAI
from azure.identity import ManagedIdentityCredential,DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from io import StringIO
from azure.keyvault.secrets import SecretClient
from libs.hrbot import hrbot
from libs.retriever import CustomRetriever
from prompts.prompt_templates import general_hr_prompt
from api.environment_variables import EnvironmentVariables
from langchain.globals import set_debug, set_verbose
from libs.answer import Answer, Sources
import uuid
from langsmith import traceable
from langchain_core.tracers.context import tracing_v2_enabled
from langsmith import Client
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from libs.models import GraphState, User_Input
from libs.uitls import map_response, map_client_id_response, data_sources_mapping, create_dataset
from langgraph.checkpoint.postgres import PostgresSaver
from libs.db_connections import pool
from docx import Document
from io import BytesIO

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Load environment variables
load_dotenv()
env = EnvironmentVariables.get_instance()

memory = PostgresSaver(pool)

memory.setup()

class ClientGraph:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ClientGraph, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            logger.debug("Initializing ClientGraph instance")
            self.load_environment_variables()
            self.initialize_llm()
            self.load_client_demographics()
            self._initialized = True
            
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_environment_variables(self):
        logger.debug("Loading environment variables")
        self.credential = DefaultAzureCredential()
        self.openai_gpt_4o_model_name = env.openai_gpt_4o_model_name
        self.openai_api_endpoint = env.openai_api_endpoint
        self.openai_api_key = env.openai_api_key
        self.account_url = env.account_url
        self.container_name = env.container_name
        self.blob_path = env.client_demographics_blob_path
        self.job_description_sample_blob_path=env.job_description_sample_blob_path
        self.config_path = "configs/hrbot_config.json"
        with open(self.config_path) as f:
            config_file = json.load(f)
        self.categories_list = config_file['knowledge_categories']
        self.tools_list=config_file['tools']
        self.categories = ', '.join(self.categories_list+self.tools_list)
        logger.debug("Environment variables loaded")

    def initialize_llm(self):
        logger.debug("Initializing LLM")
        self.llm = AzureChatOpenAI(
            temperature=0.0,
            deployment_name=self.openai_gpt_4o_model_name,
            azure_endpoint=self.openai_api_endpoint,
            api_key=self.openai_api_key
        )
        logger.debug("LLM initialized")

    def load_client_demographics(self):
        logger.debug("Loading client demographics")
        blob_service_client = BlobServiceClient(account_url=self.account_url, credential=self.credential)
        blob_client = blob_service_client.get_blob_client(container=self.container_name, blob=self.blob_path)
        blob_data = blob_client.download_blob().readall().decode('utf-8')
        self.client_demographics = pd.read_csv(StringIO(blob_data))
        #print(self.client_demographics.CltNbr.to_list())
        logger.debug("Client demographics loaded")

    def verify_client_id(self, state):
        client_id = state.get('client_id', '').strip()
        logger.debug("Verifying client ID: %s", client_id)
        if client_id in self.client_demographics.CltNbr.to_list():
            return {"client_id": client_id}
        else:
            return {"client_id": 'Not Found'}

    def get_client_id(self, *args, **kwargs):
        logger.debug("Getting client ID")
        return {"human_ask": "Hello! The client id you provided cannot be found. Can you double check and input the correct client id?"}

    def classify(self, question):
        logger.debug("Classifying question: %s", question)
        response = self.llm(f"classify intent of given input question in specific to one of the following categories: {self.categories}. Output just the category it fits or None if it fits none of the categories. Input: {question}")
        logger.debug("Classification result: %s", response.content.strip())
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
        if state.get('client_name', '').strip()!='':
            input=input+ " client name: " + state.get('client_name', '').strip()
        print(input)
      
        example=self.read_job_description_sample()
        response = self.llm.invoke(f"Produce a detailed job description using the job title and primary duties and client demographics provided in the input. Produce the job description if valid job titles or positions are found in the input. if not ask for the job title or position. Use the format and structure of the example: {example} ,Input:{input}")
        return {"response": response.content.strip()}

    def extract_client_dem(self, state):
        question = state.get('question', '').strip()
        client_id = state.get('client_id', '').strip()
        logger.debug("Extracting client demographics for client ID: %s", client_id)
        client_state = self.client_demographics[self.client_demographics['CltNbr'] == client_id]['LegalState'].iloc[0]
        client_industry = self.client_demographics[self.client_demographics['CltNbr'] == client_id]['NAICSLevel01'].iloc[0]
        client_name = self.client_demographics[self.client_demographics['CltNbr'] == client_id]['CltName'].iloc[0]
        logger.debug("Extracted client state: %s, client industry: %s", client_state, client_industry)
        return {"client_state": client_state, "client_industry": client_industry,"client_name": client_name}

    def classify_input_node(self, state):
        question = state.get('question', '').strip()
        logger.debug("Classifying input node for question: %s", question)
        classification = self.classify(question)
        logger.debug("Input node classification result: %s", classification)
        return {"classification": classification}

    def initial_greeting(self, *args, **kwargs):
        response = f"Hello! I am an HR AI Assistant. I can only answer questions about: {self.categories} for now but I am still learning."
        logger.debug("Initial greeting response: %s", response)
        return {"response": response}

    def handle_RAG_human_input(self, state):
        query = state.get('question', '').strip() + " Client State: " + state.get('client_state', '').strip() + " Client Industry: " + state.get('client_industry', '').strip()
        logger.debug("Handling RAG with human input for query: %s", query)
        retriever = CustomRetriever(nr_top_docs=3, retrieval_type='all').get_retriever()
        hr_general_prompt = general_hr_prompt()
        hrcoplilot = hrbot(hr_general_prompt)
        response = hrcoplilot.get_answer(query, retriever)
        logger.debug("RAG response: %s", response)


        sources = data_sources_mapping(response[1])
        state['source_title'] = [source.title for source in sources]
        state['source_metadata_id'] = [source.reference_id for source in sources]
        state['source_url'] = [source.url for source in sources]
        logger.debug(f"RAG response with human input sources: {response[1]}")
        return {"response": response[0],"sources":response[1],"source_title":state['source_title'],"source_url":state['source_url']}
    
    def classify_knowledge_tool(self, state):
        classification = state.get('classification', '').strip()
        return {"classification": classification}
    

    def decide_next_node(self, state):
        logger.debug(f"Deciding next node for state: {state}")
        if state.get('classification') in self.categories_list:
            next_node = "extract_client_dem"
        elif state.get('classification') in self.tools_list:
            next_node = "extract_client_dem"
        else:
            next_node = "initial_greeting"
        logger.debug(f"Next node: {next_node}")
        return next_node

    def check_client_id_validity(self, state):
        logger.debug("Checking client ID validity for state: %s", state)
        next_node = "get_client_id" if state.get('client_id') == 'Not Found' else "classify_input"
        logger.debug(f"Next node: {next_node}")
        return next_node
    
    


    def tool_knowledge_node(self, state):
        next_node = "produce_job_description" if state.get('classification') == 'job descriptions' else "handle_RAG_human_input"
        logger.debug(f"Next node: {next_node}")
        return next_node
        

    def build_graph(self):
        logger.debug("Building graph")
        workflow = StateGraph(GraphState)
        workflow.add_node("classify_input", self.classify_input_node)
        workflow.add_node("extract_client_dem", self.extract_client_dem)
        workflow.add_node("verify_client_id", self.verify_client_id)
        workflow.add_node("get_client_id", self.get_client_id)
        workflow.add_node("initial_greeting", self.initial_greeting)
        workflow.add_node("classify_knowledge_tool", self.classify_knowledge_tool)
        
        workflow.add_node("handle_RAG_human_input", self.handle_RAG_human_input)
        workflow.add_node("produce_job_description", self.produce_job_description)
        workflow.set_entry_point("verify_client_id")
        workflow.add_edge("extract_client_dem", "classify_knowledge_tool")
        workflow.add_edge('handle_RAG_human_input', END)
        workflow.add_edge('produce_job_description', END)
        workflow.add_conditional_edges(
            "classify_input",
            self.decide_next_node,
            {
                "extract_client_dem": "extract_client_dem",
                "initial_greeting": "initial_greeting",
            }
        )

        workflow.add_conditional_edges(
            "classify_knowledge_tool",
            self.tool_knowledge_node,
            {
                "handle_RAG_human_input": "handle_RAG_human_input",
                "produce_job_description": "produce_job_description"
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
        logger.debug("Graph built successfully")
        return workflow

    def initiate_graph(self):
        logger.debug("Initiating graph")
        workflow = self.build_graph()
        app = workflow.compile(checkpointer=memory)
        logger.debug("Graph initiated successfully")
        return app

    def get_answer(self, query, user_answer, thread_id,client_state=None,client_industry=None,client_id=None):
        logger.info("Getting answer for query: %s", query)
        # input_graph = InputGraph.get_instance()
        # app = input_graph.initiate_graph()

        # client_graph = Client_graph.get_instance()
        # client_app = client_graph.initiate_graph()

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
                # with tracing_v2_enabled():
                #     if(client_state and client_state !=""):
                #         response = self.invoke({"question": query, 'length': 0,'client_state':client_state,'client_industry':client_industry}, config=config, interrupt_before=[breakpoint])
                #     else:
                app.update_state(config, {"client_id": client_id})
                logger.debug("updated state with client id %s",client_id)
                breakpoint="check_client_id_validity"
                with tracing_v2_enabled():
                    response = app.invoke({"question": query, 'length': 0}, config=config, interrupt_before=[breakpoint])


            else:
                with tracing_v2_enabled():
                    breakpoint = "check_user_input"
                    logger.debug("Updating state to process humer input %s",user_answer)
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