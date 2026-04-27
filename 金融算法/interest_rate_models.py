# -*- coding: utf-8 -*-
"""
算法实现：金融算法 / interest_rate_models

本文件实现 interest_rate_models 相关的算法功能。
"""

import numpy as np
from scipy.optimize import brentq


def vasicek_zero_coupon(r, T, alpha, mu, sigma):
    """
    Vasicek 模型的零息债券价格

    瞬时利率过程：
    dr = α(μ - r)dt + σdW

    参数：
    - α: 均值回复速度
    - μ: 长期均值
    - σ: 波动率

    零息债券价格：
    P(t, T) = exp(A(τ) - B(τ) * r)
    其中 τ = T - t, B(τ) = (1 - exp(-ατ)) / α
    A(τ) = (B(τ) - τ)(α²μ - σ²/2) / α² - σ²B(τ)² / (4α)
    """
    if T <= 0:
        return 1.0

    # 对于零时刻定价，τ = T
    tau = T

    B = (1 - np.exp(-alpha * tau)) / alpha
    A = (B - tau) * (alpha**2 * mu - 0.5 * sigma**2) / alpha**2 - sigma**2 * B**2 / (4 * alpha)

    price = np.exp(A - B * r)

    return price


def vasicek_forward_rate(r, T, alpha, mu, sigma):
    """
    Vasicek 模型的瞬时远期利率
    f(t, T) = -∂lnP/∂T = B'(τ)*r - A'(τ)
    B'(τ) = exp(-ατ)
    A'(τ) = (σ²/α²)(1 - exp(-ατ)) - (αμ - σ²/2)(1 - exp(-ατ))/α
    """
    if T <= 0:
        return r

    tau = T
    exp_alpha_tau = np.exp(-alpha * tau)

    B_prime = exp_alpha_tau
    A_prime = (sigma**2 / alpha**2) * (1 - exp_alpha_tau) - (alpha * mu - 0.5 * sigma**2) * (1 - exp_alpha_tau) / alpha

    forward = B_prime * r - A_prime

    return forward


def cir_zero_coupon(r, T, kappa, theta, sigma):
    """
    Cox-Ingersoll-Ross (CIR) 模型的零息债券价格

    瞬时利率过程：
    dr = κ(θ - r)dt + σ√r dW

    CIR 确保 r >= 0（平方根过程）

    零息债券价格：
    P(t, T) = A(τ) * exp(-B(τ) * r)
    A(τ) = [2κθ e^(κτ)] / [(κ+γ)(e^(γτ) - 1) + 2γ]
    B(τ) = [2(e^(γτ) - 1)] / [(κ+γ)(e^(γτ) - 1) + 2γ]
    其中 γ = √(κ² + 2σ²)
    """
    if T <= 0:
        return 1.0

    tau = T
    gamma = np.sqrt(kappa**2 + 2 * sigma**2)

    exp_gamma_tau = np.exp(gamma * tau)

    B = 2 * (exp_gamma_tau - 1) / ((kappa + gamma) * (exp_gamma_tau - 1) + 2 * gamma)
    A = (2 * kappa * theta / (sigma**2)) * np.log(
        2 * gamma * np.exp(0.5 * (kappa + gamma) * tau) /
        ((kappa + gamma) * (exp_gamma_tau - 1) + 2 * gamma)
    )

    price = np.exp(A - B * r)

    return price


def cir_forward_rate(r, T, kappa, theta, sigma):
    """CIR 模型的瞬时远期利率"""
    if T <= 0:
        return r

    tau = T
    gamma = np.sqrt(kappa**2 + 2 * sigma**2)
    exp_gamma_tau = np.exp(gamma * tau)

    denominator = ((kappa + gamma) * (exp_gamma_tau - 1) + 2 * gamma)

    B_tau = 2 * (exp_gamma_tau - 1) / denominator

    # f(t, T) = r * B'(τ) + 条件均值调整
    forward = r * np.exp(-gamma * tau) + theta * (1 - np.exp(-gamma * tau))

    return forward


def hull_white_zero_coupon(r, T, a, sigma, B_t):
    """
    Hull-White 模型（扩展 Vasicek）

    dr = (θ(t) - ar)dt + σdW

    零息债券价格：
    P(t, T) = exp(A(t, T) - B(t, T) * r)
    B(t, T) = (1 - exp(-a(T-t))) / a
    A(t, T) = ...
    """
    if T <= 0:
        return 1.0

    tau = T
    B = (1 - np.exp(-a * tau)) / a

    # 简化：假设 θ(t) 使得模型与初始期限结构匹配
    # 实际需要拟合初始收益率曲线
    A = 0  # 简化

    price = np.exp(A - B * r)

    return price


def bond_option_price(put_price_S, S, T, r, sigma, K, option_type='put'):
    """
    债券期权的近似定价（使用权益期权框架）

    债券作为标的资产，行权价为债券面值

    实际中需要使用期限结构模型
    """
    if T <= 0:
        return max(K - S, 0) if option_type == 'put' else max(S - K, 0)

    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'call':
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    return price


def forward_rate_agreement(principal, rate, T, r):
    """
    远期利率协议 (FRA) 定价

    FRA 约定在未来 T 时刻开始、T+S 时刻结束的名义本金利率

    价值 = (固定利率 - 浮动利率) * 本金 * 时间 / (1 + 浮动利率 * 时间)
    """
    S = 0.25  # 假设 3 个月
    # 简化 FRA 定价
    forward_value = principal * (rate - r) * S / (1 + r * S)
    return forward_value


def swap_rate(tenors, discount_factors):
    """
    利率互换的公平互换率计算

    互换率 = Σ(D_i * Δ_i) / Σ(D_i * Δ_i)

    其中 D_i 是贴现因子，Δ_i 是天数比例
    """
    return 0.05  # 简化


def bootstrap_yield_curve(maturities, prices):
    """
    自举法从零息债券价格构建收益率曲线

    Parameters
    ----------
    maturities : list
        到期时间（年）
    prices : list
        零息债券价格
    """
    n = len(maturities)
    yields = np.zeros(n)

    for i in range(n):
        T = maturities[i]
        P = prices[i]

        if T == 0:
            yields[i] = 0
        else:
            # y = -ln(P) / T
            y = -np.log(P) / T
            yields[i] = y

    return yields


def Nelson_Siegel_yield(T, beta0, beta1, beta2, tau):
    """
    Nelson-Siegel 收益率曲线拟合

    收益率：
    y(T) = β0 + β1 * (1 - exp(-T/τ)) / (T/τ) + β2 * ((1 - exp(-T/τ)) / (T/τ) - exp(-T/τ))

    参数：
    - β0: 长期水平
    - β1: 短期斜率
    - β2: 曲率
    - τ: lambda，衰减速
    """
    if T == 0:
        return beta0 + beta1 + beta2 * 0  # 当 T→0 时，第三项为0

    lambda_t = T / tau
    exp_term = np.exp(-lambda_t)

    y = (beta0 +
         beta1 * (1 - exp_term) / lambda_t +
         beta2 * ((1 - exp_term) / lambda_t - exp_term))

    return y


def fit_Nelson_Siegel(maturities, yields):
    """
    拟合 Nelson-Siegel 参数
    """
    from scipy.optimize import minimize

    def objective(params):
        beta0, beta1, beta2, tau = params
        if tau <= 0:
            return 1e10
        predicted = [Nelson_Siegel_yield(T, beta0, beta1, beta2, tau) for T in maturities]
        return np.sum((np.array(predicted) - np.array(yields))**2)

    # 初始猜测
    init = [np.mean(yields), -0.01, 0.01, 2.0]

    result = minimize(objective, init, method='L-BFGS-B',
                     bounds=[(-1, 1), (-2, 2), (-2, 2), (0.1, 10)])

    return {
        'beta0': result.x[0],
        'beta1': result.x[1],
        'beta2': result.x[2],
        'tau': result.x[3]
    }


if __name__ == "__main__":
    print("=" * 60)
    print("利率期限结构模型")
    print("=" * 60)

    # Vasicek 模型
    r = 0.05  # 当前瞬时利率
    alpha = 0.1  # 均值回复速度
    mu = 0.06  # 长期均值
    sigma = 0.02  # 波动率

    print(f"\nVasicek 模型: r={r:.2%}, α={alpha}, μ={mu:.2%}, σ={sigma:.2%}")

    maturities = [0.5, 1, 2, 3, 5, 7, 10]

    print(f"\n{'期限':>8} {'零债价格':>12} {'零息利率':>12} {'远期利率':>12}")
    print("-" * 50)

    for T in maturities:
        price = vasicek_zero_coupon(r, T, alpha, mu, sigma)
        y = -np.log(price) / T
        f = vasicek_forward_rate(r, T, alpha, mu, sigma)
        print(f"{T:>8.1f} {price:>12.4f} {y:>12.4%} {f:>12.4%}")

    # CIR 模型
    print("\n--- CIR 模型 ---")
    kappa = 0.1
    theta = 0.06
    sigma_cir = 0.05

    print(f"CIR 模型: κ={kappa}, θ={theta:.2%}, σ={sigma_cir:.2%}")

    print(f"\n{'期限':>8} {'零债价格':>12} {'零息利率':>12}")
    print("-" * 35)

    for T in maturities:
        price = cir_zero_coupon(r, T, kappa, theta, sigma_cir)
        y = -np.log(price) / T
        print(f"{T:>8.1f} {price:>12.4f} {y:>12.4%}")

    # 自举法
    print("\n--- 自举法收益率曲线 ---")
    # 假设一些零息债券价格
    maturities_zb = [0.5, 1, 2, 3, 5]
    prices_zb = [0.98, 0.96, 0.92, 0.88, 0.82]

    yields = bootstrap_yield_curve(maturities_zb, prices_zb)

    for m, y in zip(maturities_zb, yields):
        print(f"  {m}年: {y:.4%}")

    # Nelson-Siegel
    print("\n--- Nelson-Siegel 拟合 ---")
    maturities_ns = [0.5, 1, 2, 3, 5, 7, 10]
    yields_ns = [0.03, 0.035, 0.04, 0.045, 0.05, 0.052, 0.055]

    ns_params = fit_Nelson_Siegel(maturities_ns, yields_ns)
    print(f"参数: β0={ns_params['beta0']:.4f}, β1={ns_params['beta1']:.4f}, "
          f"β2={ns_params['beta2']:.4f}, τ={ns_params['tau']:.4f}")

    print(f"\n{'期限':>8} {'实际':>10} {'拟合':>10}")
    print("-" * 30)
    for m, y in zip(maturities_ns, yields_ns):
        y_fit = Nelson_Siegel_yield(m, ns_params['beta0'], ns_params['beta1'],
                                   ns_params['beta2'], ns_params['tau'])
        print(f"{m:>8.1f} {y:>10.4%} {y_fit:>10.4%}")
