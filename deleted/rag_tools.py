from langchain.tools.retriever import create_retriever_tool
import chromadb
import logging
from langchain_community.vectorstores import Chroma
from load_rag import load_documents, embed_documents    
from langchain_openai import OpenAIEmbeddings


logger = logging.getLogger(__name__)

chunks = load_documents("data")

vectorstore = Chroma.from_documents(
    documents=chunks,
    collection_name="stripe_collection",
    embedding=OpenAIEmbeddings()
)

retriever = vectorstore.as_retriever()

retriever_tool = create_retriever_tool(
    retriever,
   "stripe_collection_procedures_retriever",
    "Search and return information about Stripe procedures and provide relevant responses.")


