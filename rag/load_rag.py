from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter,RecursiveCharacterTextSplitter
from langchain_core.document_loaders import BlobLoader
from langchain_community.document_loaders import PyPDFLoader,DirectoryLoader
from langchain_core.documents import Document
import chromadb
import os
import uuid

def load_documents(directory: str, glob_pattern: str = "*.pdf"):
    """Load documents from a directory using the specified glob pattern."""
    print("Loading documents...")
    loader = DirectoryLoader(directory, glob=glob_pattern, use_multithreading=True, loader_cls=PyPDFLoader)

    documents = loader.load()

    print(f"# of documents loaded = {len(documents)}")

    # loader = BlobLoader(directory, glob=glob_pattern, use_multithreading=True)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    out_documents = []

    out_documents = text_splitter.split_documents(documents)
    
    print(f"# of documents after split = {len(out_documents)}")

    return out_documents

def embed_documents(docs):
    """Embed documents using OpenAI embeddings."""
    print("Embedding documents...")

    api_key = os.environ.get("OPENAI_API_KEY")

    print("Using OpenAI API key:", api_key)

    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    embed_documents = []
    for doc in docs:
        print("Embedding document:", doc.metadata)
        embed_documents.append(embeddings.embed_documents(doc.page_content))
    
    print("Documents embedded.")

    return embed_documents

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

def add_documents_to_collection(collection, embedding_docs,docs):
    """Add documents to the specified ChromaDB collection."""
    print("Adding documents to collection...")
    print("Number of documents:", str(docs[0]))
   
    
    count = 0
    #ids = [str(uuid.uuid4()) for _ in range(len(embedding_docs[count]))]
    for doc in docs:
        print("Adding document:", doc.metadata)
       
        ids = [str(uuid.uuid4()) for _ in range(len(embedding_docs[count]))]
        print("IDs:", len(ids))
        collection.add(documents=doc.page_content, embeddings=embedding_docs[count],ids=ids)
        count += 1
    

def main():
    try:
        directory = 'data'
        collection_name = 'stripe_collection'

        docs = load_documents(directory)

        print("documents loaded:", len(docs))

        # Embed documents using OpenAI embeddings

        chroma_client = create_chroma_client()
        pdf_collection = get_or_create_collection(chroma_client, collection_name)


        embedded_docs = embed_documents(docs)
        #print("embedded docs:", len(embedded_docs))
        add_documents_to_collection(pdf_collection, embedded_docs,docs)
    except Exception as e:
        print(f"Error: {e}")
    
    

if __name__ == "__main__":
    main()