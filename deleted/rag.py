
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import DirectoryLoader,PyPDFLoader
import chromadb

print("Loading documents...")

#folder_loader = PyPDFLoader('data/customer_email_stripe.pdf')

folder_loader = DirectoryLoader('data', glob="*.pdf", use_multithreading=True, loader_cls=PyPDFLoader)
    
print("Splitting documents...")

docs = folder_loader.load_and_split(CharacterTextSplitter(chunk_size=1000, chunk_overlap=100))

print("Embedding documents...")

embeddings = OpenAIEmbeddings()

print("Creating ChromaDB client...")
chroma_client = chromadb.HttpClient(host='localhost', port=8000)

print("Creating collection...")

if chroma_client.get_collection('stripe_collection') is not None:
    pdf_collection = chroma_client.create_collection('stripe_collection')
else:
    pdf_collection = chroma_client.get_or_create_collection('stripe_collection')

print("Adding documents to collection...")
pdf_collection.add(docs,embeddings)


