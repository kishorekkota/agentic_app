from fastapi.testclient import TestClient
from simple_langchain.fast_api import app

client = TestClient(app)

def test_chat_long_paragraph():
    long_paragraph = (
        "This is a very long paragraph meant to test the chat endpoint of the FastAPI application. "
        "It contains multiple sentences, various punctuation marks, and aims to simulate a real-world "
        "scenario where a user might send a detailed message to the chatbot. The purpose of this test "
        "is to ensure that the application can handle long inputs gracefully and return a coherent response "
        "without any errors or unexpected behavior. The paragraph continues with more text to further "
        "increase its length and complexity, challenging the robustness of the system."
    )
    response = client.post("/chat", json={"message": long_paragraph})
    assert response.status_code == 200
    assert "response" in response.json()
