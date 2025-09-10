import sqlite3
import requests
import yfinance as yf
from utils import ALPHA_VANTAGE_KEY, NEWSAPI_KEY

DB_NAME = "finance.db"

# ---------------- EXPENSE FUNCTIONS ----------------
def add_expense(category, amount, description=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (category, amount, description) VALUES (?, ?, ?)", 
                   (category, amount, description))
    conn.commit()
    conn.close()

def get_expenses():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# ---------------- INVESTMENT FUNCTIONS ----------------
def add_investment(type, symbol, amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO investments (type, symbol, amount) VALUES (?, ?, ?)", 
                   (type, symbol, amount))
    conn.commit()
    conn.close()

def get_investments():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM investments ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# ---------------- MARKET DATA ----------------
def get_stock_price(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1d")
    if not data.empty:
        return data["Close"].iloc[-1]
    return None

def get_crypto_price(symbol="bitcoin"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    response = requests.get(url).json()
    return response[symbol]["usd"]

def get_finance_news():
    url = f"https://newsapi.org/v2/top-headlines?category=business&apiKey={NEWSAPI_KEY}"
    response = requests.get(url).json()
    return [article["title"] for article in response["articles"][:5]]
