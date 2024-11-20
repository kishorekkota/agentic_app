# logical_graph.py

import os
import logging
from dotenv import load_dotenv
from typing import Dict, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import AzureChatOpenAI
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from libs.hrbot import hrbot
from libs.retriever import CustomRetriever
from prompts.prompt_templates import general_hr_prompt
from api.environment_variables import EnvironmentVariables

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
env = EnvironmentVariables.get_instance()

memory = MemorySaver()

class GraphState(TypedDict):
    question: Optional[str] = None
    classification: Optional[str] = None
    client_state: Optional[str] = None  
    response: Optional[str] = None
    human_ask: Optional[str] = None
    human_state: Optional[str] = None

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
            openai_gpt_4o_model_name = env.azure_openai_deployment_name
            openai_api_endpoint = env.azure_openai_endpoint
            openai_api_key = env.azure_openai_api_key
            self.llm = AzureChatOpenAI(temperature=0.0, deployment_name=openai_gpt_4o_model_name, azure_endpoint=openai_api_endpoint, api_key=openai_api_key)
            self._initialized = True

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def classify(self, question):
        logger.debug(f"Classifying question: {question}")
        response = self.llm(f"classify intent of given input question in one of the following categories: overtime, sick leave, other. Output just the class. Input: {question}")
        logger.debug(f"Classification result: {response.content.strip()}")
        return response.content.strip()

    def extract_client_state(self, question):
        logger.debug(f"Extracting client state from question: {question}")
        response = self.llm(f"classify if the state of the client is specified in the question. If so, extract and output that state. If not, output only 'No state'. Output just the class. Input: {question}")
        logger.debug(f"Extracted client state: {response.content.strip()}")
        return response.content.strip()

    def verify_user_feedback(self, human_state):
        logger.debug(f"Verifying user feedback: {human_state}")
        response = self.llm(f"classify if a valid US state name or short name is provided in the input. If yes, return only the state converted to its long name. If not, output 'Not Valid'. Output just the class. Input: {human_state}")
        logger.debug(f"Verified user feedback: {response.content.strip()}")
        return response.content.strip()

    def classify_client_state(self, state):
        question = state.get('question', '').strip()
        logger.debug(f"Classifying client state for question: {question}")
        client_state = self.extract_client_state(question)
        logger.debug(f"Client state classification result: {client_state}")
        return {"client_state": client_state}

    def classify_input_node(self, state):
        question = state.get('question', '').strip()
        logger.debug(f"Classifying input node for question: {question}")
        classification = self.classify(question)
        logger.debug(f"Input node classification result: {classification}")
        return {"classification": classification}

    def get_state(self, *args, **kwargs):
        logger.debug("Getting state")
        return {"human_ask": "Hello! Could you please provide the state you are in?"}

    def check_user_feedback(self, state):
        human_state = state.get('human_state', '').strip()
        logger.debug(f"Checking user feedback for state: {human_state}")
        updated_human_state = self.verify_user_feedback(human_state)
        logger.debug(f"Updated human state: {updated_human_state}")
        return {"human_state": updated_human_state}

    def handle_RAG(self, state):
        query = state.get('question', '').strip()
        logger.debug(f"Handling RAG for query: {query}")
        retriever = CustomRetriever(nr_top_docs=5)
        hr_general_prompt = general_hr_prompt()
        hrcoplilot = hrbot(hr_general_prompt)
        response = hrcoplilot.get_answer(query, retriever)
        logger.debug(f"RAG response: {response}")
        return {"response": response}

    def handle_RAG_human_feedback(self, state):
        query = state.get('question', '').strip() + state.get('human_state', '').strip()
        logger.debug(f"Handling RAG with human feedback for query: {query}")
        retriever = CustomRetriever(nr_top_docs=5)
        hr_general_prompt = general_hr_prompt()
        hrcoplilot = hrbot(hr_general_prompt)
        response = hrcoplilot.get_answer(query, retriever)
        logger.debug(f"RAG response with human feedback: {response}")
        return {"response": response}

    def decide_next_node(self, state):
        logger.debug(f"Deciding next node for state: {state}")
        next_node = "extract_client_state" if state.get('classification') == "overtime" else "handle_RAG"
        logger.debug(f"Next node: {next_node}")
        return next_node

    def get_client_data(self, state):
        logger.debug(f"Getting client data for state: {state}")
        next_node = "get_client_state" if state.get('client_state') == "No state" else "handle_RAG"
        logger.debug(f"Next node: {next_node}")
        return next_node

    def reply_human_state(self, state):
        logger.debug(f"Replying human state for state: {state}")
        next_node = "get_client_state" if state.get('human_state') == "Not Valid" else "handle_RAG_human_feedback"
        logger.debug(f"Next node: {next_node}")
        return next_node

    def build_graph(self):
        logger.debug("Building graph")
        workflow = StateGraph(GraphState)
        workflow.add_node("classify_input", self.classify_input_node)
        workflow.add_node("extract_client_state", self.classify_client_state)
        workflow.add_node("get_client_state", self.get_state)
        workflow.add_node("check_user_feedback", self.check_user_feedback)
        workflow.add_node("handle_RAG", self.handle_RAG)
        workflow.add_node("handle_RAG_human_feedback", self.handle_RAG_human_feedback)
        workflow.set_entry_point("classify_input")
        workflow.add_edge('handle_RAG', END)
        workflow.add_edge('handle_RAG_human_feedback', END)
        workflow.add_edge('get_client_state', 'check_user_feedback')
        workflow.add_conditional_edges(
            "classify_input",
            self.decide_next_node,
            {
                "extract_client_state": "extract_client_state",
                "handle_RAG": "handle_RAG"
            }
        )
        workflow.add_conditional_edges(
            "extract_client_state",
            self.get_client_data,
            {
                "get_client_state": "get_client_state",
                "handle_RAG": "handle_RAG"
            }
        )
        workflow.add_conditional_edges(
            "check_user_feedback",
            self.reply_human_state,
            {
                "get_client_state": "get_client_state",
                "handle_RAG_human_feedback": "handle_RAG_human_feedback"
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

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test the InputGraph via command line")
    parser.add_argument("question", type=str, help="The question to classify and process")
    args = parser.parse_args()
    print(" getting answer for question: ", args.question)
    input_graph = InputGraph.get_instance()
    app = input_graph.initiate_graph()

    state = {"question": args.question}
    try:
        response = app.run(state)
        print(response)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()