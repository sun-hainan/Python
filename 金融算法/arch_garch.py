# -*- coding: utf-8 -*-

"""

算法实现：金融算法 / arch_garch



本文件实现 arch_garch 相关的算法功能。

"""



import numpy as np

from scipy.optimize import minimize





def arch_fit(returns, p=1):

    """

    拟合 ARCH(p) 模型

    r_t = μ + ε_t, ε_t = σ_t * z_t, z_t ~ N(0,1)

    σ_t² = α_0 + α_1 * ε_{t-1}² + α_2 * ε_{t-2}² + ... + α_p * ε_{t-p}²



    Parameters

    ----------

    returns : np.ndarray

        收益率序列

    p : int

        ARCH 阶数

    """

    n = len(returns)

    T = n - p



    # 中心化收益率

    r = returns - np.mean(returns)



    # 构建设计矩阵

    # 条件方差 σ_t² = α_0 + Σα_i * ε_{t-i}²

    Y = r[p:] ** 2  # 因变量：r_t²

    X = np.column_stack([np.ones(T)] + [r[p-i-1:-i-1] ** 2 if i > 0 else r[p-1:-1] ** 2 for i in range(p)])



    # OLS 估计（这是拟MLE，真正的MLE需要迭代）

    # 但 ARCH 模型的 OLS 不是最优的，这里为了简单演示

    # 约束：α_0 > 0, α_i >= 0

    XT = X.T

    beta = np.linalg.solve(XT @ X, XT @ Y)  # OLS 系数



    alpha0 = max(beta[0], 1e-8)

    alphas = beta[1:]



    # 计算拟合的波动率序列

    sigma2 = np.zeros(n)

    sigma2[:p] = np.var(r)  # 初始化

    for t in range(p, n):

        sigma2[t] = alpha0 + sum(alphas[i] * r[t-i-1]**2 for i in range(p))



    # 计算对数似然

    ll = -0.5 * np.sum(np.log(2*np.pi) + np.log(sigma2[p:]) + Y / sigma2[p:])



    return {'alpha0': alpha0, 'alphas': alphas, 'mu': np.mean(returns),

            'sigma2': sigma2, 'log_likelihood': ll}





def garch_mle(returns, p=1, q=1):

    """

    拟合 GARCH(p,q) 模型，使用最大似然估计

    σ_t² = ω + Σα_i * ε_{t-i}² + Σβ_j * σ_{t-j}²



    使用拟牛顿法优化对数似然函数

    """

    n = len(returns)

    r = returns - np.mean(returns)



    def garch_variance(params, r, p, q):

        """给定参数，计算条件方差序列"""

        omega = params[0]

        alphas = params[1:1+p]

        betas = params[1+p:1+p+q]



        T = len(r)

        sigma2 = np.zeros(T)

        # 初始化：用无条件方差

        sigma2[:max(p, q)] = np.var(r)



        for t in range(max(p, q), T):

            arch_term = sum(alphas[i] * r[t-i-1]**2 for i in range(p) if t-i-1 >= 0)

            garch_term = sum(betas[j] * sigma2[t-j-1] for j in range(q) if t-j-1 >= 0)

            sigma2[t] = omega + arch_term + garch_term



        return sigma2



    def neg_log_likelihood(params, r, p, q):

        """负对数似然函数"""

        omega = params[0]

        if omega <= 0:

            return 1e10

        alphas = params[1:1+p]

        betas = params[1+p:]



        if any(a < 0 or a > 1 for a in alphas) or any(b < 0 or b > 1 for b in betas):

            return 1e10

        if sum(alphas) + sum(betas) >= 1:

            return 1e10  # 约束：ARCH + GARCH 项之和 < 1 保证平稳性



        sigma2 = garch_variance(params, r, p, q)

        if any(s <= 0 for s in sigma2):

            return 1e10



        ll = -0.5 * np.sum(np.log(2*np.pi) + np.log(sigma2) + r**2 / sigma2)

        return -ll  # 最小化负似然



    # 初始参数：omega, alphas, betas

    init_params = [np.var(r) * 0.1] + [0.05] * p + [0.9] * q



    result = minimize(neg_log_likelihood, init_params, args=(r, p, q),

                     method='SLSQP')

    params = result.x



    omega = params[0]

    alphas = params[1:1+p]

    betas = params[1+p:]



    sigma2 = garch_variance(params, r, p, q)



    return {

        'omega': omega,

        'alphas': alphas,

        'betas': betas,

        'mu': np.mean(returns),

        'sigma2': sigma2,

        'log_likelihood': -result.fun,

        'aic': 2 * result.fun + 2 * (1 + p + q),

        'bic': 2 * result.fun + np.log(n) * (1 + p + q)

    }





def egarch_mle(returns, p=1, q=1):

    """

    EGARCH(p,q) 模型

    ln(σ_t²) = ω + Σα_i * g(z_{t-i}) + Σβ_j * ln(σ_{t-j}²)



    其中 g(z) = θ*z + γ*(|z| - E|z|)

    杠杆效应通过区分正负 innovations 实现



    Parameters

    ----------

    returns : np.ndarray

        收益率序列

    p, q : int

        模型阶数

    """

    n = len(returns)

    r = returns - np.mean(returns)



    def egarch_variance(params, r, p, q):

        """计算 EGARCH 条件方差"""

        omega = params[0]

        alphas = params[1:1+p]

        betas = params[1+p:1+p+q]

        gamma = params[-2] if len(params) > 1+p+q else 0  # 杠杆系数

        theta = params[-1] if len(params) > 1+p+q else 0



        T = len(r)

        log_sigma2 = np.zeros(T)

        log_sigma2[:max(p, q)] = np.log(np.var(r))



        for t in range(max(p, q), T):

            arch_sum = 0

            for i in range(p):

                z_prev = r[t-i-1] / np.sqrt(log_sigma2[t-i-1] + 1e-10)

                arch_sum += alphas[i] * (theta * z_prev + gamma * (abs(z_prev) - np.sqrt(2/np.pi)))



            garch_sum = sum(betas[j] * log_sigma2[t-j-1] for j in range(q))



            log_sigma2[t] = omega + arch_sum + garch_sum



        return log_sigma2



    def neg_log_likelihood(params, r, p, q):

        omega = params[0]

        alphas = params[1:1+p]

        betas = params[1+p:1+p+q]

        gamma = params[-2] if len(params) > 1+p+q else -0.1

        theta = params[-1] if len(params) > 1+p+q else 0.1



        log_sigma2 = egarch_variance(params, r, p, q)

        sigma2 = np.exp(log_sigma2)



        if any(s <= 0 for s in sigma2):

            return 1e10



        ll = -0.5 * np.sum(np.log(2*np.pi) + log_sigma2 + r**2 / sigma2)

        return -ll



    # 初始参数

    init_params = [-0.1] + [0.1] * p + [0.9] * q + [-0.1, 0.05]



    result = minimize(neg_log_likelihood, init_params, args=(r, p, q),

                     method='SLSQP')

    params = result.x



    omega = params[0]

    alphas = params[1:1+p]

    betas = params[1+p:1+p+q]

    gamma = params[-2]

    theta = params[-1]



    log_sigma2 = egarch_variance(params, r, p, q)

    sigma2 = np.exp(log_sigma2)



    return {

        'omega': omega,

        'alphas': alphas,

        'betas': betas,

        'gamma': gamma,

        'theta': theta,

        'sigma2': sigma2,

        'log_likelihood': -result.fun

    }





def garch_forecast(params, r, p, q, h=10):

    """

    GARCH 模型向前 h 步预测

    长期波动率趋向于无条件方差 σ²_long = ω / (1 - Σα_i - Σβ_j)

    """

    omega = params['omega']

    alphas = params['alphas']

    betas = params['betas']



    n = len(r)

    forecasts = np.zeros(h)



    # 最后已知方差

    sigma2_last = params['sigma2'][-1]



    for i in range(h):

        if i == 0:

            # 第一步预测使用已知信息

            arch = sum(alphas[j] * r[n-1-j]**2 for j in range(min(p, n-1)))

            garch = sum(betas[j] * params['sigma2'][n-1-j] for j in range(min(q, n-1)))

        else:

            # 后续预测使用之前的预测值

            arch = sum(alphas[j] * r[n-1-j]**2 for j in range(min(p, n-1-i)))

            garch = sum(betas[j] * forecasts[i-1-j] for j in range(min(i, q)))



        forecasts[i] = omega + arch + garch



    return forecasts





def rolling_volatility_forecast(returns, window=60, p=1, q=1):

    """

    滚动窗口波动率预测

    使用过去 window 天的数据拟合 GARCH，然后预测明天波动率

    """

    n = len(returns)

    forecasts = np.zeros(n - window)



    for t in range(window, n):

        r_window = returns[t-window:t]

        try:

            model = garch_mle(r_window, p, q)

            # 预测下一步

            omega = model['omega']

            alphas = model['alphas']

            betas = model['betas']

            last_r = r_window[-1]

            last_sigma2 = model['sigma2'][-1]

            forecasts[t-window] = np.sqrt(omega + sum(alphas) * last_r**2 + sum(betas) * last_sigma2)

        except:

            # 拟合失败时使用简单标准差

            forecasts[t-window] = np.std(r_window)



    return forecasts





if __name__ == "__main__":

    # 模拟 GARCH(1,1) 过程

    np.random.seed(42)

    n = 1000

    T = 500



    # 参数：ω=0.00001, α=0.1, β=0.85

    # 这意味着波动率有较强的持续性（α+β=0.95）

    omega = 0.00001

    alpha = 0.1

    beta = 0.85



    r = np.zeros(n)

    sigma2 = np.zeros(n)

    sigma2[0] = 0.0004



    for t in range(1, n):

        z = np.random.standard_normal()

        sigma2[t] = omega + alpha * r[t-1]**2 + beta * sigma2[t-1]

        r[t] = np.sqrt(sigma2[t]) * z



    # 拟合 ARCH(1)

    print("--- ARCH(1) 模型 ---")

    arch_result = arch_fit(r, p=1)

    print(f"α_0 = {arch_result['alpha0']:.6f}")

    print(f"α_1 = {arch_result['alphas'][0]:.4f}")



    # 拟合 GARCH(1,1)

    print("\n--- GARCH(1,1) 模型 ---")

    garch_result = garch_mle(r, p=1, q=1)

    print(f"ω = {garch_result['omega']:.8f}")

    print(f"α = {garch_result['alphas'][0]:.4f}")

    print(f"β = {garch_result['betas'][0]:.4f}")

    print(f"α + β = {garch_result['alphas'][0] + garch_result['betas'][0]:.4f}")

    print(f"对数似然: {garch_result['log_likelihood']:.2f}")

    print(f"AIC: {garch_result['aic']:.2f}, BIC: {garch_result['bic']:.2f}")



    # 长期波动率

    long_run_vol = np.sqrt(garch_result['omega'] / (1 - sum(garch_result['alphas']) - sum(garch_result['betas'])))

    print(f"长期波动率: {long_run_vol:.6f}")



    # 波动率预测

    print("\n--- 波动率预测 ---")

    forecasts = garch_forecast(garch_result, r, p=1, q=1, h=10)

    print("未来10天波动率预测:")

    for i, f in enumerate(forecasts):

        print(f"  第{i+1}天: {np.sqrt(f):.6f}")



    # 波动率序列可视化（数值）

    print("\n--- 波动率序列（最近20天）---")

    recent_sigma = np.sqrt(garch_result['sigma2'][-20:])

    for i, s in enumerate(recent_sigma):

        bar = '█' * int(s * 1000)

        print(f"  t-{19-i:2d}: {s:.6f} {bar}")

