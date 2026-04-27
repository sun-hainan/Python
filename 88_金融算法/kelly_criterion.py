# -*- coding: utf-8 -*-

"""

算法实现：金融算法 / kelly_criterion



本文件实现 kelly_criterion 相关的算法功能。

"""



import numpy as np

from scipy.optimize import brentq





def kelly_fraction(p, b):

    """

    Kelly 最优下注比例



    Parameters

    ----------

    p : float

        获胜概率 (0 < p < 1)

    b : float

        赔率（赢了得到 b 倍赌注，输了损失赌注）

        例如：b=1 表示 1:1 赔率



    Returns

    -------

    float

        最优下注比例 f*

    """

    q = 1 - p

    # Kelly 公式：f* = (bp - q) / b

    # 推导：从最大化 E[ln(1 + f*X)] 得出

    if b <= 0:

        return 0.0

    f_star = (b * p - q) / b

    return max(0.0, min(1.0, f_star))  # 限制在 [0, 1]





def kelly_criterion(p, b):

    """

    Kelly 策略的期望增长率

    G(f) = p*ln(1 + f*b) + q*ln(1 - f)



    Parameters

    ----------

    p : float

        获胜概率

    b : float

        赔率

    """

    q = 1 - p



    def growth_rate(f):

        if f < 0 or f > 1:

            return -np.inf

        if f > 1/b:

            # 亏损超过赌注

            return -np.inf

        return p * np.log(1 + f*b) + q * np.log(1 - f)



    # 找到最优 f

    f_star = kelly_fraction(p, b)

    G_star = growth_rate(f_star)



    # 长期财富增长倍数（每局）

    return {

        'optimal_fraction': f_star,

        'growth_rate': G_star,

        'expected_wealth_multiplier': np.exp(G_star),

        'doubling_rate': G_star / np.log(2)  # 财富翻倍需要的局数

    }





def kelly_with_variance(p, b, sigma=0):

    """

    带波动率的 Kelly 修正

    当每局收益有随机波动时（如交易策略有方差）



    修正 Kelly = f* / (1 + σ_adj)

    或使用 Half Kelly 降低风险

    """

    f_star = kelly_fraction(p, b)



    # 波动率调整

    if sigma > 0:

        # 一阶修正

        f_adj = f_star / (1 + sigma**2)

    else:

        f_adj = f_star



    return {

        'full_kelly': f_star,

        'adjusted_kelly': f_adj,

        'half_kelly': f_star / 2,

        'quarter_kelly': f_star / 4

    }





def binary_kelly_optimal(f, p, b):

    """

    二元结果 Kelly（赢了得 b，输了失 f）

    通用形式

    """

    q = 1 - p

    # E[ln(wealth)] = p*ln(1+fb) + q*ln(1-f)

    if f <= 0 or f >= 1:

        return -np.inf

    if f > 1/b and b > 0:

        return -np.inf

    return p * np.log(1 + f*b) + q * np.log(1 - f)





def multi_outcome_kelly(probabilities, payouts):

    """

    多结果 Kelly（如赛马）

    probabilities: 各结果的概率 p_i

    payouts: 各结果的净赔率 b_i（输了损失 1）

    """

    n = len(probabilities)

    p = np.array(probabilities)

    b = np.array(payouts)



    def neg_log_expected_wealth(f):

        """最大化 E[ln(wealth)] = Σ p_i * ln(1 + f*b_i)"""

        f = np.array(f)

        if any(f < 0) or np.sum(f) > 1:

            return np.inf

        # 每局结束后的财富

        wealth_changes = 1 + f @ b

        if any(wealth_changes <= 0):

            return np.inf

        log_wealth = np.sum(p * np.log(wealth_changes))

        return -log_wealth  # 最小化负对数财富



    # 初始猜测

    f0 = np.ones(n) / n



    from scipy.optimize import minimize

    constraints = {'type': 'eq', 'fun': lambda f: np.sum(f) - 1}

    bounds = [(0, 1) for _ in range(n)]



    result = minimize(neg_log_wealth, f0, method='SLSQP',

                    constraints=constraints, bounds=bounds)



    f_optimal = result.x



    # 计算增长率

    wealth_changes = 1 + f_optimal @ b

    growth_rate = np.sum(p * np.log(wealth_changes))



    return {

        'optimal_fractions': f_optimal,

        'growth_rate': growth_rate,

        'expected_return': np.sum(p * f_optimal * b) - (1 - np.sum(p * f_optimal))

    }





def simulate_kelly(p, b, n_bets=1000, initial_wealth=1.0, f=None, random_seed=42):

    """

    模拟 Kelly 策略的财富变化

    """

    np.random.seed(random_seed)

    f = f if f is not None else kelly_fraction(p, b)



    wealth = np.zeros(n_bets + 1)

    wealth[0] = initial_wealth



    wins = 0

    for i in range(n_bets):

        outcome = np.random.random() < p

        if outcome:

            wealth[i+1] = wealth[i] * (1 + f * b)

            wins += 1

        else:

            wealth[i+1] = wealth[i] * (1 - f)



    final_wealth = wealth[-1]

    cagr = (final_wealth / initial_wealth) ** (1/n_bets) - 1



    return {

        'wealth_history': wealth,

        'final_wealth': final_wealth,

        'wins': wins,

        'win_rate': wins / n_bets,

        'cagr': cagr

    }





def compare_kelly_strategies(p, b, n_bets=1000, n_simulations=100):

    """

    比较不同 Kelly 比例的效果

    """

    results = {}



    for label, f_mult in [('Full Kelly', 1.0), ('Half Kelly', 0.5),

                          ('Quarter Kelly', 0.25), ('Fixed 5%', 0.05)]:

        f = kelly_fraction(p, b) * f_mult



        final_wealths = []

        for sim in range(n_simulations):

            sim_result = simulate_kelly(p, b, n_bets, f=f, random_seed=sim)

            final_wealths.append(sim_result['final_wealth'])



        results[label] = {

            'f': f,

            'mean_final': np.mean(final_wealths),

            'median_final': np.median(final_wealths),

            'std_final': np.std(final_wealths),

            'prob_below_1': np.mean([w < 1.0 for w in final_wealths])

        }



    return results





if __name__ == "__main__":

    print("=" * 60)

    print("Kelly 准则（最优下注比例）")

    print("=" * 60)



    # 简单的 1:1 赔率游戏

    p = 0.55  # 55% 胜率

    b = 1.0   # 1:1 赔率



    print(f"\n游戏设定：胜率 p={p:.0%}, 赔率 b={b}")



    kelly = kelly_criterion(p, b)

    print(f"\nKelly 分析:")

    print(f"  最优下注比例: {kelly['optimal_fraction']:.4f} ({kelly['optimal_fraction']*100:.2f}%)")

    print(f"  对数增长率: {kelly['growth_rate']:.6f}")

    print(f"  期望每局财富乘数: {kelly['expected_wealth_multiplier']:.6f}")

    print(f"  翻倍所需局数: {kelly['doubling_rate']:.1f}")



    # 不同胜率

    print("\n--- 不同胜率下的 Kelly 比例 ---")

    print(f"{'胜率':>8} {'Kelly比例':>10} {'期望增长率':>12}")

    print("-" * 35)

    for p_test in [0.45, 0.50, 0.55, 0.60, 0.65, 0.70]:

        f = kelly_fraction(p_test, b)

        kelly_test = kelly_criterion(p_test, b)

        print(f"{p_test:>8.0%} {f:>10.4f} {kelly_test['growth_rate']:>12.6f}")



    # 不同赔率

    print("\n--- 不同赔率下的 Kelly 比例 ---")

    print(f"{'赔率':>8} {'Kelly比例':>10} {'期望增长率':>12}")

    print("-" * 35)

    for b_test in [0.5, 1.0, 2.0, 3.0, 5.0]:

        f = kelly_fraction(p, b_test)

        kelly_test = kelly_criterion(p, b_test)

        print(f"{b_test:>8.2f} {f:>10.4f} {kelly_test['growth_rate']:>12.6f}")



    # 模拟比较

    print("\n--- Kelly 策略模拟 (1000 局) ---")

    np.random.seed(42)

    n_bets = 1000



    for label, f_mult in [('Full Kelly', 1.0), ('Half Kelly', 0.5), ('Fixed 10%', 0.10)]:

        f = kelly_fraction(p, b) * f_mult

        result = simulate_kelly(p, b, n_bets, f=f)

        print(f"{label:>12}: 最终财富 = {result['final_wealth']:>10.4f}, "

              f"胜率 = {result['win_rate']:.2%}, "

              f"CAGR = {result['cagr']:.2%}")



    # 多次模拟比较

    print("\n--- 多次模拟比较 (100 次模拟) ---")

    comparison = compare_kelly_strategies(p, b, n_bets=500, n_simulations=100)



    print(f"{'策略':>15} {'f':>8} {'均值':>12} {'标准差':>10} {'亏损概率':>10}")

    print("-" * 60)

    for label, res in comparison.items():

        print(f"{label:>15} {res['f']:>8.4f} {res['mean_final']:>12.4f} "

              f"{res['std_final']:>10.4f} {res['prob_below_1']:>10.2%}")

