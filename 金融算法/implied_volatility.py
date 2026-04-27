# -*- coding: utf-8 -*-
"""
算法实现：金融算法 / implied_volatility

本文件实现 implied_volatility 相关的算法功能。
"""

import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq


def black_scholes_price(S, K, T, r, sigma, option_type='call'):
    """Black-Scholes 期权定价"""
    if T <= 0:
        return max(S - K, 0) if option_type == 'call' else max(K - S, 0)

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'call':
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def vega(S, K, T, r, sigma):
    """Vega：期权价格对波动率的导数
    dC/dσ = S * φ(d1) * √T

    牛顿法需要 Vega 作为导数
    """
    if T <= 0:
        return 0

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    phi = norm.pdf(d1)

    return S * phi * np.sqrt(T)


def implied_vol_newton(market_price, S, K, T, r, option_type='call',
                       sigma0=0.2, tol=1e-6, max_iter=100):
    """
    牛顿法求解隐含波动率

    迭代公式：
    σ_{n+1} = σ_n - f(σ_n) / f'(σ_n)
           = σ_n - (BS(σ_n) - C) / Vega(σ_n)

    优点：收敛快（二阶收敛）
    缺点：可能不收敛（取决于初值）

    Parameters
    ----------
    market_price : float
        期权市场价格
    sigma0 : float
        初始猜测
    tol : float
        收敛容差
    max_iter : int
        最大迭代次数

    Returns
    -------
    float
        隐含波动率
    """
    sigma = sigma0

    for i in range(max_iter):
        # 计算 BS 价格
        bs_price = black_scholes_price(S, K, T, r, sigma, option_type)

        # 计算函数值
        f = bs_price - market_price

        # 计算导数 (Vega)
        v = vega(S, K, T, r, sigma)

        if abs(v) < 1e-10:
            # Vega 太小，换方法
            break

        # 迭代
        sigma_new = sigma - f / v

        # 防止负波动率
        sigma_new = max(sigma_new, 0.001)

        # 检查收敛
        if abs(sigma_new - sigma) < tol:
            return sigma_new

        sigma = sigma_new

    # 牛顿法不收敛，返回 NaN
    return np.nan


def implied_vol_bisection(market_price, S, K, T, r, option_type='call',
                          sigma_low=0.001, sigma_high=5.0, tol=1e-6, max_iter=100):
    """
    二分法求解隐含波动率

    思想：在 [sigma_low, sigma_high] 区间内二分查找

    优点：稳定，保证收敛
    缺点：收敛较慢（线性收敛）
    """
    # 检查边界
    price_low = black_scholes_price(S, K, T, r, sigma_low, option_type)
    price_high = black_scholes_price(S, K, T, r, sigma_high, option_type)

    # 确保区间内有解
    if (price_low - market_price) * (price_high - market_price) > 0:
        # 边界价格同侧，可能无解或需要扩大范围
        # 尝试扩大范围
        if price_low > market_price:
            # 价格太低，波动率太低
            return np.nan
        else:
            return np.nan

    for i in range(max_iter):
        sigma_mid = (sigma_low + sigma_high) / 2
        price_mid = black_scholes_price(S, K, T, r, sigma_mid, option_type)

        if abs(sigma_high - sigma_low) < tol:
            return sigma_mid

        if (price_mid - market_price) * (price_low - market_price) > 0:
            sigma_low = sigma_mid
        else:
            sigma_high = sigma_mid

    return sigma_mid


def implied_vol_brent(market_price, S, K, T, r, option_type='call',
                      sigma_low=0.001, sigma_high=5.0, tol=1e-8):
    """
    Brent 方法求解隐含波动率

    Brent 方法结合了二分法的稳定性和牛顿法的速度
    使用 scipy.optimize.brentq
    """
    def objective(sigma):
        return black_scholes_price(S, K, T, r, sigma, option_type) - market_price

    try:
        iv = brentq(objective, sigma_low, sigma_high, xtol=tol)
        return iv
    except ValueError:
        # 无解
        return np.nan


def implied_vol_approx(market_price, S, K, T, r, option_type='call'):
    """
    隐含波动率的解析近似（Li-Model）
    用于快速估计初值

    对于平价期权 (ATM, S=K)，有近似：
    σ ≈ sqrt(2π/T) * (C / S)

    更一般的近似：
    σ ≈ (C - C_intrinsic) / (S * sqrt(T) * N'(d1))
    """
    intrinsic = max(S - K, 0) if option_type == 'call' else max(K - S, 0)
    time_value = market_price - intrinsic

    if time_value <= 0:
        return 0.0

    # ATM 近似
    if abs(S - K) / K < 0.01:
        # 平价期权
        iv_approx = np.sqrt(2 * np.pi / T) * time_value / S
        return iv_approx

    # 一般情况：用数值方法
    return np.nan


def implied_vol_surface(S, strikes, maturities, market_prices, r):
    """
    计算隐含波动率曲面
    返回矩阵形式

    Parameters
    ----------
    S : float
        标的价格
    strikes : list
        行权价序列
    maturities : list
        到期时间序列
    market_prices : 2D array
        市场报价矩阵 (len(maturities) x len(strikes))
    r : float
        无风险利率

    Returns
    -------
    np.ndarray
        隐含波动率矩阵
    """
    n_maturities = len(maturities)
    n_strikes = len(strikes)

    iv_surface = np.zeros((n_maturities, n_strikes))

    for i, T in enumerate(maturities):
        for j, K in enumerate(strikes):
            price = market_prices[i, j]

            # 判断期权类型
            if S > K:
                option_type = 'call'
            else:
                option_type = 'put'

            # 尝试牛顿法，失败则用 Brent
            iv = implied_vol_newton(price, S, K, T, r, option_type)
            if np.isnan(iv):
                iv = implied_vol_brent(price, S, K, T, r, option_type)

            iv_surface[i, j] = iv

    return iv_surface


def iv_heston_calibration(market_iv, S, K, T, r, initial_params=None):
    """
    Heston 模型参数校准（简化版）
    实际中需要使用优化算法如 Levenberg-Marquardt

    这里仅演示用 Newton 迭代校准单个波动率参数
    """
    if initial_params is None:
        initial_params = {'v0': 0.04, 'kappa': 2.0, 'theta': 0.04,
                         'sigma': 0.3, 'rho': -0.5}

    # Heston 模型需要数值积分或傅里叶变换
    # 这里简化为返回输入参数
    return initial_params


if __name__ == "__main__":
    print("=" * 60)
    print("隐含波动率求解")
    print("=" * 60)

    # 参数
    S = 100  # 标的价格
    K = 100  # 平价行权价
    T = 0.5  # 6个月
    r = 0.05 # 无风险利率
    sigma_true = 0.2  # 真实波动率

    # 计算理论价格
    market_price = black_scholes_price(S, K, T, r, sigma_true)
    print(f"\n标的 S={S}, 行权价 K={K}, 到期 T={T}年")
    print(f"真实波动率 σ={sigma_true:.0%}")
    print(f"期权市场价格: {market_price:.4f}")

    # 求解隐含波动率
    print("\n--- 隐含波动率求解 ---")

    iv_newton = implied_vol_newton(market_price, S, K, T, r)
    iv_bisect = implied_vol_bisection(market_price, S, K, T, r)
    iv_brent = implied_vol_brent(market_price, S, K, T, r)

    print(f"牛顿法:   {iv_newton:.6f} (误差: {abs(iv_newton - sigma_true):.2e})")
    print(f"二分法:   {iv_bisect:.6f} (误差: {abs(iv_bisect - sigma_true):.2e})")
    print(f"Brent法:  {iv_brent:.6f} (误差: {abs(iv_brent - sigma_true):.2e})")

    # 不同行权价的隐含波动率
    print("\n--- 波动率微笑 ---")
    strikes = np.array([80, 85, 90, 95, 100, 105, 110, 115, 120])
    ivs = []

    for K in strikes:
        price = black_scholes_price(S, K, T, r, sigma_true)
        option_type = 'call' if S > K else 'put'
        iv = implied_vol_newton(price, S, K, T, r, option_type)
        ivs.append(iv)

    print(f"{'行权价':>8} {'隐含波动率':>12}")
    print("-" * 22)
    for K, iv in zip(strikes, ivs):
        print(f"{K:>8.0f} {iv:>12.4%}")

    # 不同到期日的隐含波动率
    print("\n--- 波动率期限结构 ---")
    maturities = np.array([0.1, 0.25, 0.5, 1.0, 2.0])
    K = 100  # ATM

    print(f"{'到期时间':>8} {'隐含波动率':>12}")
    print("-" * 22)
    for T in maturities:
        price = black_scholes_price(S, K, T, r, sigma_true)
        iv = implied_vol_newton(price, S, K, T, r)
        print(f"{T:>8.2f} {iv:>12.4%}")

    # 收敛性分析
    print("\n--- 牛顿法收敛性 ---")
    # 用错误的价格测试
    wrong_price = market_price * 1.1

    sigma = 0.2  # 初值
    print(f"{'迭代':>4} {'σ':>12} {'价格误差':>12}")
    print("-" * 30)

    for i in range(6):
        bs_price = black_scholes_price(S, K, T, r, sigma)
        f = bs_price - wrong_price
        v = vega(S, K, T, r, sigma)
        sigma_new = sigma - f / v
        print(f"{i+1:>4} {sigma:>12.6f} {f:>12.6f}")
        sigma = max(sigma_new, 0.001)

    print(f"最终隐含波动率: {sigma:.6f}")
