# data_fetchers.py
import yfinance as yf
import requests
import time
from utils import ALPHA_VANTAGE_KEY, NEWSAPI_KEY

def fetch_stock_history(ticker, period="1y", interval="1d"):
    # yfinance is simple and doesn't need API key
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period, interval=interval)
        return hist  # pandas DataFrame
    except Exception as e:
        print("yfinance error", e)
        return None

def fetch_current_price(ticker):
    try:
        t = yf.Ticker(ticker)
        data = t.history(period="1d")
        if not data.empty:
            return float(data["Close"].iloc[-1])
        return None
    except Exception as e:
        print("yfinance error", e)
        return None

def fetch_crypto_price(coin_id="bitcoin"):
    # uses coingecko public api (no key needed)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json().get(coin_id, {}).get("usd")
    return None

def fetch_news(query, page_size=5):
    # optional: requires NEWSAPI_KEY
    if not NEWSAPI_KEY:
        return []
    url = "https://newsapi.org/v2/everything"
    params = {"q": query, "pageSize": page_size, "apiKey": NEWSAPI_KEY, "language": "en"}
    r = requests.get(url, params=params, timeout=10)
    if r.status_code == 200:
        data = r.json()
        return data.get("articles", [])
    else:
        print("NewsAPI error", r.status_code, r.text)
        return []
