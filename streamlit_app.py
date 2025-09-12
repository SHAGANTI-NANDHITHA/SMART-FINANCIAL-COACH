# streamlit_app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from memory import init_db, get_or_create_user
from crew import Crew
import tasks

# Initialize DB & session
session = init_db()
st.set_page_config(page_title="Smart Financial Coach (Crew)", layout="wide")
st.title("💰 Smart Financial Coach — Crew Mode")

# Sidebar: User Info
st.sidebar.header("User Info")
user_name = st.sidebar.text_input("Enter your name", "Local User")
user_income = st.sidebar.number_input("Monthly Income (₹)", min_value=0.0, value=0.0)
user_risk = st.sidebar.selectbox("Risk Tolerance", ["low", "medium", "high"])

# Get or create user and persist basic profile
user = get_or_create_user(session, name=user_name)
user.income = float(user_income)
user.risk_tolerance = user_risk
session.commit()

# create crew instance
crew = Crew(session, user)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["💵 Expenses", "🎯 Goals", "📈 Investments", "👤 Profile"])

# ----------------- Expenses Tab -----------------
with tab1:
    st.header("Track Your Expenses (Crew)")
    category = st.text_input("Expense Category", "")
    amount = st.number_input("Amount (₹)", min_value=0.0)
    if st.button("Add Expense"):
        if category and amount > 0:
            payload = {"action": tasks.ADD_TRANSACTION, "category": category, "amount": float(amount)}
            res = crew.kickoff(payload)
            if res.get("result"):
                st.success(f"Added ₹{amount} to {category}")
            else:
                st.error(res.get("error", "Unknown error"))

    # Expense report via crew
    report_res = crew.kickoff({"action": tasks.EXPENSE_REPORT})
    report = report_res.get("result") or {}
    if report.get("categories"):
        st.subheader("Monthly Expense Summary")
        st.write(f"**Total Expenses:** ₹{report['total_expense']:.2f}")
        st.write(f"**Estimated Monthly Savings:** ₹{report['monthly_savings']:.2f}")

        # Pie chart
        fig, ax = plt.subplots(figsize=(3, 3))
        ax.pie(report['categories'].values(), labels=report['categories'].keys(), autopct='%1.1f%%', startangle=90)
        ax.set_title("Expenses Distribution", fontsize=10)
        st.pyplot(fig, clear_figure=True)
    else:
        st.info("No expenses added yet.")

# ----------------- Goals Tab -----------------
with tab2:
    st.header("Set and Track Goals (Crew)")
    goal_name = st.text_input("Goal Name", key="gname")
    goal_amount = st.number_input("Target Amount (₹)", min_value=0.0, key="gamt")
    goal_deadline = st.date_input("Deadline", key="gdate")

    if st.button("Add Goal"):
        if goal_name and goal_amount > 0:
            payload = {
                "action": tasks.ADD_GOAL,
                "name": goal_name,
                "target_amount": float(goal_amount),
                "deadline": str(goal_deadline)
            }
            res = crew.kickoff(payload)
            if res.get("result"):
                st.success(f"Goal '{goal_name}' added!")
            else:
                st.error(res.get("error", "Could not add goal"))

    # Show progress
    progress_res = crew.kickoff({"action": tasks.GOAL_PROGRESS})
    goals = progress_res.get("result") or []

    if goals:
        st.subheader("Goal Progress")
        for g in goals:
            st.markdown(f"**{g['name']}** 🎯")
            st.write(f"Saved: ₹{g['monthly_savings']}/month")
            st.write(f"ETA: {g['months_to_goal'] if g['months_to_goal'] else 'N/A'} months")
            st.write(f"Achievable: {'✅ Yes' if g.get('achievable') else '❌ No'}")

            # 🔑 Show suggestions if present
            if not g.get("achievable") and "suggestions" in g:
                with st.expander("💡 Suggestions to improve savings"):
                    for s in g["suggestions"]:
                        st.write(f"- {s}")

            st.markdown("---")
    else:
        st.info("No goals added yet.")


# ----------------- Investments Tab -----------------
with tab3:
    st.header("Investment Suggestions (Crew)")
    tickers = st.text_input("Enter stock tickers (comma separated)", "AAPL,GOOG,MSFT")
    tickers_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if st.button("Get Portfolio Suggestions"):
        payload = {"action": tasks.SUGGEST_PORTFOLIO, "tickers": tickers_list}
        res = crew.kickoff(payload)
        if res.get("result"):
            suggestions = res["result"]
            if "error" in suggestions:
                st.warning(suggestions["error"])
            else:
                st.subheader("Target Portfolio Weights")
                st.json(suggestions["weights"])
                if suggestions.get("rebalance_suggestions"):
                    st.subheader("Rebalance Suggestions (Shares)")
                    st.json(suggestions["rebalance_suggestions"])
                else:
                    st.info("No current holdings to rebalance.")
        else:
            st.error(res.get("error", "Unknown error"))

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
