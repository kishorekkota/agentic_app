# azure_search.py

import os
import logging

os.environ["AZURESEARCH_FIELDS_ID"] = "chunk_id"
os.environ["AZURESEARCH_FIELDS_CONTENT"] = "chunk"
os.environ["AZURESEARCH_FIELDS_CONTENT_VECTOR"] = "text_vector"

from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from azure.identity import DefaultAzureCredential
from langchain_core.tools import tool
from azure.search.documents.indexes.models import SimpleField

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_vector_store() -> AzureSearch:
    """
    Creates and returns an AzureCognitiveSearch vector store instance.

    Returns:
        AzureCognitiveSearch: An instance of the AzureCognitiveSearch vector store.

    Raises:
        ValueError: If required environment variables are missing.
    """
    logger.info("Creating AzureCognitiveSearch vector store...")
    
    # Retrieve environment variables for Azure Search
    azure_search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    azure_search_key = os.getenv('AZURE_SEARCH_KEY')
    search_index_name = os.getenv('SEARCH_INDEX_NAME')
    
    # Retrieve environment variables for Azure OpenAI Embeddings
    azure_openai_api_key = os.getenv('AZURE_OPENAI_API_KEY')
    azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    azure_openai_embedding_deployment = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT','text-embedding-3-large')
    azure_openai_api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2023-05-15')
    embedding_model_name = os.getenv('EMBEDDING_MODEL_NAME', 'text-embedding-3-large')


    print(azure_openai_api_version, azure_openai_api_key, azure_openai_endpoint, azure_openai_embedding_deployment)

    if not all([azure_search_endpoint, azure_search_key, search_index_name,
                azure_openai_api_key, azure_openai_endpoint, azure_openai_embedding_deployment]):
        logger.error("Missing Azure configuration environment variables.")
        raise ValueError("Missing Azure configuration environment variables.")

    try:

        embeddings = AzureOpenAIEmbeddings(model=embedding_model_name,azure_deployment="text-embedding-3-large")

        # Create the vector store
        vector_store = AzureSearch(
            azure_search_endpoint=azure_search_endpoint,
            azure_search_key=azure_search_key,
            index_name=search_index_name,
            embedding_function=embeddings.embed_query,
        )

        logger.info("AzureCognitiveSearch vector store created successfully.")
        return vector_store

    except Exception as e:
        logger.error(f"An error occurred while creating the vector store: {e}")
        raise

def create_vector_store_tool(vector_store: AzureSearch):
    """
    Creates and returns a retriever tool from the provided vector store.

    Args:
        vector_store (AzureCognitiveSearch): The vector store instance.

    Returns:
        Tool: A retriever tool instance.
    """
    logger.info("Creating retriever tool...")
    try:

        retriever_ = vector_store.as_retriever()


        retrieve_policy_document = create_retriever_tool(
        retriever=retriever_,
        name="retriever",
        description="Search and Return  tool for HR Related questions and Leave Policy in NewYork.",
        
        )
        logger.info("Retriever tool created successfully.")
        return retrieve_policy_document

    except Exception as e:
        logger.error(f"An error occurred while creating the retriever tool: {e}")
        raise

def test_retriever_tool():
    """
    Tests the retriever tool created from the vector store.
    """
    logger.info("Testing the retriever tool...")
    try:

        vector_store = create_vector_store() 
        # Create the retriever tool
        retriever_tool = create_vector_store_tool(vector_store)

        # Define a test query
        test_query = "What is the company's leave policy?"

        logger.info(f"Running test query using the retriever tool: {test_query}")

        # Use the retriever tool to retrieve relevant documents
        results = retriever_tool.run(test_query)

        # Print the results
        print("Retriever Tool Results:")
        print(results)

    except Exception as e:
        logger.error(f"An error occurred during the retriever tool test: {e}")

if __name__ == "__main__":
    logger.info("Starting test execution for azure_search.py...")
    test_retriever_tool()