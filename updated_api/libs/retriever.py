import os
from api.environment_variables import EnvironmentVariables
from langchain.docstore.document import Document
from langchain_core.retrievers import BaseRetriever
from langchain.retrievers import EnsembleRetriever
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from libs.embedder import EmbeddingModel
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.core.credentials import AzureKeyCredential
from typing import ClassVar
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
env = EnvironmentVariables.get_instance()

azure_search_endpoint = env.azure_search_endpoint
print("azure_search_endpoint",azure_search_endpoint)
internal_guidelines_index_name = env.internal_guidelines_index_name
print("internal_guidelines_index_name",internal_guidelines_index_name)
external_regulations_index_name = env.external_regulations_index_name
print("external_regulations_index_name",external_regulations_index_name)

azure_hrcopilot_search_api_key = env.azure_hrcopilot_search_api_key

azure_hrcopilot_search_credential = AzureKeyCredential(azure_hrcopilot_search_api_key)

class InternalGuidelinesRetriever(BaseRetriever):
    nr_top_docs: int
    search_client: ClassVar = None
    search_client = SearchClient(endpoint=azure_search_endpoint, index_name=internal_guidelines_index_name, credential=azure_hrcopilot_search_credential)

    def search_query(self, query):
        logger.debug("Performing search query for internal guidelines")
        embedder = EmbeddingModel(type='openai')
        v = VectorizedQuery(vector=embedder.generate_embeddings(query), k_nearest_neighbors=3, fields="title_vector,content_vector")
        search_results = self.search_client.search(
            search_text=query,
            search_fields=["title", "content"],
            vector_queries=[v],
            select=["document_id", "title", "content", "reference_link", "main_topics"],
            query_type="semantic",
            semantic_configuration_name="curated-semantic-config",
            query_caption="extractive",
            query_answer="extractive",
            top=self.nr_top_docs
        )
        logger.debug("Search results retrieved: %s", search_results)
        return search_results

    def create_content_list(self, search_results):
        logger.debug("Creating content list from search results")
        content_list = []
        for result in search_results:
            d = Document(page_content=result['content'])
            d.metadata = {
                'document_id': result['document_id'],
                'reference_link': result['reference_link'],
                'title': result['main_topics'],
            }
            content_list.append(d)
        logger.debug("Content list created: %s", content_list)
        return content_list

    def _get_relevant_documents(self, query):
        logger.debug("Getting relevant documents for query: %s", query)
        search_results = self.search_query(query)
        initial_list = self.create_content_list(search_results)
        logger.debug("Relevant documents retrieved: %s", initial_list)
        return initial_list

class ExternalRegulationsRetriever(BaseRetriever):
    nr_top_docs: int
    search_client: ClassVar = None
    search_client = SearchClient(endpoint=azure_search_endpoint, index_name=external_regulations_index_name, credential=azure_hrcopilot_search_credential)

    def search_query(self, query):
        logger.debug("Performing search query for external regulations")
        embedder = EmbeddingModel(type='openai')
        v = VectorizedQuery(vector=embedder.generate_embeddings(query), k_nearest_neighbors=3, fields="title_vector,content_vector")
        search_results = self.search_client.search(
            search_text=query,
            search_fields=["title", "content"],
            vector_queries=[v],
            select=["document_id", "title", "content", "reference_link"],
            query_type="semantic",
            semantic_configuration_name="regulation-semantic-config",
            query_caption="extractive",
            query_answer="extractive",
            top=self.nr_top_docs
        )
        logger.debug("Search results retrieved: %s", search_results)
        return search_results

    def create_content_list(self, search_results):
        logger.debug("Creating content list from search results")
        content_list = []
        for result in search_results:
            d = Document(page_content=result['content'])
            d.metadata = {
                'document_id': result['document_id'],
                'reference_link': result['reference_link'],
                'title': result['title'],
            }
            content_list.append(d)
        logger.debug("Content list created: %s", content_list)
        return content_list

    def _get_relevant_documents(self, query):
        logger.debug("Getting relevant documents for query: %s", query)
        search_results = self.search_query(query)
        initial_list = self.create_content_list(search_results)
        logger.debug("Relevant documents retrieved: %s", initial_list)
        return initial_list

class CustomRetriever():
    def __init__(self, nr_top_docs, retrieval_type='all', weights=[0.5, 0.5], filter_state=None, filter_industry=None):
        self.retrieval_type = retrieval_type
        self.nr_top_docs = nr_top_docs
        self.filter_state = filter_state
        self.filter_industry = filter_industry

        logger.debug("Initializing CustomRetriever with type: %s", retrieval_type)
        if retrieval_type == 'internal':
            self.retriever = InternalGuidelinesRetriever(nr_top_docs=nr_top_docs)
        elif retrieval_type == 'external':
            self.retriever = ExternalRegulationsRetriever(nr_top_docs=nr_top_docs)
        elif retrieval_type == "all":
            self.retriever = EnsembleRetriever(retrievers=[InternalGuidelinesRetriever(nr_top_docs=nr_top_docs), ExternalRegulationsRetriever(nr_top_docs=nr_top_docs)], weights=weights)
        else:
            logger.error("Invalid retrieval type specified: %s", retrieval_type)
            raise ValueError('Please specify the correct type of search (internal, external, all)')

    def get_retriever(self):
        logger.debug("Getting retriever of type: %s", self.retrieval_type)
        return self.retriever