import os
import uuid
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
from db_connection import pool
from typing import Literal
from tools import search_google, get_weather_by_zip,search_azure_rag
from chat_response import ChatBot
import logging
from langsmith.run_helpers import get_current_run_tree
from langsmith import traceable, run_helpers
from langchain.callbacks.tracers.langchain import wait_for_all_tracers


logger = logging.getLogger(__name__)

class AIAssistant:
    def __init__(self, thread_id: str,new_conversation: bool = True):
        self.ai_api_key = os.environ.get("OPENAI_API_KEY")
        self.tavily_api_key =  os.environ.get("TAVILY_API_KEY")

        if not self.ai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        if not self.tavily_api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set.")
        
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=self.ai_api_key)  # Added temperature for control
        self.thread_id = thread_id
        self.user_message = None
        self.new_conversation = new_conversation
        self._setup_tools()
        self._setup_workflow()

    def _setup_tools(self):
        self.tools = [search_google, get_weather_by_zip]

    def _setup_workflow(self):
        print("Setting up workflow... __setup_workflow__")
        tool_node = ToolNode(self.tools)
        llm_with_tools = self.llm.bind_tools(self.tools)

        def call_model(state: MessagesState):
            logger.info("call_model calling model...")
            messages = state["messages"]
            logger.debug(f"call_model: {messages}")  # For debugging purposes, print the messages received.
            response = llm_with_tools.invoke(messages)
            logger.debug(f"call_model: {response}")  # For debugging purposes, print the response received.
            return {"messages": [response]}

        def should_continue(state: MessagesState) -> Literal["tools", END]:
            print("should_continue called...")
            messages = state['messages']
            last_message = messages[-1]
            return "tools" if last_message.tool_calls else END
        
        try:

            workflow = StateGraph(MessagesState)
            workflow.add_node("agent", call_model)
            workflow.add_node("tools", tool_node)
            workflow.add_edge(START, "agent")
            workflow.add_conditional_edges("agent", should_continue)
            workflow.add_edge("tools", "agent")

            memory = PostgresSaver(pool)
            memory.setup()
            logger.info("Workflow setup completed.")
            logger.debug(pool.get_stats())

            self.workflow = workflow.compile(checkpointer=memory)
        except Exception as e:
            logger.error(f"Error setting up workflow: {e}")
            print("Error setting up workflow: ", e)
            raise e
        # config = {"configurable": {"thread_id": self.thread_id}}
        # checkpoint = memory.get(config)

        # if checkpoint:
        #     self.workflow.load_state(checkpoint)
        #     print("Loaded state from checkpoint.")

    def start_new_session(self):
        self.thread_id = uuid.uuid4().hex
        self.new_conversation = False
        logger.info(f"Started new session with thread_id: {self.thread_id}")

    def run(self, user_message: str):
        self.user_message = user_message
        if self.new_conversation:
            self.start_new_session()
        
        run_id = uuid.uuid4()
        print("*********Run ID:", run_id)
        config = {"configurable": {"thread_id": self.thread_id},"run_id": run_id}
        self.workflow.get_state(config)
        try:
            response = self.workflow.invoke(
                {"messages": [HumanMessage(content=self.user_message)]}, config)
        finally:
            wait_for_all_tracers()          
        
        langsmith_run = get_current_run_tree()
        print("Langsmith Run:", langsmith_run)
        #print(f"Run ID for processing: {langsmith_run.}") 
        
        print("*****Response from workflow:", response)

        for message in response["messages"]:
            message.pretty_print()  # Print the response in a pretty format for readability.

        chat_response = ChatBot(user_message,response["messages"][-1].content,self.thread_id,run_id)

        return chat_response