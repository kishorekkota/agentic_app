import os
from dotenv import load_dotenv

# Detect environment (default to development)
# Expected ENV Variable : ENVIRONMENT=production or ENVIRONMENT=development
environment = os.getenv("ENVIRONMENT", "development")

# Load environment-specific .env file
if environment == "production":
    load_dotenv(".env.prod")
else:
    load_dotenv(".env.dev")