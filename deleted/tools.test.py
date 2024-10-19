import logging
from unittest.mock import patch, MagicMock

logger = logging.getLogger(__name__)


@patch('simple_langchain.langchain_with_function.TavilyClient')
def test_search_google_missing_api_key(mock_tavily_client):
    with patch.dict('os.environ', {'TAVILY_API_KEY': ''}):
        result = search_google("test query")
        assert result == "Tavily Search Error: 'TAVILY_API_KEY' environment variable is missing"
        mock_tavily_client.assert_not_called()

@patch('simple_langchain.langchain_with_function.TavilyClient')
def test_search_google_successful(mock_tavily_client):
    mock_response = {"result": "Top search result"}
    mock_tavily_client.return_value.search.return_value = mock_response

    with patch('logging.Logger.info') as mock_logger_info, \
         patch('logging.Logger.debug') as mock_logger_debug:
        result = search_google("test query")
        assert result == mock_response
        mock_logger_info.assert_called_once_with("search_google calling model...test query")
        mock_logger_debug.assert_called_once_with(f"Tavily Search Results: {mock_response}")

@patch('simple_langchain.langchain_with_function.OpenCageGeocode')
def test_get_lat_lon_missing_api_key(MockOpenCageGeocode):
    with patch.dict('os.environ', {'OPENCAGE_API_KEY': ''}):
        lat, lon = get_lat_lon("75078")
        assert lat is None
        assert lon is None
        MockOpenCageGeocode.assert_not_called()

@patch('simple_langchain.langchain_with_function.OpenCageGeocode')
def test_get_lat_lon_geocoding_failure(MockOpenCageGeocode):
    mock_geocode = MockOpenCageGeocode.return_value
    mock_geocode.geocode.side_effect = Exception("Geocoding service failed")
    
    with patch('logging.Logger.error') as mock_logger_error:
        lat, lon = get_lat_lon("75078")
        assert lat is None
        assert lon is None
        mock_logger_error.assert_called_once_with("Error getting coordinates for ZIP code 75078: Geocoding service failed")


@patch('simple_langchain.langchain_with_function.OpenCageGeocode')
def test_get_lat_lon_valid_zip_code(MockOpenCageGeocode):
    mock_geocode = MockOpenCageGeocode.return_value
    mock_geocode.geocode.return_value = [{'geometry': {'lat': 33.0198, 'lng': -96.6989}}]

    lat, lon = get_lat_lon("75078")
    assert lat == 33.0198
    assert lon == -96.6989
    MockOpenCageGeocode.assert_called_once_with(opencage_api_key)
@patch('simple_langchain.langchain_with_function.OpenCageGeocode')
def test_get_lat_lon_invalid_zip_code(MockOpenCageGeocode):
    mock_geocode = MockOpenCageGeocode.return_value
    mock_geocode.geocode.return_value = None  # Simulate no results for invalid ZIP code

    with patch('logging.Logger.error') as mock_logger_error:
        lat, lon = get_lat_lon("invalid_zip")
        assert lat is None
        assert lon is None
        mock_logger_error.assert_called_once_with("Error getting coordinates for ZIP code invalid_zip: ")

@patch('simple_langchain.langchain_with_function.requests.get')
def test_get_weather_by_zip_malformed_response(mock_requests_get):
    malformed_response = MagicMock()
    malformed_response.json.return_value = {}  # Simulate a malformed response with missing 'properties' key
    mock_requests_get.return_value = malformed_response

    with patch('logging.Logger.error') as mock_logger_error:
        result = get_weather_by_zip("75078")
        assert result == "Weather API Error: 'forecast'"
        mock_logger_error.assert_called_once_with("Weather API Error: 'forecast'")

@patch('simple_langchain.langchain_with_function.requests.get')
@patch('simple_langchain.langchain_with_function.OpenCageGeocode')
def test_get_weather_by_zip_no_periods(mock_opencage, mock_requests_get):
    mock_geocode = mock_opencage.return_value
    mock_geocode.geocode.return_value = [{'geometry': {'lat': 33.0198, 'lng': -96.6989}}]

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "properties": {
            "forecast": "https://api.weather.gov/gridpoints/FWD/80,90/forecast"
        }
    }
    mock_requests_get.return_value = mock_response

    mock_forecast_response = MagicMock()
    mock_forecast_response.json.return_value = {
        "properties": {
            "periods": []
        }
    }
    mock_requests_get.side_effect = [mock_response, mock_forecast_response]

    result = get_weather_by_zip("75078")
    assert result == []

@patch('simple_langchain.langchain_with_function.requests.get')
@patch('simple_langchain.langchain_with_function.OpenCageGeocode')
def test_get_weather_by_zip_logs_coordinates(mock_opencage, mock_requests_get):
    mock_geocode = mock_opencage.return_value
    mock_geocode.geocode.return_value = [{'geometry': {'lat': 33.0198, 'lng': -96.6989}}]

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "properties": {
            "forecast": "https://api.weather.gov/gridpoints/FWD/80,90/forecast"
        }
    }
    mock_requests_get.return_value = mock_response

    mock_forecast_response = MagicMock()
    mock_forecast_response.json.return_value = {
        "properties": {
            "periods": [{"name": "Tonight", "temperature": 75, "shortForecast": "Clear"}]
        }
    }
    mock_requests_get.side_effect = [mock_response, mock_forecast_response]

    with patch('logging.Logger.debug') as mock_logger_debug:
        result = get_weather_by_zip("75078")
        assert result == [{"name": "Tonight", "temperature": 75, "shortForecast": "Clear"}]
        mock_logger_debug.assert_any_call("get_weather_by_zip: 33.0198, -96.6989")
