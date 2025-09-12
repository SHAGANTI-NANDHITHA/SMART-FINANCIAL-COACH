# crew.py
"""
Simple local Crew runtime to orchestrate agents.
It provides run_task(agent_name, task_name, payload) and kickoff convenience method.
"""

from agents import ExpenseAgent, MarketAgent, InvestmentAgent, GoalAgent

class Crew:
    def __init__(self, session, user):
        # create agent instances that share the same DB session and user
        self.session = session
        self.user = user
        self.agents = {
            "expense": ExpenseAgent(session, user),
            "market": MarketAgent(session, user),
            "investment": InvestmentAgent(session, user),
            "goal": GoalAgent(session, user),
        }

    def run_task(self, agent_name, task_name, payload=None):
        payload = payload or {}
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Unknown agent {agent_name}"}
        try:
            result = agent.handle_task(task_name, payload)
            return {"agent": agent_name, "task": task_name, "result": result}
        except Exception as e:
            return {"agent": agent_name, "task": task_name, "error": str(e)}

    def kickoff(self, inputs):
        """
        Convenience method: interpret inputs and call appropriate tasks.
        inputs should contain an 'action' key describing the requested operation.
        Example:
         { "action": "add_transaction", "category":"Food", "amount":100 }
        """
        action = inputs.get("action")
        if action in ("add_transaction", "monthly_summary", "expense_report", "monthly_savings"):
            return self.run_task("expense", action, inputs)
        if action in ("get_stock_prices", "fetch_price_dataframe", "get_news", "get_crypto_price"):
            return self.run_task("market", action, inputs)
        if action == "suggest_portfolio":
            return self.run_task("investment", "suggest_portfolio", inputs)
        if action in ("add_goal", "progress"):
            return self.run_task("goal", action, inputs)
        return {"error": "Unknown action for kickoff", "action": action}
