# node_processor.py

import logging
from typing import Literal
from typing_extensions import Annotated
from pydantic import BaseModel, Field

from langchain import hub
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI 
import azure_search
import os
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

vector_store = azure_search.create_vector_store()
retriever_tool = azure_search.create_vector_store_tool(vector_store)

model = AzureChatOpenAI(temperature=0, streaming=True, model="gpt-4-turbo",api_version="2024-08-01-preview",azure_deployment='gpt-35-turbo',azure_endpoint=os.environ.get("AZURE_ENDPOINT"),openai_api_key=os.environ.get("AZURE_API_KEY"))

model_tool = model.bind_tools([retriever_tool])  # Bind the tools to the model

class NodeProcessor:
    """
    Singleton class that encapsulates the nodes functionality, allowing it to be invoked from other classes.
    It provides methods for grading documents, acting as an agent, rewriting queries, and generating answers.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NodeProcessor, cls).__new__(cls)
            # Any initialization code can go here
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Initialization code for the singleton instance
        # vector_store = azure_search.create_vector_store()
        # self.retriever_tool = azure_search.create_vector_store_tool(vector_store)
        # self.tools = [self.retriever_tool]

        print("NodeProcessor initialized.")
        

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

            response = model_tool.invoke(messages)
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

# If needed, you can still include the main block for debugging
if __name__ == "__main__":
    logger.info("Displaying the RAG prompt.")
    prompt = hub.pull("rlm/rag-prompt")
    print("*" * 20 + "Prompt [rlm/rag-prompt]" + "*" * 20)
    print(prompt.pretty_print())