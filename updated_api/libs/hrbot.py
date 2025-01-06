import pandas as pd
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai import AzureOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import RetrievalQA
from langchain.chains import create_retrieval_chain
from dotenv import load_dotenv
from libs.answer import Answer
import uuid
import logging
from api.environment_variables import EnvironmentVariables

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

env = EnvironmentVariables.get_instance()

class hrbot:

    def __init__(self, prompt, config_file=None):
        self.openai_api_key = env.openai_api_key
        self.openai_api_version = env.openai_api_version
        self.openai_api_endpoint = env.openai_api_endpoint
        self.azure_search_endpoint = env.azure_search_endpoint
        self.embedding_model = env.embedding_model
        self.openai_gpt_4o_model_name = env.openai_gpt_4o_model_name
        
        self.client = AzureOpenAI(api_key=self.openai_api_key, api_version=self.openai_api_version, azure_endpoint=self.openai_api_endpoint)
        self.prompt = prompt

    def get_case_ids(self, response):
        sources = pd.DataFrame()
        logger.debug("Extracting case IDs from response")
        for i in range(len(response["context"])):
            metas = pd.DataFrame()
            metas["reference_id"] = pd.DataFrame.from_dict([response["context"][i].metadata])['document_id']
            metas["title"] = pd.DataFrame.from_dict([response["context"][i].metadata])['title']
            metas["reference_link"] = pd.DataFrame.from_dict([response["context"][i].metadata])['reference_link']
            sources = pd.concat([sources, metas])
        logger.debug("Extracted sources: %s", sources)
        return sources

    def get_answer(self, query, search_index):
        logger.info("Inside get_answer with query: %s", query)

        llm = AzureChatOpenAI(
            temperature=0.0, deployment_name=self.openai_gpt_4o_model_name, azure_endpoint=self.openai_api_endpoint, api_key=self.openai_api_key, logprobs=True, openai_api_version="2024-06-01"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompt),
                ("human", "{input}"),
            ]
        )
        logger.debug("Prompt created")

        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        logger.debug("Question-answer chain created")

        rag_chain = create_retrieval_chain(search_index, question_answer_chain)
        logger.debug("RAG chain created")

        # Define Run ID for tracing and feedback collection
        run_id = uuid.uuid4()
        config = {"run_id": run_id}
        logger.debug("Config built with run_id: %s", run_id)

        response = rag_chain.invoke({"input": query}, config=config)
        sources = self.get_case_ids(response)
        logger.debug("Sources: %s", sources)
        return response["answer"], sources