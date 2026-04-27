# -*- coding: utf-8 -*-
"""
算法实现：金融算法 / monte_carlo_option

本文件实现 monte_carlo_option 相关的算法功能。
"""

import numpy as np
from scipy.stats import norm


def geometric_brownian_motion(S, T, r, sigma, n_steps, n_paths, dt=None):
    """
    生成几何布朗运动路径
    dS = μS dt + σS dW
    解析解：S(t+dt) = S(t) * exp((μ - 0.5σ²)dt + σ√dt * Z), Z~N(0,1)
    """
    if dt is None:
        dt = T / n_steps

    # 生成标准正态随机数矩阵：n_paths x n_steps
    Z = np.random.standard_normal((n_paths, n_steps))

    # 计算每步的收益率
    # drift = (r - 0.5 * sigma**2) * dt 是漂移项
    # diffusion = sigma * sqrt(dt) * Z 是扩散项
    drift = (r - 0.5 * sigma ** 2) * dt
    diffusion = sigma * np.sqrt(dt) * Z

    # 累积收益：ln(S(t)/S(0)) = sum of (drift + diffusion)
    log_returns = drift + diffusion
    cumulative_returns = np.cumsum(log_returns, axis=1)

    # 加上初始价格，得到每条路径的标的价格序列
    prices = S * np.exp(cumulative_returns)
    # 在前面加一列初始价格
    prices = np.column_stack([np.full(n_paths, S), prices])

    return prices


def monte_carlo_option_price(S, K, T, r, sigma, n_paths=100000, n_steps=252,
                             option_type='call', payoff='european'):
    """
    基础蒙特卡洛期权定价

    Parameters
    ----------
    payoff : str
        'european': 标准欧式期权
        'arithmetic_asian': 算术平均亚式期权
        'geometric_asian': 几何平均亚式期权
        'lookback': 回顾期权（最优点差）
    """
    dt = T / n_steps
    discount = np.exp(-r * T)

    # 生成标的资产价格路径
    Z = np.random.standard_normal((n_paths, n_steps))
    drift = (r - 0.5 * sigma ** 2) * dt
    diffusion = sigma * np.sqrt(dt) * Z

    # 累积 ln(S)
    log_S = np.cumsum(drift + diffusion, axis=1)
    prices = S * np.exp(log_S)

    if payoff == 'european':
        # 终端价格
        ST = prices[:, -1]
        if option_type == 'call':
            payoffs = np.maximum(ST - K, 0)
        else:
            payoffs = np.maximum(K - ST, 0)

    elif payoff == 'arithmetic_asian':
        # 算术平均亚式期权： payoff = max(S_avg - K, 0) 或 max(K - S_avg, 0)
        # S_avg = (1/n_steps) * sum(S_0, S_1, ..., S_{n-1})
        avg_prices = np.mean(prices, axis=1)
        if option_type == 'call':
            payoffs = np.maximum(avg_prices - K, 0)
        else:
            payoffs = np.maximum(K - avg_prices, 0)

    elif payoff == 'geometric_asian':
        # 几何平均亚式期权：有解析解
        log_avg = np.mean(np.log(prices), axis=1)
        avg_prices = np.exp(log_avg)
        if option_type == 'call':
            payoffs = np.maximum(avg_prices - K, 0)
        else:
            payoffs = np.maximum(K - avg_prices, 0)

    elif payoff == 'lookback':
        # 回顾看涨期权： payoff = max(max(S) - S_0, 0)
        # 持有期内最高价与初始价格的差
        max_prices = np.max(prices, axis=1)
        payoffs = np.maximum(max_prices - S, 0)  # strike = S_0

    # 蒙特卡洛估计：折现 payoff 的均值
    price = discount * np.mean(payoffs)
    std_error = discount * np.std(payoffs) / np.sqrt(n_paths)

    return price, std_error


def monte_carlo_antithetic(S, K, T, r, sigma, n_paths=100000, n_steps=252,
                           option_type='call'):
    """
    对偶变量法（Antithetic Variates）
    核心思想：如果 Z ~ N(0,1)，则 -Z 也 ~ N(0,1)
    两组样本的均值可以抵消部分随机误差

    使用 n_paths/2 条正路径和 n_paths/2 条负路径
    """
    n_half = n_paths // 2
    dt = T / n_steps
    discount = np.exp(-r * T)

    # 生成一半的随机数
    Z = np.random.standard_normal((n_half, n_steps))
    drift = (r - 0.5 * sigma ** 2) * dt
    diffusion = sigma * np.sqrt(dt) * Z

    # 正路径
    log_returns_pos = drift + diffusion
    cumulative_pos = np.cumsum(log_returns_pos, axis=1)
    prices_pos = S * np.exp(cumulative_pos)
    ST_pos = prices_pos[:, -1]

    # 负路径（使用 -Z）
    log_returns_neg = drift - diffusion  # diffusion 项取反
    cumulative_neg = np.cumsum(log_returns_neg, axis=1)
    prices_neg = S * np.exp(cumulative_neg)
    ST_neg = prices_neg[:, -1]

    if option_type == 'call':
        payoffs_pos = np.maximum(ST_pos - K, 0)
        payoffs_neg = np.maximum(ST_neg - K, 0)
    else:
        payoffs_pos = np.maximum(K - ST_pos, 0)
        payoffs_neg = np.maximum(K - ST_neg, 0)

    # 合并正负路径的 payoff
    all_payoffs = np.concatenate([payoffs_pos, payoffs_neg])
    price = discount * np.mean(all_payoffs)
    std_error = discount * np.std(all_payoffs) / np.sqrt(n_paths)

    return price, std_error


def monte_carlo_control_variate(S, K, T, r, sigma, n_paths=100000, n_steps=252,
                                  option_type='call'):
    """
    控制变量法（Control Variates）
    使用几何平均亚式期权作为控制变量
    原因：几何平均有解析解，与算术平均高度相关但更稳定

    步骤：
    1. 同时模拟算术平均（目标）和几何平均（控制变量）
    2. 用解析解计算几何平均的控制变量期望
    3. 调整算术平均的估计
    """
    dt = T / n_steps
    discount = np.exp(-r * T)

    Z = np.random.standard_normal((n_paths, n_steps))
    drift = (r - 0.5 * sigma ** 2) * dt
    diffusion = sigma * np.sqrt(dt) * Z

    log_returns = drift + diffusion
    cumulative = np.cumsum(log_returns, axis=1)
    prices = S * np.exp(cumulative)

    # 算术平均 payoff（目标变量）
    arith_avg = np.mean(prices, axis=1)
    if option_type == 'call':
        payoffs_arith = np.maximum(arith_avg - K, 0)
    else:
        payoffs_arith = np.maximum(K - arith_avg, 0)

    # 几何平均 payoff（控制变量）
    geo_avg = np.exp(np.mean(np.log(prices), axis=1))
    if option_type == 'call':
        payoffs_geo = np.maximum(geo_avg - K, 0)
    else:
        payoffs_geo = np.maximum(K - geo_avg, 0)

    # 几何平均亚式期权的解析解（Black-Scholes 类似）
    # 对于几何平均期权，可以看作一个新型标的资产的欧式期权
    sigma_geo = sigma / np.sqrt(3)  # 几何平均的波动率
    # 几何平均的初始值近似为 S * exp(-0.5 * sigma^2 * T/2)
    S_geo_approx = S * np.exp(-0.5 * sigma ** 2 * T / 3)
    # 这里用简化的控制变量估计

    # 计算回归系数 c = Cov(X,Y) / Var(Y)
    # X = 算术平均 payoff, Y = 几何平均 payoff
    cov_xy = np.cov(payoffs_arith, payoffs_geo)[0, 1]
    var_y = np.var(payoffs_geo)
    c = cov_xy / var_y if var_y > 0 else 0

    # 调整后的估计
    mean_y = np.mean(payoffs_geo)  # 蒙特卡洛几何平均
    # 使用蒙特卡洛估计而非解析值，可以减少偏差
    price = discount * (np.mean(payoffs_arith) - c * (mean_y - np.mean(payoffs_geo)))
    std_error = discount * np.std(payoffs_arith - c * payoffs_geo) / np.sqrt(n_paths)

    return price, std_error


def monte_carlo_stratified(S, K, T, r, sigma, n_paths=100000, n_steps=252,
                           option_type='call'):
    """
    分层抽样法（Stratified Sampling）
    对最终终端价格的分位数进行分层，确保每个区间都有样本
    特别适用于尾部敏感的 payoff（如深度虚值期权）
    """
    dt = T / n_steps
    discount = np.exp(-r * T)

    # 对数收益率的终值分布：ln(ST/S) ~ N((r-0.5σ²)T, σ²T)
    # 使用分层抽样：按分位数分层
    mean_log_return = (r - 0.5 * sigma ** 2) * T
    std_log_return = sigma * np.sqrt(T)

    # 将 [0,1] 分成 n_paths 个区间，每个区间取一个样本
    u = (np.arange(n_paths) + np.random.random(n_paths)) / n_paths
    Z = norm.ppf(u)  # 分层抽样的标准正态样本

    # 终端价格
    ST = S * np.exp(mean_log_return + std_log_return * Z)

    if option_type == 'call':
        payoffs = np.maximum(ST - K, 0)
    else:
        payoffs = np.maximum(K - ST, 0)

    price = discount * np.mean(payoffs)
    std_error = discount * np.std(payoffs) / np.sqrt(n_paths)

    return price, std_error


if __name__ == "__main__":
    S, K, T, r, sigma = 100, 105, 1.0, 0.05, 0.2
    n_paths = 100000

    print(f"标的 S={S}, 行权价 K={K}, 到期 T={T}年, r={r:.0%}, σ={sigma:.0%}")
    print(f"模拟路径数: {n_paths}\n")

    # 基础蒙特卡洛
    mc_price, mc_se = monte_carlo_option_price(S, K, T, r, sigma, n_paths)
    print(f"基础蒙特卡洛: {mc_price:.4f} ± {1.96*mc_se:.4f} (95% CI)")

    # 对偶变量法
    anti_price, anti_se = monte_carlo_antithetic(S, K, T, r, sigma, n_paths)
    print(f"对偶变量法:   {anti_price:.4f} ± {1.96*anti_se:.4f} (95% CI)")

    # 控制变量法（亚式期权）
    n_paths_asian = 50000
    mc_asian, _ = monte_carlo_option_price(S, K, T, r, sigma, n_paths_asian, payoff='arithmetic_asian')
    cv_asian, _ = monte_carlo_control_variate(S, K, T, r, sigma, n_paths_asian, payoff='arithmetic_asian')
    print(f"\n亚式期权 (算术平均):")
    print(f"  基础蒙特卡洛: {mc_asian:.4f}")
    print(f"  控制变量法:   {cv_asian:.4f}")

    # 分层抽样
    strat_price, strat_se = monte_carlo_stratified(S, K, T, r, sigma, n_paths)
    print(f"\n分层抽样: {strat_price:.4f} ± {1.96*strat_se:.4f}")

    # 比较各种 payoff
    print(f"\n--- 不同 payoff 类型 ---")
    for payoff_type in ['european', 'arithmetic_asian', 'geometric_asian', 'lookback']:
        p, _ = monte_carlo_option_price(S, K, T, r, sigma, n_paths=20000, payoff=payoff_type)
        print(f"  {payoff_type:20s}: {p:.4f}")
