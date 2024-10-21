import os
import uuid
import logging
from pprint import pprint
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_core.documents import Document
import chromadb

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChromaRAG:
    def __init__(self, host: str = 'localhost', port: int = 8000, collection_name: str = 'stripe_collection'):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.client = self.create_chroma_client()
        self.collection = self.get_or_create_collection()

    def create_chroma_client(self):
        """Create a ChromaDB client."""
        logger.info("Creating ChromaDB client...")
        return chromadb.HttpClient(host=self.host, port=self.port)

    def get_or_create_collection(self):
        """Get or create a ChromaDB collection."""
        logger.info("Getting or creating collection: %s", self.collection_name)
        collection = self.client.get_collection(self.collection_name)
        if collection is None:
            collection = self.client.create_collection(self.collection_name)
        return collection

    def query_collection(self, query_texts, n_results=2):
        """Query the ChromaDB collection."""
        logger.info("Querying collection with texts: %s", query_texts)
        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results
        )
        logger.debug("Query results: %s", results)
        return results

def main():
    chroma_rag = ChromaRAG()
    query_texts = ["How to generate email using Stripe ?"]
    
    results = chroma_rag.query_collection(query_texts)

    pprint(results)
    

if __name__ == "__main__":
    main()