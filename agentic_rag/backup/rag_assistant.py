# rag_assistant.py

import os
import uuid
import logging
from typing import Literal

from langchain_openai import AzureChatOpenAI 
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langchain.schema import HumanMessage
# from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from db_connection import pool
from chat_response import ChatBot
from azure_search import create_vector_store_tool,create_vector_store
from agent_state import AgentState
# from node_processor import NodeProcessor
from langgraph.prebuilt import tools_condition
import azure_search 

logger = logging.getLogger(__name__)

class RAGAIAssistant:
    def __init__(self, thread_id: str, new_conversation: bool = True):

        self.azure_ai_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")

        if not self.azure_ai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")

        # https://azure-open-ai-kishore.openai.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15

        GROUNDED_PROMPT="""
        You are an AI assistant that helps users learn from the information found in the source material.
        Answer the query using only the sources provided below.
        Use bullets if the answer has multiple points.
        If the answer is longer than 3 sentences, provide a summary.
        Answer ONLY with the facts listed in the list of sources below. Cite your source when you answer the question
        If there isn't enough information below, say you don't know.
        Do not generate answers that don't use the sources below.
        Query: {query}
        Sources:\n{sources}
        """
        self.llm = AzureChatOpenAI(model="gpt-4", temperature=0, openai_api_key=self.azure_ai_api_key,azure_endpoint=self.azure_endpoint,api_version="2024-08-01-preview",azure_deployment='gpt-35-turbo')
        self.thread_id = thread_id
        self.user_message = None
        self.new_conversation = new_conversation
        vector_store = azure_search.create_vector_store()
        retriever_tool = azure_search.create_vector_store_tool(vector_store)

        #model = AzureChatOpenAI(temperature=0, streaming=True, model="gpt-4-turbo",api_version="2024-08-01-preview",azure_deployment='gpt-35-turbo',azure_endpoint=os.environ.get("AZURE_ENDPOINT"),openai_api_key=os.environ.get("AZURE_API_KEY"))

        self.model_tool = self.llm.bind_tools([retriever_tool])  # Bind the tools to the model
        self._setup_workflow()



    def _setup_workflow(self):
        logger.info("Setting up workflow...")
        
        #tool_node = ToolNode(self.tools)
        
        #llm_with_tools = self.llm.bind_tools(self.tools)

        # Define functions used in the workflow
        # def call_model(state: MessagesState):
        #     logger.info("call_model invoking model...")
        #     messages = state["messages"]
        #     logger.debug(f"call_model messages: {messages}")
        #     response = self.llm.invoke(messages)
        #     logger.debug(f"call_model response: {response}")
        #     return {"messages": [response]}

        # def should_continue(state: MessagesState) -> Literal["tools", END]:
        #     messages = state['messages']
        #     last_message = messages[-1]
        #     if last_message.tool_calls:
        #         return "tools"
        #     else:
        #         return END

        # def grade_documents(state: MessagesState) -> Literal["generate", "rewrite"]:
        #     # Implement your logic to grade documents here
        #     # For illustration, we'll assume all documents are relevant
        #     logger.info("Grading documents...")
        #     return "generate"

        # Define your workflow graph
        workflow = StateGraph(AgentState)

        # node_processor = NodeProcessor()

        # Add nodes to the workflow
        workflow.add_node("agent", self.agent)
        retriever_tool = create_vector_store_tool(create_vector_store())
        retrieve_node = ToolNode([retriever_tool])
        workflow.add_node("retrieve", retrieve_node)
        workflow.add_node("rewrite", self.rewrite)
        # Generating a response after we know the documents are relevant
        # Call agent node to decide to retrieve or not
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
        logger.debug(f"Database pool stats: {pool.get_stats()}")

        self.workflow = workflow.compile()

        print("Workflow setup completed..............")


    def start_new_session(self):
        self.thread_id = uuid.uuid4().hex
        self.new_conversation = False
        logger.info(f"Started new session with thread_id: {self.thread_id}")

    def run(self, user_message: str) -> ChatBot:
        self.user_message = user_message
        if self.new_conversation:
            self.start_new_session()
        config = {"configurable": {"thread_id": self.thread_id}}
        #self.workflow.get_state(config)

        logger.info(f"Running workflow for message: {user_message}")
        response_state = self.workflow.invoke(
            {"messages": [HumanMessage(content=self.user_message)]}, config
        )

        logger.debug(f"Workflow response state: {response_state}")

        last_message = response_state["messages"][-1].content if response_state["messages"] else ""
        response = ChatBot(self.user_message, last_message, self.thread_id)

        return response
    def grade_documents(self, state) -> Literal["generate", "rewrite"]:
        """
        Determines whether the retrieved documents are relevant to the question.

        Args:
            state (dict): The current state containing messages.

        Returns:
            str: A decision for whether to 'generate' or 'rewrite'.
        """
        logger.info("Starting document grading process.")

        # Data model
        class Grade(BaseModel):
            """Binary score for relevance check."""
            binary_score: str = Field(description="Relevance score 'yes' or 'no'.")

        try:
            # Initialize LLM
            model = AzureChatOpenAI(temperature=0, model="gpt-4-0125-preview", streaming=True)
            llm_with_tool = model.with_structured_output(Grade)

            # Prompt
            prompt = PromptTemplate(
                template=(
                    "You are a grader assessing relevance of a retrieved document to a user question.\n"
                    "Here is the retrieved document:\n\n{context}\n\n"
                    "Here is the user question: {question}\n"
                    "If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant.\n"
                    "Give a binary 'yes' or 'no' score to indicate whether the document is relevant to the question."
                ),
                input_variables=["context", "question"],
            )

            # Chain
            chain = prompt | llm_with_tool

            messages = state.get("messages", [])
            if not messages:
                logger.error("No messages found in state.")
                return "rewrite"

            last_message = messages[-1]
            question = messages[0].content
            docs = last_message.content

            logger.debug(f"Question: {question}")
            logger.debug(f"Document: {docs}")

            # Run the chain
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

    def agent(self, state):
        """
        Invokes the agent model to generate a response based on the current state.
        Given the question, it will decide to retrieve using the retriever tool, or simply end.

        Args:
            state (dict): The current state containing messages.

        Returns:
            dict: The updated state with the agent response appended to messages.
        """
        logger.info("--------Invoking agent.")
        try:
            messages = state["messages"]
            print(messages)
            if not messages:
                logger.error("No messages found in state.")
                return {"messages": []}

            response = self.model_tool.invoke(messages)
            logger.info("Agent invoked successfully.")

            print(response.pretty_print())
            print("----------------------------------------------------------------")

            return {"messages": [response]}

        except Exception as e:
            logger.error(f"An error occurred in agent: {e}")
            return {"messages": []}

    def rewrite(self, state):
        """
        Transform the query to produce a better question.

        Args:
            state (dict): The current state containing messages.

        Returns:
            dict: The updated state with the rephrased question.
        """
        logger.info("Starting query rewrite process.")

        try:
            messages = state.get("messages", [])
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

            # Initialize LLM
            model = AzureChatOpenAI(temperature=0, model="gpt-4-0125-preview", streaming=True)
            response = model.invoke(msg)
            logger.info("Query rewritten successfully.")

            return {"messages": [response]}

        except Exception as e:
            logger.error(f"An error occurred during query rewrite: {e}")
            return {"messages": []}

    def generate(self, state):
        """
        Generate an answer based on the context and question.

        Args:
            state (dict): The current state containing messages.

        Returns:
            dict: The updated state with the generated response.
        """
        logger.info("Starting answer generation process.")

        try:
            messages = state.get("messages", [])
            if not messages:
                logger.error("No messages found in state.")
                return {"messages": []}

            question = messages[0].content
            last_message = messages[-1]
            docs = last_message.content

            # Pull prompt from hub
            prompt = hub.pull("rlm/rag-prompt")
            print(prompt.pretty_print())
            logger.debug("Prompt pulled from hub.")

            # Initialize LLM
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, streaming=True)

            # Chain
            rag_chain = prompt | llm | StrOutputParser()

            # Run the chain
            response = rag_chain.invoke({"context": docs, "question": question})
            logger.info("Answer generated successfully.")

            return {"messages": [response]}

        except Exception as e:
            logger.error(f"An error occurred during answer generation: {e}")
            return {"messages": []}

if __name__ == "__main__":
    print("Testing RAGAIAssistant...")
    rag_assistant = RAGAIAssistant(thread_id="test_thread_id", new_conversation=True)   
    response = rag_assistant.run("Are there any cloud formations specific to oceans and large bodies of water?")
    print(response.get_response())
    # response = rag_assistant.run("What is the mission of NASA")
    # print(response.get_response())