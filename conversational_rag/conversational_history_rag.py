# conversational_rag_assistant.py

import os

# Set Azure Search field mapping (if required)
os.environ["AZURESEARCH_FIELDS_ID"] = "chunk_id"
os.environ["AZURESEARCH_FIELDS_CONTENT"] = "chunk"
os.environ["AZURESEARCH_FIELDS_CONTENT_VECTOR"] = "text_vector"

import logging
from langchain_community.chat_models import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

class ConversationalRAGAssistant:
    def __init__(self):
        # Set up logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

        # Load environment variables
        self.logger.info("Loading environment variables...")
        self.azure_openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        self.azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.azure_openai_embedding_deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        self.azure_search_endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
        self.azure_search_key = os.environ.get("AZURE_SEARCH_KEY")
        self.azure_search_index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME")

        # Check that all necessary environment variables are set
        required_env_vars = [
            "azure_openai_api_key", "azure_openai_endpoint", "azure_openai_deployment_name",
            "azure_openai_embedding_deployment", "azure_search_endpoint", "azure_search_key",
            "azure_search_index_name"
        ]
        missing_vars = [var for var in required_env_vars if not getattr(self, var)]
        if missing_vars:
            self.logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        else:
            self.logger.info("All required environment variables are set.")

        # Initialize components
        self._initialize_embeddings()
        self._create_vector_store()
        self._initialize_retriever()
        self._initialize_memory()
        self._initialize_llm()
        self._define_prompt()
        self._create_chain()

    def _initialize_embeddings(self):
        self.logger.info("Initializing Azure OpenAI Embeddings...")
        self.embeddings = AzureOpenAIEmbeddings(
            deployment=self.azure_openai_embedding_deployment,
            openai_api_key=self.azure_openai_api_key,
            openai_api_type='azure',
            openai_api_version='2023-05-15'
        )
        self.logger.info("Embeddings initialized.")

    def _create_vector_store(self):
        self.logger.info("Creating Azure Cognitive Search vector store...")
        self.vector_store = AzureSearch(
            azure_search_endpoint=self.azure_search_endpoint,
            azure_search_key=self.azure_search_key,
            index_name=self.azure_search_index_name,
            embedding_function=self.embeddings.embed_query,
        )
        self.logger.info("Vector store created.")

    def _initialize_retriever(self):
        self.logger.info("Initializing retriever...")
        self.retriever = self.vector_store.as_retriever()
        self.logger.info("Retriever initialized.")

    def _initialize_memory(self):
        self.logger.info("Initializing conversation memory...")
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.logger.info("Conversation memory initialized.")

    def _initialize_llm(self):
        self.logger.info("Initializing Azure Chat OpenAI model...")
        self.llm = AzureChatOpenAI(
            azure_endpoint=self.azure_openai_endpoint,
            openai_api_key=self.azure_openai_api_key,
            deployment_name=self.azure_openai_deployment_name,
            openai_api_version='2023-03-15-preview',
            openai_api_type='azure',
            temperature=0.7
        )
        self.logger.info("Chat model initialized.")

    def _define_prompt(self):
        self.logger.info("Defining custom prompt template...")
        self.prompt_template = PromptTemplate(
            input_variables=["chat_history", "question", "context"],
            template="""
You are an AI assistant that provides helpful answers to the user's questions based on the provided context.

Context:
{context}

Chat History:
{chat_history}

Question:
{question}

Provide a detailed and informative answer considering the conversation history and the provided context. If the question is not relevant to the context, then simply return "I don't know".
Answer:
""".strip()
        )
        self.logger.info("Custom prompt template defined.")

    def _create_chain(self):
        self.logger.info("Creating Conversational Retrieval Chain...")
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={'prompt': self.prompt_template},
            return_source_documents=False
        )
        self.logger.info("Conversational Retrieval Chain created.")

    def ask_question(self, question):
        self.logger.info(f"Received question: {question}")
        result = self.qa_chain({"question": question})
        answer = result["answer"]
        self.logger.info(f"Assistant's answer: {answer}")
        return answer

    def start_conversation(self):
        self.logger.info("Starting conversation loop.")
        print("Welcome to the Conversational RAG assistant. Type 'exit' to quit.")
        while True:
            question = input("You: ")
            if question.lower() in ["exit", "quit"]:
                self.logger.info("Exiting the conversation.")
                print("Goodbye!")
                break
            answer = self.ask_question(question)
            print(f"Assistant: {answer}")

# Example usage:
if __name__ == "__main__":
    assistant = ConversationalRAGAssistant()
    assistant.start_conversation()