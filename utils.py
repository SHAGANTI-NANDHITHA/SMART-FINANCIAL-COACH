# utils.py
import os
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-secret")
