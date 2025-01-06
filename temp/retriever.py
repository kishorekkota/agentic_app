import os
from dotenv import load_dotenv
load_dotenv()
from langchain.docstore.document import Document
from langchain_core.retrievers import BaseRetriever
from langchain.retrievers import EnsembleRetriever
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from libs.embedder import  EmbeddingModel
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.core.credentials import AzureKeyCredential
from typing import ClassVar
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


azure_search_endpoint=os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
internal_guidelines_index_name =os.getenv("INTERNAL_GUIDELINES_INDEX_NAME")
external_regulations_index_name =os.getenv("EXTERNAL_REGULATIONS_INDEX_NAME")
credential = DefaultAzureCredential()
key_vault = os.getenv("AZURE_KEY_VAULT_ENDPOINT")
keyvault_client = SecretClient(vault_url=key_vault, credential=credential)
azure_hrcopilot_search_api_key = keyvault_client.get_secret("AZURE-SEARCH-HRCOPILOT-API-KEY").value
azure_hrcopilot_search_credential = AzureKeyCredential(azure_hrcopilot_search_api_key)



class InternalGuidelinesRetriever(BaseRetriever):
        nr_top_docs: int
        
        search_client: ClassVar = None
        search_client = SearchClient(endpoint=azure_search_endpoint,index_name=internal_guidelines_index_name,credential=azure_hrcopilot_search_credential)
    
        
        
        
        
        def search_query(self,query):
            embedder=EmbeddingModel(type='openai')
          

            v = VectorizedQuery(vector=embedder.generate_embeddings(query),k_nearest_neighbors=3,fields="title_vector,content_vector")
            search_results = self.search_client.search(  
            search_text=query,
            search_fields= ["title","content"],
            vector_queries=[v],
            select=["document_id","title","content","reference_link","main_topics"],
            query_type="semantic",  
            semantic_configuration_name="curated-semantic-config",
            query_caption="extractive",
            query_answer="extractive",
            top=self.nr_top_docs)
            return search_results
        

        
        def create_content_list(self,search_results):
            content_list=[]
            for result in search_results:
                d = Document(page_content=result['content'])
                d.metadata = {
                        'document_id' : result['document_id'],
                        'reference_link' : result['reference_link'],
                        'title' : result['main_topics'],
                    }
                content_list.append(d)
            return content_list
        
        
        
        

        def _get_relevant_documents(self,query):
            search_results =self.search_query(query)
            initial_list=self.create_content_list(search_results)
            
            return initial_list
        

class ExternalRegulationsRetriever(BaseRetriever):
        nr_top_docs: int
        
        search_client: ClassVar = None
        search_client = SearchClient(endpoint=azure_search_endpoint,index_name=external_regulations_index_name,credential=azure_hrcopilot_search_credential)
    
        
        
        
        
        def search_query(self,query):
            embedder=EmbeddingModel(type='openai')
          

            v = VectorizedQuery(vector=embedder.generate_embeddings(query),k_nearest_neighbors=3,fields="title_vector,content_vector")
            search_results = self.search_client.search(  
            search_text=query,
            search_fields= ["title","content"],
            vector_queries=[v],
            select=["document_id","title","content","reference_link"],
            query_type="semantic",  
            semantic_configuration_name="regulation-semantic-config",
            query_caption="extractive",
            query_answer="extractive",
            top=self.nr_top_docs)
            return search_results
        

        
        def create_content_list(self,search_results):
            content_list=[]
            for result in search_results:
                d = Document(page_content=result['content'])
                d.metadata = {
                        'document_id' : result['document_id'],
                        'reference_link' : result['reference_link'],
                        'title' : result['title'],
                    }
                content_list.append(d)
            return content_list
        
        
        
        

        def _get_relevant_documents(self,query):
            search_results =self.search_query(query)
            initial_list=self.create_content_list(search_results)
            
            return initial_list



class CustomRetriever():
    def __init__(self,nr_top_docs,retrieval_type='all',weights=[0.5,0.5],filter_state=None,filter_industry=None):
        self.retrieval_type=retrieval_type
        self.nr_top_docs=nr_top_docs
        self.filter_state=filter_state
        self.filter_industry=filter_industry

        if retrieval_type=='internal':
            self.retriever=InternalGuidelinesRetriever(nr_top_docs=nr_top_docs)
        elif retrieval_type=='external':
            self.retriever=ExternalRegulationsRetriever(nr_top_docs=nr_top_docs)
        elif retrieval_type=="all":
            self.retriever=EnsembleRetriever(retrievers=[InternalGuidelinesRetriever(nr_top_docs=nr_top_docs),ExternalRegulationsRetriever(nr_top_docs=nr_top_docs)],weights=weights)
        else:
             raise ValueError('Please specify the correct type of search(internal,external,all)')

    def get_retriever(self):
        return self.retriever










