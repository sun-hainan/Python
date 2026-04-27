# -*- coding: utf-8 -*-
"""
算法实现：金融算法 / binomial_tree

本文件实现 binomial_tree 相关的算法功能。
"""

import numpy as np


def crr_binomial_tree(S, K, T, r, sigma, N=100, option_type='call'):
    """
    Cox-Ross-Rubinstein 二叉树模型
    使用风险中性概率构建树，参数选择确保收敛到 Black-Scholes

    CRR 参数：
    - u = exp(σ*√Δt)  上涨幅度
    - d = 1/u         下跌幅度
    - p = (exp(r*Δt) - d) / (u - d)  风险中性概率

    Parameters
    ----------
    N : int
        树的步数（步数越多越精确，但计算量越大）
    """
    dt = T / N  # 每步的时间间隔
    u = np.exp(sigma * np.sqrt(dt))  # 上涨因子
    d = 1 / u  # 下跌因子
    # 风险中性概率：在风险中性世界中，标的资产的期望增长率等于无风险利率
    p = (np.exp(r * dt) - d) / (u - d)
    discount = np.exp(-r * dt)  # 单步折现因子

    # 构建终端标的价格数组
    # 每个节点表示一种可能的标的价格路径
    # 终端价格：S * u^j * d^(N-j)，j 为上涨次数
    j = np.arange(N + 1)
    ST = S * (u ** j) * (d ** (N - j))

    # 计算终端期权 payoff
    if option_type == 'call':
        option_values = np.maximum(ST - K, 0)
    else:
        option_values = np.maximum(K - ST, 0)

    # 从终端向前折现，使用风险中性概率加权
    # 这是倒推法的核心：每个节点的期权价值 = 折现后的期望值
    for i in range(N - 1, -1, -1):
        option_values = discount * (p * option_values[:-1] + (1 - p) * option_values[1:])

        if option_type == 'american':
            # 美式期权：比较持有期权价值和立即行权价值
            # 在每个中间节点，标的价格为 S * u^j * d^(i-j)
            j_i = np.arange(i + 1)
            S_i = S * (u ** j_i) * (d ** (i - j_i))
            if option_type == 'call':
                exercise = np.maximum(S_i - K, 0)
            else:
                exercise = np.maximum(K - S_i, 0)
            option_values = np.maximum(option_values, exercise)

    return option_values[0]


def ej_binomial_tree(S, K, T, r, sigma, N=100, option_type='call'):
    """
    Jarrow-Rudd 二叉树模型（等概率模型）
    使用等概率 p = 0.5，通过调整 u 和 d 使期望收益为无风险利率

    EJ 参数：
    - u = exp((r - 0.5*σ²)*Δt + σ*√Δt)
    - d = exp((r - 0.5*σ²)*Δt - σ*√Δt)
    - p = 0.5
    """
    dt = T / N
    drift = (r - 0.5 * sigma ** 2) * dt  # 漂移项
    vol_term = sigma * np.sqrt(dt)  # 波动项

    u = np.exp(drift + vol_term)
    d = np.exp(drift - vol_term)
    p = 0.5  # 等概率
    discount = np.exp(-r * dt)

    # 终端价格
    j = np.arange(N + 1)
    ST = S * (u ** j) * (d ** (N - j))

    if option_type == 'call':
        option_values = np.maximum(ST - K, 0)
    else:
        option_values = np.maximum(K - ST, 0)

    for i in range(N - 1, -1, -1):
        option_values = discount * (p * option_values[:-1] + (1 - p) * option_values[1:])

    return option_values[0]


def american_option_crr(S, K, T, r, sigma, N=100, option_type='call'):
    """
    CRR 美式期权定价
    美式期权允许持有者在到期日前任何时间行权
    在每个节点需要比较：继续持有的折现期望值 vs 立即行权价值
    """
    dt = T / N
    u = np.exp(sigma * np.sqrt(dt))
    d = 1 / u
    p = (np.exp(r * dt) - d) / (u - d)
    discount = np.exp(-r * dt)

    # 构建完整的 N+1 x N+1 价格树（用于存储中间行权价值）
    # 这里使用压缩存储：每步存储 N+1-i 个节点
    j = np.arange(N + 1)
    ST = S * (u ** j) * (d ** (N - j))

    if option_type == 'call':
        option_values = np.maximum(ST - K, 0)
    else:
        option_values = np.maximum(K - ST, 0)

    # 逐层向前折现，同时检查是否需要提前行权
    for i in range(N - 1, -1, -1):
        # 折现：计算持有期权的价值
        option_values = discount * (p * option_values[:-1] + (1 - p) * option_values[1:])

        # 计算当前层的标的价格
        j_i = np.arange(i + 1)
        S_i = S * (u ** j_i) * (d ** (i - j_i))

        # 计算行权价值
        if option_type == 'call':
            exercise = np.maximum(S_i - K, 0)
        else:
            exercise = np.maximum(K - S_i, 0)

        # 美式期权取两者较大值
        option_values = np.maximum(option_values, exercise)

    return option_values[0]


def binomial_tree_with_volatility_surface(S, K, T, r, sigma_func, N=100):
    """
    变波动率二叉树：允许波动率随时间和标的价格变化
    sigma_func(t, S): 时间和价格依赖的波动率函数

    这可以用于：
    1. 本地波动率模型
    2. 随机波动率模型的近似
    """
    dt = T / N
    discount = np.exp(-r * dt)

    # 初始化终端价格
    j = np.arange(N + 1)
    u = np.exp(sigma_func(T, S * np.exp(sigma_func(T, S) * np.sqrt(dt))) * np.sqrt(dt))
    d = 1 / u
    ST = S * (u ** j) * (d ** (N - j))
    option_values = np.maximum(ST - K, 0)

    for i in range(N - 1, -1, -1):
        t = i * dt
        # 估计中间节点的波动率（需要插值）
        j_i = np.arange(i + 1)
        u_i = np.exp(sigma_func(t, S) * np.sqrt(dt))
        d_i = 1 / u_i
        S_i = S * (u_i ** j_i) * (d_i ** (i - j_i))

        p_i = (np.exp(r * dt) - d_i) / (u_i - d_i)

        option_values = discount * (p_i * option_values[:-1] + (1 - p_i) * option_values[1:])

    return option_values[0]


if __name__ == "__main__":
    S, K, T, r, sigma = 100, 105, 1.0, 0.05, 0.2

    print(f"标的 S={S}, 行权价 K={K}, 到期 T={T}年, r={r:.0%}, σ={sigma:.0%}\n")

    # 欧式期权：比较 CRR、EJ 与 Black-Scholes
    from math import sqrt, exp, log, fabs

    def bs_price(S, K, T, r, sigma):
        d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)
        from scipy.stats import norm
        return S * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)

    bs = bs_price(S, K, T, r, sigma)
    print(f"Black-Scholes 参考价格: {bs:.4f}")
    print(f"CRR (N=100):  {crr_binomial_tree(S, K, T, r, sigma, N=100):.4f}")
    print(f"CRR (N=500):  {crr_binomial_tree(S, K, T, r, sigma, N=500):.4f}")
    print(f"EJ  (N=100):  {ej_binomial_tree(S, K, T, r, sigma, N=100):.4f}")
    print(f"EJ  (N=500):  {ej_binomial_tree(S, K, T, r, sigma, N=500):.4f}")

    # 美式期权
    print(f"\n美式看跌期权:")
    american_put = american_option_crr(S, K, T, r, sigma, N=200, option_type='put')
    print(f"  CRR 美式看跌: {american_put:.4f}")

    # 收敛性分析
    print(f"\n--- 收敛性分析 (CRR vs BS) ---")
    for N in [10, 50, 100, 200, 500, 1000]:
        price = crr_binomial_tree(S, K, T, r, sigma, N=N)
        print(f"  N={N:4d}: {price:.6f}  误差: {abs(price - bs):.6f}")
