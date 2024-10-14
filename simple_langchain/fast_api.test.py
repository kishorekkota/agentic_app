from fastapi.testclient import TestClient
from simple_langchain.fast_api import app

client = TestClient(app)
