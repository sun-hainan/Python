# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / t_learner

本文件实现 t_learner 相关的算法功能。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor


@dataclass
class TLearnerConfig:
    """T-Learner配置"""
    control_model: any = None  # 控制组模型
    treatment_model: any = None  # 处理组模型
    propensity_model: any = None  # 倾向性评分模型(可选)
    use_propensity: bool = False  # 是否使用倾向性评分加权
    min_treatment_group_size: int = 10  # 最小处理组大小


class TLearner:
    """
    T-Learner因果推断方法

    方法概述:
    T-Learner将因果推断问题转化为两个独立的监督学习问题:
    1. 学习控制组的响应函数: E[Y | X, T=0]
    2. 学习处理组的响应函数: E[Y | X, T=1]

    个体处理效应(ITE)估计:
    τ(x) = E[Y(1) - Y(0) | X=x]
         ≈ μ₁(x) - μ₀(x)

    其中:
    - μ₀(x) = E[Y | X=x, T=0] (控制组响应函数)
    - μ₁(x) = E[Y | X=x, T=1] (处理组响应函数)
    - Y(t) 是潜在结果
    """

    def __init__(self, config: TLearnerConfig = None):
        self.config = config or TLearnerConfig()
        self.control_model = None  # 控制组模型
        self.treatment_model = None  # 处理组模型
        self.propensity_model = None  # 倾向性评分模型
        self.trained = False
        self.feature_names: List[str] = []

    def fit(self, X: pd.DataFrame, T: np.ndarray, Y: np.ndarray) -> 'TLearner':
        """
        训练T-Learner

        参数:
            X: 特征矩阵 (n x d)
            T: 处理指示器 (n,), T=0表示控制组, T=1表示处理组
            Y: 观测结果 (n,)

        返回:
            self
        """
        # 数据验证
        if len(X) != len(T) or len(T) != len(Y):
            raise ValueError("X, T, Y 长度必须一致")

        if self.config.use_propensity:
            # 训练倾向性评分模型
            self._fit_propensity_model(X, T)

        # 分割数据
        control_mask = T == 0
        treatment_mask = T == 1

        X_control = X[control_mask]
        Y_control = Y[control_mask]
        X_treatment = X[treatment_mask]
        Y_treatment = Y[treatment_mask]

        # 检查组大小
        if len(X_control) < self.config.min_treatment_group_size:
            raise ValueError(f"控制组样本太少: {len(X_control)}")
        if len(X_treatment) < self.config.min_treatment_group_size:
            raise ValueError(f"处理组样本太少: {len(X_treatment)}")

        # 保存特征名
        self.feature_names = list(X.columns)

        # 训练控制组模型 μ₀(x)
        self._fit_control_model(X_control, Y_control)

        # 训练处理组模型 μ₁(x)
        self._fit_treatment_model(X_treatment, Y_treatment)

        self.trained = True
        return self

    def _fit_propensity_model(self, X: pd.DataFrame, T: np.ndarray):
        """训练倾向性评分模型"""
        self.propensity_model = LogisticRegression(max_iter=1000)
        self.propensity_model.fit(X, T)

    def _fit_control_model(self, X: pd.DataFrame, Y: np.ndarray):
        """训练控制组响应函数 μ₀(x)"""
        if self.config.control_model is None:
            # 默认使用随机森林
            self.control_model = GradientBoostingRegressor(n_estimators=100)
        else:
            self.control_model = copy.deepcopy(self.config.control_model)

        self.control_model.fit(X, Y)

    def _fit_treatment_model(self, X: pd.DataFrame, Y: np.ndarray):
        """训练处理组响应函数 μ₁(x)"""
        if self.config.treatment_model is None:
            # 默认使用随机森林
            self.treatment_model = GradientBoostingRegressor(n_estimators=100)
        else:
            self.treatment_model = copy.deepcopy(self.config.treatment_model)

        self.treatment_model.fit(X, Y)

    def predict_ite(self, X: pd.DataFrame) -> np.ndarray:
        """
        预测个体处理效应(ITE)

        参数:
            X: 特征矩阵 (n x d)

        返回:
            ITE估计 τ(x) = μ₁(x) - μ₀(x)
        """
        if not self.trained:
            raise ValueError("模型未训练,请先调用fit()")

        # 确保X是DataFrame
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X, columns=self.feature_names)

        # 预测 μ₀(x) 和 μ₁(x)
        mu0 = self.control_model.predict(X)
        mu1 = self.treatment_model.predict(X)

        # 计算ITE
        ite = mu1 - mu0

        return ite

    def predict_ate(self, X: pd.DataFrame) -> float:
        """
        预测平均处理效应(ATE)

        参数:
            X: 特征矩阵

        返回:
            ATE估计
        """
        ite = self.predict_ite(X)
        return np.mean(ite)

    def predict_cate(self, X: pd.DataFrame, target_level: float = None) -> np.ndarray:
        """
        预测条件平均处理效应(CATE)

        可以按分位数或指定阈值划分群体

        参数:
            X: 特征矩阵
            target_level: 如果指定,返回该分位数以上的CATE

        返回:
            CATE估计
        """
        ite = self.predict_ite(X)

        if target_level is None:
            return ite

        # 按分位数划分
        threshold = np.quantile(ite, target_level)
        cate = np.where(ite >= threshold, ite, 0)
        return cate

    def predict_ate_with_ci(self, X: pd.DataFrame,
                           n_bootstrap: int = 100,
                           confidence_level: float = 0.95) -> Tuple[float, float, float]:
        """
        使用Bootstrap预测ATE及其置信区间

        返回:
            (ATE估计, 下界, 上界)
        """
        ite_estimates = []

        n = len(X)
        for _ in range(n_bootstrap):
            # Bootstrap采样
            indices = np.random.choice(n, size=n, replace=True)
            X_boot = X.iloc[indices] if isinstance(X, pd.DataFrame) else X[indices]

            # 预测
            ite_boot = self.predict_ite(X_boot)
            ite_estimates.append(np.mean(ite_boot))

        ite_estimates = np.array(ite_estimates)
        mean_ate = np.mean(ite_estimates)

        # 计算置信区间
        alpha = 1 - confidence_level
        lower = np.percentile(ite_estimates, alpha / 2 * 100)
        upper = np.percentile(ite_estimates, (1 - alpha / 2) * 100)

        return mean_ate, lower, upper

    def get_heterogeneity_report(self, X: pd.DataFrame,
                                  n_groups: int = 4) -> Dict:
        """
        生成处理效应异质性报告

        将样本按特征分组,分析组间处理效应差异
        """
        ite = self.predict_ite(X)

        # 按ITE分位数划分群体
        quantiles = np.linspace(0, 1, n_groups + 1)
        boundaries = [np.quantile(ite, q) for q in quantiles]

        groups = []
        for i in range(n_groups):
            lower = boundaries[i]
            upper = boundaries[i + 1]
            mask = (ite >= lower) & (ite < upper)
            if i == n_groups - 1:  # 最后一个包含上界
                mask = (ite >= lower) & (ite <= upper)

            group_data = {
                "group_id": i + 1,
                "size": np.sum(mask),
                "mean_ite": np.mean(ite[mask]),
                "std_ite": np.std(ite[mask]),
                "ite_range": (lower, upper)
            }
            groups.append(group_data)

        return {
            "ate": np.mean(ite),
            "groups": groups
        }


import copy


def simple_example():
    """T-Learner简单示例"""
    np.random.seed(42)
    n = 1000

    # 生成特征
    X = pd.DataFrame({
        "age": np.random.normal(40, 10, n),
        "income": np.random.normal(50000, 15000, n),
        "education": np.random.randint(12, 20, n)
    })

    # 生成处理组
    T = np.random.binomial(1, 0.5, n)

    # 生成潜在结果
    # Y(0) = 10000 + 100*age + 0.1*income + 500*education + noise
    # Y(1) = Y(0) + 2000 + 50*age + 2000*(education - 16)  (处理效应随年龄和教育增加)
    Y0 = 10000 + 100 * X["age"] + 0.1 * X["income"] + 500 * X["education"] + np.random.normal(0, 1000, n)
    Y1 = Y0 + 2000 + 50 * X["age"] + 2000 * (X["education"] - 16) + np.random.normal(0, 1000, n)

    # 观测结果
    Y = np.where(T == 1, Y1, Y0)

    print("=== T-Learner因果推断示例 ===")
    print(f"样本数: {n}")
    print(f"处理组样本: {np.sum(T)}")
    print(f"控制组样本: {n - np.sum(T)}")

    # 训练T-Learner
    learner = TLearner()
    learner.fit(X, T, Y)

    # 预测
    ite = learner.predict_ite(X)
    ate = learner.predict_ate(X)

    print(f"\n平均处理效应(ATE)估计: {ate:.2f}")
    print(f"真实ATE(平均): {np.mean(Y1 - Y0):.2f}")

    # ATE置信区间
    ate_est, lower, upper = learner.predict_ate_with_ci(X, n_bootstrap=50)
    print(f"\n95%置信区间: [{lower:.2f}, {upper:.2f}]")

    # 异质性报告
    report = learner.get_heterogeneity_report(X, n_groups=4)
    print(f"\n=== 异质性报告 ===")
    print(f"总体ATE: {report['ate']:.2f}")
    for group in report['groups']:
        print(f"  组{group['group_id']}: n={group['size']}, "
              f"平均ITE={group['mean_ite']:.2f} ± {group['std_ite']:.2f}, "
              f"范围=[{group['ite_range'][0]:.1f}, {group['ite_range'][1]:.1f}]")


if __name__ == "__main__":
    simple_example()
