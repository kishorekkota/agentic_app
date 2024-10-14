import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import MessagesState

from simple_langchain.langchain_with_function import (
    search_google, get_weather_by_zip, get_lat_lon, assistant, call_model, should_continue, app
)

@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("OPENCAGE_API_KEY", "test_opencage_api_key")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_api_key")
    monkeypatch.setenv("LANGCHAIN_OPENAI_API_KEY", "test_langchain_openai_api_key")

@patch('simple_langchain.langchain_with_function.search')
def test_search_google(mock_search):
    mock_search.return_value = ["https://example.com"]
    result = search_google("test query")
    assert result == ["https://example.com"]
    mock_search.assert_called_once_with("test query", num_results=1)

@patch('simple_langchain.langchain_with_function.OpenCageGeocode')
@patch('simple_langchain.langchain_with_function.requests.get')
def test_get_weather_by_zip(mock_requests_get, MockOpenCageGeocode, mock_env_vars):
    mock_geocode = MockOpenCageGeocode.return_value
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

    result = get_weather_by_zip("75078")
    assert result == [{"name": "Tonight", "temperature": 75, "shortForecast": "Clear"}]

@patch('simple_langchain.langchain_with_function.OpenCageGeocode')
def test_get_lat_lon(MockOpenCageGeocode, mock_env_vars):
    mock_geocode = MockOpenCageGeocode.return_value
    mock_geocode.geocode.return_value = [{'geometry': {'lat': 33.0198, 'lng': -96.6989}}]

    lat, lon = get_lat_lon("75078")
    assert lat == 33.0198
    assert lon == -96.6989

def test_assistant():
    mock_state = MessagesState(messages=[HumanMessage(content="Hello")])
    with patch('simple_langchain.langchain_with_function.llm_with_tools.invoke') as mock_invoke:
        mock_invoke.return_value = SystemMessage(content="Hi there!")
        result = assistant(mock_state)
        assert result["messages"][0].content == "Hi there!"

def test_call_model():
    mock_state = MessagesState(messages=[HumanMessage(content="Hello")])
    with patch('simple_langchain.langchain_with_function.llm_with_tools.invoke') as mock_invoke:
        mock_invoke.return_value = SystemMessage(content="Hi there!")
        result = call_model(mock_state)
        assert result["messages"][0].content == "Hi there!"

def test_should_continue():
    mock_state = MessagesState(messages=[SystemMessage(content="Hi there!")])
    mock_state.messages[-1].tool_calls = True
    result = should_continue(mock_state)
    assert result == "tools"

    mock_state.messages[-1].tool_calls = False
    result = should_continue(mock_state)
    assert result == "END"

def test_app_invoke():
    mock_message = HumanMessage(content="Can run outside tomorrow living in 75078 ? Also let me know next week as well.")
    with patch('simple_langchain.langchain_with_function.llm_with_tools.invoke') as mock_invoke:
        mock_invoke.return_value = SystemMessage(content="Yes, you can run outside.")
        response = app.invoke({"messages": [mock_message]}, config={"configurable": {"thread_id": 42}})
        assert response["messages"][-1].content == "Yes, you can run outside."