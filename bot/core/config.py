import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./telegram_poster_detailed.db")
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Europe/Helsinki")

# Example of how to ensure critical configs are present
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Missing critical environment variable: TELEGRAM_BOT_TOKEN")

# Add other configurations as needed, e.g. logging level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
