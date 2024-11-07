# conv_rag_history_assistant.py
import os

os.environ["AZURESEARCH_FIELDS_ID"] = "chunk_id"
os.environ["AZURESEARCH_FIELDS_CONTENT"] = "chunk"
os.environ["AZURESEARCH_FIELDS_CONTENT_VECTOR"] = "text_vector"

import logging
from typing import Sequence, TypedDict, Annotated
from typing_extensions import Annotated

from langchain.chains import (
    create_history_aware_retriever,
    create_retrieval_chain,
)
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import AzureChatOpenAI
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from environment_variables import EnvironmentVariables

from db_connection import pool

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

env_vars = EnvironmentVariables()

# Define the state schema
class State(TypedDict):
    input: str
    chat_history: Annotated[Sequence[BaseMessage], add_messages]
    context: str
    answer: str

# InputModel class for user interaction
class InputModel:
    def __init__(self, user_input: str, chat_history: Sequence[BaseMessage] = None):
        self.input = user_input
        self.chat_history = chat_history if chat_history is not None else []
        self.context = ""
        self.answer = ""

    def to_state(self) -> State:
        return {
            "input": self.input,
            "chat_history": self.chat_history,
            "context": self.context,
            "answer": self.answer,
        }

# Conversational RAG Assistant Class
class ConversationalRAGAssistant:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing Conversational RAG Assistant...")
        self.llm = self.initialize_llm()
        self.embeddings = self.initialize_embeddings()
        self.vector_store = self.create_vector_store(self.embeddings)
        self.retriever = self.create_retriever(self.vector_store)
        self.history_aware_retriever = self.create_history_aware_retriever_chain(self.llm, self.retriever)
        self.question_answer_chain = self.create_question_answer_chain(self.llm)
        self.rag_chain = self.build_rag_chain(self.history_aware_retriever, self.question_answer_chain)
        self.workflow = self.build_workflow()
        self.app = self.workflow.compile(checkpointer=PostgresSaver(pool))
        self.chat_history = []
        self.logger.info("Conversational RAG Assistant initialized.")

    def initialize_llm(self):
        self.logger.info("Initializing LLM...")
        llm = AzureChatOpenAI(
            openai_api_key=env_vars.azure_openai_api_key,
            azure_endpoint=env_vars.azure_openai_endpoint,
            deployment_name=env_vars.azure_openai_deployment_name,
            openai_api_type='azure',
            openai_api_version='2023-03-15-preview',
            temperature=0.7
        )
        return llm

    def initialize_embeddings(self):
        self.logger.info("Initializing embeddings...")
        embeddings = AzureOpenAIEmbeddings(
            deployment=env_vars.azure_openai_embedding_deployment,
            openai_api_key=env_vars.azure_openai_api_key,
            openai_api_type='azure',
            openai_api_version='2023-05-15',
        )
        self.logger.info("Embeddings initialized.")
        return embeddings

    def create_vector_store(self, embeddings):
        self.logger.info("Creating vector store...")
        vector_store = AzureSearch(
            azure_search_endpoint=env_vars.azure_search_endpoint,
            azure_search_key=env_vars.azure_search_key,
            index_name=env_vars.azure_search_index_name,
            embedding_function=embeddings.embed_query,
        )
        self.logger.info("Vector store created.")
        return vector_store

    def create_retriever(self, vector_store: AzureSearch):
        self.logger.info("Initializing retriever...")
        retriever = vector_store.as_retriever()
        self.logger.info("Retriever initialized.")
        return retriever

    def create_history_aware_retriever_chain(self, llm, retriever):
        self.logger.info("Creating history-aware retriever chain...")
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )
        return history_aware_retriever

    def create_question_answer_chain(self, llm):
        self.logger.info("Creating question-answer chain...")
        # system_prompt = (
        #     "You are an assistant for question-answering tasks. "
        #     "Use the following pieces of retrieved context to answer "
        #     "the question. If you don't know the answer, say that you "
        #     "don't know. Use three sentences maximum and keep the "
        #     "answer concise.\n\n{context}"
        # )

        system_prompt = """
You are an AI assistant that helps scientists identify locations for future study.
Answer the query cocisely, using bulleted points.
Answer ONLY with the facts listed in the list of sources below.
If there isn't enough information below, say you don't know.
Do not generate answers that don't use the sources below.
Do not exceed 5 bullets.
{context}
{input}
{chat_history}
"""
        
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        return question_answer_chain

    def build_rag_chain(self, history_aware_retriever, question_answer_chain):
        self.logger.info("Building RAG chain...")
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        return rag_chain

    def call_model(self, state: State):
        response = self.rag_chain.invoke(state)
        return {
            "chat_history": state["chat_history"] + [
                HumanMessage(content=state["input"]),
                AIMessage(content=response["answer"]),
            ],
            "context": response["context"],
            "answer": response["answer"],
        }

    def build_workflow(self):
        self.logger.info("Building workflow...")
        workflow = StateGraph(state_schema=State)
        workflow.add_edge(START, "model")
        workflow.add_node("model", self.call_model)
        return workflow

    def ask_question(self, question: str):
        self.logger.info(f"Received question: {question}")
        input_model = InputModel(question, self.chat_history)
        state = input_model.to_state()
        response = self.app(state)
        self.chat_history = response["chat_history"]
        answer = response["answer"]
        self.logger.info(f"Assistant's answer: {answer}")
        return answer

# Example usage:
if __name__ == "__main__":
    assistant = ConversationalRAGAssistant()
    # print("Welcome to the Conversational RAG assistant. Type 'exit' to quit.")
    # while True:
    #     user_input = input("You: ")
    #     if user_input.lower() in ["exit", "quit"]:
    #         print("Goodbye!")
    #         break
    #     answer = assistant.ask_question(user_input)
    #     print(f"Assistant: {answer}")
    try:

        config = {"configurable": {"thread_id": "abc12312"}}

        result = assistant.app.invoke(
            {"input": "How to make pasta ?"},
            config=config,
        )
        print(result["answer"])
    except Exception as e:
        print(f"Error: {e}")