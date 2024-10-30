from langchain_community.retrievers import AzureAISearchRetriever
from langchain.tools.retriever import create_retriever_tool

retriever = AzureAISearchRetriever(
    content_key="<Content Key>", top_k=1, index_name="<Define Index Name>"
)


retriever_tool = create_retriever_tool(
    retriever,
    "retrieve_blog_posts",
    "Search and return information about Lilian Weng blog posts on LLM agents, prompt engineering, and adversarial attacks on LLMs.",
)
