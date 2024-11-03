# azure_search.py

import os
import logging
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_search_client() -> SearchClient:
    """
    Creates and returns an Azure Search client instance.

    Returns:
        SearchClient: An instance of the Azure Search client.

    Raises:
        ValueError: If required environment variables are missing.
    """
    print("Creating Azure Search client...")
    # Retrieve environment variables
    azure_search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    azure_search_key = os.getenv('AZURE_SEARCH_KEY')
    search_index_name = os.getenv('SEARCH_INDEX_NAME')

    print(azure_search_endpoint, azure_search_key, search_index_name)

    if not azure_search_endpoint or not azure_search_key or not search_index_name:
        logger.error("Missing Azure Search configuration environment variables.")
        raise ValueError("Missing Azure Search configuration environment variables.")

    try:
        # Create the SearchClient
        search_client = SearchClient(
            endpoint=azure_search_endpoint,
            index_name=search_index_name,
            credential=AzureKeyCredential(azure_search_key),
            api_version="2024-09-01-preview",
            fields=["text_vector"]
        )
        logger.info("Azure Search client created successfully---.")
        return search_client

    except Exception as e:
        logger.error(f"An error occurred while creating the search client: {e}")
        raise

def search_documents(search_client: SearchClient, query: str):
    """
    Searches documents in the Azure Search index.

    Args:
        search_client (SearchClient): The search client instance.
        query (str): The query string to search for.

    Returns:
        list: A list of search results.
    """
    logger.info("--------------------------------")
    logger.info(f"Searching documents for query: {query}")
    try:
        results = search_client.search(query,top=5)

        #print(results)

        # Print the retrieved documents
        for result in results:
            print("parent id")
            print(result.get('parent_id'))
            print("search score")
            print(result.get('@search.score'))
            print("chunk")
            print(result.get('chunk'))
            print("title")
            print(result.get('title'))


    except Exception as e:
        logger.error(f"An error occurred while searching documents: {e}")
        raise

def test_search_documents():
    """
    Tests searching documents in the Azure Search index.
    """
    try:
        # Create the search client
        search_client = create_search_client()

        # Define a test query
        test_query = "NASA"

        # Search for documents
        search_documents(search_client, test_query)

    except Exception as e:
        logger.error(f"An error occurred during the test search: {e}")

if __name__ == "__main__":
    logger.info("Starting test execution for azure_search.py...")
    test_search_documents()
