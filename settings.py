import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

# Model configuration
DEFAULT_MODEL_ID = os.getenv("DEFAULT_MODEL_ID", "gemini-2.0-flash-exp")
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.1"))

# Service configuration
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "9000"))
SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")

# Backend URLs
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Restaurant configuration
MAX_ORDER_ITEMS = int(os.getenv("MAX_ORDER_ITEMS", "20"))
MAX_PARTY_SIZE = int(os.getenv("MAX_PARTY_SIZE", "12"))
KITCHEN_DELAY_SECONDS = int(os.getenv("KITCHEN_DELAY_SECONDS", "180"))