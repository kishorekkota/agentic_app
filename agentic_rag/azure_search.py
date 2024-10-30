# azure_search.py

import os
import logging
from langchain.vectorstores import AzureSearch
from langchain.embeddings import OpenAIEmbeddings
from langchain.tools import create_retriever_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_vector_store() -> AzureSearch:
    """
    Creates and returns an AzureSearch vector store instance.

    Returns:
        AzureSearch: An instance of the AzureSearch vector store.

    Raises:
        ValueError: If required environment variables are missing.
    """
    # Retrieve environment variables
    azure_search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    azure_search_key = os.getenv('AZURE_SEARCH_KEY')
    search_index_name = os.getenv('SEARCH_INDEX_NAME')
    embedding_model_name = os.getenv('EMBEDDING_MODEL_NAME', 'text-embedding-ada-002')

    if not azure_search_endpoint or not azure_search_key or not search_index_name:
        logger.error("Missing Azure Search configuration environment variables.")
        raise ValueError("Missing Azure Search configuration environment variables.")

    try:
        # Initialize embeddings
        embeddings = OpenAIEmbeddings(model=embedding_model_name)

        # Create the vector store
        vector_store = AzureSearch(
            azure_search_endpoint=azure_search_endpoint,
            azure_search_key=azure_search_key,
            index_name=search_index_name,
            embedding_function=embeddings.embed_query,
        )

        logger.info("AzureSearch vector store created successfully.")
        return vector_store

    except Exception as e:
        logger.error(f"An error occurred while creating the vector store: {e}")
        raise

def create_vector_store_tool(vector_store: AzureSearch):
    """
    Creates and returns a retriever tool from the provided vector store.

    Args:
        vector_store (AzureSearch): The vector store instance.

    Returns:
        Tool: A retriever tool instance.
    """
    try:
        retriever = vector_store.as_retriever()
        retriever_tool = create_retriever_tool(
            retriever,
            name="retrieval_tool",
            description="Search HR Knowledge base and provide information related to the query.",
        )
        logger.info("Retriever tool created successfully.")
        return retriever_tool

    except Exception as e:
        logger.error(f"An error occurred while creating the retriever tool: {e}")
        raise

# Example usage
if __name__ == "__main__":
    try:
        vector_store = create_vector_store()
        retriever_tool = create_vector_store_tool(vector_store)

        # Now you can use retriever_tool in your application
        # For example:
        # query = "What is Tesla's revenue forecast for next year?"
        # result = retriever_tool.run(query)
        # print(result)

    except Exception as e:
        logger.error(f"An error occurred in the main execution: {e}")