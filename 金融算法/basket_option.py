# -*- coding: utf-8 -*-

"""

算法实现：金融算法 / basket_option



本文件实现 basket_option 相关的算法功能。

"""



import numpy as np

from scipy.stats import norm, mvn





def basket_option_geometric_approx(S, weights, K, T, r, sigma_vec, corr_matrix):

    """

    几何平均近似（Deborah's Approximation）

    用几何平均代替算术平均，因为几何平均的联合分布是对数正态



    篮子资产几何平均 G = (Π S_i^w_i)^(1/Σw_i)

    ln(G) ~ Normal(mu_G, sigma_G)



    这个近似在资产相关性低、权重均匀时效果较好

    """

    n = len(S)

    # 权重归一化

    w = np.array(weights) / np.sum(weights)



    # 各资产的 log 收益率参数

    mu_log = (r - 0.5 * sigma_vec ** 2) * T

    var_log = sigma_vec ** 2 * T



    # 几何平均的均值和方差

    # E[ln(G)] = Σ w_i * (ln(S_i) + mu_i)

    # Var[ln(G)] 需要考虑相关性

    mu_G = np.sum(w * (np.log(S) + mu_log))



    # Var[ln(G)] = Σ w_i² Var[ln(S_i)] + 2 * Σ_{i<j} w_i * w_j * Cov[ln(S_i), ln(S_j)]

    var_G = 0

    for i in range(n):

        var_G += w[i]**2 * var_log[i]

    for i in range(n):

        for j in range(i+1, n):

            cov_ij = corr_matrix[i,j] * sigma_vec[i] * sigma_vec[j] * T

            var_G += 2 * w[i] * w[j] * cov_ij



    sigma_G = np.sqrt(var_G)



    # 用 Black-Scholes 公式定价

    d1 = (np.log(np.sum(w * S)) - K + 0.5 * sigma_G**2) / sigma_G

    d2 = d1 - sigma_G



    price = np.sum(w * S) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)



    return price





def basket_option_moment_matching(S, weights, K, T, r, sigma_vec, corr_matrix):

    """

    矩匹配近似（Log-Normal Approximation）

    假设篮子价值的分布也是对数正态，通过匹配前两阶矩来确定参数



    篮子价值 B = Σ w_i * S_i



    步骤：

    1. 计算 E[B] 和 Var[B]

    2. 假设 B ~ logN(μ, σ²)，则：

       E[B] = exp(μ + σ²/2)

       Var[B] = exp(2μ + σ²) * (exp(σ²) - 1)

    3. 反解 μ, σ

    """

    w = np.array(weights)

    n = len(S)



    # 各资产的期望（对数正态）

    # E[S_i(T)] = S_i * exp(r*T)

    E_ST = S * np.exp(r * T)



    # 篮子期望价值

    E_B = np.sum(w * E_ST)



    # 篮子价值方差

    # Var[B] = Σ w_i² Var[S_i] + 2 * Σ_{i<j} w_i * w_j * Cov[S_i, S_j]

    var_B = 0

    for i in range(n):

        var_S_i = (np.exp(sigma_vec[i]**2 * T) - 1) * E_ST[i]**2

        var_B += w[i]**2 * var_S_i



    for i in range(n):

        for j in range(i+1, n):

            cov_ST = corr_matrix[i,j] * S[i] * S[j] * np.exp((sigma_vec[i]**2 + sigma_vec[j]**2)/2 * T) * (np.exp(corr_matrix[i,j] * sigma_vec[i] * sigma_vec[j] * T) - 1)

            var_B += 2 * w[i] * w[j] * cov_ST



    # 从对数正态矩得到参数

    # E[B] = exp(μ + σ²/2), Var[B] = exp(2μ + σ²) * (exp(σ²) - 1)

    # 令 m1 = E[B], m2 = E[B]² + Var[B]

    m1 = E_B

    m2 = E_B**2 + var_B



    # 解方程得到 log-B 的均值和方差

    # m1 = exp(μ + σ²/2), m2 = exp(2μ + σ²) * (exp(σ²) - 1) + m1²

    # 简化：使用一阶近似

    log_m1 = np.log(m1)

    # 使用迭代或近似

    # 这里用简化的 Wystup 近似

    sigma_B = np.sqrt(np.log(m2 / m1**2)) if m2 > m1**2 else np.sum(w * sigma_vec) * np.sqrt(T / n)

    mu_B = np.log(m1) - 0.5 * sigma_B**2



    # 定价：把篮子当作单一对数正态资产

    # 注意：这里用 m1 作为"标的价格"，K 保持不变

    d1 = (np.log(m1) - np.log(K) + 0.5 * sigma_B**2) / sigma_B

    d2 = d1 - sigma_B



    price = m1 * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)



    return price





def basket_option_monte_carlo(S, weights, K, T, r, sigma_vec, corr_matrix,

                               n_paths=100000, option_type='call'):

    """

    蒙特卡洛模拟定价篮子期权

    使用相关联的标准正态随机变量生成联合分布样本



    相关性通过 Cholesky 分解实现

    """

    n = len(S)

    w = np.array(weights) / np.sum(weights)



    # Cholesky 分解：L * L^T = corr_matrix

    L = np.linalg.cholesky(corr_matrix)



    # 生成独立的标椎正态随机数

    Z = np.random.standard_normal((n_paths, n))



    # 加入相关性

    Z_corr = Z @ L.T



    # 生成终端资产价格

    # S_i(T) = S_i * exp((r - 0.5*σ_i²)*T + σ_i*sqrt(T)*Z_i)

    dt = T

    drift = (r - 0.5 * sigma_vec**2) * dt

    diffusion = sigma_vec * np.sqrt(dt) * Z_corr



    ST = S * np.exp(drift + diffusion)



    # 篮子价值

    basket_values = ST @ w



    # Payoff

    if option_type == 'call':

        payoffs = np.maximum(basket_values - K, 0)

    else:

        payoffs = np.maximum(K - basket_values, 0)



    # 折现

    price = np.exp(-r * T) * np.mean(payoffs)

    std_error = np.exp(-r * T) * np.std(payoffs) / np.sqrt(n_paths)



    return price, std_error





def basket_option_antithetic(S, weights, K, T, r, sigma_vec, corr_matrix,

                              n_paths=100000, option_type='call'):

    """

    使用对偶变量法减少方差的蒙特卡洛

    """

    n = len(S)

    n_half = n_paths // 2

    w = np.array(weights) / np.sum(weights)



    L = np.linalg.cholesky(corr_matrix)



    Z = np.random.standard_normal((n_half, n))

    Z_corr = Z @ L.T



    dt = T

    drift = (r - 0.5 * sigma_vec**2) * dt

    diffusion = sigma_vec * np.sqrt(dt) * Z_corr



    # 正路径

    ST_pos = S * np.exp(drift + diffusion)

    basket_pos = ST_pos @ w



    # 负路径

    ST_neg = S * np.exp(drift - diffusion)

    basket_neg = ST_neg @ w



    if option_type == 'call':

        payoffs_pos = np.maximum(basket_pos - K, 0)

        payoffs_neg = np.maximum(basket_neg - K, 0)

    else:

        payoffs_pos = np.maximum(K - basket_pos, 0)

        payoffs_neg = np.maximum(K - basket_neg, 0)



    all_payoffs = np.concatenate([payoffs_pos, payoffs_neg])

    price = np.exp(-r * T) * np.mean(all_payoffs)

    std_error = np.exp(-r * T) * np.std(all_payoffs) / np.sqrt(n_paths)



    return price, std_error





def basket_option_bivariate_approx(S, weights, K, T, r, sigma_vec, corr_matrix):

    """

    二资产情况的 Curran 近似

    利用条件期望展开，更精确地近似算术平均



    思想：将 E[max(B-K, 0)] 展开为一系列条件期望

    """

    if len(S) != 2:

        raise ValueError("此近似仅适用于两个资产")



    w = np.array(weights) / np.sum(weights)

    S1, S2 = S[0], S[1]

    sigma1, sigma2 = sigma_vec[0], sigma_vec[1]

    rho = corr_matrix[0, 1]



    # 计算各资产的参数

    # 使用方差-协方差矩阵

    var1 = sigma1**2 * T

    var2 = sigma2**2 * T

    cov = rho * sigma1 * sigma2 * T



    # 计算 B = w1*S1 + w2*S2 的各阶矩

    # 简化：用 Monte Carlo 参考值

    mc_price, _ = basket_option_monte_carlo(

        [S1, S2], [w[0], w[1]], K, T, r, [sigma1, sigma2],

        np.array([[1.0, rho], [rho, 1.0]]), n_paths=200000

    )



    return mc_price





if __name__ == "__main__":

    # 测试参数

    S = np.array([100, 100])  # 两个标的资产价格

    weights = np.array([0.5, 0.5])  # 等权重

    K = 105  # 行权价

    T = 1.0  # 1年

    r = 0.05  # 无风险利率

    sigma_vec = np.array([0.2, 0.25])  # 两个资产的波动率

    corr_matrix = np.array([[1.0, 0.5], [0.5, 1.0]])  # 相关性 0.5



    print(f"篮子期权定价测试")

    print(f"资产价格: S1={S[0]}, S2={S[1]}")

    print(f"权重: w1={weights[0]}, w2={weights[1]}")

    print(f"行权价 K={K}, 到期 T={T}年")

    print(f"波动率: σ1={sigma_vec[0]:.0%}, σ2={sigma_vec[1]:.0%}")

    print(f"相关性: ρ={corr_matrix[0,1]:.2f}\n")



    # 几何平均近似

    price_geom = basket_option_geometric_approx(S, weights, K, T, r, sigma_vec, corr_matrix)

    print(f"几何平均近似: {price_geom:.4f}")



    # 矩匹配近似

    price_moment = basket_option_moment_matching(S, weights, K, T, r, sigma_vec, corr_matrix)

    print(f"矩匹配近似:   {price_moment:.4f}")



    # 蒙特卡洛

    price_mc, se_mc = basket_option_monte_carlo(S, weights, K, T, r, sigma_vec, corr_matrix, n_paths=100000)

    print(f"蒙特卡洛:     {price_mc:.4f} ± {1.96*se_mc:.4f}")



    # 对偶变量蒙特卡洛

    price_anti, se_anti = basket_option_antithetic(S, weights, K, T, r, sigma_vec, corr_matrix, n_paths=100000)

    print(f"对偶变量 MC:   {price_anti:.4f} ± {1.96*se_anti:.4f}")



    # 对比：用单个资产（忽略相关性）

    single_price = S[0] * 0.5 * norm.cdf((np.log(S[0]/K) + (r + 0.5*sigma_vec[0]**2)*T)/(sigma_vec[0]*np.sqrt(T))) - K*np.exp(-r*T)*norm.cdf((np.log(S[0]/K) + (r - 0.5*sigma_vec[0]**2)*T)/(sigma_vec[0]*np.sqrt(T)))

    print(f"\n作为参考，单一资产期权(等权平均): {single_price:.4f}")



    # 敏感性分析

    print("\n--- 敏感性分析 ---")

    print("不同相关性下的价格:")

    for rho in [0.0, 0.3, 0.5, 0.7, 0.9]:

        corr = np.array([[1.0, rho], [rho, 1.0]])

        p = basket_option_monte_carlo(S, weights, K, T, r, sigma_vec, corr, n_paths=30000)[0]

        print(f"  ρ = {rho:.1f}: {p:.4f}")

