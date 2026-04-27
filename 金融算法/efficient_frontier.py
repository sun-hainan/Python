# -*- coding: utf-8 -*-
"""
算法实现：金融算法 / efficient_frontier

本文件实现 efficient_frontier 相关的算法功能。
"""

import numpy as np
from scipy.optimize import minimize


def portfolio_return(weights, expected_returns):
    """组合期望收益 = w'μ"""
    return np.dot(weights, expected_returns)


def portfolio_variance(weights, cov_matrix):
    """组合方差 = w'Σw"""
    return np.dot(weights, np.dot(cov_matrix, weights))


def portfolio_std(weights, cov_matrix):
    """组合标准差（波动率）"""
    return np.sqrt(portfolio_variance(weights, cov_matrix))


def sharpe_ratio(weights, expected_returns, cov_matrix, rf):
    """夏普比率 = (E[Rp] - Rf) / σp"""
    p_return = portfolio_return(weights, expected_returns)
    p_std = portfolio_std(weights, cov_matrix)
    return (p_return - rf) / p_std if p_std > 0 else 0


def minimum_variance_portfolio(expected_returns, cov_matrix):
    """
    求解最小方差组合（无卖空限制）
    min w'Σw
    s.t. Σw_i = 1

    解析解：w = Σ^(-1) * 1 / (1'Σ^(-1)1)
    """
    n = len(expected_returns)
    ones = np.ones(n)

    # Σ^(-1)
    cov_inv = np.linalg.inv(cov_matrix)

    # w = Σ^(-1) * 1 / (1'Σ^(-1)1)
    numerator = cov_inv @ ones
    denominator = ones @ cov_inv @ ones
    weights = numerator / denominator

    ret = portfolio_return(weights, expected_returns)
    var = portfolio_variance(weights, cov_matrix)

    return {
        'weights': weights,
        'expected_return': ret,
        'variance': var,
        'std': np.sqrt(var)
    }


def minimum_variance_portfolio_with_return(expected_returns, cov_matrix, target_return):
    """
    给定目标收益的最小方差组合
    min w'Σw
    s.t. w'μ = target_return
          Σw_i = 1
    """
    n = len(expected_returns)

    def objective(w):
        return portfolio_variance(w, cov_matrix)

    # 约束
    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # 权重和为1
        {'type': 'eq', 'fun': lambda w: portfolio_return(w, expected_returns) - target_return}  # 目标收益
    ]

    # 初始猜测：等权重
    w0 = np.ones(n) / n

    result = minimize(objective, w0, method='SLSQP', constraints=constraints)
    weights = result.x

    return {
        'weights': weights,
        'expected_return': target_return,
        'variance': portfolio_variance(weights, cov_matrix),
        'std': portfolio_std(weights, cov_matrix)
    }


def tangency_portfolio(expected_returns, cov_matrix, rf):
    """
    切点组合（最大夏普比率组合）
    max (w'μ - rf) / sqrt(w'Σw)
    s.t. Σw_i = 1
    """
    n = len(expected_returns)

    def neg_sharpe(w):
        p_ret = portfolio_return(w, expected_returns)
        p_std = portfolio_std(w, cov_matrix)
        return -(p_ret - rf) / p_std if p_std > 0 else 0

    constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
    w0 = np.ones(n) / n

    result = minimize(neg_sharpe, w0, method='SLSQP', constraints=constraints)
    weights = result.x

    p_return = portfolio_return(weights, expected_returns)
    p_std = portfolio_std(weights, cov_matrix)

    return {
        'weights': weights,
        'expected_return': p_return,
        'variance': portfolio_variance(weights, cov_matrix),
        'std': p_std,
        'sharpe_ratio': (p_return - rf) / p_std
    }


def efficient_frontier(expected_returns, cov_matrix, rf, n_points=50):
    """
    计算有效前沿上的多个组合

    步骤：
    1. 找到最小方差组合
    2. 找到切点组合
    3. 在两者之间插值生成有效组合
    """
    # 最小方差组合
    mvp = minimum_variance_portfolio(expected_returns, cov_matrix)

    # 切点组合
    tp = tangency_portfolio(expected_returns, cov_matrix, rf)

    # 确定收益范围
    min_return = min(mvp['expected_return'], tp['expected_return'])
    max_return = max(mvp['expected_return'], tp['expected_return']) * 1.2

    target_returns = np.linspace(min_return, max_return, n_points)

    portfolios = []
    for target in target_returns:
        # 只考虑收益 >= MVP 收益的组合
        if target >= mvp['expected_return']:
            try:
                p = minimum_variance_portfolio_with_return(expected_returns, cov_matrix, target)
                portfolios.append(p)
            except:
                pass

    return {
        'portfolios': portfolios,
        'min_variance_portfolio': mvp,
        'tangency_portfolio': tp
    }


def efficient_frontier_quadratic(expected_returns, cov_matrix, rf, n_points=50):
    """
    使用二次规划直接求解有效前沿（更高效）
    对每个目标收益求解一个 QP
    """
    n = len(expected_returns)

    def solve_for_return(target_return):
        def objective(w):
            return portfolio_variance(w, cov_matrix)

        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
            {'type': 'eq', 'fun': lambda w: portfolio_return(w, expected_returns) - target_return}
        ]

        w0 = np.ones(n) / n
        result = minimize(objective, w0, method='SLSQP', constraints=constraints)

        if result.success:
            w = result.x
            return {
                'weights': w,
                'expected_return': portfolio_return(w, expected_returns),
                'variance': portfolio_variance(w, cov_matrix),
                'std': np.sqrt(portfolio_variance(w, cov_matrix))
            }
        return None

    # 找到收益范围
    mvp = minimum_variance_portfolio(expected_returns, cov_matrix)
    tp = tangency_portfolio(expected_returns, cov_matrix, rf)

    min_ret = mvp['expected_return']
    max_ret = tp['expected_return'] * 1.5

    target_returns = np.linspace(min_ret, max_ret, n_points)

    portfolios = []
    for target in target_returns:
        p = solve_for_return(target)
        if p is not None:
            portfolios.append(p)

    return {
        'portfolios': portfolios,
        'min_variance_portfolio': mvp,
        'tangency_portfolio': tp
    }


def portfolio_with_constraints(expected_returns, cov_matrix, rf, long_only=True,
                               max_weight=None, min_weight=None):
    """
    带约束的组合优化
    """
    n = len(expected_returns)

    def objective(w):
        p_ret = portfolio_return(w, expected_returns)
        p_var = portfolio_variance(w, cov_matrix)
        # 最大化效用：E[R] - λ * Var
        # 等价于最小化 Var - (1/λ) * E[R]，这里用简化的负夏普
        return -p_ret / np.sqrt(p_var) if p_var > 0 else 0

    constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}

    bounds = []
    if max_weight is not None:
        bounds = [(min_weight or 0, max_weight) for _ in range(n)]
    elif long_only:
        bounds = [(0, 1) for _ in range(n)]

    w0 = np.ones(n) / n
    result = minimize(objective, w0, method='SLSQP',
                     constraints=constraints, bounds=bounds if bounds else None)

    weights = result.x

    return {
        'weights': weights,
        'expected_return': portfolio_return(weights, expected_returns),
        'variance': portfolio_variance(weights, cov_matrix),
        'std': portfolio_std(weights, cov_matrix)
    }


def capital_market_line(rf, tangency_portfolio, std_range):
    """
    资本市场线 (CML)
    E[R_p] = R_f + (E[R_T] - R_f) / σ_T * σ_p

    投资者可以在无风险资产和切点组合之间选择
    """
    sharpe = tangency_portfolio['sharpe_ratio']
    expected_returns = rf + sharpe * std_range
    return expected_returns


if __name__ == "__main__":
    print("=" * 60)
    print("有效前沿与最优组合")
    print("=" * 60)

    # 模拟 5 只股票
    np.random.seed(42)
    n_assets = 5
    n_months = 120

    # 年化期望收益和波动率
    annual_returns = np.array([0.08, 0.12, 0.10, 0.07, 0.09])
    annual_vols = np.array([0.16, 0.24, 0.20, 0.14, 0.18])
    rf = 0.03  # 无风险利率

    # 月度参数
    monthly_returns = annual_returns / 12
    monthly_vols = annual_vols / np.sqrt(12)

    # 模拟收益率
    corr_matrix = np.array([
        [1.0, 0.3, 0.2, 0.1, 0.15],
        [0.3, 1.0, 0.25, 0.2, 0.1],
        [0.2, 0.25, 1.0, 0.15, 0.2],
        [0.1, 0.2, 0.15, 1.0, 0.3],
        [0.15, 0.1, 0.2, 0.3, 1.0]
    ])

    # 协方差矩阵
    cov_matrix = np.outer(monthly_vols, monthly_vols) * corr_matrix

    # 估计的期望收益（用样本均值）
    returns_sim = np.random.multivariate_normal(monthly_returns, cov_matrix, (n_months,))
    expected_returns_est = np.mean(returns_sim, axis=0)
    cov_matrix_est = np.cov(returns_sim.T)

    print("\n资产期望收益 (年化):")
    for i, r in enumerate(expected_returns_est):
        print(f"  资产 {i+1}: {r*12:.2%}")

    # 最小方差组合
    print("\n--- 最小方差组合 ---")
    mvp = minimum_variance_portfolio(expected_returns_est, cov_matrix_est)
    print(f"期望收益 (年化): {mvp['expected_return']*12:.2%}")
    print(f"波动率 (年化): {mvp['std']*np.sqrt(12):.2%}")
    print("权重:")
    for i, w in enumerate(mvp['weights']):
        print(f"  资产 {i+1}: {w:.4f}")

    # 切点组合
    print("\n--- 切点组合 (最大夏普) ---")
    tp = tangency_portfolio(expected_returns_est, cov_matrix_est, rf/12)
    print(f"夏普比率: {tp['sharpe_ratio']:.4f}")
    print(f"期望收益 (年化): {tp['expected_return']*12:.2%}")
    print(f"波动率 (年化): {tp['std']*np.sqrt(12):.2%}")
    print("权重:")
    for i, w in enumerate(tp['weights']):
        print(f"  资产 {i+1}: {w:.4f}")

    # 有效前沿
    print("\n--- 有效前沿 (部分点) ---")
    ef = efficient_frontier_quadratic(expected_returns_est, cov_matrix_est, rf/12, n_points=20)

    print(f"{'收益(年化)':>12} {'波动率(年化)':>12} {'夏普比率':>10}")
    print("-" * 40)
    for p in ef['portfolios'][::3]:
        sr = (p['expected_return'] - rf/12) / p['std']
        print(f"{p['expected_return']*12:>12.2%} {p['std']*np.sqrt(12):>12.2%} {sr:>10.4f}")

    # 资本市场线
    print("\n--- 资本市场线 ---")
    std_range = np.linspace(0, 0.4, 50)
    cml = capital_market_line(rf/12, tp, std_range)
    print("波动率 -> 期望收益:")
    for s, e in zip(std_range[:5], cml[:5]):
        print(f"  {s:.2%} -> {e*12:.2%}")
