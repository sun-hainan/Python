# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / x_learner

本文件实现 x_learner 相关的算法功能。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import copy


@dataclass
class XLearnerConfig:
    """X-Learner配置"""
    outcome_model: any = None  # 结果模型
    treatment_effect_model: any = None  # 处理效应模型
    propensity_model: any = None  # 倾向性评分模型
    use_propensity_weighting: bool = True  # 是否使用倾向性加权
    min_group_size: int = 10  # 最小组大小


class XLearner:
    """
    X-Learner因果推断方法

    方法概述:
    X-Learner是T-Learner的扩展,专门处理处理效应异质性问题。

    算法步骤:
    1. 第一阶段: 分别估计控制组和处理组的结果函数
       - μ₀(x) = E[Y | X=x, T=0]
       - μ₁(x) = E[Y | X=x, T=1]

    2. 第二阶段: 计算伪处理效应
       - 控制组样本的伪处理效应: D₀ = μ₁(X_control) - Y_control
       - 处理组样本的伪处理效应: D₁ = Y_treatment - μ₀(X_treatment)

    3. 第三阶段: 分别估计两个子群体的处理效应函数
       - τ₀(x) = E[D₀ | X=x] (控制组的处理效应)
       - τ₁(x) = E[D₁ | X=x] (处理组的处理效应)

    4. 第四阶段: 使用倾向性评分加权组合
       - τ(x) = g(x)·τ₀(x) + (1-g(x))·τ₁(x)
       其中 g(x) 是倾向性评分

    优势:
    - 能够处理处理组和控制组样本量不平衡的情况
    - 自动学习哪些特征导致异质性
    - 在倾向性评分接近0.5时效果更好
    """

    def __init__(self, config: XLearnerConfig = None):
        self.config = config or XLearnerConfig()
        self.control_model = None
        self.treatment_model = None
        self.tau0_model = None
        self.tau1_model = None
        self.propensity_model = None
        self.trained = False
        self.feature_names: List[str] = []

    def fit(self, X: pd.DataFrame, T: np.ndarray, Y: np.ndarray) -> 'XLearner':
        """
        训练X-Learner

        参数:
            X: 特征矩阵
            T: 处理指示器 (0=控制组, 1=处理组)
            Y: 观测结果

        返回:
            self
        """
        if len(X) != len(T) or len(T) != len(Y):
            raise ValueError("X, T, Y 长度必须一致")

        self.feature_names = list(X.columns)

        # 分割数据
        control_mask = T == 0
        treatment_mask = T == 1

        X_c = X[control_mask]
        Y_c = Y[control_mask]
        X_t = X[treatment_mask]
        Y_t = Y[treatment_mask]

        # 验证组大小
        if len(X_c) < self.config.min_group_size:
            raise ValueError(f"控制组样本太少: {len(X_c)}")
        if len(X_t) < self.config.min_group_size:
            raise ValueError(f"处理组样本太少: {len(X_t)}")

        # 训练倾向性评分模型
        self._fit_propensity_model(X, T)

        # 阶段1: 训练结果模型
        self._fit_stage1_models(X_c, Y_c, X_t, Y_t)

        # 阶段2: 计算伪处理效应
        D_c, D_t = self._compute_pseudo_effects(X_c, Y_c, X_t, Y_t)

        # 阶段3: 训练处理效应模型
        self._fit_stage3_models(X_c, D_c, X_t, D_t)

        self.trained = True
        return self

    def _fit_propensity_model(self, X: pd.DataFrame, T: np.ndarray):
        """训练倾向性评分模型"""
        if self.config.propensity_model is None:
            self.propensity_model = LogisticRegression(max_iter=1000)
        else:
            self.propensity_model = copy.deepcopy(self.config.propensity_model)

        self.propensity_model.fit(X, T)

    def _fit_stage1_models(self, X_c: pd.DataFrame, Y_c: np.ndarray,
                          X_t: pd.DataFrame, Y_t: np.ndarray):
        """第一阶段: 训练结果模型 μ₀ 和 μ₁"""
        # 控制组模型 μ₀(x)
        if self.config.outcome_model is None:
            self.control_model = GradientBoostingRegressor(n_estimators=100)
        else:
            self.control_model = copy.deepcopy(self.config.outcome_model)

        self.control_model.fit(X_c, Y_c)

        # 处理组模型 μ₁(x)
        if self.config.outcome_model is None:
            self.treatment_model = GradientBoostingRegressor(n_estimators=100)
        else:
            self.treatment_model = copy.deepcopy(self.config.outcome_model)

        self.treatment_model.fit(X_t, Y_t)

    def _compute_pseudo_effects(self, X_c: pd.DataFrame, Y_c: np.ndarray,
                               X_t: pd.DataFrame, Y_t: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        第二阶段: 计算伪处理效应

        D₀ = μ₁(X_c) - Y_c  (控制组样本用处理组模型预测,减去真实结果)
        D₁ = Y_t - μ₀(X_t)  (处理组样本用控制组模型预测,从真实结果减去)
        """
        # 控制组的伪处理效应
        mu1_pred = self.treatment_model.predict(X_c)
        D_c = mu1_pred - Y_c

        # 处理组的伪处理效应
        mu0_pred = self.control_model.predict(X_t)
        D_t = Y_t - mu0_pred

        return D_c, D_t

    def _fit_stage3_models(self, X_c: pd.DataFrame, D_c: np.ndarray,
                          X_t: pd.DataFrame, D_t: np.ndarray):
        """第三阶段: 训练处理效应模型 τ₀ 和 τ₁"""
        # τ₀(x): 控制组伪效应的条件期望
        if self.config.treatment_effect_model is None:
            self.tau0_model = GradientBoostingRegressor(n_estimators=100)
        else:
            self.tau0_model = copy.deepcopy(self.config.treatment_effect_model)

        self.tau0_model.fit(X_c, D_c)

        # τ₁(x): 处理组伪效应的条件期望
        if self.config.treatment_effect_model is None:
            self.tau1_model = GradientBoostingRegressor(n_estimators=100)
        else:
            self.tau1_model = copy.deepcopy(self.config.treatment_effect_model)

        self.tau1_model.fit(X_t, D_t)

    def predict_propensity(self, X: pd.DataFrame) -> np.ndarray:
        """预测倾向性评分"""
        if self.propensity_model is None:
            raise ValueError("模型未训练")
        return self.propensity_model.predict_proba(X)[:, 1]

    def predict_ite(self, X: pd.DataFrame) -> np.ndarray:
        """
        预测个体处理效应(ITE)

        τ(x) = g(x)·τ₀(x) + (1-g(x))·τ₁(x)

        其中 g(x) 是倾向性评分
        """
        if not self.trained:
            raise ValueError("模型未训练")

        # 确保X是DataFrame
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X, columns=self.feature_names)

        # 预测倾向性评分
        g = self.predict_propensity(X)

        # 预测两个处理效应函数
        tau0 = self.tau0_model.predict(X)
        tau1 = self.tau1_model.predict(X)

        # 加权组合
        ite = g * tau0 + (1 - g) * tau1

        return ite

    def predict_ate(self, X: pd.DataFrame) -> float:
        """
        预测平均处理效应(ATE)
        """
        ite = self.predict_ite(X)
        return np.mean(ite)

    def predict_ate_with_ci(self, X: pd.DataFrame,
                           n_bootstrap: int = 100,
                           confidence_level: float = 0.95) -> Tuple[float, float, float]:
        """
        Bootstrap置信区间
        """
        ite_estimates = []
        n = len(X)

        for _ in range(n_bootstrap):
            indices = np.random.choice(n, size=n, replace=True)
            X_boot = X.iloc[indices] if isinstance(X, pd.DataFrame) else X[indices]
            ite_boot = self.predict_ite(X_boot)
            ite_estimates.append(np.mean(ite_boot))

        ite_estimates = np.array(ite_estimates)
        mean_ate = np.mean(ite_estimates)

        alpha = 1 - confidence_level
        lower = np.percentile(ite_estimates, alpha / 2 * 100)
        upper = np.percentile(ite_estimates, (1 - alpha / 2) * 100)

        return mean_ate, lower, upper

    def get_subgroup_effects(self, X: pd.DataFrame,
                             subgroups: Dict[str, callable]) -> Dict[str, Dict]:
        """
        计算子群体的处理效应

        参数:
            X: 特征矩阵
            subgroups: 子群体定义 {"name": lambda X: condition}

        返回:
            各子群体的处理效应统计
        """
        ite = self.predict_ite(X)
        propensity = self.predict_propensity(X)

        results = {}
        for name, condition in subgroups.items():
            mask = condition(X)
            if np.sum(mask) > 0:
                results[name] = {
                    "n": int(np.sum(mask)),
                    "ate": float(np.mean(ite[mask])),
                    "std": float(np.std(ite[mask])),
                    "mean_propensity": float(np.mean(propensity[mask]))
                }

        return results


def simple_comparison():
    """T-Learner vs X-Learner对比"""
    np.random.seed(42)
    n = 500

    # 生成特征(异质性结构)
    X = pd.DataFrame({
        "age": np.random.normal(40, 10, n),
        "income": np.random.normal(50000, 15000, n),
        "severity": np.random.normal(5, 2, n)  # 疾病严重程度
    })

    # 处理分配(非随机,基于严重程度)
    logit_p = -2 + 0.3 * X["severity"]
    p = 1 / (1 + np.exp(-logit_p))
    T = np.random.binomial(1, p, n)

    # 潜在结果
    # 基准结果
    Y0_base = 10000 + 100 * X["age"] + 0.2 * X["income"] + 1000 * X["severity"]

    # 处理效应(高度异质:严重程度越高,效果越好)
    treatment_effect = 500 + 500 * X["severity"]

    # 添加噪声
    Y0 = Y0_base + np.random.normal(0, 2000, n)
    Y1 = Y0_base + treatment_effect + np.random.normal(0, 2000, n)

    # 观测结果
    Y = np.where(T == 1, Y1, Y0)

    print("=== T-Learner vs X-Learner 对比 ===")
    print(f"样本数: {n}")
    print(f"处理组: {np.sum(T)}, 控制组: {n - np.sum(T)}")
    print(f"真实ATE(均值): {np.mean(treatment_effect):.2f}")

    # T-Learner
    from t_learner import TLearner, TLearnerConfig

    print("\n--- T-Learner ---")
    t_learner = TLearner()
    t_learner.fit(X, T, Y)
    t_ate = t_learner.predict_ate(X)
    t_est, t_lower, t_upper = t_learner.predict_ate_with_ci(X, n_bootstrap=50)
    print(f"ATE估计: {t_ate:.2f}")
    print(f"95% CI: [{t_lower:.2f}, {t_upper:.2f}]")

    # X-Learner
    print("\n--- X-Learner ---")
    x_learner = XLearner()
    x_learner.fit(X, T, Y)
    x_ate = x_learner.predict_ate(X)
    x_est, x_lower, x_upper = x_learner.predict_ate_with_ci(X, n_bootstrap=50)
    print(f"ATE估计: {x_ate:.2f}")
    print(f"95% CI: [{x_lower:.2f}, {x_upper:.2f}]")

    # 子群体分析
    print("\n=== 子群体分析(按严重程度) ===")
    subgroups = {
        "轻度(severity<4)": lambda X: X["severity"] < 4,
        "中度(4<=severity<6)": lambda X: (X["severity"] >= 4) & (X["severity"] < 6),
        "重度(severity>=6)": lambda X: X["severity"] >= 6
    }

    print("\nT-Learner:")
    t_subgroups = t_learner.get_heterogeneity_report(X, n_groups=3)
    for group in t_subgroups['groups']:
        print(f"  组{group['group_id']}: ITE={group['mean_ite']:.2f}")

    print("\nX-Learner:")
    x_subgroups = x_learner.get_subgroup_effects(X, subgroups)
    for name, stats in x_subgroups.items():
        print(f"  {name}: n={stats['n']}, ATE={stats['ate']:.2f} ± {stats['std']:.2f}")


if __name__ == "__main__":
    simple_comparison()
