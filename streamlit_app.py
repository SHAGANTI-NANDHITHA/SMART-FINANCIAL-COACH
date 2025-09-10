import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from memory import init_db, get_or_create_user
from agents import ExpenseTrackerAgent, InvestmentAdvisorAgent, GoalTrackerAgent

# Initialize DB
session = init_db()
st.set_page_config(page_title="Smart Financial Coach", layout="wide")
st.title("💰 Smart Financial Coach")

# Sidebar: User Info
st.sidebar.header("User Info")
user_name = st.sidebar.text_input("Enter your name", "Local User")
user_income = st.sidebar.number_input("Monthly Income (₹)", min_value=0.0, value=0.0)
user_risk = st.sidebar.selectbox("Risk Tolerance", ["low", "medium", "high"])

# Get or create user
user = get_or_create_user(session, name=user_name)
user.income = user_income
user.risk_tolerance = user_risk
session.commit()

# Initialize Agents
expense_agent = ExpenseTrackerAgent(session, user)
goal_agent = GoalTrackerAgent(session, user)
investment_agent = InvestmentAdvisorAgent(session, user)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["💵 Expenses", "🎯 Goals", "📈 Investments", "👤 Profile"])

# ----------------- Expenses Tab -----------------
with tab1:
    st.header("Track Your Expenses")
    category = st.text_input("Expense Category", "")
    amount = st.number_input("Amount (₹)", min_value=0.0)
    if st.button("Add Expense"):
        if category and amount > 0:
            expense_agent.add_transaction(category, amount)
            st.success(f"Added ₹{amount} to {category}")

    # Expense report
    expense_report = expense_agent.expense_report()
    if expense_report['categories']:
        st.subheader("Monthly Expense Summary")
        st.write(f"**Total Expenses:** ₹{expense_report['total_expense']:.2f}")
        st.write(f"**Estimated Monthly Savings:** ₹{expense_report['monthly_savings']:.2f}")

        # Small pie chart
        fig, ax = plt.subplots(figsize=(3, 3))
        ax.pie(
            expense_report['categories'].values(),
            labels=expense_report['categories'].keys(),
            autopct='%1.1f%%',
            startangle=90
        )
        ax.set_title("Expenses Distribution", fontsize=10)
        st.pyplot(fig, clear_figure=True)
    else:
        st.info("No expenses added yet.")

# ----------------- Goals Tab -----------------
with tab2:
    st.header("Set and Track Goals")
    goal_name = st.text_input("Goal Name")
    goal_amount = st.number_input("Target Amount (₹)", min_value=0.0)
    goal_deadline = st.date_input("Deadline")
    if st.button("Add Goal"):
        if goal_name and goal_amount > 0:
            goal_agent.add_goal(goal_name, goal_amount, str(goal_deadline))
            st.success(f"Goal '{goal_name}' added!")

    goals = goal_agent.progress()
    if goals:
        st.subheader("Goal Progress")
        for g in goals:
            st.write(f"**{g['name']}**: Saved {g['monthly_savings']}₹/month, "
                     f"ETA: {g['months_to_goal'] if g['months_to_goal'] else 'N/A'} months, "
                     f"Achievable: {'Yes' if g.get('achievable') else 'No'}")
    else:
        st.info("No goals added yet.")

# ----------------- Investments Tab -----------------
with tab3:
    st.header("Investment Suggestions")
    tickers = st.text_input("Enter stock tickers (comma separated)", "AAPL,GOOG,MSFT")
    tickers_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if st.button("Get Portfolio Suggestions"):
        suggestions = investment_agent.suggest_portfolio(tickers_list)
        if "error" in suggestions:
            st.warning(suggestions["error"])
        else:
            st.subheader("Target Portfolio Weights")
            st.json(suggestions["weights"])
            if suggestions["rebalance_suggestions"]:
                st.subheader("Rebalance Suggestions (Shares)")
                st.json(suggestions["rebalance_suggestions"])
            else:
                st.info("No current holdings to rebalance.")

# ----------------- Profile Tab -----------------
with tab4:
    st.header("Your Profile")
    st.write(f"**Name:** {user.name}")
    st.write(f"**Monthly Income:** ₹{user.income}")
    st.write(f"**Risk Tolerance:** {user.risk_tolerance}")
    st.write("**Goals:**")
    if user.goals:
        st.json(user.goals)
    else:
        st.info("No goals set yet.")
