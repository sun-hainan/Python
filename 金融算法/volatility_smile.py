# -*- coding: utf-8 -*-
"""
算法实现：金融算法 / volatility_smile

本文件实现 volatility_smile 相关的算法功能。
"""

import numpy as np
from scipy.optimize import minimize, curve_fit
from scipy.interpolate import interp1d


def SABR_volatility(F, K, T, alpha, beta, rho, nu):
    """
    SABR 隐含波动率近似公式
    适合波动率微笑建模

    Parameters
    ----------
    F : float
        远期价格
    K : float
        行权价
    T : float
        到期时间
    alpha : float
        初始波动率
    beta : float
        弹性参数 (0 <= beta <= 1)
    rho : float
        波动率-价格相关性
    nu : float
        波动率的波动率

    Returns
    -------
    float
        隐含波动率
    """
    # 避免数值问题
    if K <= 0 or F <= 0:
        return alpha

    FK = F * K
    logFK = np.log(F / K)
    FK_mid = np.sqrt(FK)

    # z 和 x(z)
    z = (nu / alpha) * FK_mid * logFK
    chi_z = np.sqrt(1 - 2 * rho * z + z**2)

    # 特殊情况：F ≈ K (ATM)
    if abs(F - K) < 1e-10:
        # ATM 近似
        V = alpha / (FK_mid ** (1 - beta)) * (1 + ((1 - beta)**2 / 24 * alpha**2 / (FK_mid ** (2 - 2*beta))
                + 0.25 * rho * beta * nu * alpha / (FK_mid ** (1 - beta))) * T)
        return V

    # 一般公式
    numerator = alpha / ((FK_mid ** (1 - beta)) * (1 + (1 - beta)**2 / 24 * logFK**2
                    + (1 - beta)**4 / 1920 * logFK**4))
    z_term = np.log((chi_z + z - rho) / (1 - rho))

    denominator = 1 + ((1 - beta)**2 / 24 * alpha**2 / (FK_mid ** (2 - 2*beta))
              + 0.25 * rho * beta * nu * alpha / (FK_mid ** (1 - beta))
              + (2 - 3 * rho**2) / 24 * nu**2) * T

    V = numerator * z_term / denominator

    return V


def fit_sabr_volatility(maturities, strikes, market_vols, F, initial_guess=None):
    """
    校准 SABR 模型参数
    最小化模型波动率与市场波动率的均方误差

    Parameters
    ----------
    maturities : array
        到期时间
    strikes : array
        行权价
    market_vols : 2D array
        市场隐含波动率
    F : float
        远期价格
    """
    if initial_guess is None:
        # 典型参数：alpha, beta, rho, nu
        initial_guess = [0.2, 0.5, -0.3, 0.3]

    def objective(params):
        alpha, beta, rho, nu = params
        total_error = 0
        n_points = 0

        for i, T in enumerate(maturities):
            for j, K in enumerate(strikes):
                try:
                    vol = SABR_volatility(F, K, T, alpha, beta, rho, nu)
                    total_error += (vol - market_vols[i, j]) ** 2
                    n_points += 1
                except:
                    pass

        return total_error / n_points if n_points > 0 else 1e10

    # 约束
    bounds = [(0.001, 2.0), (0.0, 0.999), (-0.999, 0.999), (0.001, 2.0)]

    result = minimize(objective, initial_guess, method='L-BFGS-B', bounds=bounds)

    return {
        'alpha': result.x[0],
        'beta': result.x[1],
        'rho': result.x[2],
        'nu': result.x[3],
        'mse': result.fun
    }


def local_volatility_from_smile(strikes, maturities, implied_vols, spot, r):
    """
    从波动率微笑提取局部波动率（简化版）
    使用 dupire 公式的离散近似

    局部波动率 σ²(L, t) = [∂C/∂T + r*K*∂C/∂K + q*C] / [0.5*K²*∂²C/∂K²]

    实际中需要插值和数值微分
    """
    n_K = len(strikes)
    n_T = len(maturities)

    local_vol = np.zeros((n_T, n_K))

    # 简化的局部波动率估计
    for i, T in enumerate(maturities):
        for j, K in enumerate(strikes):
            iv = implied_vols[i, j]

            # 局部波动率 ≈ 隐含波动率（简化）
            local_vol[i, j] = iv

    return local_vol


def volatility_smile_parametric(strikes, a=None, b=None, c=None, d=None):
    """
    参数化波动率微笑
    常用模型：SVI (Stochastic Volatility Inspired)

    SVI: w(k) = a + b*(rho*(k-m) + sqrt((k-m)² + s²))
    其中 k = ln(K/F)

    Parameters
    ----------
    a, b, rho, m, s : float
        SVI 参数
    """
    if a is None:
        # 默认参数
        a, b, rho, m, s = 0.04, 0.1, -0.5, 0, 0.5

    k = np.log(strikes)  # 简化的 log-moneyness

    w = a + b * (rho * (k - m) + np.sqrt((k - m)**2 + s**2))

    return np.sqrt(w)


def skew_and_smile_metrics(implied_vols, strikes, spot):
    """
    计算偏度和微笑相关的度量
    """
    # ATM 波动率
    atm_idx = np.argmin(np.abs(strikes - spot))
    atm_vol = implied_vols[atm_idx]

    # 25-delta skew
    # 需要插值找到 25-delta 对应的行权价和波动率
    # 这里简化：使用几个关键行权价

    # 10% OTM put 的波动率
    otm_put_strike = spot * 0.9
    if otm_put_strike in strikes:
        put_vol_90 = implied_vols[np.argwhere(strikes == otm_put_strike)[0, 0]]
    else:
        put_vol_90 = np.interp(otm_put_strike, strikes, implied_vols)

    # 10% OTM call 的波动率
    otm_call_strike = spot * 1.1
    if otm_call_strike in strikes:
        call_vol_110 = implied_vols[np.argwhere(strikes == otm_call_strike)[0, 0]]
    else:
        call_vol_110 = np.interp(otm_call_strike, strikes, implied_vols)

    # Skew
    put_skew = put_vol_90 - atm_vol
    call_skew = atm_vol - call_vol_110

    return {
        'atm_vol': atm_vol,
        'put_skew_90': put_skew,
        'call_skew_110': call_skew,
        'smile_slope': (call_vol_110 - put_vol_90) / (spot * 0.2)  # 近似 slope
    }


def interpolation_vol_surface(strikes, maturities, implied_vols, method='cubic'):
    """
    波动率曲面的插值
    用于填充规则网格或重采样

    Parameters
    ----------
    method : str
        'linear', 'cubic', 'spline'
    """
    from scipy.interpolate import griddata

    # 展平数据
    points = []
    for i, T in enumerate(maturities):
        for j, K in enumerate(strikes):
            points.append([T, K])

    points = np.array(points)
    values = implied_vols.flatten()

    # 插值函数
    def interp_func(T, K):
        return griddata(points, values, (T, K), method=method)

    return interp_func


if __name__ == "__main__":
    print("=" * 60)
    print("波动率微笑分析")
    print("=" * 60)

    F = 100  # 远期价格
    T = 1.0  # 1年

    # SABR 参数
    alpha = 0.2
    beta = 0.5
    rho = -0.4
    nu = 0.3

    # 计算不同行权价的隐含波动率
    strikes = np.array([70, 80, 85, 90, 95, 100, 105, 110, 115, 120, 130])
    vols = []

    print(f"\nSABR 模型隐含波动率 (T={T}年, F={F})")
    print(f"参数: α={alpha}, β={beta}, ρ={rho}, ν={nu}")
    print(f"\n{'行权价':>8} {'隐含波动率':>12}")
    print("-" * 22)

    for K in strikes:
        vol = SABR_volatility(F, K, T, alpha, beta, rho, nu)
        vols.append(vol)
        print(f"{K:>8.0f} {vol:>12.4%}")

    vols = np.array(vols)

    # 偏度和微笑度量
    print("\n--- 偏度和微笑分析 ---")
    metrics = skew_and_smile_metrics(vols, strikes, F)
    print(f"ATM 波动率: {metrics['atm_vol']:.4%}")
    print(f"10% OTM Put Skew: {metrics['put_skew_90']:.4%}")
    print(f"10% OTM Call Skew: {metrics['call_skew_110']:.4%}")

    # 波动率微笑可视化
    print("\n--- 波动率微笑形状 ---")
    moneyness = np.log(strikes / F)
    for k, v in zip(moneyness, vols):
        bar = '█' * int(v * 200)
        print(f"k={k:>6.3f} ({k*100:>5.1f}%): {v:.4%} {bar}")

    # 不同 rho 的影响
    print("\n--- 不同 ρ 的影响 ---")
    for rho_test in [-0.6, -0.3, 0.0, 0.3]:
        vols_test = [SABR_volatility(F, K, T, alpha, beta, rho_test, nu) for K in [80, 100, 120]]
        print(f"ρ = {rho_test:>5.1f}: K=80: {vols_test[0]:.4%}, K=100: {vols_test[1]:.4%}, K=120: {vols_test[2]:.4%}")
