import os, getpass
from langchain_core.messages import HumanMessage
from googlesearch import search
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from typing import Literal
from langgraph.graph import START,END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from opencage.geocoder import OpenCageGeocode
import requests
import uuid
from requests.exceptions import RequestException
from tavily import TavilyClient
from langgraph.checkpoint.memory import MemorySaver

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

class AIAssistant:
    def __init__(self, ai_api_key: str = None,tavily_api_key: str = None):
        self.ai_api_key = ai_api_key or os.environ.get("OPENAI_API_KEY")
        self.tavily_api_key = tavily_api_key or os.environ.get("TAVILY_API_KEY")
        if not self.ai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=self.ai_api_key) #Added temperature for control
        self.thread_id = None  #Initialize thread id to None
        self.user_message = None
        self.new_conversation = True
        self._setup_tools()
        self._setup_workflow()


    def _setup_tools(self):
        @tool
        def search_google(query: str):
            """Performs a Google search and returns the top result."""
            print("search_google calling model..." + query)
            try:
                tavily_client = TavilyClient(self.tavily_api_key)                
                response = tavily_client.search(query)
                return response
            except Exception as e:
                return f"Tavily Search Error: {e}"

        @tool
        def get_weather_by_zip(zip_code: str):
            """Fetches weather data for a given Zipcode."""
            
            print("get_weather_by_zip calling model..."+ zip_code)

            try:
                lat, lon = self._get_lat_lon(zip_code)

                print(f"get_weather_by_zip: {lat}, {lon}")  # For debugging purposes, print the coordinates received.

                if lat is None or lon is None:
                    return f"Could not get coordinates for ZIP code {zip_code}"

                base_url = f"https://api.weather.gov/points/{lat},{lon}"
                response = requests.get(base_url)
                response.raise_for_status()
                forecast_url = response.json()["properties"]["forecast"]
                forecast_response = requests.get(forecast_url)
                forecast_response.raise_for_status()
                return forecast_response.json()["properties"]["periods"]
            except (RequestException, KeyError, ValueError) as e:
                return f"Weather API Error: {e}"

        self.tools = [search_google, get_weather_by_zip]


    def _get_lat_lon(self, zip_code: str):
        """Gets latitude and longitude from a zip code using OpenCage API."""

        print("get_lat_lon calling model..."+zip_code)

        try:
            geocoder = OpenCageGeocode(os.environ.get("OPENCAGE_API_KEY"))
            results = geocoder.geocode(zip_code)
            if results:
                return results[0]['geometry']['lat'], results[0]['geometry']['lng']
            return None, None
        except Exception as e:
            print(f"Error getting coordinates for ZIP code {zip_code}: {e}")
            return None, None  #Handle exceptions gracefully.


    def _setup_workflow(self):

        print("Setting up workflow... __setup_workflow__")

        tool_node = ToolNode(self.tools)
        llm_with_tools = self.llm.bind_tools(self.tools)

        def call_model(state: MessagesState):
            
            print("call_model calling model...")

            messages = state["messages"]

            print(f"call_model: {messages}")  # For debugging purposes, print the messages received.

            response = llm_with_tools.invoke(messages)

            print(f"call_model: {response}")  # For debugging purposes, print the response received.

            return {"messages": [response]}

        def should_continue(state: MessagesState) -> Literal["tools", END]:
            messages = state['messages']
            last_message = messages[-1]
            return "tools" if last_message.tool_calls else END

        workflow = StateGraph(MessagesState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", tool_node)
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", should_continue)
        workflow.add_edge("tools", "agent")        
        memory = MemorySaver()
        self.workflow = workflow.compile(checkpointer=memory)


    def start_new_session(self):
        self.thread_id = uuid.uuid4()
        self.new_conversation = False
        print(f"Started new session with thread_id: {self.thread_id}")


    def run(self, user_message: str):
        self.user_message = user_message

        if self.new_conversation:
            self.start_new_session()

        response = self.workflow.invoke(
            {"messages": [HumanMessage(content=self.user_message)]},
            config={"configurable": {"thread_id": self.thread_id}}
        )

        for message in response["messages"]:
            message.pretty_print()  # Print the response in a pretty format for readability.

        return response["messages"][-1].content

#Set Environment variables before instantiating the class
_set_env("OPENCAGE_API_KEY")
_set_env("OPENAI_API_KEY")
_set_env("LANGCHAIN_OPENAI_API_KEY")
_set_env("TAVILY_API_KEY")

#Instantiate the AIAssistant class.
assistant = AIAssistant()


# user_input = "Can I run outside tomorrow living in 75078? Also let me know next week as well."
# response = assistant.run(user_input)
# print(response)


# user_input = "What's the weather like in 90210 next week?"
# response = assistant.run(user_input)
# print(response)


user_input = "I am living in 75075"
assistant.new_conversation = True
response = assistant.run(user_input)
print(response)

user_input = "Can I run outside tomorrow?"

response = assistant.run(user_input)
print(response)


user_input = "Can I run outside tomorrow?"

response = assistant.run(user_input)
print(response)
