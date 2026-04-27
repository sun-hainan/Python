# -*- coding: utf-8 -*-

"""

算法实现：时间序列分析 / exponential_smoothing



本文件实现 exponential_smoothing 相关的算法功能。

"""



import numpy as np

from typing import Tuple, Optional





class SimpleExponentialSmoothing:

    """一次指数平滑，适用于无趋势序列"""

    

    def __init__(self, alpha: float = 0.3):

        """

        参数:

            alpha: 平滑系数，范围(0, 1)

        """

        self.alpha = alpha

        self.level = None

        self.fitted = False

    

    def fit(self, y: np.ndarray) -> dict:

        """拟合模型"""

        n = len(y)

        

        # 初始化：使用第一个值

        self.level = y[0]

        

        # 递归更新

        for t in range(1, n):

            self.level = self.alpha * y[t] + (1 - self.alpha) * self.level

        

        self.fitted = True

        

        # 计算残差

        fitted_values = np.full(n, self.level)

        residuals = y - fitted_values

        sigma2 = np.var(residuals)

        

        return {

            'level': self.level,

            'sigma2': sigma2,

            'aic': n * np.log(sigma2) + 2

        }

    

    def predict(self, n_periods: int) -> np.ndarray:

        """预测未来值"""

        if not self.fitted:

            raise ValueError("模型未拟合")

        return np.full(n_periods, self.level)





class HoltLinearSmoothing:

    """二次指数平滑，适用于线性趋势数据（Holt线性趋势法）"""

    

    def __init__(self, alpha: float = 0.3, beta: float = 0.1):

        """

        参数:

            alpha: 水平平滑系数

            beta: 趋势平滑系数

        """

        self.alpha = alpha

        self.beta = beta

        self.level = None

        self.trend = None

        self.fitted = False

    

    def fit(self, y: np.ndarray) -> dict:

        """拟合Holt线性趋势模型"""

        n = len(y)

        

        # 初始化

        self.level = y[0]

        self.trend = y[1] - y[0] if n > 1 else 0

        

        # 递归更新

        for t in range(1, n):

            # 上一步的预测值

            y_pred = self.level + self.trend

            

            # 更新水平和趋势

            self.level = self.alpha * y[t] + (1 - self.alpha) * (self.level + self.trend)

            self.trend = self.beta * (self.level - self.level_prev) + (1 - self.beta) * self.trend

            self.level_prev = self.level

        

        self.fitted = True

        

        # 计算拟合值和残差

        fitted = np.zeros(n)

        for t in range(n):

            fitted[t] = self.level if t == 0 else self.level + t * self.trend

        

        residuals = y - fitted

        sigma2 = np.var(residuals)

        

        return {

            'level': self.level,

            'trend': self.trend,

            'sigma2': sigma2,

            'aic': n * np.log(sigma2) + 4

        }

    

    def predict(self, n_periods: int) -> np.ndarray:

        """预测未来n期"""

        if not self.fitted:

            raise ValueError("模型未拟合")

        return np.array([self.level + (i + 1) * self.trend for i in range(n_periods)])





class HoltWintersSmoothing:

    """

    三次指数平滑（ Holt-Winters加法季节性）

    

    状态方程:

    - level: 水平分量

    - trend: 趋势分量

    - seasonal: 季节分量

    

    预测: y[t+h] = level + h*trend + seasonal[t-s+h]

    """

    

    def __init__(self, alpha: float = 0.3, beta: float = 0.1, 

                 gamma: float = 0.1, s: int = 12, m: int = 'additive'):

        """

        参数:

            alpha: 水平平滑系数

            beta: 趋势平滑系数

            gamma: 季节平滑系数

            s: 季节周期

            m: 季节性类型 ('additive' 或 'multiplicative')

        """

        self.alpha = alpha

        self.beta = beta

        self.gamma = gamma

        self.s = s

        self.m = m

        self.level = None

        self.trend = None

        self.seasonal = None

        self.fitted = False

    

    def fit(self, y: np.ndarray) -> dict:

        """拟合Holt-Winters模型"""

        n = len(y)

        

        if n < 2 * self.s:

            raise ValueError(f"数据长度至少需要2倍的季节周期(2*{self.s}={2*self.s})")

        

        # 初始化水平和趋势（使用初期数据拟合线性回归）

        x = np.arange(self.s)

        y_init = y[:self.s]

        

        # 线性回归: y = a + b*t

        X = np.column_stack([np.ones(self.s), x])

        beta_init = np.linalg.lstsq(X, y_init, rcond=None)[0]

        

        self.level = beta_init[0]

        self.trend = beta_init[1]

        

        # 初始化季节因子（第一年的观测值减去趋势）

        self.seasonal = np.zeros(self.s)

        for i in range(self.s):

            self.seasonal[i] = y[i] - (self.level + i * self.trend)

        

        # 递归更新

        for t in range(self.s, n):

            # 预测值

            if self.m == 'additive':

                y_pred = self.level + self.trend + self.seasonal[t % self.s]

            else:

                y_pred = (self.level + self.trend) * self.seasonal[t % self.s]

            

            # 更新水平

            if self.m == 'additive':

                self.level = self.alpha * (y[t] - self.seasonal[t % self.s]) + \

                             (1 - self.alpha) * (self.level + self.trend)

            else:

                self.level = self.alpha * (y[t] / self.seasonal[t % self.s]) + \

                             (1 - self.alpha) * (self.level + self.trend)

            

            # 更新趋势

            self.trend = self.beta * (self.level - self.level_prev) + \

                         (1 - self.beta) * self.trend

            

            # 更新季节因子

            if self.m == 'additive':

                self.seasonal[t % self.s] = self.gamma * (y[t] - self.level - self.trend) + \

                                             (1 - self.gamma) * self.seasonal[t % self.s]

            else:

                self.seasonal[t % self.s] = self.gamma * (y[t] / (self.level + self.trend)) + \

                                             (1 - self.gamma) * self.seasonal[t % self.s]

            

            self.level_prev = self.level

        

        self.fitted = True

        

        # 计算拟合值和残差

        fitted = np.zeros(n)

        for t in range(n):

            if self.m == 'additive':

                fitted[t] = self.level + t * self.trend + self.seasonal[t % self.s]

            else:

                fitted[t] = (self.level + t * self.trend) * self.seasonal[t % self.s]

        

        residuals = y - fitted

        sigma2 = np.var(residuals)

        

        return {

            'level': self.level,

            'trend': self.trend,

            'seasonal': self.seasonal,

            'sigma2': sigma2,

            'aic': n * np.log(sigma2) + 6

        }

    

    def predict(self, n_periods: int) -> np.ndarray:

        """预测未来n_periods期"""

        if not self.fitted:

            raise ValueError("模型未拟合")

        

        predictions = np.zeros(n_periods)

        last_t = len(self.seasonal)  # 已知的季节索引数

        

        for h in range(1, n_periods + 1):

            idx = (last_t + h - 1) % self.s

            

            if self.m == 'additive':

                predictions[h - 1] = self.level + h * self.trend + self.seasonal[idx]

            else:

                predictions[h - 1] = (self.level + h * self.trend) * self.seasonal[idx]

        

        return predictions





def optimize_smoothing_params(y: np.ndarray, model_type: str = 'holt_winters',

                              alpha_range: Tuple[float, float] = (0.1, 0.9),

                              n_grid: int = 10) -> dict:

    """

    通过网格搜索优化平滑参数

    

    参数:

        y: 时间序列

        model_type: 模型类型 ('simple', 'holt', 'holt_winters')

        alpha_range: 参数搜索范围

        n_grid: 网格点数

    

    返回:

        最优参数和结果

    """

    from itertools import product

    

    best_sse = float('inf')

    best_params = {}

    

    alphas = np.linspace(alpha_range[0], alpha_range[1], n_grid)

    

    if model_type == 'simple':

        for alpha in alphas:

            model = SimpleExponentialSmoothing(alpha=alpha)

            result = model.fit(y)

            sse = result['sigma2'] * len(y)

            if sse < best_sse:

                best_sse = sse

                best_params = {'alpha': alpha, 'result': result}

    

    elif model_type == 'holt':

        betas = np.linspace(0.1, 0.5, 5)

        for alpha, beta in product(alphas, betas):

            try:

                model = HoltLinearSmoothing(alpha=alpha, beta=beta)

                result = model.fit(y)

                sse = result['sigma2'] * len(y)

                if sse < best_sse:

                    best_sse = sse

                    best_params = {'alpha': alpha, 'beta': beta, 'result': result}

            except:

                pass

    

    elif model_type == 'holt_winters':

        gammas = np.linspace(0.1, 0.5, 5)

        for alpha, beta, gamma in product(alphas[:5], alphas[:5], gammas):

            try:

                model = HoltWintersSmoothing(alpha=alpha, beta=beta, gamma=gamma, s=12)

                result = model.fit(y)

                sse = result['sigma2'] * len(y)

                if sse < best_sse:

                    best_sse = sse

                    best_params = {'alpha': alpha, 'beta': beta, 'gamma': gamma, 'result': result}

            except:

                pass

    

    return best_params





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("指数平滑法测试 - Holt-Winters三次指数平滑")

    print("=" * 50)

    

    # 生成测试数据：趋势 + 季节 + 噪声

    np.random.seed(42)

    n = 120

    t = np.arange(n)

    

    # 趋势分量

    trend = 0.5 * t

    # 季节分量（年周期12）

    seasonal = 10 * np.sin(2 * np.pi * t / 12)

    # 噪声

    noise = np.random.randn(n) * 2

    

    y = 100 + trend + seasonal + noise

    

    print(f"\n数据生成: n={n}, 均值={np.mean(y):.2f}")

    

    # 一次指数平滑

    print("\n--- 一次指数平滑 ---")

    model1 = SimpleExponentialSmoothing(alpha=0.3)

    result1 = model1.fit(y)

    print(f"平滑水平: {result1['level']:.2f}")

    pred1 = model1.predict(12)

    print(f"预测12期: {pred1[:3]}...")

    

    # 二次指数平滑（Holt线性趋势）

    print("\n--- Holt线性趋势 ---")

    model2 = HoltLinearSmoothing(alpha=0.3, beta=0.1)

    result2 = model2.fit(y)

    print(f"水平: {result2['level']:.2f}, 趋势: {result2['trend']:.2f}")

    pred2 = model2.predict(12)

    print(f"预测12期: {pred2[:3]}...")

    

    # 三次指数平滑（Holt-Winters）

    print("\n--- Holt-Winters加法季节性 ---")

    model3 = HoltWintersSmoothing(alpha=0.2, beta=0.1, gamma=0.1, s=12, m='additive')

    result3 = model3.fit(y)

    print(f"水平: {result3['level']:.2f}")

    print(f"趋势: {result3['trend']:.2f}")

    print(f"季节因子前4个: {result3['seasonal'][:4]}")

    pred3 = model3.predict(12)

    print(f"预测12期: {pred3}")

    

    print("\n" + "=" * 50)

    print("测试完成")

