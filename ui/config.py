# config.py

import os

# LangSmith API Key
LANGSMITH_API_KEY = os.getenv('LANGSMITH_API_KEY')

# Streamlit Authenticator Configuration
AUTH_COOKIE_NAME = 'chatbot_cookie'
AUTH_COOKIE_KEY = 'some_signature_key'
AUTH_COOKIE_EXPIRY_DAYS = 1