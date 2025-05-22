import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("TELEGRAM_API_KEY")

# OpenAI API Key
AI_API_KEY = os.getenv("AI_API_KEY")

# Model Name
MODEL_NAME = os.getenv("MODEL_NAME")

# API Request route
API_REQUEST_ROUTE = os.getenv("API_REQUEST_ROUTE", "http://localhost:5001/")

if not BOT_TOKEN:
    raise ValueError("Error: TELEGRAM_API_KEY is not set in the .env file.")
if not AI_API_KEY:
    raise ValueError("Error: AI_API_KEY is not set in the .env file.")
if not MODEL_NAME:
    raise ValueError("Error: MODEL_NAME is not set in the .env file.")