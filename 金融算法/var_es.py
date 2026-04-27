# -*- coding: utf-8 -*-
"""
算法实现：金融算法 / var_es

本文件实现 var_es 相关的算法功能。
"""

import numpy as np
from scipy.stats import norm, chi2
from scipy.linalg import cholesky


def historical_var(returns, confidence_level=0.95, holding_period=1):
    """
    历史模拟法计算 VaR
    直接使用历史收益率数据的经验分位数

    优点：无需分布假设，计算简单
    缺点：依赖于历史数据的代表性，极端事件可能被低估

    Parameters
    ----------
    returns : np.ndarray
        历史收益率序列（一维数组）
    confidence_level : float
        置信水平（如 0.95 表示 95% VaR）
    holding_period : int
        持有期（天），用于从日 VaR 扩展到多天 VaR
    """
    # VaR 是损失的分位数，所以取负的收益率
    # 95% VaR：5% 的概率损失超过 VaR
    alpha = 1 - confidence_level
    # 使用线性插值获得更精确的分位数
    var = -np.percentile(returns, alpha * 100)
    # 持有期扩展：通常假设日收益独立同分布，平方根法则
    var_scaled = var * np.sqrt(holding_period)

    return var_scaled


def historical_es(returns, confidence_level=0.95, holding_period=1):
    """
    历史模拟法计算 ES
    ES = 所有超过 VaR 的极端损失的平均值
    """
    alpha = 1 - confidence_level
    var_threshold = -np.percentile(returns, alpha * 100)
    # 提取所有超过 VaR 的损失（即收益率低于 -VaR）
    tail_losses = returns[returns <= -var_threshold]
    # 如果没有超过 VaR 的样本，使用 VaR 作为估计
    if len(tail_losses) == 0:
        es = var_threshold
    else:
        es = -np.mean(tail_losses)
    es_scaled = es * np.sqrt(holding_period)

    return es_scaled


def parametric_var(mu, sigma, confidence_level=0.95, holding_period=1):
    """
    方差-协方差法计算 VaR（参数法）
    假设收益率服从正态分布，使用解析公式

    优点：计算快速，不需要历史数据
    缺点：正态分布假设可能低估肥尾风险

    Parameters
    ----------
    mu : float
        日均收益率（mean）
    sigma : float
        日收益率标准差
    """
    alpha = 1 - confidence_level
    # 正态分布的分位数
    z_score = norm.ppf(alpha)  # 左侧分位数（如 95% 时为 -1.645）
    # VaR = -(μ + z*σ)，z 为负所以 VaR 为正
    var = -(mu + z_score * sigma)
    var_scaled = var * np.sqrt(holding_period)

    return var_scaled


def parametric_es(mu, sigma, confidence_level=0.95, holding_period=1):
    """
    正态分布下 ES 的解析解
    ES_α = -(μ - σ * φ(z) / (1-α))

    其中 z 是标准正态分布的 (1-α) 分位数
    φ(z) 是标准正态密度函数
    """
    alpha = 1 - confidence_level
    z_score = norm.ppf(alpha)
    phi_z = norm.pdf(z_score)
    # ES 公式：E[L | L > VaR]
    es = -(mu - sigma * phi_z / alpha)
    es_scaled = es * np.sqrt(holding_period)

    return es_scaled


def parametric_var_t_dist(returns, confidence_level=0.95, holding_period=1):
    """
    学生 t 分布的 VaR（更适合金融肥尾）
    自由度 ν 越小，尾部越肥
    """
    alpha = 1 - confidence_level
    # 估计 t 分布参数
    mu = np.mean(returns)
    sigma = np.std(returns, ddof=1)
    # 使用矩估计法估计自由度
    # 峰度 = 3 + 6/(ν-4)，样本峰度 = Kurtosis + 3
    kurtosis = np.mean(((returns - mu) / sigma) ** 4)
    # 简化的自由度估计
    nu = max(4.1, 6.0 / (kurtosis - 3) + 4) if kurtosis > 3 else 10

    from scipy.stats import t as t_dist
    t_alpha = t_dist.ppf(alpha, df=nu)
    var = -(mu + t_alpha * sigma)
    var_scaled = var * np.sqrt(holding_period)

    return var_scaled


def portfolio_var_cov(weights, cov_matrix, confidence_level=0.95):
    """
    投资组合 VaR（方差-协方差法）
    使用协方差矩阵计算组合收益分布

    Parameters
    ----------
    weights : np.ndarray
        各资产权重（n 维向量，和为 1）
    cov_matrix : np.ndarray
        协方差矩阵（n x n）
    """
    # 组合收益率的均值和方差
    # E[Rp] = w'μ，Var(Rp) = w'Σw
    # 这里假设均值为 0（简化）
    portfolio_variance = weights @ cov_matrix @ weights
    portfolio_std = np.sqrt(portfolio_variance)

    alpha = 1 - confidence_level
    z_score = norm.ppf(alpha)
    var = -z_score * portfolio_std

    return var


def var_cov_decomposition(weights, expected_returns, cov_matrix, confidence_level=0.95):
    """
    VaR 的边际分解（Marginal VaR / Component VaR）
    计算每个资产对组合 VaR 的贡献

    边际 VaR (Marginal VaR) = ρ_i,p * σ_p / σ_i
    = Cov(Ri, Rp) / Var(Rp)
    = (Σw_j * Cov_ij) / σ_p²
    """
    alpha = 1 - confidence_level
    z_score = norm.ppf(alpha)

    # 组合标准差
    port_var = weights @ cov_matrix @ weights
    port_std = np.sqrt(port_var)

    # 组合 VaR
    port_var_value = -z_score * port_std

    # 各资产的边际 VaR
    # Marginal VaR_i = ∂VaR/∂w_i = z * Cov(Ri, Rp) / σ_p
    marginal_vars = z_score * (cov_matrix @ weights) / port_std

    # 各资产的 Component VaR（对总 VaR 的绝对贡献）
    component_vars = weights * marginal_vars

    # 验证：Component VaR 之和 = 组合 VaR
    total_component = np.sum(component_vars)

    return {
        'portfolio_var': port_var_value,
        'marginal_vars': marginal_vars,
        'component_vars': component_vars,
        'pct_contribution': component_vars / port_var_value * 100  # 百分比贡献
    }


def monte_carlo_var(initial_value, returns_sim, confidence_level=0.95):
    """
    蒙特卡洛 VaR：使用模拟生成的收益率分布
    返回模拟的 P&L 分布，然后取分位数
    """
    alpha = 1 - confidence_level
    # 模拟 P&L = 初始值 * 收益率
    pnl = initial_value * returns_sim
    var = -np.percentile(pnl, alpha * 100)

    # ES：超过 VaR 的平均损失
    tail_pnl = pnl[pnl <= -var]
    es = -np.mean(tail_pnl) if len(tail_pnl) > 0 else var

    return var, es


def cornish_fisher_var(mu, sigma, skewness, kurtosis, confidence_level=0.95):
    """
    Cornish-Fisher 展开修正的 VaR
    在正态分位数基础上用矩修正，捕捉肥尾和非对称性

    修正分位数：z_cf = z + (z²-1)*S/6 + (z³-3z)*K/24 - (2z³-5z)*S²/36
    其中 S=偏度，K=超额峰度
    """
    alpha = 1 - confidence_level
    z = norm.ppf(alpha)

    S = skewness  # 偏度（Skewness）
    K = kurtosis  # 超额峰度（Excess Kurtosis）

    # Cornish-Fisher 修正
    z_cf = (z +
            (z**2 - 1) * S / 6 +
            (z**3 - 3*z) * K / 24 -
            (2*z**3 - 5*z) * S**2 / 36)

    var = -(mu + z_cf * sigma)
    return var


if __name__ == "__main__":
    # 模拟历史收益率数据
    np.random.seed(42)
    n_days = 1000
    daily_return = 0.0005
    daily_vol = 0.02

    # 假设日收益率服从正态分布
    returns = np.random.normal(daily_return, daily_vol, n_days)

    # 模拟资产组合（3个资产）
    n_assets = 3
    weights = np.array([0.4, 0.4, 0.2])  # 40% 股票, 40% 债券, 20% 商品
    corr_matrix = np.array([
        [1.0, 0.3, 0.1],
        [0.3, 1.0, 0.2],
        [0.1, 0.2, 1.0]
    ])
    vols = np.array([0.02, 0.01, 0.015])  # 各资产波动率
    cov_matrix = np.outer(vols, vols) * corr_matrix

    initial_portfolio = 1_000_000  # 100万组合

    print(f"历史数据: {n_days} 天, 日均收益 {daily_return:.4f}, 日波动率 {daily_vol:.4f}")
    print(f"组合初始价值: {initial_portfolio:,.0f}\n")

    for conf in [0.95, 0.99]:
        print(f"--- 置信水平 {conf:.0%} ---")
        var_hist = historical_var(returns, confidence_level=conf)
        es_hist = historical_es(returns, confidence_level=conf)
        var_param = parametric_var(daily_return, daily_vol, confidence_level=conf)
        es_param = parametric_es(daily_return, daily_vol, confidence_level=conf)
        var_cf = cornish_fisher_var(daily_return, daily_vol,
                                     skewness=0.0, kurtosis=0.0,  # 假设正态
                                     confidence_level=conf)

        print(f"  历史模拟 VaR:  {var_hist:.4f} ({var_hist*initial_portfolio:,.0f})")
        print(f"  历史模拟 ES:   {es_hist:.4f} ({es_hist*initial_portfolio:,.0f})")
        print(f"  参数 VaR (正态): {var_param:.4f} ({var_param*initial_portfolio:,.0f})")
        print(f"  参数 ES (正态): {es_param:.4f} ({es_param*initial_portfolio:,.0f})")
        print()

    # 投资组合 VaR 分解
    print("--- 投资组合 VaR 分解 ---")
    port_var = portfolio_var_cov(weights, cov_matrix, confidence_level=0.95)
    decomp = var_cov_decomposition(weights, None, cov_matrix, confidence_level=0.95)
    print(f"组合 VaR (95%): {decomp['portfolio_var']:.4f}")
    print(f"各资产贡献:")
    for i, (w, cv) in enumerate(zip(weights, decomp['component_vars'])):
        print(f"  资产{i+1}: 权重={w:.0%}, Component VaR={cv:.4f}, 贡献={decomp['pct_contribution'][i]:.1f}%")
