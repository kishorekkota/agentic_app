# nodes.py

import logging
from typing import Literal
from typing_extensions import Annotated
from pydantic import BaseModel, Field

from langchain import hub
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureOpenAI as ChatOpenAI

from langgraph.prebuilt import tools_condition

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

### Edges

def grade_documents(state) -> Literal["generate", "rewrite"]:
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
        model = ChatOpenAI(temperature=0, model="gpt-4-0125-preview", streaming=True)
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

### Nodes

def agent(state):
    """
    Invokes the agent model to generate a response based on the current state.
    Given the question, it will decide to retrieve using the retriever tool, or simply end.

    Args:
        state (dict): The current state containing messages.

    Returns:
        dict: The updated state with the agent response appended to messages.
    """
    logger.info("Invoking agent.")
    try:
        messages = state.get("messages", [])
        if not messages:
            logger.error("No messages found in state.")
            return {"messages": []}

        model = ChatOpenAI(temperature=0, streaming=True, model="gpt-4-turbo")
        model = model.bind_tools(tools_condition)  # Assuming 'tools_condition' is defined elsewhere.

        response = model.invoke(messages)
        logger.info("Agent invoked successfully.")

        return {"messages": [response]}

    except Exception as e:
        logger.error(f"An error occurred in agent: {e}")
        return {"messages": []}

def rewrite(state):
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
        model = ChatOpenAI(temperature=0, model="gpt-4-0125-preview", streaming=True)
        response = model.invoke(msg)
        logger.info("Query rewritten successfully.")

        return {"messages": [response]}

    except Exception as e:
        logger.error(f"An error occurred during query rewrite: {e}")
        return {"messages": []}

def generate(state):
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

# If needed, print the prompt for debugging
if __name__ == "__main__":
    logger.info("Displaying the RAG prompt.")
    prompt = hub.pull("rlm/rag-prompt")
    print("*" * 20 + "Prompt [rlm/rag-prompt]" + "*" * 20)
    print(prompt.pretty_print())