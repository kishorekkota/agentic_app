from typing import Union
import requests
from requests.exceptions import RequestException
from opencage.geocoder import OpenCageGeocode
from tavily import TavilyClient
from langchain_core.tools import tool

@tool
def search_google(query: str, tavily_api_key: str) -> Union[str, dict]:
    """
    Performs a Google search and returns the top result.

    Parameters:
    query (str): The search query to be executed.
    tavily_api_key (str): The API key for TavilyClient to authenticate the search request.

    Returns:
    Union[str, dict]: If the search is successful, it returns a dictionary containing the search results.
                      If there is an error during the search, it returns a string describing the error.
    """
    print("search_google calling model..." + query)
    try:
        tavily_client = TavilyClient(tavily_api_key)
        response = tavily_client.search(query)
        return response
    except Exception as e:
        return f"Tavily Search Error: {e}"

@tool
def get_weather_by_zip(zip_code: str, opencage_api_key: str):
    """
    Fetches weather data for a given Zipcode.

    Parameters:
    zip_code (str): The ZIP code for which to fetch the weather data.
    opencage_api_key (str): The API key for OpenCageGeocode to authenticate the request for geocoding.

    Returns:
    list: A list of dictionaries containing weather forecast periods if successful.
    str: An error message if there is an issue fetching the weather data.
    """
    print("get_weather_by_zip calling model..." + zip_code)
    try:
        lat, lon = get_lat_lon(zip_code, opencage_api_key)
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

def get_lat_lon(zip_code: str, opencage_api_key: str):
    """Gets latitude and longitude from a zip code using OpenCage API."""
    print("get_lat_lon calling model..." + zip_code)
    try:
        geocoder = OpenCageGeocode(opencage_api_key)
        results = geocoder.geocode(zip_code)
        if results:
            return results[0]['geometry']['lat'], results[0]['geometry']['lng']
        return None, None
    except Exception as e:
        print(f"Error getting coordinates for ZIP code {zip_code}: {e}")
        return None, None  # Handle exceptions gracefully.