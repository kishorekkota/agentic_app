import unittest
from unittest.mock import patch, MagicMock
from tools import search_google, get_weather_by_zip, get_lat_lon

class TestTools(unittest.TestCase):

    @patch('tools.TavilyClient')
    def test_search_google_success(self, MockTavilyClient):
        mock_client = MockTavilyClient.return_value
        mock_client.search.return_value = {"result": "test result"}
        
        result = search_google("test query")
        self.assertEqual(result, {"result": "test result"})
        mock_client.search.assert_called_once_with("test query")

    @patch('tools.TavilyClient')
    def test_search_google_failure(self, MockTavilyClient):
        mock_client = MockTavilyClient.return_value
        mock_client.search.side_effect = Exception("Test error")
        
        result = search_google("test query")
        self.assertIn("Tavily Search Error", result)
        mock_client.search.assert_called_once_with("test query")

    @patch('tools.requests.get')
    @patch('tools.get_lat_lon')
    def test_get_weather_by_zip_success(self, mock_get_lat_lon, mock_requests_get):
        mock_get_lat_lon.return_value = (40.7128, -74.0060)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "properties": {
                "forecast": "https://api.weather.gov/gridpoints/forecast"
            }
        }
        mock_requests_get.return_value = mock_response

        mock_forecast_response = MagicMock()
        mock_forecast_response.json.return_value = {
            "properties": {
                "periods": [{"name": "Today", "temperature": 70}]
            }
        }
        mock_requests_get.return_value = mock_forecast_response

        result = get_weather_by_zip("10001")
        self.assertEqual(result, [{"name": "Today", "temperature": 70}])
        mock_get_lat_lon.assert_called_once_with("10001")
        mock_requests_get.assert_called()

    @patch('tools.requests.get')
    @patch('tools.get_lat_lon')
    def test_get_weather_by_zip_failure(self, mock_get_lat_lon, mock_requests_get):
        mock_get_lat_lon.return_value = (40.7128, -74.0060)
        mock_requests_get.side_effect = requests.RequestException("Test error")

        result = get_weather_by_zip("10001")
        self.assertIn("Weather API Error", result)
        mock_get_lat_lon.assert_called_once_with("10001")
        mock_requests_get.assert_called()

    @patch('tools.OpenCageGeocode')
    def test_get_lat_lon_success(self, MockOpenCageGeocode):
        mock_geocoder = MockOpenCageGeocode.return_value
        mock_geocoder.geocode.return_value = [{
            'geometry': {'lat': 40.7128, 'lng': -74.0060}
        }]

        lat, lon = get_lat_lon("10001")
        self.assertEqual(lat, 40.7128)
        self.assertEqual(lon, -74.0060)
        mock_geocoder.geocode.assert_called_once_with("10001")

    @patch('tools.OpenCageGeocode')
    def test_get_lat_lon_failure(self, MockOpenCageGeocode):
        mock_geocoder = MockOpenCageGeocode.return_value
        mock_geocoder.geocode.side_effect = Exception("Test error")

        lat, lon = get_lat_lon("10001")
        self.assertIsNone(lat)
        self.assertIsNone(lon)
        mock_geocoder.geocode.assert_called_once_with("10001")
        @patch('tools.requests.get')
        @patch('tools.get_lat_lon')
        def test_get_weather_by_zip_success(self, mock_get_lat_lon, mock_requests_get):
            mock_get_lat_lon.return_value = (40.7128, -74.0060)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "properties": {
                    "forecast": "https://api.weather.gov/gridpoints/forecast"
                }
            }
            mock_requests_get.return_value = mock_response

            mock_forecast_response = MagicMock()
            mock_forecast_response.json.return_value = {
                "properties": {
                    "periods": [{"name": "Today", "temperature": 70}]
                }
            }
            mock_requests_get.return_value = mock_forecast_response

            result = get_weather_by_zip("10001")
            self.assertEqual(result, [{"name": "Today", "temperature": 70}])
            mock_get_lat_lon.assert_called_once_with("10001")
            mock_requests_get.assert_called()

        @patch('tools.requests.get')
        @patch('tools.get_lat_lon')
        def test_get_weather_by_zip_failure(self, mock_get_lat_lon, mock_requests_get):
            mock_get_lat_lon.return_value = (40.7128, -74.0060)
            mock_requests_get.side_effect = requests.RequestException("Test error")

            result = get_weather_by_zip("10001")
            self.assertIn("Weather API Error", result)
            mock_get_lat_lon.assert_called_once_with("10001")
            mock_requests_get.assert_called()

        @patch('tools.OpenCageGeocode')
        def test_get_lat_lon_success(self, MockOpenCageGeocode):
            mock_geocoder = MockOpenCageGeocode.return_value
            mock_geocoder.geocode.return_value = [{
                'geometry': {'lat': 40.7128, 'lng': -74.0060}
            }]

            lat, lon = get_lat_lon("10001")
            self.assertEqual(lat, 40.7128)
            self.assertEqual(lon, -74.0060)
            mock_geocoder.geocode.assert_called_once_with("10001")

        @patch('tools.OpenCageGeocode')
        def test_get_lat_lon_failure(self, MockOpenCageGeocode):
            mock_geocoder = MockOpenCageGeocode.return_value
            mock_geocoder.geocode.side_effect = Exception("Test error")

            lat, lon = get_lat_lon("10001")
            self.assertIsNone(lat)
            self.assertIsNone(lon)
            mock_geocoder.geocode.assert_called_once_with("10001")
if __name__ == '__main__':
    unittest.main()