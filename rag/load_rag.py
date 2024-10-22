import os
import uuid
import logging
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_core.documents import Document
import chromadb

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_documents(directory: str, glob_pattern: str = "*.pdf"):
    """Load documents from a directory using the specified glob pattern."""
    logger.info("Loading documents from directory: %s", directory)
    loader = DirectoryLoader(directory, glob=glob_pattern, use_multithreading=True, loader_cls=PyPDFLoader)
    documents = loader.load()
    logger.debug("# of documents loaded = %d", len(documents))

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    logger.debug("# of documents after split = %d", len(chunks))

    return chunks

def embed_documents(chunks_with_ids: list[Document]):
    """Embed documents using OpenAI embeddings."""
    logger.info("Embedding documents...")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set.")
        raise ValueError("OPENAI_API_KEY environment variable not set.")
    logger.debug("Using OpenAI API key: %s", api_key)

    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    embedded_docs = []
    for chunk in chunks_with_ids:
        logger.debug("Embedding document: %s", chunk.metadata)
        embedded_docs.append(embeddings.embed_documents(chunk.page_content))
        logger.debug("Embedding size: %d", len(embedded_docs[-1]))

    logger.info("Documents embedded.")
    return embedded_docs

def create_chroma_client(host: str = 'localhost', port: int = 8000):
    """Create a ChromaDB client."""
    logger.info("Creating ChromaDB client...")
    return chromadb.HttpClient(host=host, port=port)

def get_or_create_collection(client, collection_name: str):
    """Get or create a ChromaDB collection."""
    logger.info("Creating collection: %s", collection_name)
    try:
        collection = client.get_collection(name=collection_name)
    except Exception as e:
        logger.info("Error getting collection: %s", str(e))
        collection = None
    logger.info("Collection: %s", collection)
    if collection is None:
        logger.info("Collection not found. Creating new collection...")
        collection = client.create_collection(name=collection_name)
    return collection

def add_documents_to_collection(collection, docs):
    """Add documents to the specified ChromaDB collection."""
    logger.info("Adding documents to collection...")
    logger.debug("Number of documents: %d", len(docs))
    ids = [str(uuid.uuid4()) for _ in range(len(docs))]
    docs_content = [doc.page_content for doc in docs]
    docs_metadata = [doc.metadata for doc in docs]
    collection.add(documents=docs_content, metadatas=docs_metadata, ids=ids)
    logger.info("Documents added to collection.")

def calculate_chunk_ids(chunks):
    """Calculate unique IDs for document chunks."""
    logger.info("Calculating chunk IDs...")
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id
        chunk.metadata["id"] = chunk_id

    logger.debug("Chunk IDs calculated.")
    return chunks

def main():
    try:
        directory = 'data'
        collection_name = 'stripe_collection'

        chunks = load_documents(directory)
        chunks_with_ids = calculate_chunk_ids(chunks)
        logger.info("Documents loaded: %d", len(chunks))

        chroma_client = create_chroma_client()
        pdf_collection = get_or_create_collection(chroma_client, collection_name)
        add_documents_to_collection(pdf_collection, chunks_with_ids)
        logger.info("Documents embedded and added to ChromaDB collection.")
    except Exception as e:
        logger.error("Error: %s", e)

if __name__ == "__main__":
    main()