# -*- coding: utf-8 -*-

"""

算法实现：金融算法 / credit_risk_merton



本文件实现 credit_risk_merton 相关的算法功能。

"""



import numpy as np

from scipy.stats import norm





def merton_model_price(V, D, T, r, sigma_V, option_type='call'):

    """

    Merton 模型下的股权定价

    股权 = max(V_T - D, 0)，类似以公司资产为标的的看涨期权



    Parameters

    ----------

    V : float

        公司资产当前价值

    D : float

        到期债务面值（违约边界）

    T : float

        期限

    r : float

        无风险利率

    sigma_V : float

        公司资产波动率

    """

    # d2 是使得 V_T > D 的概率调整

    d2 = (np.log(V / D) + (r - 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T))

    d1 = d2 + sigma_V * np.sqrt(T)



    # 股权价值（使用 Black-Scholes 形式）

    equity = V * norm.cdf(d1) - D * np.exp(-r * T) * norm.cdf(d2)



    # 违约概率 = P(V_T < D) = N(-d2)

    default_prob = norm.cdf(-d2)



    # 风险中性违约概率（用于信用违约互换定价）

    # 实际概率需要用实际漂移率调整



    return {

        'equity': equity,

        'default_prob': default_prob,

        'd1': d1,

        'd2': d2

    }





def merton_debt_value(V, D, T, r, sigma_V):

    """

    Merton 模型下的债务定价

    债务 = D * e^(-rT) - put_option_on_assets

    即债务价值 = 无风险价值 - 信用风险溢价（类似看跌期权空头）



    债务价值 = D*e^(-rT) - D*e^(-rT)*N(-d2) + V*N(-d1)

             = D*e^(-rT)*N(d2) + V*N(-d1)

    """

    d2 = (np.log(V / D) + (r - 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T))

    d1 = d2 + sigma_V * np.sqrt(T)



    # 债务价值

    debt_value = D * np.exp(-r * T) * norm.cdf(d2) + V * norm.cdf(-d1)



    # 信用利差：使债务价值等于面值的折现

    risk_free_value = D * np.exp(-r * T)

    credit_spread = -np.log(debt_value / D) / T if debt_value > 0 else 0



    return {

        'debt_value': debt_value,

        'risk_free_value': risk_free_value,

        'credit_spread': credit_spread,

        'loss_given_default': (D * np.exp(-r * T) - debt_value) / D * np.exp(-r * T)

    }





def kmv_expected_default_frequency(V, D, sigma_V, T=1, horizon=1):

    """

    KMV 模型的 EDF（预期违约频率）计算



    步骤：

    1. 计算距离违约点（DD，Distance to Default）

    2. 将 DD 映射到实际违约概率



    DD = (V - D) / (σ_V * V)

    这是资产价值到违约边界的标准化距离



    实际中，DD 到 EDF 的映射需要历史违约数据

    这里使用简化：假设资产价值服从对数正态

    EDF = P(V_T < D) = N(-DD * sqrt(horizon/T))



    Parameters

    ----------

    horizon : int

        预测期限（年）

    """

    # 距离违约点（标准化的资产价值到违约边界的距离）

    DD = (V - D) / (sigma_V * V)



    # 违约概率（假设资产价值对数正态分布）

    # P(V_T < D) = N( -DD )

    # 多期需要调整

    default_prob = norm.cdf(-DD * np.sqrt(horizon))



    # 理论上的 EDF（风险中性概率）

    # 实际中使用历史数据校准



    return {

        'DD': DD,

        'default_prob': default_prob,

        'asset_value': V,

        'debt': D,

        'sigma_V': sigma_V

    }





def kmv_calibrate_from_market(equity_value, D, r, T, risk_free_rate=0.05):

    """

    从市场价格反推资产价值和波动率

    使用迭代方法求解



    股权价格已知（市场可观测），需要反推 V 和 sigma_V

    需要两个方程：

    1. 股权 = f(V, sigma_V)

    2. sigma_E = g(V, sigma_V)  （来自 Ito 引理）

    """

    # 迭代求解

    # 初始猜测：V0 ≈ equity + D

    V = equity_value + D

    sigma_V = 0.2  # 初始猜测



    for _ in range(100):

        d2 = (np.log(V / D) + (r - 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T))

        d1 = d2 + sigma_V * np.sqrt(T)



        # 股权对 V 的导数 = N(d1)

        equity_calc = V * norm.cdf(d1) - D * np.exp(-r * T) * norm.cdf(d2)



        # 股权波动率

        # sigma_E = N(d1) * sigma_V * V / E

        sigma_E_calc = norm.cdf(d1) * sigma_V * V / equity_value



        # 更新 V 和 sigma_V

        V_new = V + (equity_value - equity_calc) / norm.cdf(d1)

        sigma_V_new = sigma_V + (0.2 - sigma_E_calc) * 0.1  # 简化



        if abs(V_new - V) < 1e-8 and abs(sigma_V_new - sigma_V) < 1e-8:

            break



        V = max(V_new, D * 0.5)  # 防止 V 过小

        sigma_V = max(sigma_V_new, 0.01)



    return {

        'asset_value': V,

        'asset_volatility': sigma_V,

        'equity_value': equity_value,

        'debt': D,

        'd1': d1,

        'd2': d2

    }





def credit_spread_from_merton(V, D, T, r, sigma_V, risk_free_rate=0.05):

    """

    从 Merton 模型计算信用利差



    信用利差 = 使得债券价格等于理论价值的收益率溢价

    P = D * exp(-(r + cs) * T)

    cs = -ln(P/D) / T - r

    """

    debt_info = merton_debt_value(V, D, T, r, sigma_V)



    # 信用利差（年化）

    # 需要解：(r + cs) 使得 D * exp(-(r+cs)*T) = debt_value

    # cs = -ln(debt_value/D) / T - r

    if debt_info['debt_value'] > 0:

        cs = -np.log(debt_info['debt_value'] / D) / T - r

    else:

        cs = 0.1  # 高信用利差



    return {

        'credit_spread': cs,

        'debt_value': debt_info['debt_value'],

        'risk_free_value': debt_info['risk_free_value']

    }





def simulate_merton_defaults(V0, D, sigma_V, r, T, n_paths=10000, n_steps=252):

    """

    模拟 Merton 模型的违约路径

    返回违约概率和回收率分布

    """

    dt = T / n_steps

    n = len(V0) if hasattr(V0, '__len__') else 1



    if not hasattr(V0, '__len__'):

        V0 = np.array([V0])



    defaults = np.zeros(len(V0))



    for i in range(len(V0)):

        V = V0[i]

        for t in range(n_steps):

            Z = np.random.standard_normal()

            V = V * np.exp((r - 0.5 * sigma_V**2) * dt + sigma_V * np.sqrt(dt) * Z)

            if V < D:

                defaults[i] = 1

                break



    default_prob = np.mean(defaults)



    return {

        'default_probability': default_prob,

        'defaults': defaults,

        'n_defaults': np.sum(defaults),

        'n_paths': len(V0)

    }





if __name__ == "__main__":

    print("=" * 60)

    print("Merton 模型信用风险定价")

    print("=" * 60)



    # 公司参数

    V = 100  # 资产价值

    D = 80   # 债务面值（违约边界）

    T = 5    # 5年

    r = 0.05 # 无风险利率

    sigma_V = 0.25  # 资产波动率



    print(f"\n公司参数:")

    print(f"  资产价值 V = {V}")

    print(f"  债务面值 D = {D}")

    print(f"  期限 T = {T}年")

    print(f"  无风险利率 r = {r:.0%}")

    print(f"  资产波动率 σ_V = {sigma_V:.0%}")



    # 股权和债务定价

    result = merton_model_price(V, D, T, r, sigma_V)

    print(f"\n股权价值: {result['equity']:.4f}")

    print(f"违约概率: {result['default_prob']:.4f} ({result['default_prob']*100:.2f}%)")



    debt_result = merton_debt_value(V, D, T, r, sigma_V)

    print(f"\n债务定价:")

    print(f"  债务价值: {debt_result['debt_value']:.4f}")

    print(f"  无风险价值: {debt_result['risk_free_value']:.4f}")

    print(f"  隐含信用利差: {debt_result['credit_spread']*100:.2f}%")



    # KMV

    print("\n--- KMV 模型 ---")

    kmv_result = kmv_expected_default_frequency(V, D, sigma_V, T=1)

    print(f"距离违约点 (DD): {kmv_result['DD']:.4f}")

    print(f"1年违约概率: {kmv_result['default_prob']:.4f} ({kmv_result['default_prob']*100:.4f}%)")



    # 从市场数据校准

    print("\n--- 从股权市场价格校准 ---")

    # 假设股权市场价格为 40

    equity_market = 40

    calibration = kmv_calibrate_from_market(equity_market, D, r, T)

    print(f"股权市场价值: {equity_market:.4f}")

    print(f"反推资产价值: {calibration['asset_value']:.4f}")

    print(f"反推资产波动率: {calibration['asset_volatility']:.4f}")



    # 信用利差

    print("\n--- 隐含信用利差 ---")

    for sigma in [0.15, 0.25, 0.35]:

        cs_result = credit_spread_from_merton(V, D, T, r, sigma)

        print(f"  σ_V = {sigma:.0%}: 信用利差 = {cs_result['credit_spread']*100:.2f}%")



    # 蒙特卡洛模拟违约

    print("\n--- 蒙特卡洛违约模拟 ---")

    V0 = np.full(10000, V)

    sim_result = simulate_merton_defaults(V0, D, sigma_V, r, T, n_paths=10000)

    print(f"模拟路径数: {sim_result['n_paths']}")

    print(f"违约数量: {sim_result['n_defaults']}")

    print(f"模拟违约概率: {sim_result['default_probability']:.4f}")

