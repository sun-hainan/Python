# -*- coding: utf-8 -*-

"""

算法实现：时间序列分析 / garch_model



本文件实现 garch_model 相关的算法功能。

"""



import numpy as np

from typing import Tuple, Optional

from scipy import stats, optimize





class GARCHModel:

    """

    GARCH模型类

    

    参数:

        p: ARCH项阶数 (ε²的滞后)

        q: GARCH项阶数 (σ²的滞后)

    """

    

    def __init__(self, p: int = 1, q: int = 1):

        self.p = p

        self.q = q

        self.params = None  # [omega, alpha_1,...,alpha_p, beta_1,...,beta_q]

        self.residuals = None

        self.conditional_volatility = None

        self.fitted = False

    

    def _garch_variance(self, returns: np.ndarray, params: np.ndarray) -> np.ndarray:

        """

        计算条件方差序列

        

        参数:

            returns: 收益率序列

            params: 参数向量 [omega, alpha_1,...,alpha_p, beta_1,...,beta_q]

        

        返回:

            条件方差序列

        """

        n = len(returns)

        omega = params[0]

        alpha = params[1:self.p + 1]

        beta = params[self.p + 1:]

        

        h = np.zeros(n)

        

        # 初始化

        for i in range(max(self.p, self.q)):

            h[i] = omega / (1 - np.sum(alpha) - np.sum(beta) + 1e-10)

        

        # 递归计算

        for t in range(max(self.p, self.q), n):

            h[t] = omega

            

            # ARCH项

            for i in range(self.p):

                if t - i - 1 >= 0:

                    h[t] += alpha[i] * (returns[t - i - 1] ** 2)

            

            # GARCH项

            for j in range(self.q):

                if t - j - 1 >= 0:

                    h[t] += beta[j] * h[t - j - 1]

        

        return h

    

    def _negative_log_likelihood(self, params: np.ndarray, returns: np.ndarray) -> float:

        """负对数似然函数"""

        n = len(returns)

        

        # 参数约束

        if params[0] <= 0:  # omega > 0

            return 1e10

        if np.any(params[1:self.p + 1] < 0) or np.any(params[1:self.p + 1] > 0.99):  # alpha >= 0

            return 1e10

        if np.any(params[self.p + 1:] < 0) or np.any(params[self.p + 1:] > 0.99):  # beta >= 0

            return 1e10

        if np.sum(params[1:self.p + 1]) + np.sum(params[self.p + 1:]) >= 0.999:  # 稳定性

            return 1e10

        

        # 计算条件方差

        h = self._garch_variance(returns, params)

        

        # 对数似然（正态分布假设）

        # L = -0.5 * sum(log(h_t) + r_t^2 / h_t)

        log_likelihood = -0.5 * np.sum(np.log(h + 1e-10) + (returns ** 2) / (h + 1e-10))

        

        return -log_likelihood

    

    def fit(self, returns: np.ndarray) -> dict:

        """

        拟合GARCH模型

        

        参数:

            returns: 收益率序列

        

        返回:

            拟合结果字典

        """

        n = len(returns)

        

        # 参数个数: omega + p(alpha) + q(beta)

        n_params = 1 + self.p + self.q

        

        # 初始参数猜测

        # omega = 0.01 * var(returns)

        # alpha = 0.1

        # beta = 0.8

        omega_init = 0.01 * np.var(returns)

        alpha_init = [0.1] * self.p

        beta_init = [0.8] * self.q

        

        initial_params = np.array([omega_init] + alpha_init + beta_init)

        

        # 优化

        result = optimize.minimize(

            self._negative_log_likelihood,

            initial_params,

            args=(returns,),

            method='L-BFGS-B',

            bounds=[(1e-6, None)] + [(0, 0.99)] * (n_params - 1)

        )

        

        self.params = result.x

        

        # 计算残差和条件波动率

        h = self._garch_variance(returns, self.params)

        self.conditional_volatility = np.sqrt(h)

        self.residuals = returns / self.conditional_volatility

        

        self.fitted = True

        

        # 计算信息准则

        nll = result.fun

        aic = 2 * nll + 2 * n_params

        bic = 2 * nll + n_params * np.log(n)

        

        return {

            'params': self.params,

            'omega': self.params[0],

            'alpha': self.params[1:self.p + 1],

            'beta': self.params[self.p + 1:],

            'conditional_volatility': self.conditional_volatility,

            'aic': aic,

            'bic': bic,

            'log_likelihood': -nll

        }

    

    def predict_volatility(self, n_steps: int) -> np.ndarray:

        """

        预测未来波动率

        

        参数:

            n_steps: 预测步数

        

        返回:

            预测波动率序列

        """

        if not self.fitted:

            raise ValueError("模型未拟合")

        

        # 使用最后一个条件方差作为起点

        h_last = self.conditional_volatility[-1]

        omega = self.params[0]

        alpha = self.params[1:self.p + 1]

        beta = self.params[self.p + 1:]

        

        # 无冲击下的长期波动率（无条件方差）

        h_uncond = omega / (1 - np.sum(alpha) - np.sum(beta) + 1e-10)

        

        # 简单预测：假设方差回归到无条件方差

        decay = np.sum(alpha) + np.sum(beta)

        

        forecasts = np.zeros(n_steps)

        h_current = h_last

        

        for i in range(n_steps):

            h_current = (1 - decay) * h_uncond + decay * h_current

            forecasts[i] = np.sqrt(h_current)

        

        return forecasts

    

    def forecast(self, n_steps: int, last_return: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray]:

        """

        预测未来收益和波动率

        

        参数:

            n_steps: 预测步数

            last_return: 最后一个观测收益（用于更新）

        

        返回:

            (预测波动率, 预测区间)

        """

        vol = self.predict_volatility(n_steps)

        

        # 95%预测区间（假设正态）

        z_critical = 1.96

        

        lower = -z_critical * vol

        upper = z_critical * vol

        

        return vol, np.column_stack([lower, upper])





class GJRGARCHModel:

    """

    GJR-GARCH模型（非对称GARCH）

    

    允许负收益（坏消息）对波动率有更大的影响

    

    σ_t² = ω + Σα_i * ε_{t-i}² + Σγ_i * I_{t-i} * ε_{t-i}² + Σβ_j * σ_{t-j}²

    

    其中 I_t = 1 如果 ε_t < 0（利空消息）

    """

    

    def __init__(self, p: int = 1, q: int = 1):

        self.p = p

        self.q = q

        self.params = None

        self.conditional_volatility = None

        self.fitted = False

    

    def _gjrgarch_variance(self, returns: np.ndarray, params: np.ndarray) -> np.ndarray:

        """计算GJR-GARCH条件方差"""

        n = len(returns)

        omega = params[0]

        alpha = params[1:self.p + 1]

        gamma = params[self.p + 1:2 * self.p + 1]

        beta = params[2 * self.p + 1:]

        

        h = np.zeros(n)

        

        for i in range(max(self.p, self.q)):

            h[i] = omega / (1 - np.sum(alpha) - 0.5 * np.sum(gamma) - np.sum(beta) + 1e-10)

        

        for t in range(max(self.p, self.q), n):

            h[t] = omega

            

            for i in range(self.p):

                if t - i - 1 >= 0:

                    h[t] += alpha[i] * (returns[t - i - 1] ** 2)

                    # 非对称项：负收益时有额外的冲击

                    if returns[t - i - 1] < 0:

                        h[t] += gamma[i] * (returns[t - i - 1] ** 2)

            

            for j in range(self.q):

                if t - j - 1 >= 0:

                    h[t] += beta[j] * h[t - j - 1]

        

        return h

    

    def fit(self, returns: np.ndarray) -> dict:

        """拟合GJR-GARCH模型"""

        n = len(returns)

        n_params = 1 + 2 * self.p + self.q

        

        # 初始参数

        omega_init = 0.01 * np.var(returns)

        alpha_init = [0.1] * self.p

        gamma_init = [0.05] * self.p  # 非对称效应

        beta_init = [0.8] * self.q

        

        initial_params = np.array([omega_init] + alpha_init + gamma_init + beta_init)

        

        # 定义负对数似然

        def neg_ll(params, returns):

            if params[0] <= 0 or np.any(params < 0) or np.sum(params[1:self.p + 1]) + np.sum(params[self.p + 1:2 * self.p + 1]) + np.sum(params[-self.q:]) >= 0.999:

                return 1e10

            

            h = self._gjrgarch_variance(returns, params)

            ll = -0.5 * np.sum(np.log(h + 1e-10) + (returns ** 2) / (h + 1e-10))

            return -ll

        

        result = optimize.minimize(neg_ll, initial_params, args=(returns,), method='L-BFGS-B')

        

        self.params = result.x

        h = self._gjrgarch_variance(returns, self.params)

        self.conditional_volatility = np.sqrt(h)

        

        self.fitted = True

        

        return {

            'params': self.params,

            'omega': self.params[0],

            'alpha': self.params[1:self.p + 1],

            'gamma': self.params[self.p + 1:2 * self.p + 1],

            'beta': self.params[2 * self.p + 1:],

            'conditional_volatility': self.conditional_volatility

        }





def generate_garch_data(n: int = 1000, omega: float = 0.01, 

                        alpha: float = 0.1, beta: float = 0.85) -> np.ndarray:

    """

    生成GARCH模拟数据

    

    参数:

        n: 数据点数量

        omega, alpha, beta: GARCH参数

    

    返回:

        模拟收益率序列

    """

    np.random.seed(42)

    

    returns = np.zeros(n)

    h = np.zeros(n)

    

    # 初始条件

    h[0] = omega / (1 - alpha - beta)

    

    for t in range(1, n):

        h[t] = omega + alpha * (returns[t-1] ** 2) + beta * h[t-1]

        returns[t] = np.sqrt(h[t]) * np.random.randn()

    

    return returns





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("GARCH波动率模型测试")

    print("=" * 50)

    

    np.random.seed(42)

    

    # 生成模拟数据

    returns = generate_garch_data(n=1000, omega=0.01, alpha=0.1, beta=0.85)

    

    print(f"\n数据统计:")

    print(f"  均值: {np.mean(returns):.4f}")

    print(f"  标准差: {np.std(returns):.4f}")

    print(f"  偏度: {stats.skew(returns):.4f}")

    print(f"  峰度: {stats.kurtosis(returns):.4f}")

    

    # 拟合GARCH(1,1)

    print("\n--- GARCH(1,1)拟合 ---")

    model = GARCHModel(p=1, q=1)

    result = model.fit(returns)

    

    print(f"参数估计:")

    print(f"  ω (omega): {result['omega']:.6f}")

    print(f"  α (alpha): {result['alpha']}")

    print(f"  β (beta): {result['beta']}")

    print(f"  AIC: {result['aic']:.2f}")

    print(f"  BIC: {result['bic']:.2f}")

    

    # 波动率序列

    print(f"\n波动率统计:")

    vol = result['conditional_volatility']

    print(f"  均值: {np.mean(vol):.4f}")

    print(f"  范围: [{np.min(vol):.4f}, {np.max(vol):.4f}]")

    

    # 预测波动率

    print("\n--- 波动率预测 ---")

    vol_forecast = model.predict_volatility(n_steps=10)

    print(f"未来10期预测波动率: {vol_forecast[:5]}...")

    

    # 生成非对称数据（杠杆效应）

    print("\n--- GJR-GARCH杠杆效应测试 ---")

    n = 500

    leverage_returns = np.zeros(n)

    h = np.zeros(n)

    h[0] = 0.01

    

    for t in range(1, n):

        # 负收益带来更大的冲击

        shock = np.random.randn()

        if t > 1 and leverage_returns[t-1] < 0:

            shock *= 1.5  # 杠杆效应

        h[t] = 0.01 + 0.08 * (leverage_returns[t-1] ** 2) + 0.85 * h[t-1]

        leverage_returns[t] = np.sqrt(h[t]) * shock

    

    # 拟合GJR-GARCH

    gjrmodel = GJRGARCHModel(p=1, q=1)

    gjr_result = gjrmodel.fit(leverage_returns)

    

    print(f"GJR-GARCH杠杆参数 γ: {gjr_result['gamma']}")

    

    # ARCH效应检验

    print("\n--- ARCH效应检验 ---")

    from statsmodels.stats.diagnostic import acorr_ljungbox

    

    # 对残差平方进行Ljung-Box检验

    squared_residuals = model.residuals ** 2

    lb_result = acorr_ljungbox(squared_residuals, lags=[10], return_df=True)

    print(f"Ljung-Box检验 (残差平方): Q={lb_result['lb_stat'].values[0]:.2f}, p={lb_result['lb_pvalue'].values[0]:.4f}")

    

    print("\n" + "=" * 50)

    print("测试完成")

