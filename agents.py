from data_fetchers import fetch_stock_history, fetch_current_price, fetch_crypto_price, fetch_news
from portfolio import mean_variance_optimization, simple_rebalance_suggestion
from memory import Transaction, Portfolio
import pandas as pd
import numpy as np
import json

class ExpenseTrackerAgent:
    def __init__(self, session, user):
        self.session = session
        self.user = user

    def add_transaction(self, category, amount):
        t = Transaction(user_id=self.user.id, category=category, amount=amount)
        self.session.add(t)
        self.session.commit()

    def monthly_summary(self):
        import datetime
        now = datetime.datetime.utcnow()
        start = datetime.datetime(now.year, now.month, 1)
        txs = self.session.query(Transaction).filter(
            Transaction.user_id == self.user.id,
            Transaction.timestamp >= start
        ).all()
        cats = {}
        for t in txs:
            cats[t.category] = cats.get(t.category, 0) + t.amount
        return cats

    def monthly_savings(self):
        total_expense = sum(self.monthly_summary().values())
        income = self.user.income or 0
        return max(0, income - total_expense)

    def expense_report(self):
        summary = self.monthly_summary()
        savings = self.monthly_savings()
        report = {
            "categories": summary,
            "total_expense": sum(summary.values()),
            "monthly_savings": savings
        }
        return report

class MarketAnalysisAgent:
    def get_stock_prices(self, tickers):
        prices = {}
        for t in tickers:
            price = fetch_current_price(t)
            if price:
                prices[t] = price
        return prices

    def fetch_price_dataframe(self, tickers, period="1y"):
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
        price_df = self.market.fetch_price_dataframe(tickers)
        if price_df.empty:
            return {"error": "No price data for selected tickers."}

        # Generate optimal portfolio weights
        weights = mean_variance_optimization(price_df)
        prices = self.market.get_stock_prices(tickers)

        # Suggest rebalance if current holdings exist
        suggestions = {}
        portfolio_record = self.session.query(Portfolio).filter_by(user_id=self.user.id).first()
        if portfolio_record:
            current_holdings = portfolio_record.holdings or {}
            suggestions = simple_rebalance_suggestion(current_holdings, weights, prices)

        # Save portfolio if not exists
        if not portfolio_record:
            portfolio_record = Portfolio(user_id=self.user.id, holdings={})
            self.session.add(portfolio_record)
            self.session.commit()

        return {
            "weights": weights.to_dict(),
            "prices": prices,
            "rebalance_suggestions": suggestions
        }

class GoalTrackerAgent:
    def __init__(self, session, user):
        self.session = session
        self.user = user

    def add_goal(self, name, target_amount, deadline):
        goals = json.loads(self.user.goals) if self.user.goals else []
        goals.append({
            "name": name,
            "target": target_amount,
            "deadline": deadline,
            "created": str(pd.Timestamp.utcnow())
        })
        self.user.goals = json.dumps(goals)
        self.session.commit()

    def progress(self):
        et = ExpenseTrackerAgent(self.session, self.user)
        monthly_savings = et.monthly_savings()
        goals = json.loads(self.user.goals) if self.user.goals else []

        for g in goals:
            g['monthly_savings'] = monthly_savings
            if monthly_savings > 0:
                g['months_to_goal'] = round(g['target'] / monthly_savings, 1)
                g['achievable'] = g['months_to_goal'] <= self._months_until(g['deadline'])
            else:
                g['months_to_goal'] = None
                g['achievable'] = False

        return goals

    def _months_until(self, deadline_str):
        import datetime
        try:
            deadline = pd.to_datetime(deadline_str)
            now = datetime.datetime.utcnow()
            delta = (deadline.year - now.year) * 12 + (deadline.month - now.month)
            return max(delta, 0)
        except:
            return 0
