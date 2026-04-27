# -*- coding: utf-8 -*-

"""

算法实现：金融算法 / black_scholes



本文件实现 black_scholes 相关的算法功能。

"""



import numpy as np

from scipy.stats import norm





def black_scholes_price(S, K, T, r, sigma, option_type='call'):

    """

    计算 Black-Scholes 期权价格



    Parameters

    ----------

    S : float

        标的资产当前价格（Underlying price）

    K : float

        行权价格（Strike price）

    T : float

        到期时间，单位年（Time to maturity in years）

    r : float

        无风险利率（Risk-free rate）

    sigma : float

        标的资产波动率（Volatility）

    option_type : str

        'call' 或 'put'



    Returns

    -------

    float

        期权价格

    """

    # 处理极端情况

    if T <= 0:

        if option_type == 'call':

            return max(S - K, 0.0)

        else:

            return max(K - S, 0.0)



    # d1 和 d2 是 Black-Scholes 公式的核心

    # d1 反映了到期日前标的资产上涨到行权价以上的概率调整

    # d2 是风险中性测度下的到期日指数分布均值参数

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

    d2 = d1 - sigma * np.sqrt(T)



    if option_type == 'call':

        # 欧式看涨期权：C = S*N(d1) - K*e^(-rT)*N(d2)

        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

    else:

        # 欧式看跌期权：P = K*e^(-rT)*N(-d2) - S*N(-d1)

        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)



    return price





def black_scholes_with_dividend(S, K, T, r, sigma, q, option_type='call'):

    """

    考虑连续股息的 Black-Scholes 模型

    标的资产支付连续股息收益率 q（如指数成分股）



    Parameters

    ----------

    q : float

        连续股息收益率（Continuous dividend yield）

    """

    # 股息收益率导致标的资产漂移率从 r 变为 r-q

    # 在风险中性测度下，标的资产期望增长率为 (r - q)

    d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

    d2 = d1 - sigma * np.sqrt(T)



    if option_type == 'call':

        price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

    else:

        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)



    return price





if __name__ == "__main__":

    # 测试用例：假设标的资产价格为 100，行权价 105，6个月到期

    # 无风险利率 5%，波动率 20%

    S, K, T, r, sigma = 100, 105, 0.5, 0.05, 0.2



    call_price = black_scholes_price(S, K, T, r, sigma, 'call')

    put_price = black_scholes_price(S, K, T, r, sigma, 'put')



    print(f"标的价格 S = {S}, 行权价 K = {K}, 到期 T = {T}年")

    print(f"无风险利率 r = {r:.0%}, 波动率 σ = {sigma:.0%}")

    print(f"看涨期权价格: {call_price:.4f}")

    print(f"看跌期权价格: {put_price:.4f}")



    # 验证看涨-看跌平价关系

    # C - P = S - K*e^(-rT)

    parity = call_price - put_price

    actual = S - K * np.exp(-r * T)

    print(f"\n看涨-看跌平价验证: C - P = {parity:.4f}, S - K*e^(-rT) = {actual:.4f}")

    print(f"平价成立: {np.isclose(parity, actual)}")



    # 股息收益率测试

    q = 0.03

    call_div = black_scholes_with_dividend(S, K, T, r, sigma, q, 'call')

    put_div = black_scholes_with_dividend(S, K, T, r, sigma, q, 'put')

    print(f"\n含股息(q={q:.0%}) 看涨期权: {call_div:.4f}, 看跌期权: {put_div:.4f}")

