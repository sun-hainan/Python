# -*- coding: utf-8 -*-

"""

算法实现：时间序列分析 / arima_aic_bic



本文件实现 arima_aic_bic 相关的算法功能。

"""



import numpy as np

from scipy import stats





def compute_acf(series, max_lag):

    """

    计算自相关函数（ACF）

    

    参数:

        series: 时间序列

        max_lag: 最大滞后期数

    

    返回:

        acf_values: ACF值数组，长度为max_lag+1

    """

    n = len(series)

    mean_val = np.mean(series)

    acf_values = [1.0]  # lag=0时ACF=1

    

    for lag in range(1, max_lag + 1):

        numerator = 0.0

        for i in range(lag, n):

            numerator += (series[i] - mean_val) * (series[i - lag] - mean_val)

        denominator = np.sum((series - mean_val) ** 2)

        acf_values.append(numerator / denominator)

    

    return np.array(acf_values)





def compute_pacf(series, max_lag):

    """

    计算偏自相关函数（PACF）

    使用Levinson-Durbin递归算法

    

    参数:

        series: 时间序列

        max_lag: 最大滞后期数

    

    返回:

        pacf_values: PACF值数组

    """

    n = len(series)

    acf = compute_acf(series, max_lag)

    pacf = np.zeros(max_lag + 1)

    pacf[0] = 1.0

    

    # Levinson-Durbin递归

    for k in range(1, max_lag + 1):

        # 计算反射系数phi_kk

        sum_num = 0.0

        sum_den = 0.0

        for j in range(k):

            sum_num += acf[k - j] * pacf[j]

            sum_den += acf[j] * pacf[j]

        

        if abs(sum_den) < 1e-10:

            phi_kk = 0.0

        else:

            phi_kk = (acf[k] - sum_num) / sum_den

        

        pacf[k] = phi_kk

        

        # 更新pacf[1..k-1]

        if k > 1:

            for j in range(1, k):

                pacf[j] -= phi_kk * pacf[k - j]

    

    return pacf[1:]  # 返回lag=1..max_lag





def aic_bic_likelihood(series, p, d, q):

    """

    计算ARIMA(p,d,q)的对数似然，然后得到AIC和BIC

    

    参数:

        series: 原始序列

        p: AR阶数

        d: 差分阶数

        q: MA阶数

    

    返回:

        aic: 赤池信息准则

        bic: 贝叶斯信息准则

        log_likelihood: 对数似然值

    """

    n = len(series)

    

    # 差分操作

    diff_series = series.copy()

    for _ in range(d):

        diff_series = np.diff(diff_series)

    

    T = len(diff_series)

    if T <= p + q:

        return np.inf, np.inf, -np.inf

    

    # 参数数量

    k = p + q + 1  # AR(p) + MA(q) + variance

    

    # 简化的残差方差估计

    # 对于AR(p)，用Yule-Walker估计

    acf_vals = compute_acf(diff_series, p)

    

    # 构建Toeplitz矩阵估计AR参数

    toeplitz = np.zeros((p, p))

    for i in range(p):

        for j in range(p):

            toeplitz[i, j] = acf_vals[abs(i - j)]

    

    try:

        # AR参数估计

        ar_params = np.linalg.solve(toeplitz, acf_vals[1:p+1])

        # 残差方差

        residual_var = 1.0 - np.sum(acf_vals[1:p+1] * ar_params)

        residual_var = max(residual_var, 0.01)  # 避免负值

    except:

        residual_var = np.var(diff_series)

    

    # 对数似然（假设高斯分布）

    log_likelihood = -0.5 * T * (np.log(2 * np.pi * residual_var) + 1)

    

    # AIC和BIC

    aic = -2 * log_likelihood + 2 * k

    bic = -2 * log_likelihood + k * np.log(T)

    

    return aic, bic, log_likelihood





def select_arima_order(series, max_p=5, max_q=5, d=1):

    """

    自动定阶：遍历所有(p,q)组合，选择AIC/BIC最小的模型

    

    参数:

        series: 时间序列

        max_p: AR阶数搜索上限

        max_q: MA阶数搜索上限

        d: 差分阶数（默认1）

    

    返回:

        best_p: 最优AR阶数

        best_q: 最优MA阶数

        results_table: 所有组合的结果表格

    """

    results = []

    

    for p in range(0, max_p + 1):

        for q in range(0, max_q + 1):

            if p == 0 and q == 0:

                continue  # 跳过无效模型

            

            try:

                aic, bic, ll = aic_bic_likelihood(series, p, d, q)

                

                if not np.isinf(aic):

                    results.append({

                        'p': p,

                        'q': q,

                        'aic': aic,

                        'bic': bic,

                        'log_likelihood': ll

                    })

            except:

                continue

    

    if not results:

        return 1, 1, []

    

    # 转换为numpy数组便于排序

    results_table = np.array([

        [r['p'], r['q'], r['aic'], r['bic']] for r in results

    ])

    

    # 按AIC排序

    sorted_idx = np.argsort(results_table[:, 2])

    sorted_table = results_table[sorted_idx]

    

    # 最优选择

    best_p = int(sorted_table[0, 0])

    best_q = int(sorted_table[0, 1])

    

    return best_p, best_q, sorted_table





if __name__ == "__main__":

    # 测试代码

    np.random.seed(42)

    n = 150

    

    # 生成AR(2)过程的测试数据：y_t = 0.6*y_{t-1} - 0.3*y_{t-2} + e_t

    y = np.zeros(n)

    for t in range(2, n):

        y[t] = 0.6 * y[t-1] - 0.3 * y[t-2] + np.random.normal(0, 1)

    

    print(f"测试序列长度: {n}")

    print(f"序列均值: {np.mean(y):.4f}, 标准差: {np.std(y):.4f}")

    

    # 计算ACF和PACF

    max_lag = 10

    acf_vals = compute_acf(y, max_lag)

    pacf_vals = compute_pacf(y, max_lag)

    

    print(f"\n自相关函数(ACF)前{max_lag}阶:")

    for lag in range(1, max_lag + 1):

        print(f"  lag={lag}: {acf_vals[lag]:.4f}")

    

    print(f"\n偏自相关函数(PACF)前{max_lag}阶:")

    for lag in range(1, max_lag + 1):

        print(f"  lag={lag}: {pacf_vals[lag-1]:.4f}")

    

    # 自动定阶搜索

    best_p, best_q, results_table = select_arima_order(y, max_p=4, max_q=4, d=1)

    

    print(f"\n=== ARIMA定阶结果 ===")

    print(f"最优模型: ARIMA({best_p}, 1, {best_q})")

    print(f"\nAIC/BIC排名前5的模型:")

    print(f"{'p':>4} {'q':>4} {'AIC':>12} {'BIC':>12}")

    print("-" * 36)

    for row in results_table[:5]:

        print(f"{int(row[0]):>4} {int(row[1]):>4} {row[2]:>12.4f} {row[3]:>12.4f}")

