import os
import logging
from langchain_community.vectorstores import AzureSearch
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from azure.identity import DefaultAzureCredential
from langchain_core.tools import tool

embeddings: AzureOpenAIEmbeddings = AzureOpenAIEmbeddings(
    api_key=azure_key,
    azure_endpoint=azure_base,
    openai_api_type=azure_api_type,
    deployment="embeddings",
    model="text-embedding-ada-002",
)

vector_store: AzureSearch = AzureSearch(
    azure_search_endpoint=COGNITIVE_SEARCH_API,
    azure_search_key=COGNITIVE_SEARCH_KEY,
    index_name=INDEX_NAME,
    embedding_function=embeddings.embed_query,
    search_type="similarity",
    cors_options="*",
)

azure_search_retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 5, "score_threshold": 0.8},

qa_tool = create_retriever_tool(
            azure_search_retriever,
            "azure_search_tool",
            "Search Azure Vector Database for Documentation. Always use this to look up documentation.",
        )

[
Tool(
                name="azure-vector-search",
                func=qa_tool.run,
                description="Useful for fetching documentation using Vector Search in Azure Cognitive Search.",
            )
]