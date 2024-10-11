import os, getpass
import json
from langchain_core.messages import HumanMessage
from googlesearch import search
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from typing import Literal
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from opencage.geocoder import OpenCageGeocode
from pprint import pprint
from opencage.geocoder import OpenCageGeocode
from opencage.geocoder import InvalidInputError, RateLimitExceededError, UnknownError
import requests
import pprint

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


_set_env("OPENCAGE_API_KEY")
_set_env("OPENAI_API_KEY")
_set_env("LANGCHAIN_OPENAI_API_KEY")

@tool
def search_google(string):
    """Performs a Google search and returns the top result."""
    print("search_google calling model...")
    return search(string, num_results=1)    


@tool
def get_weather_by_zip(zip_code):
    """Fetches weather data for a given Zipcode."""
    print("get_weather_by_zip calling model...")
    # Get latitude and longitude from the ZIP code
    lat, lon = get_lat_lon(zip_code)
    if lat is None or lon is None:
        return f"Could not get coordinates for ZIP code {zip_code}"

    # The base URL for the weather.gov API
    base_url = f"https://api.weather.gov/points/{lat},{lon}"

    try:
        # Make a GET request to the base URL
        response = requests.get(base_url)
        response.raise_for_status()  # Check for HTTP errors
        
        # Extract the forecast URL from the response JSON
        forecast_url = response.json()["properties"]["forecast"]
        
        # Make another GET request to fetch the forecast
        forecast_response = requests.get(forecast_url)
        forecast_response.raise_for_status()

        # Parse and return the forecast data
        forecast_data = forecast_response.json()

        return forecast_data["properties"]["periods"]

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"


def get_lat_lon(zip_code):

    print("get_lat_lon calling model..."+zip_code)
    # Make a GET request to the OpenCage API
    OPENCAGE_API_KEY=os.environ.get("OPENCAGE_API_KEY")

    # url = f"https://api.opencagedata.com/geocode/v1/json?q={zip_code}&key={OPENCAGE_API_KEY}"
    geocoder = OpenCageGeocode(OPENCAGE_API_KEY)

    results = geocoder.geocode(zip_code)


    if results and len(results):
        # Extract latitude and longitude from the result
        lat = results[0]['geometry']['lat']
        lng = results[0]['geometry']['lng']
        return lat, lng
    else:
        print(f"Could not get coordinates for ZIP code {zip_code}")
        return None, None

    # try:
    #     print("calling opencage api...")
    #     response = requests.get(url)
    #     print("respone from opencage "+response)
    #     response.raise_for_status()
    #     data = response.json()
        
    #     # Extract latitude and longitude from the response
    #     print(data['results'])
    #     if data['results']:
    #         lat = data['results'][0]['geometry']['lat']
    #         lon = data['results'][0]['geometry']['lng']
    #         return lat, lon
    #     else:
    #         return None, None

    # except requests.exceptions.RequestException as e:
    #     print(f"An error occurred: {e}")
    #     return None, None


tools = [search_google,get_weather_by_zip]

tool_node = ToolNode(tools)


# Define LLM with bound tools
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)




sys_msg = SystemMessage(content="You are a helpful assistant tasked with performing google search.")

def assistant(state: MessagesState):
   print("assitant calling model...")
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}



# def extract_intent(user_input):
#     # Extract intent from user input
#     return LLMTask(prompt="What is the intent of the following user input: {user_input}",model="gpt-4").run();

def call_model(state: MessagesState):
    print("call_model calling model... ")
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# Define the function that determines whether to continue or not
def should_continue(state: MessagesState) -> Literal["tools", END]:
    print("should_continue calling model... ")
    messages = state['messages']
    last_message = messages[-1]
    # If the LLM makes a tool call, then we route to the "tools" node
    if last_message.tool_calls:
        return "tools"
    # Otherwise, we stop (reply to the user)
    return END


workflow = StateGraph(MessagesState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)

workflow.add_edge("tools", "agent")

checkpointer = MemorySaver()

app = workflow.compile(checkpointer=checkpointer)


response_from_llm = app.invoke({"messages": [HumanMessage(content="Can run outside tomorrow living in 75078 ? Also let me know next week as well.")]}, config={"configurable": {"thread_id": 42}})

print(response_from_llm["messages"][-1].content)
