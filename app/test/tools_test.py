import unittest
from unittest.mock import patch, MagicMock
import requests
import sys
import types

try:
    from app.tools import search_google, get_weather_by_zip, get_lat_lon
except ModuleNotFoundError as exc:
    if exc.name != "langchain_core":
        raise

    # Provide a minimal @tool decorator fallback for environments without langchain_core.
    fake_langchain_core = types.ModuleType("langchain_core")
    fake_tools_mod = types.ModuleType("langchain_core.tools")

    def tool(fn):
        fn.func = fn
        return fn

    fake_tools_mod.tool = tool
    fake_langchain_core.tools = fake_tools_mod
    sys.modules["langchain_core"] = fake_langchain_core
    sys.modules["langchain_core.tools"] = fake_tools_mod

    from app.tools import search_google, get_weather_by_zip, get_lat_lon

class TestTools(unittest.TestCase):

    @patch('app.tools.TavilyClient')
    def test_search_google_success(self, MockTavilyClient):
        mock_client = MockTavilyClient.return_value
        mock_client.search.return_value = {"result": "test result"}

        result = search_google.func("test query")
        self.assertEqual(result, {"result": "test result"})
        mock_client.search.assert_called_once_with("test query")

    @patch('app.tools.TavilyClient')
    def test_search_google_failure(self, MockTavilyClient):
        mock_client = MockTavilyClient.return_value
        mock_client.search.side_effect = Exception("Test error")

        result = search_google.func("test query")
        self.assertIn("Tavily Search Error", result)
        mock_client.search.assert_called_once_with("test query")

    @patch("app.tools.requests.get")
    @patch("app.tools.get_lat_lon")
    def test_get_weather_by_zip_success(self, mock_get_lat_lon, mock_requests_get):
        mock_get_lat_lon.return_value = (40.7128, -74.0060)

        point_response = MagicMock()
        point_response.json.return_value = {
            "properties": {
                "forecast": "https://api.weather.gov/gridpoints/forecast"
            }
        }
        forecast_response = MagicMock()
        forecast_response.json.return_value = {
            "properties": {
                "periods": [{"name": "Today", "temperature": 70}]
            }
        }
        mock_requests_get.side_effect = [point_response, forecast_response]

        result = get_weather_by_zip.func("10001")
        self.assertEqual(result, [{"name": "Today", "temperature": 70}])
        mock_get_lat_lon.assert_called_once_with("10001")
        self.assertEqual(mock_requests_get.call_count, 2)

    @patch("app.tools.requests.get")
    @patch("app.tools.get_lat_lon")
    def test_get_weather_by_zip_failure(self, mock_get_lat_lon, mock_requests_get):
        mock_get_lat_lon.return_value = (40.7128, -74.0060)
        mock_requests_get.side_effect = requests.RequestException("Test error")

        result = get_weather_by_zip.func("10001")
        self.assertIn("Weather API Error", result)
        mock_get_lat_lon.assert_called_once_with("10001")
        mock_requests_get.assert_called()

    @patch("app.tools.OpenCageGeocode")
    def test_get_lat_lon_success(self, MockOpenCageGeocode):
        mock_geocoder = MockOpenCageGeocode.return_value
        mock_geocoder.geocode.return_value = [{
            'geometry': {'lat': 40.7128, 'lng': -74.0060}
        }]

        lat, lon = get_lat_lon("10001")
        self.assertEqual(lat, 40.7128)
        self.assertEqual(lon, -74.0060)
        mock_geocoder.geocode.assert_called_once_with("10001")

    @patch("app.tools.OpenCageGeocode")
    def test_get_lat_lon_failure(self, MockOpenCageGeocode):
        mock_geocoder = MockOpenCageGeocode.return_value
        mock_geocoder.geocode.side_effect = Exception("Test error")

        lat, lon = get_lat_lon("10001")
        self.assertIsNone(lat)
        self.assertIsNone(lon)
        mock_geocoder.geocode.assert_called_once_with("10001")


if __name__ == '__main__':
    unittest.main()