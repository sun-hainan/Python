# -*- coding: utf-8 -*-

"""

算法实现：因果推断算法 / s_learner



本文件实现 s_learner 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Optional

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor

from sklearn.linear_model import LinearRegression





class SLearner:

    """

    S-Learner单学习器

    

    使用单一模型，t作为特征

    """

    

    def __init__(self, model_class=None, model_params: dict = None):

        """

        初始化

        

        Args:

            model_class: 模型类

            model_params: 模型参数

        """

        self.model_class = model_class or LinearRegression

        self.model_params = model_params or {}

        self.model = None

    

    def fit(self, X: np.ndarray, T: np.ndarray, Y: np.ndarray):

        """

        拟合模型

        

        Args:

            X: 协变量

            T: 处理指示

            Y: 结果

        """

        # 将T作为特征加入

        X_with_T = np.column_stack([X, T])

        

        self.model = self.model_class(**self.model_params)

        self.model.fit(X_with_T, Y)

    

    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:

        """

        预测处理效应

        

        Args:

            X: 协变量

        

        Returns:

            (tau_hat, tau_se) - CATE估计和标准误

        """

        # 预测T=0的情况

        X0 = np.column_stack([X, np.zeros(len(X))])

        mu0 = self.model.predict(X0)

        

        # 预测T=1的情况

        X1 = np.column_stack([X, np.ones(len(X))])

        mu1 = self.model.predict(X1)

        

        # CATE

        tau = mu1 - mu0

        

        # 标准误（简化）

        tau_se = np.std(tau) / np.sqrt(len(tau))

        

        return tau, tau_se

    

    def predict_ite(self, X: np.ndarray, T: np.ndarray, Y: np.ndarray) -> np.ndarray:

        """

        预测个体处理效应

        

        Args:

            X: 协变量

            T: 处理指示

            Y: 结果

        

        Returns:

            ITE估计

        """

        tau, _ = self.predict(X)

        return tau





class SLearnerWithConfidence:

    """

    带置信区间的S-Learner

    """

    

    def __init__(self, n_estimators: int = 100):

        self.n_estimators = n_estimators

        self.models = []

    

    def fit(self, X: np.ndarray, T: np.ndarray, Y: np.ndarray):

        """拟合多个模型"""

        for _ in range(self.n_estimators):

            # 自助采样

            indices = np.random.choice(len(X), len(X), replace=True)

            X_boot = X[indices]

            T_boot = T[indices]

            Y_boot = Y[indices]

            

            model = GradientBoostingRegressor(n_estimators=50)

            model.fit(np.column_stack([X_boot, T_boot]), Y_boot)

            self.models.append(model)

    

    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:

        """

        预测

        

        Returns:

            (mean_effect, confidence_interval)

        """

        # 预测T=0和T=1

        X0 = np.column_stack([X, np.zeros(len(X))])

        X1 = np.column_stack([X, np.ones(len(X))])

        

        effects = []

        

        for model in self.models:

            mu0 = model.predict(X0)

            mu1 = model.predict(X1)

            effects.append(mu1 - mu0)

        

        effects = np.array(effects)

        

        mean_effect = effects.mean(axis=0)

        ci_lower = np.percentile(effects, 2.5, axis=0)

        ci_upper = np.percentile(effects, 97.5, axis=0)

        

        return mean_effect, (ci_lower, ci_upper)





class SLearnerCate:

    """

    用于CATE估计的S-Learner改进

    """

    

    def __init__(self):

        self.models = []

        self.propensity_model = None

    

    def fit(self, X: np.ndarray, T: np.ndarray, Y: np.ndarray):

        """拟合"""

        from sklearn.linear_model import LogisticRegression

        

        # 倾向得分模型

        self.propensity_model = LogisticRegression()

        self.propensity_model.fit(X, T)

        

        # 逆概率加权

        pscore = self.propensity_model.predict_proba(X)[:, 1]

        ipw = T / (pscore + 1e-10) - (1 - T) / (1 - pscore + 1e-10)

        

        # 加权数据

        weights = np.abs(ipw)

        

        # 拟合模型

        X_with_T = np.column_stack([X, T])

        self.model = GradientBoostingRegressor(n_estimators=50)

        self.model.fit(X_with_T, Y, sample_weight=weights)

    

    def predict(self, X: np.ndarray) -> np.ndarray:

        """预测"""

        X0 = np.column_stack([X, np.zeros(len(X))])

        X1 = np.column_stack([X, np.ones(len(X))])

        

        mu0 = self.model.predict(X0)

        mu1 = self.model.predict(X1)

        

        return mu1 - mu0





def demo_s_learner():

    """演示S-Learner"""

    print("=== S-Learner演示 ===\n")

    

    np.random.seed(42)

    

    # 生成数据

    n = 1000

    

    X = np.random.randn(n, 2)

    T = (X[:, 0] + X[:, 1] > 0).astype(int)

    

    # 异质性处理效应

    tau = 1 + 0.5 * X[:, 0]

    Y = tau * T + X[:, 0] + X[:, 1] + np.random.randn(n) * 0.1

    

    print(f"样本量: {n}")

    print(f"效应: τ(x) = 1 + 0.5 * X₁")

    

    # S-Learner

    learner = SLearner()

    learner.fit(X, T, Y)

    

    tau_hat, se = learner.predict(X)

    

    print(f"\nS-Learner结果:")

    print(f"  估计效应均值: {tau_hat.mean():.4f}")

    print(f"  真实效应均值: {tau.mean():.4f}")

    

    # 分组结果

    print("\n按X₁分组:")

    for x1_range in [(-2, 0), (0, 2)]:

        mask = (X[:, 0] >= x1_range[0]) & (X[:, 0] < x1_range[1])

        print(f"  X₁ ∈ [{x1_range[0]}, {x1_range[1]}):")

        print(f"    估计: {tau_hat[mask].mean():.4f}")

        print(f"    真值: {tau[mask].mean():.4f}")





def demo_s_vs_t():

    """对比S-Learner和T-Learner"""

    print("\n=== S-Learner vs T-Learner ===\n")

    

    print("S-Learner:")

    print("  - 一个模型")

    print("  - T作为特征")

    print("  - μ(x, t) 联合建模")

    print("  - 简单但可能有偏")

    

    print("\nT-Learner:")

    print("  - 两个模型")

    print("  - μ₀(x)和μ₁(x)分别建模")

    print("  - 更灵活")

    print("  - 样本量需求大")





def demo_s_learner_advantages():

    """演示S-Learner优缺点"""

    print("\n=== S-Learner优缺点 ===\n")

    

    print("优点:")

    print("  - 实现简单")

    print("  - 可用任意回归模型")

    print("  - 样本量需求相对较低")

    

    print("\n缺点:")

    print("  - 处理效应可能被低估")

    print("  - 对模型假设敏感")

    print("  - 不适合高维稀疏数据")





def demo_s_learner_variants():

    """演示S-Learner变体"""

    print("\n=== S-Learner变体 ===\n")

    

    print("1. 带置信区间:")

    print("   - Bootstrap多次拟合")

    print("   - 估计不确定性")

    

    print("\n2. 逆概率加权:")

    print("   - 减少选择偏差")

    print("   - 更稳健")

    

    print("\n3. 双重稳健:")

    print("   - 结合回归和IPW")

    print("   - 半参数效率")





if __name__ == "__main__":

    print("=" * 60)

    print("S-Learner 单机器学习方法")

    print("=" * 60)

    

    # S-Learner演示

    demo_s_learner()

    

    # S vs T

    demo_s_vs_t()

    

    # 优缺点

    demo_s_learner_advantages()

    

    # 变体

    demo_s_learner_variants()

    

    print("\n" + "=" * 60)

    print("S-Learner核心:")

    print("=" * 60)

    print("""

1. 方法:

   - 单一模型 μ(x, t)

   - T作为特征

   - τ(x) = μ(x, 1) - μ(x, 0)



2. 实现:

   - 任意回归模型

   - 联合建模处理和结果



3. 优缺点:

   - 简单易实现

   - 但处理效应可能被模型低估

   - 不如T-Learner灵活



4. 适用:

   - 基线模型

   - 快速原型

   - 样本量较小时

""")

