import google.generativeai as genai
from utils import GEMINI_API_KEY
from finance_tools import get_expenses, get_finance_news

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def get_financial_advice():
    expenses = get_expenses()
    news = get_finance_news()

    expense_text = "\n".join([f"{e[1]} - {e[2]} USD ({e[3]})" for e in expenses[-5:]])
    news_text = "\n".join(news)

    prompt = f"""
    I am a personal finance coach. Here are the recent expenses:
    {expense_text}

    And here is the latest market news:
    {news_text}

    Please analyze the expenses and give financial tips, along with market investment advice in simple terms.
    """

    response = model.generate_content(prompt)
    return response.text
