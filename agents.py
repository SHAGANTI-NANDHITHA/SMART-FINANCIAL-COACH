# agents.py
"""
Crew-style agents implemented as small classes with a uniform handle_task interface.
These use your existing data_fetchers, portfolio, and memory modules.
"""

from data_fetchers import fetch_stock_history, fetch_current_price, fetch_crypto_price, fetch_news
from portfolio import mean_variance_optimization, simple_rebalance_suggestion
from memory import Transaction, Portfolio, User
import pandas as pd
import numpy as np
import json
import datetime


class ExpenseAgent:
    name = "expense"

    def __init__(self, session, user):
        self.session = session
        self.user = user

    # core helpers (kept similar to original)
    def add_transaction(self, category, amount):
        t = Transaction(user_id=self.user.id, category=category, amount=amount)
        self.session.add(t)
        self.session.commit()
        return {"status": "ok", "added": {"category": category, "amount": amount}}

    def monthly_summary(self):
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

    # uniform agent entry
    def handle_task(self, task_name, payload):
        if task_name == "add_transaction":
            return self.add_transaction(payload.get("category"), float(payload.get("amount", 0)))
        if task_name == "monthly_summary":
            return self.monthly_summary()
        if task_name == "expense_report":
            return self.expense_report()
        if task_name == "monthly_savings":
            return {"monthly_savings": self.monthly_savings()}
        raise ValueError(f"Unknown task {task_name} for ExpenseAgent")


class MarketAgent:
    name = "market"

    def __init__(self, session=None, user=None):
        self.session = session
        self.user = user

    def get_stock_prices(self, tickers):
        prices = {}
        for t in tickers:
            price = fetch_current_price(t)
            if price is not None:
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
        return df.ffill().dropna()

    def get_crypto_price(self, coin_id):
        return fetch_crypto_price(coin_id)

    def get_news(self, query):
        return fetch_news(query)

    def handle_task(self, task_name, payload):
        if task_name == "get_stock_prices":
            return self.get_stock_prices(payload.get("tickers", []))
        if task_name == "fetch_price_dataframe":
            return self.fetch_price_dataframe(payload.get("tickers", []), payload.get("period", "1y"))
        if task_name == "get_crypto_price":
            return {"price": self.get_crypto_price(payload.get("coin_id", "bitcoin"))}
        if task_name == "get_news":
            return self.get_news(payload.get("query", "finance"))
        raise ValueError(f"Unknown task {task_name} for MarketAgent")


class InvestmentAgent:
    name = "investment"

    def __init__(self, session, user):
        self.session = session
        self.user = user
        self.market = MarketAgent(session, user)

    def suggest_portfolio(self, tickers, current_holdings=None):
        # fetch historical price dataframe
        price_df = self.market.fetch_price_dataframe(tickers)
        if price_df.empty:
            return {"error": "No price data for selected tickers."}

        # compute optimal weights
        weights = mean_variance_optimization(price_df)
        prices = self.market.get_stock_prices(tickers)

        # load or create portfolio record
        portfolio_record = self.session.query(Portfolio).filter_by(user_id=self.user.id).first()
        suggestions = {}
        current_holdings = current_holdings or {}
        if portfolio_record:
            current_holdings = portfolio_record.holdings or {}
            suggestions = simple_rebalance_suggestion(current_holdings, weights, prices)

        if not portfolio_record:
            portfolio_record = Portfolio(user_id=self.user.id, holdings={})
            self.session.add(portfolio_record)
            self.session.commit()

        return {
            "weights": weights.to_dict(),
            "prices": prices,
            "rebalance_suggestions": suggestions
        }

    def handle_task(self, task_name, payload):
        if task_name == "suggest_portfolio":
            tickers = payload.get("tickers", [])
            return self.suggest_portfolio(tickers, payload.get("current_holdings"))
        raise ValueError(f"Unknown task {task_name} for InvestmentAgent")


class GoalAgent:
    name = "goal"

    def __init__(self, session, user):
        self.session = session
        self.user = user

    def add_goal(self, name, target_amount, deadline):
        goals = json.loads(self.user.goals) if self.user.goals else []
        goals.append({
            "name": name,
            "target": float(target_amount),
            "deadline": deadline,
            "created": str(pd.Timestamp.utcnow())
        })
        self.user.goals = json.dumps(goals)
        self.session.commit()
        return {"status": "ok", "goal": {"name": name, "target": target_amount, "deadline": deadline}}

    def progress(self):
        et = ExpenseAgent(self.session, self.user)
        monthly_savings = et.monthly_savings()
        expense_summary = et.monthly_summary()
        goals = json.loads(self.user.goals) if self.user.goals else []

        for g in goals:
            g['monthly_savings'] = monthly_savings
            if monthly_savings > 0:
                g['months_to_goal'] = round(g['target'] / monthly_savings, 1)
                g['achievable'] = g['months_to_goal'] <= self._months_until(g['deadline'])
            else:
                g['months_to_goal'] = None
                g['achievable'] = False

            # Suggestions if not achievable
            if not g['achievable']:
                suggestions = []
                months_left = self._months_until(g['deadline'])
                if months_left > 0:
                    required_savings = g['target'] / months_left
                    extra_needed = required_savings - monthly_savings
                    # Suggest cutting from biggest categories first
                    sorted_expenses = sorted(expense_summary.items(), key=lambda x: x[1], reverse=True)
                    for cat, amt in sorted_expenses:
                        if extra_needed <= 0:
                            break
                        cut = min(amt * 0.2, extra_needed)  # suggest cutting up to 20% per category
                        if cut > 0:
                            suggestions.append(f"Reduce {cat} expenses by ₹{cut:.2f}")
                            extra_needed -= cut
                    if extra_needed > 0:
                        suggestions.append(f"Still need extra savings of ₹{extra_needed:.2f} or extend the deadline.")
                    g['suggestions'] = suggestions
                else:
                    g['suggestions'] = ["Deadline already passed or invalid."]

        return goals

    def _months_until(self, deadline_str):
        try:
            deadline = pd.to_datetime(deadline_str)
            now = datetime.datetime.utcnow()
            delta = (deadline.year - now.year) * 12 + (deadline.month - now.month)
            return max(delta, 0)
        except Exception:
            return 0

    def handle_task(self, task_name, payload):
        if task_name == "add_goal":
            return self.add_goal(payload.get("name"), payload.get("target_amount"), payload.get("deadline"))
        if task_name == "progress":
            return self.progress()
        raise ValueError(f"Unknown task {task_name} for GoalAgent")
