# -*- coding: utf-8 -*-
"""
算法实现：金融算法 / delta_gamma_hedge

本文件实现 delta_gamma_hedge 相关的算法功能。
"""

import numpy as np
from scipy.stats import norm


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


def calculate_greeks(S, K, T, r, sigma, option_type='call'):
    """计算 Greeks"""
    if T <= 0:
        return {'delta': 1.0 if option_type == 'call' and S > K else (0.0 if option_type == 'call' else -1.0),
                'gamma': 0.0, 'vega': 0.0, 'theta': 0.0}

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    phi = norm.pdf(d1)
    Phi = norm.cdf(d1)

    delta = Phi if option_type == 'call' else Phi - 1
    gamma = phi / (S * sigma * np.sqrt(T))
    vega = S * phi * np.sqrt(T) / 100
    theta = (-S * phi * sigma / (2 * np.sqrt(T))
             - r * K * np.exp(-r * T) * (norm.cdf(d2) if option_type == 'call' else norm.cdf(-d2))) / 365

    return {'delta': delta, 'gamma': gamma, 'vega': vega, 'theta': theta}


def delta_hedge(portfolio_value, spot_price, options, target_delta=0):
    """
    Delta 对冲：调整标的资产或期权头寸使组合 Delta 为目标值

    Parameters
    ----------
    portfolio_value : float
        组合总价值
    spot_price : float
        当前标的价格
    options : list of dict
        现有期权头寸 [{'type': 'call', 'K': 100, 'T': 0.5, 'r': 0.05, 'sigma': 0.2, 'quantity': 10}]
    target_delta : float
        目标 Delta（0 表示 Delta 中性）

    Returns
    -------
    dict
        对冲建议
    """
    # 计算现有期权的组合 Delta
    total_delta = 0
    for opt in options:
        greeks = calculate_greeks(spot_price, opt['K'], opt['T'], opt['r'], opt['sigma'], opt['type'])
        # 期权的 Delta = N(d1) * 合约乘数 * 数量
        # 简化：假设每份期权对应 1 单位标的
        position_delta = greeks['delta'] * opt.get('quantity', 1)
        total_delta += position_delta

    # 需要添加的标的资产数量以达到目标 Delta
    # 标的资产的 Delta = 1（每持有一股，Delta = 1）
    shares_to_trade = target_delta - total_delta

    # 或者用期权对冲（当无法交易标的时，如个股期权）
    # 需要找到期权 D 使：D1*S1 + D2*S2 = target_delta

    return {
        'current_delta': total_delta,
        'target_delta': target_delta,
        'shares_to_trade': shares_to_trade,
        'action': 'BUY' if shares_to_trade > 0 else 'SELL',
        'shares': abs(shares_to_trade)
    }


def gamma_neutral_hedge(spot_price, options, available_strikes, available_sigmas, T, r):
    """
    Gamma 中性对冲：在 Delta 中性基础上进一步消除 Gamma 风险

    思路：
    - 持有期权 A（有正 Gamma）和期权 B（有负 Gamma）
    - 通过调整数量使组合 Gamma = 0

    实际中，看涨期权 Gamma > 0（做多 Gamma）
    深度实值和深度虚值期权的 Gamma 较小，平值期权 Gamma 最大
    """
    # 找到两个不同行权价的期权来构建 Gamma 中性组合
    # 这里简化处理，假设可以用标的对冲（但标的 Gamma = 0）

    # 对于一个期权组合，Gamma 中性需要：
    # Σ(Γ_i * N_i) + Γ_underlying * N_underlying = 0
    # 标的资产的 Gamma = 0（股票的 Gamma 近似为 0）

    # 所以需要加入期权来对冲 Gamma
    # 选择一个 ATM 期权作为对冲工具

    # 找最近的 ATM 行权价
    atm_strike = spot_price

    # 计算现有组合的 Gamma
    total_gamma = 0
    for opt in options:
        greeks = calculate_greeks(spot_price, opt['K'], opt['T'], opt['r'], opt['sigma'], opt['type'])
        total_gamma += greeks['gamma'] * opt.get('quantity', 1)

    # 如果组合 Gamma > 0，需要卖出期权来对冲（期权空头 Gamma < 0）
    # 如果组合 Gamma < 0，需要买入期权来对冲

    # 选择对冲期权：ATM 附近、剩余期限相近
    hedge_K = atm_strike
    hedge_sigma = available_sigmas.get(hedge_K, 0.2) if isinstance(available_sigmas, dict) else 0.2

    greeks_hedge = calculate_greeks(spot_price, hedge_K, T, r, hedge_sigma, 'call')
    gamma_hedge_option = greeks_hedge['gamma']

    # 需要的对冲期权数量
    if abs(gamma_hedge_option) > 1e-10:
        n_hedge = -total_gamma / gamma_hedge_option
    else:
        n_hedge = 0

    return {
        'current_gamma': total_gamma,
        'hedge_strike': hedge_K,
        'hedge_quantity': n_hedge,
        'action': 'BUY' if n_hedge > 0 else 'SELL',
        'hedge_greeks': greeks_hedge
    }


def vega_hedge(spot_price, options, available_strikes, available_sigmas, T, r):
    """
    Vega 中性对冲：使组合对波动率变化免疫

    波动率微笑/偏斜使得不同行权价的期权有不同的隐含波动率
    可以用不同 Vega 的期权组合来对冲
    """
    total_vega = 0
    for opt in options:
        greeks = calculate_greeks(spot_price, opt['K'], opt['T'], opt['r'], opt['sigma'], opt['type'])
        total_vega += greeks['vega'] * opt.get('quantity', 1)

    # 选择 Vega 对冲期权
    # 通常用不同期限的期权来对冲期限结构的风险
    # 这里简化：用 ATM 期权
    atm_strike = spot_price

    hedge_K = atm_strike
    hedge_sigma = available_sigmas.get(hedge_K, 0.2) if isinstance(available_sigmas, dict) else 0.2
    greeks_hedge = calculate_greeks(spot_price, hedge_K, T, r, hedge_sigma, 'call')
    vega_hedge_option = greeks_hedge['vega']

    if abs(vega_hedge_option) > 1e-10:
        n_hedge = -total_vega / vega_hedge_option
    else:
        n_hedge = 0

    return {
        'current_vega': total_vega,
        'hedge_strike': hedge_K,
        'hedge_quantity': n_hedge,
        'action': 'BUY' if n_hedge > 0 else 'SELL',
        'hedge_greeks': greeks_hedge
    }


def delta_gamma_hedge(spot_price, options, spot_hedge_ratio=None):
    """
    Delta-Gamma 同时对冲
    同时使用标的资产（Delta = 1, Gamma = 0）和期权来对冲

    方程组：
    Δ_total + Δ_stock * N_stock + Δ_hedge * N_hedge = 0  (Delta 中性)
    Γ_total + Γ_hedge * N_hedge = 0  (Gamma 中性)

    求解：
    N_hedge = -Γ_total / Γ_hedge
    N_stock = -(Δ_total + Δ_hedge * N_hedge)
    """
    total_delta = 0
    total_gamma = 0

    for opt in options:
        greeks = calculate_greeks(spot_price, opt['K'], opt['T'], opt['r'], opt['sigma'], opt['type'])
        q = opt.get('quantity', 1)
        total_delta += greeks['delta'] * q
        total_gamma += greeks['gamma'] * q

    # 选择一个期权作为 Gamma 对冲工具
    # 假设用 ATM call
    atm_strike = spot_price
    atm_sigma = 0.2  # 简化
    greeks_atm = calculate_greeks(spot_price, atm_strike, 0.25, 0.05, atm_sigma, 'call')

    gamma_hedge = greeks_atm['gamma']
    delta_hedge = greeks_atm['delta']

    # 计算对冲数量
    n_hedge = -total_gamma / gamma_hedge if abs(gamma_hedge) > 1e-10 else 0
    # 标的资产数量
    n_stock = -(total_delta + delta_hedge * n_hedge)

    return {
        'current_delta': total_delta,
        'current_gamma': total_gamma,
        'stock_shares': n_stock,
        'stock_action': 'BUY' if n_stock > 0 else 'SELL',
        'hedge_options': [{'strike': atm_strike, 'quantity': n_hedge,
                          'action': 'BUY' if n_hedge > 0 else 'SELL'}],
        'resulting_delta': total_delta + n_stock + delta_hedge * n_hedge,
        'resulting_gamma': total_gamma + gamma_hedge * n_hedge
    }


def portfolio_greeks_analysis(spot_price, r, options):
    """
    分析期权组合的 Greeks 暴露
    输出每个希腊字母的总暴露
    """
    result = {'delta': 0, 'gamma': 0, 'vega': 0, 'theta': 0, 'details': []}

    for i, opt in enumerate(options):
        greeks = calculate_greeks(spot_price, opt['K'], opt['T'], opt['r'], opt['sigma'], opt['type'])
        q = opt.get('quantity', 1)

        result['delta'] += greeks['delta'] * q
        result['gamma'] += greeks['gamma'] * q
        result['vega'] += greeks['vega'] * q
        result['theta'] += greeks['theta'] * q

        result['details'].append({
            'option': f"Call K={opt['K']}" if opt['type'] == 'call' else f"Put K={opt['K']}",
            'quantity': q,
            'delta': greeks['delta'] * q,
            'gamma': greeks['gamma'] * q,
            'vega': greeks['vega'] * q,
            'theta': greeks['theta'] * q
        })

    return result


if __name__ == "__main__":
    S = 100  # 标的价格
    r = 0.05  # 无风险利率
    T = 0.5  # 6个月

    # 现有期权组合
    options = [
        {'type': 'call', 'K': 95, 'T': 0.5, 'r': 0.05, 'sigma': 0.2, 'quantity': 20},
        {'type': 'call', 'K': 100, 'T': 0.5, 'r': 0.05, 'sigma': 0.2, 'quantity': -10},
        {'type': 'put', 'K': 105, 'T': 0.5, 'r': 0.05, 'sigma': 0.25, 'quantity': 15},
    ]

    print(f"标的价格 S = {S}, 无风险利率 r = {r:.0%}, 到期 T = {T}年\n")
    print("="*60)

    # Greeks 分析
    print("--- 期权组合 Greeks 分析 ---")
    analysis = portfolio_greeks_analysis(S, r, options)
    print(f"总 Delta: {analysis['delta']:.4f}")
    print(f"总 Gamma: {analysis['gamma']:.6f}")
    print(f"总 Vega:  {analysis['vega']:.4f} (波动率±1%)")
    print(f"总 Theta: {analysis['theta']:.4f} (每天)")

    print("\n各期权明细:")
    for detail in analysis['details']:
        print(f"  {detail['option']:15s} Q={detail['quantity']:4d}: "
              f"Δ={detail['delta']:7.4f} Γ={detail['gamma']:8.6f} ν={detail['vega']:6.4f}")

    # Delta 对冲
    print("\n--- Delta 对冲建议 ---")
    hedge = delta_hedge(100000, S, options, target_delta=0)
    print(f"当前 Delta: {hedge['current_delta']:.4f}")
    print(f"目标 Delta: {hedge['target_delta']:.4f}")
    print(f"操作: {hedge['action']} {hedge['shares']:.2f} 股股票")

    # Delta-Gamma 对冲
    print("\n--- Delta-Gamma 对冲建议 ---")
    dg_hedge = delta_gamma_hedge(S, options)
    print(f"当前 Delta: {dg_hedge['current_delta']:.4f}")
    print(f"当前 Gamma: {dg_hedge['current_gamma']:.6f}")
    print(f"股票操作: {dg_hedge['stock_action']} {abs(dg_hedge['stock_shares']):.2f} 股")
    for h in dg_hedge['hedge_options']:
        print(f"期权操作: {h['action']} {abs(h['quantity']):.2f} 份 K={h['strike']} Call")
    print(f"对冲后 Delta: {dg_hedge['resulting_delta']:.6f}")
    print(f"对冲后 Gamma: {dg_hedge['resulting_gamma']:.10f}")

    # 敏感性分析：对冲效果
    print("\n--- 对冲效果模拟 ---")
    spot_range = np.linspace(90, 110, 21)
    original_pnl = []
    hedged_pnl = []

    for S_new in spot_range:
        # 原始组合价值变化
        original_value = 0
        for opt in options:
            p = black_scholes_price(S_new, opt['K'], opt['T']-0.01, opt['r'], opt['sigma'], opt['type'])
            original_value += p * opt.get('quantity', 1)
        original_pnl.append(original_value)

    print("标的价格变化时的组合价值变化已计算")
    print(f"原始组合在 S=100 价值变化基准: {original_pnl[10]:.2f}")
