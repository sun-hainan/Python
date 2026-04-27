# -*- coding: utf-8 -*-
"""
算法实现：金融算法 / capm_apt

本文件实现 capm_apt 相关的算法功能。
"""

import numpy as np
from scipy import stats


def capm_expected_return(rf, beta, rm):
    """
    CAPM 期望收益公式
    E[R_i] = R_f + β_i * (E[R_m] - R_f)

    Parameters
    ----------
    rf : float
        无风险利率
    beta : float
        贝塔系数 = Cov(Ri, Rm) / Var(Rm)
    rm : float
        市场组合期望收益

    Returns
    -------
    float
        资产期望收益
    """
    return rf + beta * (rm - rf)


def calculate_beta(asset_returns, market_returns):
    """
    计算贝塔系数
    β = Cov(Ri, Rm) / Var(Rm)

    使用 OLS 回归：R_i = α + β * R_m + ε
    """
    # 使用线性回归
    slope, intercept, r_value, p_value, std_err = stats.linregress(market_returns, asset_returns)

    # 贝塔 = slope
    beta = slope

    # 阿尔法 = intercept
    alpha = intercept

    # R²
    r_squared = r_value ** 2

    # 残差标准差（非系统性风险）
    residuals = asset_returns - (alpha + beta * market_returns)
    residual_std = np.std(residuals, ddof=2)

    # 系统性风险占比
    total_var = np.var(asset_returns, ddof=2)
    systematic_var = beta**2 * np.var(market_returns, ddof=2)
    systematic_ratio = systematic_var / total_var if total_var > 0 else 0

    return {
        'beta': beta,
        'alpha': alpha,
        'r_squared': r_squared,
        'residual_std': residual_std,
        'systematic_ratio': systematic_ratio,
        'p_value': p_value
    }


def security_market_line(beta, rf, rm):
    """
    证券市场线（SML）
    表示在 CAPM 下期望收益与贝塔的关系
    """
    expected_return = rf + beta * (rm - rf)
    return expected_return


def capm_portfolio_optimization(returns, rf, market_returns=None):
    """
    基于 CAPM 的组合优化
    找出切点组合和最优组合

    步骤：
    1. 计算各资产的贝塔和阿尔法
    2. 确定市场组合（如果有）
    3. 计算最优夏普比率组合
    """
    n_assets = returns.shape[1]
    asset_names = [f'Asset_{i+1}' for i in range(n_assets)]

    # 计算各资产的统计量
    results = []
    for i in range(n_assets):
        asset_ret = returns[:, i]
        if market_returns is not None:
            beta_info = calculate_beta(asset_ret, market_returns)
        else:
            # 使用平均收益作为市场代理
            market_proxy = np.mean(returns, axis=1)
            beta_info = calculate_beta(asset_ret, market_proxy)

        mean_ret = np.mean(asset_ret)
        std_ret = np.std(asset_ret, ddof=2)
        sharpe = (mean_ret - rf) / std_ret if std_ret > 0 else 0

        results.append({
            'name': asset_names[i],
            'mean_return': mean_ret,
            'std': std_ret,
            'beta': beta_info['beta'],
            'alpha': beta_info['alpha'],
            'sharpe': sharpe
        })

    return results


def apt_factor_model(returns, factors, rf):
    """
    APT 多因子模型回归
    R_i - R_f = α_i + β_i1*F1 + β_i2*F2 + ... + ε_i

    Parameters
    ----------
    returns : np.ndarray
        资产收益率 (n_obs x n_assets)
    factors : np.ndarray
        因子收益率 (n_obs x n_factors)
    rf : float
        无风险利率

    Returns
    -------
    dict
        各资产的因子暴露和阿尔法
    """
    n_assets = returns.shape[1]
    n_factors = factors.shape[1]

    excess_returns = returns - rf

    betas = np.zeros((n_assets, n_factors))
    alphas = np.zeros(n_assets)
    residuals = np.zeros((n_assets, returns.shape[0]))

    for i in range(n_assets):
        y = excess_returns[:, i]

        # OLS 回归
        X = np.column_stack([np.ones(factors.shape[0]), factors])
        # 使用最小二乘
        beta_ols = np.linalg.lstsq(X, y, rcond=None)[0]

        alphas[i] = beta_ols[0]
        betas[i, :] = beta_ols[1:]

        # 残差
        residuals[i, :] = y - X @ beta_ols

    # 因子协方差矩阵
    factor_cov = np.cov(factors.T)
    # 因子收益
    factor_returns = np.mean(factors, axis=0)

    # APT 定价误差
    predicted_returns = rf + betas @ factor_returns
    actual_returns = np.mean(returns, axis=0)
    pricing_error = actual_returns - predicted_returns

    return {
        'betas': betas,
        'alphas': alphas,
        'factor_returns': factor_returns,
        'factor_cov': factor_cov,
        'predicted_returns': predicted_returns,
        'actual_returns': actual_returns,
        'pricing_error': pricing_error,
        'residuals': residuals
    }


def roll_beta(returns, market_returns, window=60):
    """
    滚动贝塔估计
    用于跟踪资产随时间的系统性风险变化
    """
    n = len(returns)
    betas = np.zeros(n - window)

    for i in range(n - window):
        asset_window = returns[i:i+window]
        market_window = market_returns[i:i+window]
        beta_info = calculate_beta(asset_window, market_window)
        betas[i] = beta_info['beta']

    return betas


def test_alpha_significance(alpha, residual_std, n_obs, n_params):
    """
    检验阿尔法是否显著（t 检验）
    H0: α = 0
    """
    # t = α / (s(α))
    # s(α) = residual_std * sqrt(1/n + x_mean^2 / Σ(x-x_mean)²)
    # 简化版本
    se_alpha = residual_std / np.sqrt(n_obs - n_params)
    t_stat = alpha / se_alpha if se_alpha > 0 else 0

    # 双尾 p 值
    from scipy.stats import t as t_dist
    p_value = 2 * (1 - t_dist.cdf(abs(t_stat), df=n_obs - n_params))

    return {
        'alpha': alpha,
        't_stat': t_stat,
        'p_value': p_value,
        'significant': p_value < 0.05
    }


def efficient_frontier_capm(expected_market_return, market_std, rf, n_points=50):
    """
    CAPM 下的有效前沿
    在 CAPM 下，所有有效组合都在资本市场线 (CML) 上

    CML: E[R_p] = R_f + (E[R_m] - R_f) / σ_m * σ_p

    Parameters
    ----------
    expected_market_return : float
        市场期望收益
    market_std : float
        市场标准差
    rf : float
        无风险利率
    """
    # 夏普比率
    sharpe_market = (expected_market_return - rf) / market_std

    # 有效前沿上的组合
    stds = np.linspace(0, market_std * 2, n_points)
    expected_returns = rf + sharpe_market * stds

    return {
        'stds': stds,
        'expected_returns': expected_returns,
        'market_std': market_std,
        'market_return': expected_market_return,
        'sharpe': sharpe_market
    }


if __name__ == "__main__":
    print("=" * 60)
    print("CAPM 与 APT 模型")
    print("=" * 60)

    # 模拟数据
    np.random.seed(42)
    n_months = 120
    rf = 0.02 / 12  # 月无风险利率

    # 模拟市场收益（年化 8%，波动率 16%）
    market_returns = np.random.normal(0.08/12, 0.16/np.sqrt(12), n_months)

    # 模拟三只股票
    betas_true = [0.8, 1.2, 1.5]
    alphas_true = [0.001, -0.002, 0.0005]

    stock_returns = np.zeros((n_months, 3))
    for i, (beta, alpha) in enumerate(zip(betas_true, alphas_true)):
        # R_i = α + β * R_m + ε
        epsilon = np.random.normal(0, 0.05/np.sqrt(12), n_months)
        stock_returns[:, i] = alpha + beta * market_returns + epsilon

    print("\n--- CAPM 贝塔估计 ---")
    for i in range(3):
        result = calculate_beta(stock_returns[:, i], market_returns)
        print(f"股票 {i+1}: 真实 β={betas_true[i]:.2f}, 估计 β={result['beta']:.4f}, "
              f"α={result['alpha']:.6f}, R²={result['r_squared']:.4f}")

    # 期望收益
    rm = np.mean(market_returns) * 12  # 年化
    print(f"\n市场年化收益: {rm:.2%}")
    print(f"无风险利率: {rf*12:.2%}")

    print("\n--- CAPM 期望收益预测 ---")
    for i in range(3):
        expected = capm_expected_return(rf*12, betas_true[i], rm)
        print(f"股票 {i+1}: CAPM 预测收益 = {expected:.2%}")

    # APT 多因子模型
    print("\n--- APT 多因子模型 ---")

    # 模拟三个因子
    factor1 = np.random.normal(0.0005, 0.02, n_months)  # 市场因子
    factor2 = np.random.normal(0.0002, 0.01, n_months)  # 利率因子
    factor3 = np.random.normal(0.0001, 0.015, n_months)  # 通胀因子
    factors = np.column_stack([factor1, factor2, factor3])

    apt_result = apt_factor_model(stock_returns, factors, rf)

    print("因子暴露 (β):")
    for i in range(3):
        print(f"  股票 {i+1}: β = [{', '.join(f'{b:.4f}' for b in apt_result['betas'][i])}]")

    print(f"\n阿尔法 (α):")
    for i in range(3):
        print(f"  股票 {i+1}: α = {apt_result['alphas'][i]:.6f}")

    print(f"\n定价误差:")
    for i in range(3):
        print(f"  股票 {i+1}: {apt_result['pricing_error'][i]:.6f}")

    # 有效前沿
    print("\n--- CAPM 有效前沿 (资本市场线) ---")
    ef = efficient_frontier_capm(rm, 0.16, rf*12, n_points=10)
    print(f"市场夏普比率: {ef['sharpe']:.4f}")
    print(f"组合波动率 -> 期望收益:")
    for std, er in zip(ef['stds'][:5], ef['expected_returns'][:5]):
        print(f"  σ={std:.2%} -> E[R]={er:.2%}")
