import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_api_key(key_name):
    """
    Retrieves API key from environment variables.
    """
    val = os.getenv(key_name)
    if not val:
        print(f"Warning: {key_name} not found in environment variables.")
    return val

# Configuration Constants
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
SEC_HEADERS = {
    "User-Agent": "SentientCapitalAI investment_bot@gmail.com",
    "Accept-Encoding": "gzip, deflate",
}
