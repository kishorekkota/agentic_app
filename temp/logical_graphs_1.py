import os
#instantiate vars
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from operator import add
load_dotenv()
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, TypedDict, Optional,Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureChatOpenAI
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from libs.hrbot import hrbot
from libs.retriever import CustomRetriever
from prompts.prompt_templates import general_hr_prompt

class GraphState(TypedDict):
    question: Optional[str] = None
    classification: Optional[str] = None
    client_state: Optional[str] = None 
    client_industry: Optional[str] = None 
    response: Optional[str] = None
    # response:Annotated[list[str], add]
    human_ask: Optional[str] = None
    human_input: Optional[str] = None

class User_Input(BaseModel):
    """" Valid United States state name and industry name """

    state: str = Field(description="US State name")
    industry: str = Field(description="Industry name")
    






class Input_graph():



        
    def __init__(self):

        load_dotenv()

        credential = DefaultAzureCredential()
        key_vault = os.getenv("AZURE_KEY_VAULT_ENDPOINT")
        keyvault_client = SecretClient(vault_url=key_vault, credential=credential)
        openai_gpt_4o_model_name=os.getenv("AZURE_OPENAI_GPT4_MODEL_NAME")
        openai_api_endpoint = os.getenv("OPENAI_ENDPOINT")
        openai_api_key = keyvault_client.get_secret("OPENAI-API-KEY").value
        self.llm = AzureChatOpenAI(temperature=0.0, deployment_name=openai_gpt_4o_model_name, azure_endpoint=openai_api_endpoint,api_key=openai_api_key)
        self.categories_list=['overtime','sick leave','wage','exempt/not-exempt classification']
        self.categories = ', '.join(self.categories_list)

    def classify(self,question):
        response = self.llm("classify intent of given input question in specific to one of the following categories: "+self.categories+". Output just the category it fits or None if it fits none of the categories.Input:{}".format(question))
        return response.content.strip()
      

    def extract_client_state(self,question):
        response = self.llm("classify if the state of the client is specified in the question.If so extract and output that state. If not output only 'No state'. Output just the class.Input:{}".format(question))
        return response.content.strip()
      
    def extract_client_industry(self,question):
        response = self.llm("classify if the industry of the client is specified in the question.If so extract and output that industry. If not output only 'No industry'. Output just the class.Input:{}".format(question))
        return response.content.strip()
      
    def extract_client_dem(self,state):
        question = state.get('question', '').strip()
        client_state = self.extract_client_state(question)
        client_industry = self.extract_client_industry(question)
        return {"client_state": client_state, "client_industry": client_industry}


    def verify_user_input(self,state):
        human_input=state.get('human_input', '').strip()
        structured_llm = self.llm.with_structured_output(User_Input)
        system = """"Classify if a valid US state name or short name is provided in the human input.If yes return the only the US state name converted to its long name. If not output 'Not Valid'. Also classify if a valid client industry name is provided in the human input.If yes return the  the industry name. If not output 'Not Valid'. Do not consider city names."""
        prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{input}")])
        few_shot_structured_llm = prompt | structured_llm
        response = few_shot_structured_llm.invoke(input=human_input)
        return response.state, response.industry
        



    def classify_input_node(self,state):
        question = state.get('question', '').strip()
        classification = self.classify(question) 
        return {"classification": classification}

    def get_client_dem(self, *args, **kwargs):
        return {"human_ask": "Hello! Could you please provide your state and industry?"}
      
    def initial_greeting(self, *args, **kwargs):
      response= "Hello! I am an HR AI Assistant. I can only answer questions about: " +self.categories+" for now but I am still learning."
      return {"response": response}

    def check_user_input(self,state):
        client_state=self.verify_user_input(state)[0]
        client_industry=self.verify_user_input(state)[1]
        return {"client_state": client_state,"client_industry": client_industry}






    def handle_RAG(self,state):

        query = state.get('question', '').strip()
        Search_Retriever= CustomRetriever(nr_top_docs=5,retrieval_type='all')
        retriever=Search_Retriever.get_retriever()
        hr_general_prompt=general_hr_prompt()
        hrcoplilot=hrbot(hr_general_prompt)

        response=hrcoplilot.get_answer(query,retriever)[0]
        return  {"response": response}


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
    def get_client_data(self,state):
        return "get_client_dem" if state.get('client_state') == "No state" or state.get('client_industry') == "No industry" else "handle_RAG"
    def reply_human_state(self,state):
        return "get_client_dem" if state.get('client_state') == "Not Valid" or state.get('client_industry') == "Not Valid" else "handle_RAG_human_input"

    def build_graph(self):



        
        workflow = StateGraph(GraphState)
        workflow.add_node("classify_input", self.classify_input_node)
        workflow.add_node("extract_client_dem", self.extract_client_dem)
        workflow.add_node("get_client_dem", self.get_client_dem)
        workflow.add_node("initial_greeting", self.initial_greeting)
        workflow.add_node("check_user_input", self.check_user_input)
        workflow.add_node("handle_RAG", self.handle_RAG)
        workflow.add_node("handle_RAG_human_input", self.handle_RAG_human_input)
        workflow.set_entry_point("classify_input")
        workflow.add_edge('handle_RAG', END)
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
                "handle_RAG": "handle_RAG"
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

        return workflow
    

    def initiate_graph(self):
        memory = MemorySaver()
        workflow=self.build_graph()
        app = workflow.compile(checkpointer=memory)
        return app
