# config.py - Configuration file for bot settings
# Store sensitive data here or use environment variables for production.

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
ADMIN_CHANNEL_ID = int(os.getenv('ADMIN_CHANNEL_ID'))
DB_NAME = os.getenv('DB_NAME')

# Default countries (top 5 by usage, expandable)
TOP_COUNTRIES = [
    {"name": "USA", "flag": "🇺🇸", "currency": "USD"},
    {"name": "UK", "flag": "🇬🇧", "currency": "GBP"},
    {"name": "Canada", "flag": "🇨🇦", "currency": "CAD"},
    {"name": "Australia", "flag": "🇦🇺", "currency": "AUD"},
    {"name": "Germany", "flag": "🇩🇪", "currency": "EUR"},
]

BOT_USERNAME = ""  # Will be set dynamically on startup