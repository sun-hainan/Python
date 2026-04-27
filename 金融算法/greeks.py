# -*- coding: utf-8 -*-
"""
算法实现：金融算法 / greeks

本文件实现 greeks 相关的算法功能。
"""

import numpy as np
from scipy.stats import norm


def calculate_greeks(S, K, T, r, sigma, option_type='call'):
    """
    计算期权的所有 Greeks

    Parameters
    ----------
    S : float
        标的资产当前价格
    K : float
        行权价格
    T : float
        到期时间（年）
    r : float
        无风险利率
    sigma : float
        波动率
    option_type : str
        'call' 或 'put'

    Returns
    -------
    dict
        包含 price, delta, gamma, theta, vega, rho
    """
    # 处理到期情况
    if T <= 0:
        intrinsic = max(S - K, 0) if option_type == 'call' else max(K - S, 0)
        return {
            'price': intrinsic,
            'delta': 1.0 if option_type == 'call' and S > K else (0.0 if option_type == 'call' else -1.0),
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0
        }

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    # 标准正态分布的概率密度函数值
    phi = norm.pdf(d1)
    # 标准正态分布的累积分布函数
    Phi = norm.cdf(d1)
    Phi_neg = norm.cdf(-d1) if option_type == 'call' else norm.cdf(d1)
    neg_Phi_d2 = norm.cdf(-d2) if option_type == 'call' else norm.cdf(d2)

    # -------- Delta --------
    # 看涨期权 Delta = N(d1)，取值范围 [0, 1]
    # 看跌期权 Delta = N(d1) - 1 = -N(-d1)，取值范围 [-1, 0]
    if option_type == 'call':
        delta = Phi
    else:
        delta = Phi - 1

    # -------- Gamma --------
    # Gamma 对看涨和看跌期权相同，反映 Delta 变化的曲率
    # Gamma = φ(d1) / (S * σ * √T)
    gamma = phi / (S * sigma * np.sqrt(T))

    # -------- Theta --------
    # Theta 衡量时间流逝对期权价值的影响（每天损失的价值）
    # 看涨期权：Θ = -[S*φ(d1)*σ/(2√T)] - r*K*e^(-rT)*N(d2)
    # 看跌期权：Θ = -[S*φ(d1)*σ/(2√T)] + r*K*e^(-rT)*N(-d2)
    term1 = -S * phi * sigma / (2 * np.sqrt(T))
    if option_type == 'call':
        theta = (term1 - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
    else:
        theta = (term1 + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365

    # -------- Vega --------
    # Vega 衡量波动率变化对期权价格的影响
    # Vega = S * φ(d1) * √T，表示波动率增加 1% 时期权价格的变化
    vega = S * phi * np.sqrt(T) / 100

    # -------- Rho --------
    # Rho 衡量无风险利率变化对期权价格的影响
    # 看涨期权：ρ = K*T*e^(-rT)*N(d2)
    # 看跌期权：ρ = -K*T*e^(-rT)*N(-d2)
    if option_type == 'call':
        rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    else:
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100

    # -------- Price --------
    if option_type == 'call':
        price = S * Phi - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    return {
        'price': price,
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega,
        'rho': rho
    }


def calculate_greeks_with_dividend(S, K, T, r, sigma, q, option_type='call'):
    """
    考虑连续股息的 Greeks 计算
    """
    if T <= 0:
        intrinsic = max(S - K, 0) if option_type == 'call' else max(K - S, 0)
        return {
            'price': intrinsic,
            'delta': 1.0 if option_type == 'call' and S > K else (0.0 if option_type == 'call' else -1.0),
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0
        }

    d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    phi = norm.pdf(d1)
    Phi = norm.cdf(d1)

    if option_type == 'call':
        delta = np.exp(-q * T) * Phi
        price = S * np.exp(-q * T) * Phi - K * np.exp(-r * T) * norm.cdf(d2)
        rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    else:
        delta = np.exp(-q * T) * (Phi - 1)
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100

    gamma = np.exp(-q * T) * phi / (S * sigma * np.sqrt(T))
    theta_call = (-S * np.exp(-q * T) * phi * sigma / (2 * np.sqrt(T))
                  + q * S * np.exp(-q * T) * Phi
                  - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
    theta_put = (-S * np.exp(-q * T) * phi * sigma / (2 * np.sqrt(T))
                 - q * S * np.exp(-q * T) * norm.cdf(-d1)
                 + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
    theta = theta_call if option_type == 'call' else theta_put
    vega = S * np.exp(-q * T) * phi * np.sqrt(T) / 100

    return {
        'price': price,
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega,
        'rho': rho
    }


if __name__ == "__main__":
    S, K, T, r, sigma = 100, 105, 0.5, 0.05, 0.2

    print(f"标的 S={S}, 行权价 K={K}, 到期 T={T}年, r={r:.0%}, σ={sigma:.0%}\n")

    for opt_type in ['call', 'put']:
        greeks = calculate_greeks(S, K, T, r, sigma, opt_type)
        print(f"--- {opt_type.upper()} ---")
        print(f"  价格:  {greeks['price']:.4f}")
        print(f"  Delta: {greeks['delta']:.4f}")
        print(f"  Gamma: {greeks['gamma']:.4f}")
        print(f"  Theta: {greeks['theta']:.4f} (每天)")
        print(f"  Vega:  {greeks['vega']:.4f} (波动率±1%)")
        print(f"  Rho:   {greeks['rho']:.4f} (利率±1%)")
        print()

    # 敏感性分析：标的价格变化对 Delta 的影响
    print("--- Delta 敏感性分析 (S 变化) ---")
    prices = np.linspace(80, 120, 9)
    for p in prices:
        g = calculate_greeks(p, K, T, r, sigma, 'call')
        print(f"  S={p:6.1f} -> Delta={g['delta']:.4f}, Gamma={g['gamma']:.4f}")

    # 验证数值微分
    print("\n--- 数值微分验证 ---")
    h = 0.01
    g0 = calculate_greeks(S, K, T, r, sigma, 'call')
    g1 = calculate_greeks(S + h, K, T, r, sigma, 'call')
    num_delta = (g1['price'] - g0['price']) / h
    print(f"数值 Delta: {num_delta:.4f}, 解析 Delta: {g0['delta']:.4f}")
