# agents.py
from data_fetchers import fetch_stock_history, fetch_current_price, fetch_crypto_price, fetch_news
from portfolio import mean_variance_optimization, simple_rebalance_suggestion
import pandas as pd
import numpy as np
import json

class ExpenseTrackerAgent:
    def __init__(self, session, user):
        self.session = session
        self.user = user

    def add_transaction(self, category, amount):
        from memory import Transaction
        t = Transaction(user_id=self.user.id, category=category, amount=amount)
        self.session.add(t)
        self.session.commit()

    def monthly_summary(self):
        from memory import Transaction
        import datetime
        now = datetime.datetime.utcnow()
        start = datetime.datetime(now.year, now.month, 1)
        txs = self.session.query(Transaction).filter(Transaction.user_id==self.user.id, Transaction.timestamp >= start).all()
        cats = {}
        for t in txs:
            cats[t.category] = cats.get(t.category, 0) + t.amount
        return cats

class MarketAnalysisAgent:
    def get_stock_prices(self, tickers):
        prices = {}
        for t in tickers:
            prices[t] = fetch_current_price(t)
        return prices

    def fetch_price_dataframe(self, tickers, period="1y"):
        # returns DataFrame of price history for given tickers (aligning dates)
        dfs = {}
        for t in tickers:
            hist = fetch_stock_history(t, period=period)
            if hist is not None and not hist.empty:
                dfs[t] = hist['Close']
        if not dfs:
            return pd.DataFrame()
        df = pd.concat(dfs.values(), axis=1)
        df.columns = dfs.keys()
        return df.fillna(method='ffill').dropna()

    def get_crypto_price(self, coin_id):
        return fetch_crypto_price(coin_id)

    def get_news(self, query):
        return fetch_news(query)

class InvestmentAdvisorAgent:
    def __init__(self, session, user):
        self.session = session
        self.user = user
        self.market = MarketAnalysisAgent()

    def suggest_portfolio(self, tickers, current_holdings=None):
        # fetch historical prices
        price_df = self.market.fetch_price_dataframe(tickers)
        if price_df.empty:
            return {"error": "No price data"}
        weights = mean_variance_optimization(price_df)
        prices = {t: self.market.get_stock_prices([t])[t] for t in tickers}
        suggestions = {}
        if current_holdings:
            suggestions = simple_rebalance_suggestion(current_holdings, weights, prices)
        return {"weights": weights.to_dict(), "prices": prices, "suggestions": suggestions}

class GoalTrackerAgent:
    def __init__(self, session, user):
        self.session = session
        self.session = session
        self.user = user

    def add_goal(self, name, target_amount, deadline):
        import json
        goals = json.loads(self.user.goals) if self.user.goals else []
        goals.append({"name": name, "target": target_amount, "deadline": deadline, "created": str(pd.Timestamp.utcnow())})
        self.user.goals = json.dumps(goals)
        self.session.commit()

    def progress(self):
        # simplistic: compare savings (income - expenses) vs targets
        import json
        goals = json.loads(self.user.goals) if self.user.goals else []
        # compute monthly savings
        et = ExpenseTrackerAgent(self.session, self.user)
        cats = et.monthly_summary()
        monthly_spend = sum(cats.values())
        monthly_savings = max(0, (self.user.income or 0) - monthly_spend)
        for g in goals:
            g['monthly_savings'] = monthly_savings
            # add ETA months
            if monthly_savings > 0:
                g['months_to_goal'] = (g['target'] / monthly_savings)
            else:
                g['months_to_goal'] = None
        return goals
