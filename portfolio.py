# portfolio.py
import numpy as np
import pandas as pd
from scipy.optimize import minimize

def compute_returns(price_df):
    returns = price_df.pct_change().dropna()
    return returns

def mean_variance_optimization(price_df, returns_period="1y", risk_free_rate=0.02):
    returns = compute_returns(price_df)
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    num_assets = len(mean_returns)

    def portfolio_performance(weights):
        port_return = np.dot(weights, mean_returns)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return port_return, port_vol

    def neg_sharpe(weights):
        r, vol = portfolio_performance(weights)
        return -(r - risk_free_rate) / vol

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for _ in range(num_assets))
    init_guess = np.array(num_assets * [1. / num_assets])

    result = minimize(neg_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    if result.success:
        weights = result.x
        return pd.Series(weights, index=mean_returns.index)
    else:
        raise Exception("Optimization failed")

def simple_rebalance_suggestion(current_holdings, target_weights, current_prices):
    total_value = sum(current_holdings.get(sym, 0) * current_prices.get(sym, 0) for sym in target_weights.index)
    suggestions = {}
    for sym, w in target_weights.items():
        target_value = w * total_value
        current_value = current_holdings.get(sym, 0) * current_prices.get(sym, 0)
        delta_value = target_value - current_value
        delta_shares = delta_value / current_prices.get(sym, 1)
        suggestions[sym] = delta_shares
    return suggestions
