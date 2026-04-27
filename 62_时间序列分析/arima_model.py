# -*- coding: utf-8 -*-

"""

算法实现：时间序列分析 / arima_model



本文件实现 arima_model 相关的算法功能。

"""



import numpy as np

import pandas as pd

from typing import Tuple, Optional

from scipy import stats





class ARIMAModel:

    """ARIMA模型类，支持参数估计和预测"""

    

    def __init__(self, p: int = 1, d: int = 1, q: int = 1):

        """

        初始化ARIMA模型

        

        参数:

            p: 自回归项阶数

            d: 差分阶数

            q: 滑动平均阶数

        """

        self.p = p

        self.d = d

        self.q = q

        self.ar_params = None  # AR参数 phi

        self.ma_params = None  # MA参数 theta

        self.residuals = None   # 残差

        self.fitted = False

    

    def difference(self, y: np.ndarray, d: int = 1) -> np.ndarray:

        """

        对序列进行d阶差分

        

        参数:

            y: 原始序列

            d: 差分阶数

        

        返回:

            差分后的序列

        """

        y_diff = y.copy()

        for _ in range(d):

            y_diff = np.diff(y_diff)

        return y_diff

    

    def inverse_difference(self, y_diff: np.ndarray, y_orig: np.ndarray, d: int = 1) -> np.ndarray:

        """

        逆差分操作，将差分序列还原

        

        参数:

            y_diff: 差分后的序列

            y_orig: 原始序列的最后d个值

            d: 差分阶数

        

        返回:

            还原后的序列

        """

        y_recovered = y_diff.copy()

        for i in range(d):

            y_recovered = np.concatenate([[0], np.cumsum(y_recovered)]) + \

                          np.concatenate([y_orig[:i+1], np.zeros(len(y_recovered) - i - 1)])[i]

        return y_recovered

    

    def fit(self, y: np.ndarray) -> dict:

        """

        拟合ARIMA模型，使用最小二乘法估计参数

        

        参数:

            y: 时间序列数据

        

        返回:

            包含拟合结果的字典

        """

        n = len(y)

        

        # 差分处理

        if self.d > 0:

            y_diff = self.difference(y, self.d)

        else:

            y_diff = y.copy()

        

        T = len(y_diff)

        

        # 构建回归矩阵

        # AR部分: y[t] = phi1*y[t-1] + ... + phi_p*y[t-p]

        # MA部分: y[t] = theta1*e[t-1] + ... + theta_q*e[t-q]

        

        max_lag = max(self.p, self.q)

        if max_lag >= T:

            raise ValueError(f"滞后阶数过大，数据点不足")

        

        # 使用OLS估计AR参数（简化版本）

        X = np.zeros((T - max_lag, self.p))

        Y = y_diff[max_lag:]

        

        for i in range(self.p):

            X[:, i] = y_diff[max_lag - 1 - i : T - 1 - i]

        

        # 最小二乘估计

        XTX = X.T @ X

        XTY = X.T @ Y

        

        # 加正则化避免奇异矩阵

        XTX += np.eye(self.p) * 1e-6

        self.ar_params = np.linalg.solve(XTX, XTY)

        

        # 计算残差

        self.residuals = Y - X @ self.ar_params

        

        # MA参数估计（简化：使用残差自相关）

        self.ma_params = np.zeros(self.q)

        if self.q > 0 and len(self.residuals) > self.q:

            # 通过残差的滞后相关性估计MA参数

            for j in range(self.q):

                self.ma_params[j] = np.corrcoef(

                    self.residuals[self.q - j:],

                    self.residuals[:len(self.residuals) - self.q + j]

                )[0, 1] * np.std(self.residuals) / (np.std(self.residuals) + 1e-6)

        

        self.fitted = True

        

        # 计算AIC/BIC

        sigma2 = np.var(self.residuals)

        n_params = self.p + self.q + 1

        aic = n * np.log(sigma2) + 2 * n_params

        bic = n * np.log(sigma2) + n_params * np.log(n)

        

        return {

            'ar_params': self.ar_params,

            'ma_params': self.ma_params,

            'sigma2': sigma2,

            'aic': aic,

            'bic': bic,

            'residuals': self.residuals

        }

    

    def predict(self, n_periods: int, y_history: Optional[np.ndarray] = None) -> np.ndarray:

        """

        预测未来n_periods个时间点

        

        参数:

            n_periods: 预测步数

            y_history: 历史数据（用于递归预测）

        

        返回:

            预测值数组

        """

        if not self.fitted:

            raise ValueError("模型尚未拟合，请先调用fit方法")

        

        if y_history is None:

            raise ValueError("需要提供历史数据用于预测")

        

        # 逆差分还原需要的原始序列

        y_orig = y_history[-self.d:] if self.d > 0 else y_history[-1:]

        y_diff_history = self.difference(y_history, self.d)

        

        predictions = []

        current_ar = list(y_diff_history[-self.p:])

        current_ma_resid = list(self.residuals[-self.q:]) if self.residuals is not None else [0] * self.q

        

        for _ in range(n_periods):

            # AR部分

            pred_diff = np.dot(self.ar_params, current_ar[-self.p:]) if self.p > 0 else 0

            

            # MA部分

            for j in range(self.q):

                pred_diff += self.ma_params[j] * current_ma_resid[-(j + 1)]

            

            predictions.append(pred_diff)

            

            # 更新AR滞后

            current_ar.append(pred_diff)

            # 更新MA残差

            current_ma_resid.append(pred_diff - np.dot(self.ar_params, current_ar[-self.p:]))

        

        # 逆差分还原

        if self.d > 0:

            predictions = self.inverse_difference(np.array(predictions), y_orig, self.d)

        

        return np.array(predictions)





def adf_test(y: np.ndarray) -> Tuple[float, float]:

    """

    ADF检验（Augmented Dickey-Fuller Test）

    检验序列是否存在单位根（是否平稳）

    

    参数:

        y: 时间序列

    

    返回:

        (检验统计量, p值)

    """

    n = len(y)

    # 一阶差分

    dy = np.diff(y)

    

    # 回归: dy = alpha + beta*t + rho*y[t-1] + gamma1*dy[t-1] + ...

    y_lag = y[:-1]

    t = np.arange(n - 1)

    

    X = np.column_stack([np.ones(n - 1), t, y_lag])

    

    for lag in range(1, min(5, n // 5)):

        X = np.column_stack([X, dy[:-lag]])

    

    try:

        beta = np.linalg.lstsq(X, dy, rcond=None)[0]

        residuals = dy - X @ beta

        se = np.std(residuals)

        

        # t统计量

        t_stat = beta[2] / (se + 1e-10)

        

        # 简化的p值估计

        p_value = 2 * (1 - stats.norm.cdf(abs(t_stat)))

        

        return t_stat, p_value

    except:

        return 0.0, 1.0





def auto_arima(y: np.ndarray, max_p: int = 5, max_d: int = 2, max_q: int = 5) -> ARIMAModel:

    """

    自动选择最优ARIMA参数，使用AIC准则

    

    参数:

        y: 时间序列

        max_p, max_d, max_q: 参数搜索上界

    

    返回:

        最优ARIMA模型

    """

    best_aic = float('inf')

    best_model = None

    

    for p in range(max_p + 1):

        for d in range(max_d + 1):

            for q in range(max_q + 1):

                try:

                    model = ARIMAModel(p=p, d=d, q=q)

                    result = model.fit(y)

                    aic = result['aic']

                    

                    if aic < best_aic:

                        best_aic = aic

                        best_model = model

                        print(f"p={p}, d={d}, q={q}, AIC={aic:.2f}")

                except Exception as e:

                    continue

    

    return best_model





# 测试代码

if __name__ == "__main__":

    # 生成模拟数据：AR(1) + 噪声

    np.random.seed(42)

    n = 200

    phi = 0.7  # AR参数

    alpha = 5  # 截距

    sigma = 1  # 噪声标准差

    

    y = np.zeros(n)

    y[0] = alpha / (1 - phi) + np.random.randn() * sigma

    for t in range(1, n):

        y[t] = alpha + phi * y[t-1] + np.random.randn() * sigma

    

    print("=" * 50)

    print("ARIMA模型测试")

    print("=" * 50)

    

    # ADF检验

    t_stat, p_value = adf_test(y)

    print(f"\nADF检验: t统计量={t_stat:.4f}, p值={p_value:.4f}")

    print(f"结论: 序列{'平稳' if p_value < 0.05 else '非平稳'}")

    

    # 拟合ARIMA模型

    model = ARIMAModel(p=1, d=1, q=1)

    result = model.fit(y)

    

    print(f"\n拟合结果:")

    print(f"  AR参数: {result['ar_params']}")

    print(f"  MA参数: {result['ma_params']}")

    print(f"  残差方差: {result['sigma2']:.4f}")

    print(f"  AIC: {result['aic']:.2f}")

    print(f"  BIC: {result['bic']:.2f}")

    

    # 预测

    forecast = model.predict(n_periods=10, y_history=y)

    print(f"\n未来10期预测:")

    print(f"  {forecast[:5]}")

    print(f"  ...")

    

    # 自动定阶

    print("\n自动定阶搜索（简化版）:")

    auto_model = auto_arima(y[:100], max_p=2, max_d=1, max_q=2)

    if auto_model:

        print(f"最优参数: p={auto_model.p}, d={auto_model.d}, q={auto_model.q}")

