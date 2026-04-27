# -*- coding: utf-8 -*-

"""

算法实现：时间序列分析 / var_model



本文件实现 var_model 相关的算法功能。

"""



import numpy as np

from typing import Tuple, Optional

from scipy import stats





class VARModel:

    """

    VAR模型类

    

    参数:

        p: 滞后阶数

        k: 变量数

    """

    

    def __init__(self, p: int = 1):

        self.p = p

        self.k = None  # 变量数

        self.A = None  # 系数矩阵列表 [A1, A2, ..., Ap]

        self.sigma = None  # 残差协方差矩阵

        self.fitted = False

        self.residuals = None

    

    def fit(self, Y: np.ndarray) -> dict:

        """

        拟合VAR模型

        

        参数:

            Y: 多元时间序列，形状 (n_samples, n_variables)

        

        返回:

            拟合结果字典

        """

        n, self.k = Y.shape

        

        # 数据矩阵构建

        # Y_t = [y_{t-1}, y_{t-2}, ..., y_{t-p}] @ [A1', A2', ..., Ap']' + ε_t

        

        # 滞后数据

        max_lag = self.p

        T = n - max_lag

        

        # Y矩阵：被解释变量

        Y_matrix = Y[max_lag:]  # (T, k)

        

        # X矩阵：滞后解释变量

        # X = [1, y_{t-1}, y_{t-2}, ..., y_{t-p}] (T, 1 + k*p)

        X_list = []

        for t in range(max_lag, n):

            row = [1]  # 截距项

            for lag in range(1, self.p + 1):

                row.extend(Y[t - lag].tolist())

            X_list.append(row)

        

        X_matrix = np.array(X_list)  # (T, 1 + k*p)

        

        # OLS估计: Y = X @ A' => A' = (X'X)^{-1} X'Y

        # 但我们需要每个方程单独估计

        

        # 构建每个方程的X矩阵

        results = {'coefficients': [], 'residuals': [], 'sigma': None}

        

        # 分别估计每个变量的方程

        all_residuals = []

        

        for i in range(self.k):

            y_i = Y_matrix[:, i]

            

            # OLS

            XTX = X_matrix.T @ X_matrix

            XTY = X_matrix.T @ y_i

            XTX += np.eye(XTX.shape[0]) * 1e-8  # 正则化

            

            beta = np.linalg.solve(XTX, XTY)

            

            # 残差

            residual = y_i - X_matrix @ beta

            all_residuals.append(residual)

            

            results['coefficients'].append(beta)

        

        # 残差矩阵

        residuals_matrix = np.column_stack(all_residuals)

        self.residuals = residuals_matrix

        

        # 残差协方差矩阵

        self.sigma = (residuals_matrix.T @ residuals_matrix) / T

        

        # 提取系数矩阵

        self.A = []

        for lag in range(1, self.p + 1):

            A_lag = np.zeros((self.k, self.k))

            for i in range(self.k):

                # 每个变量的方程系数

                coef = results['coefficients'][i]

                # 跳过截距，从滞后lag开始提取

                start_idx = 1 + (lag - 1) * self.k

                end_idx = start_idx + self.k

                A_lag[i, :] = coef[start_idx:end_idx]

            self.A.append(A_lag)

        

        self.fitted = True

        

        # 计算信息准则

        n_params = self.k * (1 + self.k * self.p) + self.k * (self.k + 1) / 2

        T_total = T

        det_sigma = np.linalg.det(self.sigma)

        

        aic = np.log(det_sigma) + 2 * n_params / T_total

        bic = np.log(det_sigma) + n_params * np.log(T_total) / T_total

        

        return {

            'coefficients': self.A,

            'sigma': self.sigma,

            'aic': aic,

            'bic': bic,

            'residuals': self.residuals

        }

    

    def predict(self, Y_history: np.ndarray, n_steps: int) -> Tuple[np.ndarray, np.ndarray]:

        """

        预测未来n_steps步

        

        参数:

            Y_history: 历史数据 (n_samples, k)

            n_steps: 预测步数

        

        返回:

            (预测值, 预测协方差)

        """

        if not self.fitted:

            raise ValueError("模型未拟合")

        

        # 初始化

        last_p_values = Y_history[-self.p:]  # 最近p个时间点

        

        predictions = np.zeros((n_steps, self.k))

        prediction_cov = np.zeros((n_steps, self.k, self.k))

        

        for h in range(n_steps):

            # 计算预测值

            # y_{t+h} = A1 * y_{t+h-1} + ... + Ap * y_{t+h-p} + ε

            

            y_pred = np.zeros(self.k)

            

            # 获取需要的滞后值

            if h < self.p:

                # 还在使用历史数据

                available = [Y_history[-self.p + h:]]  # 需要调整

                for lag in range(1, self.p + 1):

                    idx = -lag + h

                    if idx < 0:

                        y_lag = Y_history[idx]

                    else:

                        y_lag = predictions[idx]

                    y_pred += self.A[lag - 1] @ y_lag

            else:

                # 完全使用预测值

                for lag in range(1, self.p + 1):

                    y_pred += self.A[lag - 1] @ predictions[h - lag]

            

            predictions[h] = y_pred

            

            # 简单的方差估计

            prediction_cov[h] = (h + 1) * self.sigma

        

        return predictions, prediction_cov

    

    def impulse_response(self, n_periods: int = 10, shock_size: float = 1.0) -> np.ndarray:

        """

        脉冲响应函数

        

        计算一个变量受到单位冲击后，所有变量的响应

        

        参数:

            n_periods: 冲击后观察期数

            shock_size: 冲击大小

        

        返回:

            脉冲响应矩阵 (n_periods, k, k)

        """

        if not self.fitted:

            raise ValueError("模型未拟合")

        

        # 初始化响应矩阵

        responses = np.zeros((n_periods, self.k, self.k))

        

        # 初始状态

        y_current = np.zeros(self.k)

        

        for h in range(n_periods):

            # 对每个变量施加冲击

            for shock_var in range(self.k):

                y_shocked = y_current.copy()

                y_shocked[shock_var] += shock_size

                

                # 计算下一期

                y_next = np.zeros(self.k)

                for lag in range(1, min(self.p, h + 1) + 1):

                    if lag > h:

                        break

                    y_next += self.A[lag - 1] @ y_shocked

                

                responses[h, :, shock_var] = y_next - y_current

            

            # 更新当前状态

            y_current = np.zeros(self.k)

            for lag in range(1, min(self.p, h + 1) + 1):

                y_current += self.A[lag - 1] @ responses[h - lag, :, :].T

        

        return responses





def var_information_criterion(Y: np.ndarray, max_p: int = 10) -> dict:

    """

    VAR模型定阶 - 使用信息准则

    

    参数:

        Y: 多元时间序列

        max_p: 最大滞后阶数

    

    返回:

        最优滞后阶数及信息

    """

    n, k = Y.shape

    results = []

    

    for p in range(1, max_p + 1):

        try:

            model = VARModel(p=p)

            result = model.fit(Y)

            

            results.append({

                'p': p,

                'aic': result['aic'],

                'bic': result['bic'],

                'model': model

            })

        except:

            continue

    

    if len(results) == 0:

        return {}

    

    # 找最优

    best_aic = min(results, key=lambda x: x['aic'])

    best_bic = min(results, key=lambda x: x['bic'])

    

    return {

        'best_p_aic': best_aic['p'],

        'best_p_bic': best_bic['p'],

        'all_results': results

    }





def granger_causality_test(Y: np.ndarray, x_idx: int, y_idx: int, 

                           max_lag: int = 5, alpha: float = 0.05) -> dict:

    """

    Granger因果性检验

    

    检验变量x是否有助于预测变量y

    

    参数:

        Y: 多元时间序列

        x_idx: 被检验变量的索引

        y_idx: 目标变量的索引

        max_lag: 最大滞后阶数

        alpha: 显著性水平

    

    返回:

        检验结果

    """

    n, k = Y.shape

    

    # 约束模型：只用y的滞后

    # 无约束模型：用y和x的滞后

    

    # 构建数据矩阵

    T = n - max_lag

    

    # 无约束模型: y_t = a0 + a1*y_{t-1} + ... + ap*y_{t-p} + b1*x_{t-1} + ... + bp*x_{t-p}

    

    # 简化：使用AR模型比较

    from statsmodels.api import OLS

    

    # 无约束回归

    X_unrestricted = []

    for t in range(max_lag, n):

        row = [1]  # 截距

        for lag in range(1, max_lag + 1):

            row.append(Y[t - lag, y_idx])  # y的滞后

            row.append(Y[t - lag, x_idx])  # x的滞后

        X_unrestricted.append(row)

    

    X_unr = np.array(X_unrestricted)

    y_target = Y[max_lag:, y_idx]

    

    # 约束回归（只包含y的滞后）

    X_restricted = np.zeros((T, 1 + max_lag))

    X_restricted[:, 0] = 1

    for lag in range(1, max_lag + 1):

        X_restricted[:, lag] = Y[max_lag - lag:-lag if lag > 0 else None, y_idx]

    

    # OLS估计

    beta_unr = np.linalg.lstsq(X_unr, y_target, rcond=None)[0]

    beta_r = np.linalg.lstsq(X_restricted, y_target, rcond=None)[0]

    

    # 残差平方和

    rss_unr = np.sum((y_target - X_unr @ beta_unr) ** 2)

    rss_r = np.sum((y_target - X_restricted @ beta_r) ** 2)

    

    # F检验

    df1 = max_lag

    df2 = T - 2 * max_lag - 1

    

    if rss_r == 0 or df2 <= 0:

        return {'reject': False, 'p_value': 1.0}

    

    F_stat = (rss_r - rss_unr) / df1 / (rss_unr / df2)

    p_value = 1 - stats.f.cdf(F_stat, df1, df2)

    

    return {

        'F_statistic': F_stat,

        'p_value': p_value,

        'reject': p_value < alpha,

        'causal': p_value < alpha

    }





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("VAR向量自回归模型测试")

    print("=" * 50)

    

    np.random.seed(42)

    

    # 生成VAR(1)模拟数据

    n = 200

    k = 3  # 3个变量

    

    # 真实参数

    A1 = np.array([

        [0.5, 0.1, 0.2],

        [0.2, 0.4, 0.1],

        [0.1, 0.2, 0.6]

    ])

    

    # 生成数据

    Y = np.zeros((n, k))

    Y[0] = np.random.randn(k)

    

    for t in range(1, n):

        Y[t] = A1 @ Y[t-1] + np.random.randn(k) * 0.5

    

    print(f"\n数据生成: {n} 个时间点, {k} 个变量")

    

    # 拟合VAR模型

    print("\n--- VAR模型拟合 ---")

    model = VARModel(p=1)

    result = model.fit(Y)

    

    print(f"VAR(1) 模型拟合完成")

    print(f"残差协方差矩阵:\n{result['sigma']}")

    print(f"AIC: {result['aic']:.4f}")

    print(f"BIC: {result['bic']:.4f}")

    

    print("\n系数矩阵 A1:")

    print(result['coefficients'][0])

    

    # 预测

    print("\n--- 预测 ---")

    Y_pred, Y_cov = model.predict(Y, n_steps=10)

    print(f"未来10步预测前3期:\n{Y_pred[:3]}")

    

    # 脉冲响应

    print("\n--- 脉冲响应 ---")

    irf = model.impulse_response(n_periods=10)

    print(f"脉冲响应形状: {irf.shape}")

    print(f"变量0受到变量1冲击的响应: {irf[:, 0, 1]}")

    

    # 定阶

    print("\n--- 自动定阶 ---")

    ic_results = var_information_criterion(Y, max_p=5)

    print(f"最优滞后阶数 (AIC): {ic_results['best_p_aic']}")

    print(f"最优滞后阶数 (BIC): {ic_results['best_p_bic']}")

    

    # Granger因果检验

    print("\n--- Granger因果检验 ---")

    for i in range(k):

        for j in range(k):

            if i != j:

                result_gc = granger_causality_test(Y, i, j, max_lag=2)

                print(f"变量{i} -> 变量{j}: "

                      f"F={result_gc['F_statistic']:.3f}, "

                      f"p={result_gc['p_value']:.4f}, "

                      f"{'拒绝原假设' if result_gc['reject'] else '不拒绝'}")

    

    print("\n" + "=" * 50)

    print("测试完成")

