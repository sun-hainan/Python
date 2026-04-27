# -*- coding: utf-8 -*-

"""

算法实现：因果推断算法 / metalearner



本文件实现 metalearner 相关的算法功能。

"""



import numpy as np

import pandas as pd

from typing import Dict, List, Tuple, Optional, Callable

from dataclasses import dataclass

from abc import ABC, abstractmethod

import copy





@dataclass

class MetaLearnerConfig:

    """元学习器配置"""

    model_type: str = "random_forest"  # 模型类型

    n_estimators: int = 100  # 树数量

    max_depth: int = 5  # 最大深度

    min_samples_leaf: int = 10  # 叶节点最小样本

    propensity_model: str = "logistic"  # 倾向性模型

    use_ipw: bool = False  # 是否使用逆概率加权

    use_dr: bool = True  # 是否使用双重稳健估计





class BaseMetaLearner(ABC):

    """元学习器基类"""



    def __init__(self, config: MetaLearnerConfig = None):

        self.config = config or MetaLearnerConfig()

        self.models: Dict[str, any] = {}

        self.trained = False

        self.feature_names: List[str] = []



    @abstractmethod

    def fit(self, X: pd.DataFrame, T: np.ndarray, Y: np.ndarray) -> 'BaseMetaLearner':

        """训练模型"""

        pass



    @abstractmethod

    def predict_ite(self, X: pd.DataFrame) -> np.ndarray:

        """预测个体处理效应"""

        pass



    def predict_ate(self, X: pd.DataFrame) -> float:

        """预测平均处理效应"""

        return np.mean(self.predict_ite(X))



    def _prepare_data(self, X: pd.DataFrame, T: np.ndarray, Y: np.ndarray):

        """准备训练数据"""

        self.feature_names = list(X.columns)

        return X, T, Y





class SLearner(BaseMetaLearner):

    """

    S-Learner (Single Model Learner)



    方法: 使用单个模型学习 E[Y | X, T]

    ITE估计: τ(x) = E[Y | X=x, T=1] - E[Y | X=x, T=0]



    优点: 简单,能利用所有数据

    缺点: 处理变量可能被视为不重要特征

    """



    def fit(self, X: pd.DataFrame, T: np.ndarray, Y: np.ndarray) -> 'SLearner':

        """训练S-Learner"""

        X, T, Y = self._prepare_data(X, T, Y)



        # 创建组合特征: [X, T]

        X_with_t = X.copy()

        X_with_t["T"] = T



        # 训练单个模型

        self.model_ = self._create_model()

        self.model_.fit(X_with_t, Y)



        self.trained = True

        return self



    def predict_ite(self, X: pd.DataFrame) -> np.ndarray:

        """预测ITE"""

        if not self.trained:

            raise ValueError("模型未训练")



        X = self._ensure_dataframe(X)



        # 预测 T=0 和 T=1 的结果

        X0 = X.copy()

        X0["T"] = 0

        X1 = X.copy()

        X1["T"] = 1



        y0 = self.model_.predict(X0)

        y1 = self.model_.predict(X1)



        return y1 - y0



    def _create_model(self):

        """创建模型"""

        from sklearn.ensemble import GradientBoostingRegressor

        return GradientBoostingRegressor(

            n_estimators=self.config.n_estimators,

            max_depth=self.config.max_depth,

            min_samples_leaf=self.config.min_samples_leaf

        )



    def _ensure_dataframe(self, X) -> pd.DataFrame:

        if not isinstance(X, pd.DataFrame):

            return pd.DataFrame(X, columns=self.feature_names)

        return X





class TLearner(BaseMetaLearner):

    """

    T-Learner (Two Model Learner)



    方法: 分别训练控制组和处理组模型

    ITE估计: τ(x) = μ₁(x) - μ₀(x)



    详见 t_learner.py

    """



    def fit(self, X: pd.DataFrame, T: np.ndarray, Y: np.ndarray) -> 'TLearner':

        """训练T-Learner"""

        X, T, Y = self._prepare_data(X, T, Y)



        # 分割数据

        X_c = X[T == 0]

        Y_c = Y[T == 0]

        X_t = X[T == 1]

        Y_t = Y[T == 1]



        # 训练控制组模型

        self.model_c = self._create_model()

        self.model_c.fit(X_c, Y_c)



        # 训练处理组模型

        self.model_t = self._create_model()

        self.model_t.fit(X_t, Y_t)



        self.trained = True

        return self



    def predict_ite(self, X: pd.DataFrame) -> np.ndarray:

        """预测ITE"""

        if not self.trained:

            raise ValueError("模型未训练")



        X = self._ensure_dataframe(X)



        y0 = self.model_c.predict(X)

        y1 = self.model_t.predict(X)



        return y1 - y0



    def _create_model(self):

        from sklearn.ensemble import GradientBoostingRegressor

        return GradientBoostingRegressor(

            n_estimators=self.config.n_estimators,

            max_depth=self.config.max_depth,

            min_samples_leaf=self.config.min_samples_leaf

        )



    def _ensure_dataframe(self, X) -> pd.DataFrame:

        if not isinstance(X, pd.DataFrame):

            return pd.DataFrame(X, columns=self.feature_names)

        return X





class XLearner(BaseMetaLearner):

    """

    X-Learner (Causal Inference using Heterogeneous Treatment Effects)



    方法: 三个阶段

    1. 分别训练控制组和处理组模型

    2. 计算伪处理效应

    3. 用倾向性评分加权组合



    详见 x_learner.py

    """



    def fit(self, X: pd.DataFrame, T: np.ndarray, Y: np.ndarray) -> 'XLearner':

        """训练X-Learner"""

        X, T, Y = self._prepare_data(X, T, Y)



        # 分割数据

        X_c = X[T == 0]

        Y_c = Y[T == 0]

        X_t = X[T == 1]

        Y_t = Y[T == 1]



        # 阶段1: 训练结果模型

        self.model_c = self._create_model()

        self.model_c.fit(X_c, Y_c)

        self.model_t = self._create_model()

        self.model_t.fit(X_t, Y_t)



        # 阶段2: 计算伪处理效应

        # D_c = μ₁(X_c) - Y_c

        mu1_pred_c = self.model_t.predict(X_c)

        D_c = mu1_pred_c - Y_c



        # D_t = Y_t - μ₀(X_t)

        mu0_pred_t = self.model_c.predict(X_t)

        D_t = Y_t - mu0_pred_t



        # 阶段3: 训练处理效应模型

        self.tau_model_c = self._create_model()

        self.tau_model_c.fit(X_c, D_c)

        self.tau_model_t = self._create_model()

        self.tau_model_t.fit(X_t, D_t)



        # 训练倾向性模型

        self.propensity_model = self._create_propensity_model()

        self.propensity_model.fit(X, T)



        self.trained = True

        return self



    def predict_ite(self, X: pd.DataFrame) -> np.ndarray:

        """预测ITE"""

        if not self.trained:

            raise ValueError("模型未训练")



        X = self._ensure_dataframe(X)



        # 预测倾向性评分

        g = self.propensity_model.predict_proba(X)[:, 1]



        # 预测处理效应

        tau_c = self.tau_model_c.predict(X)

        tau_t = self.tau_model_t.predict(X)



        # 加权组合

        tau = g * tau_c + (1 - g) * tau_t



        return tau



    def _create_model(self):

        from sklearn.ensemble import GradientBoostingRegressor

        return GradientBoostingRegressor(

            n_estimators=self.config.n_estimators,

            max_depth=self.config.max_depth,

            min_samples_leaf=self.config.min_samples_leaf

        )



    def _create_propensity_model(self):

        from sklearn.linear_model import LogisticRegression

        return LogisticRegression(max_iter=1000)



    def _ensure_dataframe(self, X) -> pd.DataFrame:

        if not isinstance(X, pd.DataFrame):

            return pd.DataFrame(X, columns=self.feature_names)

        return X





@dataclass

class LearnerComparison:

    """学习器对比结果"""

    name: str

    ate_estimate: float

    ate_std: float

    ate_ci: Tuple[float, float]





def compare_learners(X: pd.DataFrame, T: np.ndarray, Y: np.ndarray,

                    n_bootstrap: int = 50) -> List[LearnerComparison]:

    """

    对比不同元学习器的性能



    参数:

        X: 特征

        T: 处理指示器

        Y: 结果

        n_bootstrap: Bootstrap次数



    返回:

        各学习器的对比结果

    """

    learners = {

        "S-Learner": SLearner(),

        "T-Learner": TLearner(),

        "X-Learner": XLearner()

    }



    results = []



    for name, learner in learners.items():

        print(f"\n训练 {name}...")

        learner.fit(X, T, Y)



        # Bootstrap评估

        ate_estimates = []

        n = len(X)



        for _ in range(n_bootstrap):

            indices = np.random.choice(n, size=n, replace=True)

            X_boot = X.iloc[indices]

            ate_boot = learner.predict_ate(X_boot)

            ate_estimates.append(ate_boot)



        ate_estimates = np.array(ate_estimates)

        ate_mean = np.mean(ate_estimates)

        ate_std = np.std(ate_estimates)

        ate_ci = (np.percentile(ate_estimates, 2.5), np.percentile(ate_estimates, 97.5))



        results.append(LearnerComparison(

            name=name,

            ate_estimate=ate_mean,

            ate_std=ate_std,

            ate_ci=ate_ci

        ))



        print(f"  ATE: {ate_mean:.2f} ± {ate_std:.2f}")

        print(f"  95% CI: [{ate_ci[0]:.2f}, {ate_ci[1]:.2f}]")



    return results





if __name__ == "__main__":

    # 生成测试数据

    np.random.seed(42)

    n = 500



    X = pd.DataFrame({

        "age": np.random.normal(40, 10, n),

        "income": np.random.normal(50000, 15000, n),

        "severity": np.random.normal(5, 2, n)

    })



    # 处理分配

    T = np.random.binomial(1, 0.5, n)



    # 潜在结果(异质处理效应)

    Y0 = 10000 + 100 * X["age"] + 0.2 * X["income"] + np.random.normal(0, 2000, n)

    treatment_effect = 1000 + 500 * (X["severity"] - 5)

    Y1 = Y0 + treatment_effect + np.random.normal(0, 2000, n)



    Y = np.where(T == 1, Y1, Y0)



    print("=== Meta-Learner 对比实验 ===")

    print(f"样本数: {n}, 真实ATE: {np.mean(treatment_effect):.2f}")



    # 对比三种学习器

    results = compare_learners(X, T, Y, n_bootstrap=30)



    print("\n=== 对比结果汇总 ===")

    print(f"{'学习器':<15} {'ATE估计':<12} {'标准差':<10} {'95% CI'}")

    print("-" * 60)

    for r in results:

        print(f"{r.name:<15} {r.ate_estimate:<12.2f} {r.ate_std:<10.2f} [{r.ate_ci[0]:.2f}, {r.ate_ci[1]:.2f}]")

