# custom_retriever.py

import os
import logging
from typing import List, Optional

import openai
from dotenv import load_dotenv
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.schema import Document
from langchain.retrievers import BaseRetriever
from langchain.tools import BaseTool
from langchain.vectorstores import AzureSearch
from langchain.embeddings import OpenAIEmbeddings
from langchain.tools import Tool
from pydantic import BaseModel

# Load environment variables
load_dotenv()
openai.api_type = "openai"
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CustomRetriever(BaseRetriever):
    """
    Custom retriever that retrieves documents from Azure Cognitive Search.
    """
    vector_store: AzureSearch
    k: int = 3  # Number of top results to return

    def _get_relevant_documents(
            self, query: str, *, run_manager: Optional[CallbackManagerForRetrieverRun] = None
    ) -> List[Document]:
        """
        Retrieves relevant documents from the vector store based on the query.

        Args:
            query (str): The search query.
            run_manager (Optional[CallbackManagerForRetrieverRun]): Callback manager for logging.

        Returns:
            List[Document]: A list of relevant documents.
        """
        try:
            logger.info(f"Retrieving documents for query: {query}")
            results = self.vector_store.similarity_search(query=query, k=self.k)
            logger.info(f"Retrieved {len(results)} documents.")
            return results
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []


def get_basic_tool() -> BaseTool:
    """
    Initializes the retriever tool using Azure Cognitive Search and OpenAI embeddings.

    Returns:
        BaseTool: An instance of the retriever tool.
    """
    try:
        # Variables
        index_name: str = os.getenv('SEARCH_INDEX_NAME')
        model: str = "text-embedding-ada-002"
        embedding_deployment: str = os.getenv('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME')

        # Ensure required environment variables are set
        if not index_name or not embedding_deployment:
            raise ValueError("Environment variables for index name or embedding deployment are not set.")

        # Initialize embeddings
        embeddings = OpenAIEmbeddings(
            deployment=embedding_deployment,
            chunk_size=1
        )

        # Initialize vector store
        vector_store = AzureCognitiveSearch(
            azure_search_endpoint=os.getenv('AZURE_SEARCH_ENDPOINT'),
            azure_search_key=os.getenv('AZURE_SEARCH_KEY'),
            index_name=index_name,
            embedding_function=embeddings.embed_query,
        )

        # Initialize custom retriever
        retriever = CustomRetriever(vector_store=vector_store, k=3)

        # Define the tool function
        def retrieve_documents(query: str) -> str:
            docs = retriever.get_relevant_documents(query)
            return "\n\n".join([doc.page_content for doc in docs])

        # Create the retriever tool
        tool = Tool(
            name="Document_Retriever",
            func=retrieve_documents,
            description="Use this tool to retrieve documents relevant to the user's query."
        )

        logger.info("Retriever tool initialized successfully.")
        return tool

    except Exception as e:
        logger.error(f"Error initializing the retriever tool: {e}")
        raise


# Example usage
if __name__ == "__main__":
    try:
        tool = get_basic_tool()
        query = "Your search query here"
        result = tool.run(query)
        print(f"Retrieved Documents:\n{result}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")