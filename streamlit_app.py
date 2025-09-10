# streamlit_app.py
import streamlit as st
from memory import init_db, get_or_create_user
from agents import ExpenseTrackerAgent, InvestmentAdvisorAgent, GoalTrackerAgent
import utils
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Personal Finance Coach", layout="wide")

session = init_db()
user = get_or_create_user(session, name="local_user")

st.title("Personal Finance & Investment Coach (Demo)")

# Sidebar: profile
with st.sidebar:
    st.header("Profile")
    name = st.text_input("Name", value=user.name)
    income = st.number_input("Monthly Income (USD)", value=float(user.income or 0.0))
    rt = st.selectbox("Risk Tolerance", ["low", "medium", "high"], index=1)
    if st.button("Save Profile"):
        user.name = name
        user.income = income
        user.risk_tolerance = rt
        session.commit()
        st.success("Profile saved")

# Tabs
tabs = st.tabs(["Expenses", "Goals", "Market & Portfolio", "Advice"])

# Expenses tab
with tabs[0]:
    st.header("Add Expense / Transaction")
    cat = st.selectbox("Category", ["Food", "Transport", "Rent", "Utilities", "Entertainment", "Other"])
    amount = st.number_input("Amount (USD)", min_value=0.0, value=0.0)
    if st.button("Add Transaction"):
        et = ExpenseTrackerAgent(session, user)
        et.add_transaction(cat, float(amount))
        st.success("Transaction added")

    et = ExpenseTrackerAgent(session, user)
    summary = et.monthly_summary()
    st.subheader("This month's spending by category")
    if summary:
        df = pd.DataFrame(list(summary.items()), columns=["Category", "Amount"])
        st.table(df)
        fig = px.pie(df, names="Category", values="Amount", title="Spending Breakdown")
        st.plotly_chart(fig)
    else:
        st.info("No transactions yet")

# Goals tab
with tabs[1]:
    st.header("Goals")
    gt_name = st.text_input("Goal name (e.g., 'Emergency Fund')")
    gt_amount = st.number_input("Target Amount (USD)", value=1000.0)
    gt_deadline = st.date_input("Deadline")
    if st.button("Add Goal"):
        g = GoalTrackerAgent(session, user)
        g.add_goal(gt_name, float(gt_amount), str(gt_deadline))
        st.success("Goal added")

    g = GoalTrackerAgent(session, user)
    progress = g.progress()
    st.subheader("Goals & Progress")
    st.write(progress)

# Market & Portfolio tab
with tabs[2]:
    st.header("Market & Portfolio")
    tickers = st.text_input("Tickers to analyze (comma separated)", value="AAPL,MSFT,GOOGL")
    tickers = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    ia = InvestmentAdvisorAgent(session, user)
    if st.button("Analyze"):
        with st.spinner("Fetching data and optimizing..."):
            res = ia.suggest_portfolio(tickers, current_holdings={t: 0 for t in tickers})
        if "error" in res:
            st.error(res["error"])
        else:
            st.subheader("Target Weights")
            w = pd.Series(res["weights"])
            st.table(w.reset_index().rename(columns={"index":"Ticker", 0:"Weight"}))
            st.subheader("Current Prices")
            st.write(res["prices"])
            st.subheader("Rebalance Suggestions (shares to buy/sell)")
            st.write(res["suggestions"])

# Advice tab
with tabs[3]:
    st.header("Personalized Advice")
    st.write("This panel would show proactive alerts, overspending warnings, and rebalancing suggestions.")
    # Example simple rule:
    et = ExpenseTrackerAgent(session, user)
    summary = et.monthly_summary()
    total_spend = sum(summary.values()) if summary else 0
    if user.income and total_spend > 0:
        if total_spend > user.income * 0.8:
            st.warning(f"You're spending {total_spend:.2f} which is > 80% of your income.")
        else:
            st.success("Spending looks reasonable.")
    else:
        st.info("Add profile and transactions to get advice.")
