# rag_assistant.py

import os
import uuid
import logging

os.environ["AZURESEARCH_FIELDS_ID"] = "chunk_id"
os.environ["AZURESEARCH_FIELDS_CONTENT"] = "chunk"
os.environ["AZURESEARCH_FIELDS_CONTENT_VECTOR"] = "text_vector"

from typing import Literal

from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain import hub

from db_connection import pool
from chat_response import ChatBot
from azure_search import create_vector_store, create_vector_store_tool
from agent_state import AgentState
import prettyprinter as pp

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class RAGAIAssistant:
    def __init__(self, thread_id: str, new_conversation: bool = True):
        self.azure_openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        self.azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")

        if not self.azure_openai_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY environment variable not set.")
        if not self.azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable not set.")

        self.thread_id = thread_id
        self.user_message = None
        self.new_conversation = new_conversation

        # Initialize the language model
        self.llm = AzureChatOpenAI(
            deployment_name='gpt-35-turbo',
            openai_api_key=self.azure_openai_api_key,
            openai_api_version="2024-05-01-preview",
            openai_api_type="azure",
            azure_endpoint=self.azure_openai_endpoint,
            temperature=0
        )

        # Create vector store and retriever tool
        vector_store = create_vector_store()
        self.retrieval_tool = create_vector_store_tool(vector_store)

        # Bind the retriever tool to the LLM
        self.model_tool = self.llm.bind_tools([self.retrieval_tool])

        # Set up the workflow
        self._setup_workflow()

    def _setup_workflow(self):
        logger.info("Setting up workflow...")

        # Initialize the StateGraph with AgentState
        workflow = StateGraph(AgentState)

        # Add nodes to the workflow
        workflow.add_node("agent", self.agent)
        retrieve_node = ToolNode([self.retrieval_tool])
        workflow.add_node("retrieve", retrieve_node)
        workflow.add_node("rewrite", self.rewrite)
        workflow.add_node("generate", self.generate)

        # Define the workflow edges
        workflow.add_edge(START, "agent")

        # Conditional edges based on the agent's decision
        workflow.add_conditional_edges(
            "agent",
            tools_condition,
            {
                "tools": "retrieve",
                END: END,
            },
        )

        # Conditional edges after retrieval
        workflow.add_conditional_edges(
            "retrieve",
            self.grade_documents,
            {
                "generate": "generate",
                "rewrite": "rewrite",
            },
        )

        workflow.add_edge("generate", END)
        workflow.add_edge("rewrite", "agent")

        # Set up memory with PostgresSaver
        memory = PostgresSaver(pool)
        memory.setup()
        logger.info("Workflow setup completed.")

        self.workflow = workflow.compile(checkpointer=memory)

    def start_new_session(self):
        self.thread_id = uuid.uuid4().hex
        self.new_conversation = False
        logger.info(f"Started new session with thread_id: {self.thread_id}")

    def run(self, user_message: str) -> ChatBot:
        self.user_message = user_message
        if self.new_conversation:
            self.start_new_session()
        config = {"configurable": {"thread_id": self.thread_id}}

        logger.info(f"Running workflow for message: {user_message}")
        response_state = self.workflow.invoke(
            {"messages": [HumanMessage(content=self.user_message)]},
            config=config
        )

        messages = response_state.get("messages", [])
        if messages:
            last_message = messages[-1].content
        else:
            last_message = ""

        response = ChatBot(self.user_message, last_message, self.thread_id)

        return response

    def grade_documents(self, state: MessagesState) -> Literal["generate", "rewrite"]:
        logger.info("Starting document grading process.")

        class Grade(BaseModel):
            binary_score: str = Field(description="Relevance score 'yes' or 'no'.")

        try:
            model = AzureChatOpenAI(
                deployment_name='gpt-35-turbo',
                openai_api_key=self.azure_openai_api_key,
                openai_api_base=self.azure_openai_endpoint,
                openai_api_version="2024-05-01-preview",
                openai_api_type="azure",
                temperature=0
            )
            llm_with_tool = model.with_structured_output(Grade)

            prompt = PromptTemplate(
                template=(
                    "You are a grader assessing relevance of a retrieved document to a user question.\n"
                    "Here is the retrieved document:\n{context}\n\n"
                    "Here is the user question: {question}\n"
                    "If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant.\n"
                    "Give a binary 'yes' or 'no' score to indicate whether the document is relevant to the question."
                ),
                input_variables=["context", "question"],
            )

            chain = prompt | llm_with_tool

            messages = state["messages"]
            if not messages:
                logger.error("No messages found in state.")
                return "rewrite"

            last_message = messages[-1]
            question = messages[0].content
            docs = last_message.content

            scored_result = chain.invoke({"question": question, "context": docs})
            score = scored_result.binary_score.strip().lower()

            logger.info(f"Grading result: {score}")

            if score == "yes":
                logger.info("Decision: Documents are relevant. Proceeding to generate.")
                return "generate"
            else:
                logger.info("Decision: Documents are not relevant. Proceeding to rewrite.")
                return "rewrite"

        except Exception as e:
            logger.error(f"An error occurred during document grading: {e}")
            return "rewrite"

    def agent(self, state: MessagesState):
        """
        Invokes the agent model to generate a response based on the current state. Given
        the question, it will decide to retrieve using the retriever tool, or simply end.

        Args:
            state (messages): The current state

        Returns:
            dict: The updated state with the agent response appended to messages
        """
        logger.info("Invoking agent.")
        try:
            messages = state["messages"]
            if not messages:
                logger.error("No messages found in state.")
                return {"messages": []}
      
            pp.pprint(self.model_tool)
            response = self.model_tool.invoke(messages)
            logger.info("Agent invoked successfully.")

            print(response.pretty_print())

            return {"messages": [response]}

        except Exception as e:
            logger.error(f"An error occurred in agent: {e}")
            return {"messages": []}

    def rewrite(self, state: MessagesState):
        logger.info("Starting query rewrite process.")

        try:
            messages = state["messages"]
            if not messages:
                logger.error("No messages found in state.")
                return {"messages": []}

            question = messages[0].content

            msg = [
                HumanMessage(
                    content=(
                        "Look at the input and try to reason about the underlying semantic intent/meaning.\n"
                        "Here is the initial question:\n"
                        "-------\n"
                        f"{question}\n"
                        "-------\n"
                        "Formulate an improved question:"
                    ),
                )
            ]

            model = AzureChatOpenAI(
                deployment_name='gpt-35-turbo',
                openai_api_key=self.azure_openai_api_key,
                openai_api_base=self.azure_openai_endpoint,
                openai_api_version="2024-05-01-preview",
                openai_api_type="azure",
                temperature=0
            )
            response = model.invoke(msg)
            logger.info("Query rewritten successfully.")

            return {"messages": [response]}

        except Exception as e:
            logger.error(f"An error occurred during query rewrite: {e}")
            return {"messages": []}

    def generate(self, state: MessagesState):
        logger.info("Starting answer generation process.")

        try:
            messages = state["messages"]
            if not messages:
                logger.error("No messages found in state.")
                return {"messages": []}

            question = messages[0].content
            last_message = messages[-1]
            docs = last_message.content

            prompt = hub.pull("rlm/rag-prompt")
            logger.debug("Prompt pulled from hub.")

            model = AzureChatOpenAI(
                deployment_name='gpt-35-turbo',
                openai_api_key=self.azure_openai_api_key,
                openai_api_base=self.azure_openai_endpoint,
                openai_api_version="2024-05-01-preview",
                openai_api_type="azure",
                temperature=0
            )

            rag_chain = prompt | model | StrOutputParser()

            response = rag_chain.invoke({"context": docs, "question": question})
            logger.info("Answer generated successfully.")

            return {"messages": [response]}

        except Exception as e:
            logger.error(f"An error occurred during answer generation: {e}")
            return {"messages": []}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    
    rag_assistant = RAGAIAssistant(thread_id="test_thread_id", new_conversation=True)
    #rag_assistant.retriever_tool(" What is the leave policy ? ")
    create_vector_store().search(" What is the leave policy ? ",search_type='similarity')
    response = rag_assistant.run("What is process for taking extended leave in New York?")
    print(f"Assistant: {response}")
