from typing import Union
import requests
import os
from requests.exceptions import RequestException
from opencage.geocoder import OpenCageGeocode
from tavily import TavilyClient
from langchain_core.tools import tool
import logging


tavily_api_key = os.environ.get("TAVILY_API_KEY")
opencage_api_key = os.environ.get("OPENCAGE_API_KEY")

logger = logging.getLogger(__name__)

@tool
def search_google(query: str) -> Union[str, dict]:
    """
    Performs a Google search and returns the top result.

    Parameters:
    query (str): The search query to be executed.
    tavily_api_key (str): The API key for TavilyClient to authenticate the search request.

    Returns:
    Union[str, dict]: If the search is successful, it returns a dictionary containing the search results.
                      If there is an error during the search, it returns a string describing the error.
    """
    logger.info("search_google calling model..." + query)
    try:
        
        tavily_client = TavilyClient(tavily_api_key)
        response = tavily_client.search(query)
        logger.debug(f"Tavily Search Results: {response}")  # For debugging purposes, print the search results.bug("search_google response: " + str(response))
        return response
    except Exception as e:
        logger.error(f"Tavily Search Error: {e}")
        return f"Tavily Search Error: {e}"

@tool
def get_weather_by_zip(zip_code: str):
    """
    Fetches weather data for a given Zipcode.

    Parameters:
    zip_code (str): The ZIP code for which to fetch the weather data.
    opencage_api_key (str): The API key for OpenCageGeocode to authenticate the request for geocoding.

    Returns:
    list: A list of dictionaries containing weather forecast periods if successful.
    str: An error message if there is an issue fetching the weather data.
    """
    logger.info("get_weather_by_zip calling model..." + zip_code)
    try:
        lat, lon = get_lat_lon(zip_code)
        logger.debug(f"get_weather_by_zip: {lat}, {lon}")  # For debugging purposes, print the coordinates received.
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
        logger.error(f"Weather API Error: {e}")
        return f"Weather API Error: {e}"

def get_lat_lon(zip_code: str):
    """Gets latitude and longitude from a zip code using OpenCage API."""
    logger.info("get_lat_lon calling model..." + zip_code)
    try:
        geocoder = OpenCageGeocode(opencage_api_key)
        results = geocoder.geocode(zip_code)
        if results:
            return results[0]['geometry']['lat'], results[0]['geometry']['lng']
        return None, None
    except Exception as e:
        logger.error(f"Error getting coordinates for ZIP code {zip_code}: {e}")
        return None, None  # Handle exceptions gracefully.