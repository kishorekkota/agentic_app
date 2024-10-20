from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.document_loaders import BlobLoader
from langchain_community.document_loaders import PyPDFLoader,DirectoryLoader
from langchain_core.documents import Document
import chromadb
import os


def load_documents(directory: str, glob_pattern: str = "*.pdf"):
    """Load documents from a directory using the specified glob pattern."""
    print("Loading documents...")
    loader = DirectoryLoader(directory, glob=glob_pattern, use_multithreading=True, loader_cls=PyPDFLoader)
    # loader = BlobLoader(directory, glob=glob_pattern, use_multithreading=True)
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    return loader.load_and_split(text_splitter)

def embed_documents(docs):
    """Embed documents using OpenAI embeddings."""
    print("Embedding documents...")

    api_key = os.environ.get("OPENAI_API_KEY")

    print("Using OpenAI API key:", api_key)

    embeddings = OpenAIEmbeddings(openai_api_key=api_key)

    return embeddings.embed_documents(docs)

def create_chroma_client(host: str = 'localhost', port: int = 8000):
    """Create a ChromaDB client."""
    print("Creating ChromaDB client...")
    return chromadb.HttpClient(host=host, port=port)

def get_or_create_collection(client, collection_name: str):
    """Get or create a ChromaDB collection."""
    print("Creating collection...")
    collection = client.get_collection(collection_name)
    if collection is None:
        collection = client.create_collection(collection_name)
    return collection

def add_documents_to_collection(collection, docs):
    """Add documents to the specified ChromaDB collection."""
    print("Adding documents to collection...")
    collection.add(docs)

def main():
    directory = 'data'
    collection_name = 'stripe_collection'

    docs = load_documents(directory)
    chroma_client = create_chroma_client()
    pdf_collection = get_or_create_collection(chroma_client, collection_name)

    for doc in docs:
        embedded_docs = embed_documents(doc.page_content)
        add_documents_to_collection(pdf_collection, embedded_docs)
    
    
    

if __name__ == "__main__":
    main()