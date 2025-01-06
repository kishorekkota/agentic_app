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

# set_debug(True)
# set_verbose(True)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Load environment variables
load_dotenv()
env = EnvironmentVariables.get_instance()

memory = MemorySaver()

class GraphState(TypedDict):
    question: Optional[str] = None
    client_id: Optional[str] = None
    classification: Optional[str] = None
    client_state: Optional[str] = None
    client_industry: Optional[str] = None
    response: Optional[str] = None
    human_ask: Optional[str] = None
    human_input: Optional[str] = None
    source_title: Optional[List[str]] = None
    source_metadata_id: Optional[List[str]] = None
    source_url: Optional[List[str]] = None

class User_Input(BaseModel):
    """Valid United States state name and industry name"""
    state: str = Field(description="US State name")
    industry: str = Field(description="Industry name")


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
            credential = DefaultAzureCredential()
            key_vault = env.key_vault
            openai_gpt_4o_model_name = env.openai_gpt_4o_model_name
            openai_api_endpoint = env.openai_api_endpoint
            openai_api_key = env.openai_api_key
            self.llm = AzureChatOpenAI(temperature=0.0, deployment_name=openai_gpt_4o_model_name, azure_endpoint=openai_api_endpoint, api_key=openai_api_key)
            config_path=str(env.config_path)
            with open(config_path) as f:
                config_file = json.load(f)
            self.categories_list=config_file['knowledge_categories']
            self.categories = ', '.join(self.categories_list)
            self._initialized = True

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def classify(self, question):
        logger.debug(f"Classifying question: {question}")
        response = self.llm.invoke(f"classify intent of given input question in specific to one of the following categories: {self.categories}.Classify questions about salary in the 'wage' category. Output just the category it fits or None if it fits none of the categories. Input: {question}")
        logger.debug(f"Classification result: {response.content.strip()}")
        return response.content.strip()

    def extract_client_state(self, question):
        logger.debug(f"Extracting client state from question: {question}")
        response = self.llm.invoke(f"classify if the state of the client is specified in the question. If so, extract and output that state. If not, output only 'No state'. Output just the class. Input: {question}")
        logger.debug(f"Extracted client state: {response.content.strip()}")
        return response.content.strip()

    def extract_client_industry(self, question):
        logger.debug(f"Extracting client industry from question: {question}")
        response = self.llm.invoke(f"classify if the industry of the client is specified in the question. If so, extract and output that industry. If not, output only 'No industry'. Output just the class. Input: {question}")
        logger.debug(f"Extracted client industry: {response.content.strip()}")
        return response.content.strip()
    

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
        structured_llm = self.llm.with_structured_output(User_Input)
        system = """Classify if a valid US state name or short name is provided in the human input. If yes, return only the US state name converted to its long name. If not, output 'Not Valid'. Also classify if a valid client industry name is provided in the human input. If yes, return the industry name. If not, output 'Not Valid'. Do not consider city names."""
        prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{input}")])
        few_shot_structured_llm = prompt | structured_llm
        response = few_shot_structured_llm.invoke(input=human_input)
        return response.state, response.industry

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
        query = state.get('question', '').strip() + " Client State: " + state.get('client_state', '').strip() + " Client Industry: " + state.get('client_industry', '').strip()
        logger.debug(f"Handling RAG with human input for query: {query}")
        retriever = CustomRetriever(nr_top_docs=3, retrieval_type='all').get_retriever()
        hr_general_prompt = general_hr_prompt()
        hrcoplilot = hrbot(hr_general_prompt)
        response = hrcoplilot.get_answer(query, retriever)
        sources = self.data_sources_mapping(response[1])
        state['source_title'] = [source.title for source in sources]
        state['source_metadata_id'] = [source.reference_id for source in sources]
        state['source_url'] = [source.url for source in sources]
        logger.debug(f"RAG response with human input sources: {response[1]}")
        return {"response": response[0],"sources":response[1],"source_title":state['source_title'],"source_url":state['source_url']}

    def decide_next_node(self, state):
        logger.debug(f"Deciding next node for state: {state}")
        next_node = "extract_client_dem" if state.get('classification') in self.categories_list else "initial_greeting"
        logger.debug(f"Next node: {next_node}")
        return next_node

    def get_client_data(self, state):
        logger.debug(f"Getting client data for state: {state}")
        next_node = "get_client_dem" if state.get('client_state') == "No state" or state.get('client_industry') == "No industry" else "handle_RAG_human_input"
        logger.debug(f"Next node: {next_node}")
        return next_node

    def reply_human_state(self, state):
        logger.debug(f"Replying human state for state: {state}")
        next_node = "get_client_dem" if state.get('client_state') == "Not Valid" or state.get('client_industry') == "Not Valid" else "handle_RAG_human_input"
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
        workflow.set_entry_point("classify_input")
        workflow.add_edge('handle_RAG_human_input', END)
        workflow.add_edge('get_client_dem', 'check_user_input')
        workflow.add_conditional_edges(
            "classify_input",
            self.decide_next_node,
            {
                "extract_client_dem": "extract_client_dem",
                "initial_greeting": "initial_greeting"
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

    def map_response(self, response, query, thread_id, run_id):
        logger.debug("Mapping response")

        if "response" in response:
            logger.debug("Does not require human response")
            answer = Answer(answer=response['response'], additional_info_needed=False, sources=[], question=query, run_id=run_id, thread_id=thread_id,
                            client_industry=response['client_industry'] if 'client_industry' in response else None,
                            client_state=response['client_state'] if 'client_state' in response else None)
        elif "human_ask" in response:
            logger.debug("Requires human response")
            answer = Answer(answer=response['human_ask'], additional_info_needed=True, sources=[], question=query, run_id=run_id, thread_id=thread_id,client_industry=None,client_state=None)
        
        if "source_title" in response and "source_url" in response:
            logger.debug("Mapping sources from response")
            sources = []
            for title, url in zip(response["source_title"], response["source_url"]):
                source = Sources(reference_id="", title=title, url=url)
                sources.append(source)
            answer.sources = sources
        
        return answer


    def map_client_id_response(self, response, query, thread_id, run_id):
        logger.debug("Mapping map_client_id_response")

        answer = Answer(answer=response['response'], additional_info_needed=False, sources=[], question=query, run_id=run_id, thread_id=thread_id,
                        client_industry=response['client_industry'] if 'client_industry' in response else None,
                        client_state=response['client_state'] if 'client_state' in response else None)

        
        return answer

    def data_sources_mapping(self, dataframe_sources):
        logger.debug("Mapping dataframe sources to Sources objects")
        sources = []
        for _, row in dataframe_sources.iterrows():
            source = Sources(
                reference_id=row['reference_id'],
                title=row['title'],
                url=row['reference_link']
            )
            sources.append(source)
        return sources

    def create_dataset(self, answer):
        logger.debug("Writing to dataset: create_dataset %s", answer)
        client = Client()
        client.create_example(inputs={"question": answer.question}, outputs={"response": answer.answer}, dataset_id="93570a3b-c2ed-41c3-b526-bd3cba38da80")

    def get_answer(self, query, user_answer, thread_id,client_state=None,client_industry=None):
        logger.info("Getting answer for query: %s", query)
        # input_graph = InputGraph.get_instance()
        # app = input_graph.initiate_graph()

        # client_graph = Client_graph.get_instance()
        # client_app = client_graph.initiate_graph()

        run_id = uuid.uuid4()

        config = {"configurable": {"thread_id": thread_id}, "run_id": run_id, "metadata": {"user_id": "user name"}}
        logger.debug("Config: %s", config)
        
        try:
            breakpoint = "check_user_input"
            if user_answer == "":
                current_state = self.get_state(config)
                logger.debug("client_state: %s", client_state)
                logger.debug("client_industry: %s", client_industry)
                if(current_state.metadata):
                    logger.debug("Update state to clear response from previous interation")
                    self.update_state(config=config, values={"response": None,"source_title":None,"source_metadata_id":None,"source_url":None})
                with tracing_v2_enabled():
                    if(client_state and client_state !=""):
                        response = self.invoke({"question": query, 'length': 0,'client_state':client_state,'client_industry':client_industry}, config=config, interrupt_before=[breakpoint])
                    else:
                        response = self.invoke({"question": query, 'length': 0}, config=config, interrupt_before=[breakpoint])


            else:
                with tracing_v2_enabled():
                    breakpoint = "check_user_input"
                    logger.debug("Updating state to process humer input %s",user_answer)
                    self.update_state(config=config, values={"human_input": user_answer})
                    logger.debug("Getting answer to the question")
                    response = self.invoke(None, config=config,interrupt_before=[breakpoint])

            logger.debug("Response: %s", response)
            
            state = self.get_state(config)
            logger.debug("state: %s", state)

            answer = self.map_response(response, query, thread_id, run_id)
            logger.debug("Answer: %s", answer)

            logger.debug("Writing to dataset: %s", answer)
            self.create_dataset(answer)

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

            answer = self.map_client_id_response(response, client_id, thread_id, run_id)
            logger.debug("Answer: %s", answer)

            return answer
        except Exception as e:
            logger.error("Error getting answer: %s", e)
            return {"error": str(e)}
def main():
    input_graph = InputGraph()
    input_graph.get_answer('What is the Overtime Policy', "", 1)

if __name__ == "__main__":
    main()