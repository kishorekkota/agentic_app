# langgraph_agent.py
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.vectorstores import AzureSearch
from langchain.rewriters import Rewriter

import config

class LangGraphAgent:
    def __init__(self):
        self.search_client = SearchClient(
            endpoint=config.AZURE_SEARCH_ENDPOINT,
            index_name=config.AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(config.AZURE_SEARCH_KEY)
        )
        self.llm = OpenAI(api_key=config.OPENAI_API_KEY)
        self.rewriter = Rewriter(llm=self.llm)

    def query_azure_search(self, query):
        results = self.search_client.search(query)
        return [result["content"] for result in results]

    def get_answer(self, query):
        # Rewrite the query
        rewritten_query = self.rewriter.rewrite(query)
        # Retrieve documents
        documents = self.query_azure_search(rewritten_query)
        retriever = AzureSearch(documents)
        # Use RetrievalQA chain
        qa_chain = RetrievalQA(llm=self.llm, retriever=retriever)
        answer = qa_chain.run(query)
        return answer