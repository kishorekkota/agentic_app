# config.py
import os

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "https://kishore-rag-test.search.windows.net")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY", "<key>")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "index_test")