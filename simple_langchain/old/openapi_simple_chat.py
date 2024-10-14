import os, getpass
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


_set_env("OPENAI_API_KEY")
_set_env("LANGCHAIN_OPENAI_API_KEY")

gpt35_chat = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)

msg = HumanMessage(content="Hello world", name="Lance")

messages = [msg]


def run_chatbot(messages):
    response = gpt35_chat.invoke(messages)
    print(response)


run_chatbot(messages)