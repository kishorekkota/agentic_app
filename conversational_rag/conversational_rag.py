# conversational_rag_system.py

import os

os.environ["AZURESEARCH_FIELDS_ID"] = "chunk_id"
os.environ["AZURESEARCH_FIELDS_CONTENT"] = "chunk"
os.environ["AZURESEARCH_FIELDS_CONTENT_VECTOR"] = "text_vector"

import logging
from langchain_community.chat_models import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Load environment variables
    logger.info("Loading environment variables...")
    azure_openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_embedding_deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

    azure_search_endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
    azure_search_key = os.environ.get("AZURE_SEARCH_KEY")
    azure_search_index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME")

    # Check that all necessary environment variables are set
    required_env_vars = [
        "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT_NAME",
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_KEY",
        "AZURE_SEARCH_INDEX_NAME"
    ]
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return
    else:
        logger.info("All required environment variables are set.")

    # Initialize embeddings
    logger.info("Initializing Azure OpenAI Embeddings...")
    embeddings = AzureOpenAIEmbeddings(
        deployment=azure_openai_embedding_deployment,
        openai_api_key=azure_openai_api_key,
        openai_api_type='azure',
        openai_api_version='2023-05-15'
    )
    logger.info("Embeddings initialized.")

    # Create the vector store
    logger.info("Creating Azure Cognitive Search vector store...")
    vector_store = AzureSearch(
        azure_search_endpoint=azure_search_endpoint,
        azure_search_key=azure_search_key,
        index_name=azure_search_index_name,
        embedding_function=embeddings.embed_query,
    )
    logger.info("Vector store created.")

    # Initialize retriever
    logger.info("Initializing retriever...")
    retriever = vector_store.as_retriever()
    logger.info("Retriever initialized.")

    # Initialize conversation memory
    logger.info("Initializing conversation memory...")
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    logger.info("Conversation memory initialized.")

    # Initialize chat model (LLM)
    logger.info("Initializing Azure Chat OpenAI model...")
    llm = AzureChatOpenAI(
        azure_endpoint=azure_openai_endpoint,
        openai_api_key=azure_openai_api_key,
        deployment_name=azure_openai_deployment_name,
        openai_api_version='2023-03-15-preview',
        openai_api_type='azure',
        temperature=0.7
    )
    logger.info("Chat model initialized.")

    # Create the conversational retrieval chain
    logger.info("Creating Conversational Retrieval Chain...")
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=False
    )
    logger.info("Conversational Retrieval Chain created.")

    # Start conversation loop
    logger.info("Starting conversation loop.")
    print("Welcome to the Conversational RAG assistant. Type 'exit' to quit.")
    while True:
        question = input("You: ")
        if question.lower() in ["exit", "quit"]:
            logger.info("Exiting the conversation.")
            print("Goodbye!")
            break
        logger.info(f"Received question: {question}")

        result = qa_chain({"question": question})
        answer = result["answer"]
        logger.info(f"Assistant's answer: {answer}")
        print(f"Assistant: {answer}")

if __name__ == "__main__":
    main()