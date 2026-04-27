# -*- coding: utf-8 -*-
"""
算法实现：金融算法 / exotic_options

本文件实现 exotic_options 相关的算法功能。
"""

import numpy as np
from scipy.stats import norm


def geometric_asian_option(S, K, T, r, sigma, q=0, option_type='call'):
    """
    几何平均亚式期权（有解析解）

    几何平均 S_G = (Π S_i)^(1/n)
    ln(S_G) ~ Normal，得解析定价公式
    """
    n_steps = 252
    dt = T / n_steps

    # 几何平均的等效参数
    # 等效波动率 σ_G² = σ²/3 * (n+1)(2n+1) / (6n²)
    # 简化为 σ_G = σ / sqrt(3)
    sigma_G = sigma / np.sqrt(3)

    # 等效股息收益率（用于调整）
    # q_G = 0.5 * (r + q - σ²/6)

    d1 = (np.log(S / K) + (r + 0.5 * sigma_G**2) * T) / (sigma_G * np.sqrt(T))
    d2 = d1 - sigma_G * np.sqrt(T)

    if option_type == 'call':
        price = S * np.exp((r - q) * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp((r - q) * T) * norm.cdf(-d1)

    return price


def arithmetic_asian_option_mc(S, K, T, r, sigma, n_paths=100000, n_steps=252, option_type='call'):
    """
    算术平均亚式期权（蒙特卡洛）
    算术平均无解析解
    """
    dt = T / n_steps
    discount = np.exp(-r * T)

    # 生成价格路径
    Z = np.random.standard_normal((n_paths, n_steps))
    drift = (r - 0.5 * sigma**2) * dt
    diffusion = sigma * np.sqrt(dt) * Z

    log_returns = np.cumsum(drift + diffusion, axis=1)
    prices = S * np.exp(log_returns)

    # 算术平均
    avg_prices = np.mean(prices, axis=1)

    if option_type == 'call':
        payoffs = np.maximum(avg_prices - K, 0)
    else:
        payoffs = np.maximum(K - avg_prices, 0)

    price = discount * np.mean(payoffs)
    std_error = discount * np.std(payoffs) / np.sqrt(n_paths)

    return price, std_error


def barrier_option_price(S, K, T, r, sigma, barrier, option_type='call',
                         barrier_type='up-and-out', rebate=0):
    """
    障碍期权定价（解析近似）

    障碍类型：
    - up-and-out: 标的价格上涨触及障碍则失效
    - down-and-out: 下跌触及障碍则失效
    - up-and-in: 上涨触及障碍才生效
    - down-and-in: 下跌触及障碍才生效

    使用反射原理和镜像法
    """
    # 简化的闭式近似（对于连续障碍）
    # 完整的解析解需要复杂的 special functions

    if S <= barrier and barrier_type == 'down-and-out':
        return rebate if rebate else 0
    if S >= barrier and barrier_type == 'up-and-out':
        return rebate if rebate else 0

    # 简化：使用二叉树或蒙特卡洛
    return np.nan


def lookback_option_price(S, K, T, r, sigma, option_type='floating_strike'):
    """
    回望期权定价

    浮动行权价回望：
    - 看涨：max(S_T - S_min, 0) = S_T - S_min
    - 看跌：max(S_max - S_T, 0)

    固定行权价回望：
    - 有解析解（类似亚式期权）
    """
    if option_type == 'floating_strike_call':
        # 浮动行权价看涨
        # 价格 = S * N(d1) - S_min * e^{-rT} * N(d1 - σ√T)
        # 简化：使用 MC
        pass

    # 简化版本：使用数值方法
    return np.nan


def binary_option_price(S, K, T, r, sigma, option_type='cash_or_nothing'):
    """
    二元期权（Binary / Digital Options）

    类型：
    - Cash-or-nothing: 到期若 ATM 则获固定金额 C
    - Asset-or-nothing: 到期若 ITM 则获得标的资产

    Parameters
    ----------
    option_type : str
        'cash_or_nothing': 现金或无
        'asset_or_nothing': 资产或无
        'one_touch': 单触型（有效期内触价即付）
    """
    d2 = (np.log(S / K) + (r - 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))

    if option_type == 'cash_or_nothing':
        # 支付固定金额 C 若 S_T > K
        C = 1  # 标准化
        price = C * np.exp(-r * T) * norm.cdf(d2)
    elif option_type == 'asset_or_nothing':
        # 支付 S_T 若 S_T > K
        price = S * np.exp(-r * T) * norm.cdf(d2) * np.exp(0.5 * sigma**2 * T)
    elif option_type == 'one_touch':
        # 有效期内任何时间触价
        # 近似：使用 Black-Scholes 框架
        # 单触期权的解析解需要 special functions
        # 简化：使用 MC
        pass

    return price


def forward_start_option_price(S, T1, T2, r, sigma, K=None):
    """
    起步期权 (Forward Start Options)
    在 T1 时刻以当时的标的价格为行权价的期权
    到期 T2

    特点：
    - 行权价在 T1 时刻才确定
    - 常见的路径依赖
    """
    # T1 到 T2 的有效剩余时间
    tau = T2 - T1

    # 起步期权的波动率
    # 由于起步价格是随机的，整体波动率更高
    sigma_eff = sigma * np.sqrt((2*T2 - T1) / (2*T2)) if T1 > 0 else sigma

    # 简化的定价
    # 假设起步价格等于当前价格
    price = 0  # 需要更多参数

    return price


def compound_option_price(S, K1, K2, T1, T2, r, sigma, option_type='call_on_call'):
    """
    复合期权 (Compound Options)
    以期权为标的的期权

    类型：
    - call on call
    - call on put
    - put on call
    - put on put

    有解析解（Geske 模型）
    """
    # Geske 公式
    # 需要迭代求解两个 d 值

    # 简化的二叉树方法
    return np.nan


def range_option_price(S, r, T, sigma, period_days=30):
    """
    区间期权 (Range Options)
    支付取决于标的价格在特定期间内的最高和最低价

    例如：max(daily_high - daily_low)
    """
    n_periods = int(T * 252 / period_days)

    # 简化的 MC
    return np.nan


def shout_option_price(S, K, T, r, sigma, option_type='put'):
    """
    喊价期权 (Shout Options)
    持有人可以在到期前任何时间"喊话"锁定最小收益

    喊话后，期权变为：
    - 固定部分：锁定当时的内在价值
    - 剩余部分：到期前时间的价值
    """
    # 简化：喊价一次，在到期前
    # 喊价后的价值 ≈ 内在价值 + 部分时间价值

    # 使用 MC
    return np.nan


if __name__ == "__main__":
    print("=" * 60)
    print("奇异期权定价示例")
    print("=" * 60)

    S = 100
    K = 100
    T = 1.0
    r = 0.05
    sigma = 0.2

    # 亚式期权
    print("\n--- 几何平均亚式期权 ---")
    geo_call = geometric_asian_option(S, K, T, r, sigma, option_type='call')
    geo_put = geometric_asian_option(S, K, T, r, sigma, option_type='put')
    print(f"几何平均亚式看涨: {geo_call:.4f}")
    print(f"几何平均亚式看跌: {geo_put:.4f}")

    print("\n--- 算术平均亚式期权 (MC) ---")
    arith_call, se = arithmetic_asian_option_mc(S, K, T, r, sigma, n_paths=50000, option_type='call')
    print(f"算术平均亚式看涨: {arith_call:.4f} ± {1.96*se:.4f}")

    # 二元期权
    print("\n--- 二元期权 ---")
    cash_or_nothing = binary_option_price(S, K, T, r, sigma, 'cash_or_nothing')
    asset_or_nothing = binary_option_price(S, K, T, r, sigma, 'asset_or_nothing')
    print(f"Cash-or-nothing (ATM): {cash_or_nothing:.4f}")
    print(f"Asset-or-nothing (ATM): {asset_or_nothing:.4f}")

    # 与标准期权比较
    d2 = (np.log(S/K) + (r - 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    vanilla_call = S * norm.cdf(d2 + sigma*np.sqrt(T)) - K * np.exp(-r*T) * norm.cdf(d2)
    print(f"\n标准欧式看涨对比: {vanilla_call:.4f}")

    # 不同期权类型的比较
    print("\n--- 期权类型比较 (ATM) ---")
    strikes = [90, 95, 100, 105, 110]
    print(f"{'行权价':>8} {'Vanilla':>10} {'Cash-or-N':>10} {'Asset-or-N':>10}")
    print("-" * 42)
    for K in strikes:
        d2 = (np.log(S/K) + (r - 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        vc = S * norm.cdf(d2 + sigma*np.sqrt(T)) - K * np.exp(-r*T) * norm.cdf(d2)
        con = binary_option_price(S, K, T, r, sigma, 'cash_or_nothing')
        aon = binary_option_price(S, K, T, r, sigma, 'asset_or_nothing')
        print(f"{K:>8.0f} {vc:>10.4f} {con:>10.4f} {aon:>10.4f}")
