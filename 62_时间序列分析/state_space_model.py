# -*- coding: utf-8 -*-

"""

算法实现：时间序列分析 / state_space_model



本文件实现 state_space_model 相关的算法功能。

"""



import numpy as np

from typing import Tuple, Optional





class KalmanFilter:

    """

    卡尔曼滤波器（线性高斯系统）

    

    参数:

        F: 状态转移矩阵

        H: 观测矩阵

        Q: 过程噪声协方差

        R: 观测噪声协方差

        P_init: 初始状态协方差

        x_init: 初始状态

    """

    

    def __init__(self, F: np.ndarray, H: np.ndarray, 

                 Q: np.ndarray, R: np.ndarray,

                 P_init: Optional[np.ndarray] = None,

                 x_init: Optional[np.ndarray] = None):

        self.F = F  # 状态转移矩阵

        self.H = H  # 观测矩阵

        self.Q = Q  # 过程噪声协方差

        self.R = R  # 观测噪声协方差

        self.dim_state = F.shape[0]

        self.dim_obs = H.shape[0]

        

        # 初始化

        if x_init is None:

            self.x = np.zeros(self.dim_state)

        else:

            self.x = x_init

        

        if P_init is None:

            self.P = np.eye(self.dim_state)

        else:

            self.P = P_init

        

        # 存储滤波历史

        self.history = {

            'x_pred': [],    # 预测状态

            'P_pred': [],    # 预测协方差

            'x_update': [],  # 更新后状态

            'P_update': [],  # 更新后协方差

            'innovation': [],  # 新息

            'S': []          # 新息协方差

        }

    

    def predict(self) -> Tuple[np.ndarray, np.ndarray]:

        """

        预测步骤

        

        返回:

            (预测状态, 预测协方差)

        """

        # 状态预测

        self.x_pred = self.F @ self.x

        # 协方差预测

        self.P_pred = self.F @ self.P @ self.F.T + self.Q

        

        return self.x_pred, self.P_pred

    

    def update(self, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:

        """

        更新步骤

        

        参数:

            y: 观测值

        

        返回:

            (更新后状态, 更新后协方差)

        """

        # 计算卡尔曼增益

        S = self.H @ self.P_pred @ self.H.T + self.R

        K = self.P_pred @ self.H.T @ np.linalg.inv(S + 1e-10)

        

        # 新息（观测预测误差）

        innovation = y - self.H @ self.x_pred

        

        # 状态更新

        self.x = self.x_pred + K @ innovation

        

        # 协方差更新（Joseph形式，数值更稳定）

        I_KH = np.eye(self.dim_state) - K @ self.H

        self.P = I_KH @ self.P_pred @ I_KH.T + K @ self.R @ K.T

        

        return self.x, self.P

    

    def filter(self, observations: np.ndarray) -> dict:

        """

        对整个观测序列进行滤波

        

        参数:

            observations: 观测序列 (T, dim_obs)

        

        返回:

            滤波结果字典

        """

        T = len(observations)

        

        # 存储结果

        x_filtered = np.zeros((T, self.dim_state))

        P_filtered = np.zeros((T, self.dim_state, self.dim_state))

        

        # 预测状态序列

        x_predicted = np.zeros((T, self.dim_state))

        P_predicted = np.zeros((T, self.dim_state, self.dim_state))

        

        for t in range(T):

            if t == 0:

                # 初始预测

                x_predicted[t], P_predicted[t] = self.predict()

            else:

                # 使用上一步的更新结果进行预测

                self.x, self.P = x_filtered[t-1], P_filtered[t-1]

                x_predicted[t], P_predicted[t] = self.predict()

            

            # 更新

            x_filtered[t], P_filtered[t] = self.update(observations[t])

        

        return {

            'x_filtered': x_filtered,      # 滤波状态

            'P_filtered': P_filtered,        # 滤波协方差

            'x_predicted': x_predicted,     # 预测状态

            'P_predicted': P_predicted      # 预测协方差

        }

    

    def forecast(self, n_steps: int) -> Tuple[np.ndarray, np.ndarray]:

        """

        未来n步预测

        

        参数:

            n_steps: 预测步数

        

        返回:

            (预测状态序列, 预测协方差序列)

        """

        x_forecast = np.zeros((n_steps, self.dim_state))

        P_forecast = np.zeros((n_steps, self.dim_state, self.dim_state))

        

        for h in range(n_steps):

            x_forecast[h], P_forecast[h] = self.predict()

            # 更新内部状态用于下一步预测

            self.x, self.P = x_forecast[h], P_forecast[h]

        

        return x_forecast, P_forecast





class LocalLinearTrendModel:

    """

    局部线性趋势模型（状态空间形式的指数平滑）

    

    状态: [level, trend]

    状态方程:

        level_t = level_{t-1} + trend_{t-1} + w1_t

        trend_t = trend_{t-1} + w2_t

    

    观测方程:

        y_t = level_t + v_t

    """

    

    def __init__(self, sigma_level: float = 0.1, sigma_trend: float = 0.01, 

                 sigma_obs: float = 1.0):

        self.sigma_level = sigma_level   # 水平噪声标准差

        self.sigma_trend = sigma_trend   # 趋势噪声标准差

        self.sigma_obs = sigma_obs       # 观测噪声标准差

        

        # 状态维度

        self.dim_state = 2

        self.dim_obs = 1

        

        # 初始化卡尔曼滤波器

        self._init_kalman_filter()

    

    def _init_kalman_filter(self):

        """初始化内部卡尔曼滤波器"""

        # 状态转移矩阵

        F = np.array([[1, 1],

                      [0, 1]])

        

        # 观测矩阵

        H = np.array([[1, 0]])

        

        # 过程噪声协方差

        Q = np.array([[self.sigma_level**2, 0],

                      [0, self.sigma_trend**2]])

        

        # 观测噪声协方差

        R = np.array([[self.sigma_obs**2]])

        

        # 初始状态和协方差

        x_init = np.array([0, 0])

        P_init = np.array([[1, 0],

                           [0, 1]])

        

        self.kf = KalmanFilter(F, H, Q, R, P_init, x_init)

    

    def fit(self, y: np.ndarray) -> dict:

        """

        拟合模型

        

        参数:

            y: 时间序列

        

        返回:

            滤波结果

        """

        y = np.array(y).reshape(-1, 1)

        return self.kf.filter(y)

    

    def forecast(self, n_steps: int) -> Tuple[np.ndarray, np.ndarray]:

        """预测未来n步"""

        return self.kf.forecast(n_steps)





class UnobservedComponentsModel:

    """

    未观测成分模型（UCM）

    

    将时间序列分解为：

    - 趋势成分

    - 季节成分

    - 循环成分

    - 残差成分

    

    参数:

        trend_level_var: 趋势水平方差

        trend_slope_var: 趋势斜率方差

        seasonal_period: 季节周期

        seasonal_var: 季节方差

        cycle_var: 循环方差

        obs_var: 观测方差

    """

    

    def __init__(self, trend_level_var: float = 0.1,

                 trend_slope_var: float = 0.01,

                 seasonal_period: int = 12,

                 seasonal_var: float = 0.1,

                 cycle_var: float = 0.1,

                 obs_var: float = 1.0):

        

        self.trend_level_var = trend_level_var

        self.trend_slope_var = trend_slope_var

        self.seasonal_period = seasonal_period

        self.seasonal_var = seasonal_var

        self.cycle_var = cycle_var

        self.obs_var = obs_var

        

        # 计算状态维度

        # 趋势: 2 (level, slope)

        # 季节: period - 1 (最后一个季节由约束决定)

        # 循环: 2 (position, velocity)

        self.dim_state = 2 + (seasonal_period - 1) + 2

        

        self.kf = None

        self._setup_kalman_filter()

    

    def _setup_kalman_filter(self):

        """设置状态空间模型"""

        n = self.dim_state

        

        # 状态转移矩阵

        F = np.eye(n)

        

        # 趋势部分

        F[0, 1] = 1

        

        # 季节部分 - 循环移位矩阵

        seasonal_start = 2

        for i in range(self.seasonal_period - 2):

            F[seasonal_start + i, seasonal_start + i + 1] = 1

        F[seasonal_start + self.seasonal_period - 2, seasonal_start] = 1

        

        # 循环部分

        cycle_start = seasonal_start + self.seasonal_period - 1

        rho = 0.9  # 循环阻尼因子

        omega = 2 * np.pi / 10  # 循环频率

        F[cycle_start, cycle_start] = rho * np.cos(omega)

        F[cycle_start, cycle_start + 1] = rho * np.sin(omega)

        F[cycle_start + 1, cycle_start] = -rho * np.sin(omega)

        F[cycle_start + 1, cycle_start + 1] = rho * np.cos(omega)

        

        # 观测矩阵

        H = np.zeros((1, n))

        H[0, 0] = 1  # 趋势水平

        H[0, 2:seasonal_start] = 1  # 季节成分之和

        

        # 过程噪声协方差

        Q = np.zeros((n, n))

        Q[0, 0] = self.trend_level_var

        Q[1, 1] = self.trend_slope_var

        for i in range(self.seasonal_period - 1):

            Q[2 + i, 2 + i] = self.seasonal_var

        Q[cycle_start, cycle_start] = self.cycle_var

        Q[cycle_start + 1, cycle_start + 1] = self.cycle_var

        

        # 观测噪声

        R = np.array([[self.obs_var]])

        

        # 初始状态协方差

        P_init = np.eye(n) * 10

        

        self.kf = KalmanFilter(F, H, Q, R, P_init)

    

    def fit(self, y: np.ndarray) -> dict:

        """拟合模型"""

        y = np.array(y).reshape(-1, 1)

        self.results = self.kf.filter(y)

        

        # 提取各成分

        self.trend_level = self.results['x_filtered'][:, 0]

        self.trend_slope = self.results['x_filtered'][:, 1]

        

        return self.results

    

    def forecast(self, n_steps: int) -> Tuple[np.ndarray, np.ndarray]:

        """预测"""

        return self.kf.forecast(n_steps)





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("状态空间模型与卡尔曼滤波测试")

    print("=" * 50)

    

    np.random.seed(42)

    

    # 生成测试数据：局部线性趋势 + 噪声

    n = 200

    t = np.arange(n)

    

    # 真实状态

    true_level = 10 + 0.05 * t + 2 * np.sin(2 * np.pi * t / 50)

    true_trend = 0.05 + 2 * np.cos(2 * np.pi * t / 50) * (2 * np.pi / 50)

    

    # 观测

    y = true_level + np.random.randn(n) * 0.5

    

    print(f"\n数据生成: n={n}")

    print(f"真实状态: level从{true_level[0]:.2f}到{true_level[-1]:.2f}")

    

    # 卡尔曼滤波器测试

    print("\n--- 卡尔曼滤波器 (局部线性趋势) ---")

    model = LocalLinearTrendModel(sigma_level=0.1, sigma_trend=0.01, sigma_obs=0.5)

    results = model.fit(y)

    

    print(f"滤波状态形状: {results['x_filtered'].shape}")

    print(f"滤波水平前5点: {results['x_filtered'][:5, 0]}")

    print(f"滤波趋势前5点: {results['x_filtered'][:5, 1]}")

    

    # 预测

    forecast_x, forecast_P = model.forecast(n_steps=10)

    print(f"\n预测10步:")

    print(f"  预测水平: {forecast_x[:3, 0]}")

    print(f"  预测趋势: {forecast_x[:3, 1]}")

    

    # 未观测成分模型

    print("\n--- 未观测成分模型 ---")

    ucm = UnobservedComponentsModel(

        trend_level_var=0.05,

        trend_slope_var=0.01,

        seasonal_period=12,

        seasonal_var=0.05,

        cycle_var=0.02,

        obs_var=0.5

    )

    ucm_results = ucm.fit(y)

    

    print(f"分解趋势水平范围: [{np.min(ucm.trend_level):.2f}, {np.max(ucm.trend_level):.2f}]")

    

    print("\n" + "=" * 50)

    print("测试完成")

