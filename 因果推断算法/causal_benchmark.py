# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / causal_benchmark

本文件实现 causal_benchmark 相关的算法功能。
"""

from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
import numpy as np
import random


# =============================================================================
# 数据结构定义
# =============================================================================

@dataclass
class CausalDataset:
    """因果推断数据集"""
    name: str  # 数据集名称
    treatment: str  # 处理变量名
    outcome: str  # 结果变量名
    covariates: List[str]  # 协变量列表
    treatment_vector: np.ndarray  # 处理组标识 (n,)
    outcome_vector: np.ndarray  # 观察结果 (n,)
    potential_outcomes: Optional[Dict[str, np.ndarray]] = None  # 潜在结果 {y0, y1}
    true_ate: Optional[float] = None  # 真实ATE（如果已知）

    def get_covariates(self) -> np.ndarray:
        """获取协变量矩阵"""
        return self.covariate_matrix

    def __post_init__(self):
        self.covariate_matrix: Optional[np.ndarray] = None


@dataclass
class EvaluationResult:
    """评估结果"""
    method_name: str  # 方法名称
    ate_estimate: float  # ATE估计值
    bias: float  # 偏差（相对于真实ATE）
    mse: float  # 均方误差
    ci_coverage: float  # 置信区间覆盖率


# =============================================================================
# 合成数据生成器
# =============================================================================

class SyntheticDataGenerator:
    """
    合成因果数据生成器

    生成满足特定因果结构的合成数据，用于测试因果推断方法
    """

    @staticmethod
    def generate_linear_scm(n_samples: int, seed: int = 42) -> CausalDataset:
        """
        生成线性SCM数据

        数据生成过程：
            X1 ~ N(0, 1)
            X2 ~ N(0, 1)
            T = 0.5*X1 + 0.3*X2 + N(0, 0.1) > 0 ? 1 : 0
            Y = 2*T + X1 + 0.5*X2 + N(0, 0.1)

        真实ATE = 2
        """
        np.random.seed(seed)
        random.seed(seed)

        # 协变量
        x1 = np.random.randn(n_samples)
        x2 = np.random.randn(n_samples)
        X = np.column_stack([x1, x2])

        # 处理变量（混淆）
        logit_t = 0.5 * x1 + 0.3 * x2
        p_t = 1 / (1 + np.exp(-logit_t))
        treatment = (np.random.rand(n_samples) < p_t).astype(float)

        # 潜在结果
        y0 = x1 + 0.5 * x2 + np.random.randn(n_samples) * 0.1  # 无处理
        y1 = y0 + 2.0  # 处理效应 = 2
        observed_outcome = treatment * y1 + (1 - treatment) * y0

        dataset = CausalDataset(
            name="Linear SCM",
            treatment="T",
            outcome="Y",
            covariates=["X1", "X2"],
            treatment_vector=treatment,
            outcome_vector=observed_outcome,
            potential_outcomes={"y0": y0, "y1": y1},
            true_ate=2.0
        )
        dataset.covariate_matrix = X

        return dataset

    @staticmethod
    def generate_confounded_scm(n_samples: int, seed: int = 42) -> CausalDataset:
        """
        生成强混淆数据

        模拟现实中的混淆偏倚
        """
        np.random.seed(seed)

        # 混淆变量
        confounder = np.random.randn(n_samples)

        # 协变量
        x1 = confounder + np.random.randn(n_samples) * 0.5
        x2 = confounder * 0.5 + np.random.randn(n_samples) * 0.5
        X = np.column_stack([x1, x2])

        # 处理（强烈受混淆影响）
        t = (confounder + 0.5 * np.random.randn(n_samples)) > 0
        treatment = t.astype(float)

        # 结果
        y0 = confounder + x1 + np.random.randn(n_samples) * 0.1
        y1 = y0 + 3.0
        observed_outcome = treatment * y1 + (1 - treatment) * y0

        dataset = CausalDataset(
            name="Confounded SCM",
            treatment="T",
            outcome="Y",
            covariates=["X1", "X2"],
            treatment_vector=treatment,
            outcome_vector=observed_outcome,
            potential_outcomes={"y0": y0, "y1": y1},
            true_ate=3.0
        )
        dataset.covariate_matrix = X

        return dataset

    @staticmethod
    def generate_interaction_scm(n_samples: int, seed: int = 42) -> CausalDataset:
        """
        生成有交互效应的数据

        处理效应随协变量变化
        """
        np.random.seed(seed)

        # 协变量
        x1 = np.random.randn(n_samples)
        x2 = np.random.randn(n_samples)
        X = np.column_stack([x1, x2])

        # 处理（根据协变量选择）
        p_t = 0.5 + 0.2 * x1 - 0.2 * x2
        p_t = np.clip(p_t, 0.1, 0.9)
        treatment = (np.random.rand(n_samples) < p_t).astype(float)

        # 异质处理效应：HTE = x1 * x2
        treatment_effect = 2.0 + 0.5 * x1 * x2

        # 潜在结果
        y0 = x1 + x2 + np.random.randn(n_samples) * 0.1
        y1 = y0 + treatment_effect
        observed_outcome = treatment * y1 + (1 - treatment) * y0

        dataset = CausalDataset(
            name="Interaction SCM",
            treatment="T",
            outcome="Y",
            covariates=["X1", "X2"],
            treatment_vector=treatment,
            outcome_vector=observed_outcome,
            potential_outcomes={"y0": y0, "y1": y1},
            true_ate=np.mean(treatment_effect)
        )
        dataset.covariate_matrix = X

        return dataset


# =============================================================================
# 基准数据集加载器
# =============================================================================

class BenchmarkLoader:
    """
    基准数据集加载器

    提供常用因果推断基准数据集的加载接口
    """

    @staticmethod
    def load_ihdp(n_samples: Optional[int] = None) -> CausalDataset:
        """
        加载IHDP数据集

        IHDP（Infant Health and Development Program）：
        - 真实ATE已知（基于随机实验）
        - 包含强混淆
        - 用于测试因果推断方法

        注：这里返回合成版本（真实IHDP需要从外部获取）
        """
        n = n_samples if n_samples else 1000
        return SyntheticDataGenerator.generate_linear_scm(n, seed=123)

    @staticmethod
    def load_jobs(n_samples: Optional[int] = None) -> CausalDataset:
        """
        加载Jobs数据集

        Jobs数据集：
        - 二元处理：就业培训
        - 真实结果：是否就业
        - 强混淆：教育、经验等

        返回合成版本
        """
        np.random.seed(456)
        n = n_samples if n_samples else 2000

        # 协变量
        education = np.random.randint(12, 18, n)  # 受教育年限
        experience = np.random.randint(0, 30, n)  # 工作经验
        age = np.random.randint(25, 55, n)  # 年龄

        X = np.column_stack([education, experience, age])

        # 混淆：教育、经验与培训选择相关
        logit_t = -3 + 0.2 * education + 0.1 * experience - 0.05 * age
        p_t = 1 / (1 + np.exp(-logit_t))
        treatment = (np.random.rand(n) < p_t).astype(float)

        # 结果：就业
        logit_y = -2 + 0.3 * education + 0.15 * experience + 1.5 * treatment
        p_y = 1 / (1 + np.exp(-logit_y))
        outcome = (np.random.rand(n) < p_y).astype(float)

        # 潜在结果
        y0 = logit_y - 1.5 * treatment  # 简化
        y1 = y0 + 1.5

        dataset = CausalDataset(
            name="Jobs",
            treatment="T",
            outcome="Y",
            covariates=["Education", "Experience", "Age"],
            treatment_vector=treatment,
            outcome_vector=outcome,
            potential_outcomes={"y0": y0, "y1": y1},
            true_ate=1.5
        )
        dataset.covariate_matrix = X

        return dataset

    @staticmethod
    def load_twins(n_samples: Optional[int] = None) -> CausalDataset:
        """
        加载Twins数据集

        Twins数据集：
        - 处理：是否是较重的双胞胎
        - 结果：死亡率
        - 使用双胞胎配对消除混淆

        返回合成版本
        """
        np.random.seed(789)
        n = n_samples if n_samples else 1500

        # 共享遗传因素
        genetics = np.random.randn(n)

        # 协变量
        birth_weight = 2000 + 500 * genetics + np.random.randn(n) * 200
        gestational_age = 35 + 2 * genetics + np.random.randn(n) * 2
        prenatal_care = np.random.randint(0, 2, n)

        X = np.column_stack([birth_weight, gestational_age, prenatal_care])

        # 处理：出生体重较高
        treatment = (birth_weight > np.median(birth_weight)).astype(float)

        # 结果（死亡风险）
        risk_base = -5 + 0.001 * (37 - gestational_age) * 10
        treatment_effect = -0.5  # 较重双胞胎死亡风险降低
        risk = risk_base + treatment_effect * treatment + np.random.randn(n) * 0.1
        outcome = (risk > 0).astype(float)

        y0 = outcome.copy()
        y1 = ((risk - treatment_effect) > 0).astype(float)

        dataset = CausalDataset(
            name="Twins",
            treatment="T",
            outcome="Y",
            covariates=["BirthWeight", "GestationalAge", "PrenatalCare"],
            treatment_vector=treatment,
            outcome_vector=outcome,
            potential_outcomes={"y0": y0, "y1": y1},
            true_ate=treatment_effect
        )
        dataset.covariate_matrix = X

        return dataset


# =============================================================================
# 评估工具
# =============================================================================

class CausalEvaluator:
    """
    因果推断方法评估器
    """

    @staticmethod
    def compute_ate(dataset: CausalDataset, treatment_effect_fn: Callable) -> float:
        """
        计算ATE估计值

        参数:
            dataset: 因果数据集
            treatment_effect_fn: 处理效应估计函数

        返回:
            ATE估计值
        """
        return treatment_effect_fn(dataset)

    @staticmethod
    def evaluate_method(dataset: CausalDataset,
                       method_name: str,
                       method_fn: Callable) -> EvaluationResult:
        """
        评估因果推断方法

        参数:
            dataset: 数据集
            method_name: 方法名称
            method_fn: 方法函数，输入数据集，输出ATE估计

        返回:
            评估结果
        """
        ate_estimate = method_fn(dataset)

        if dataset.true_ate is not None:
            bias = ate_estimate - dataset.true_ate
            mse = bias ** 2
        else:
            bias = 0.0
            mse = 0.0

        return EvaluationResult(
            method_name=method_name,
            ate_estimate=ate_estimate,
            bias=bias,
            mse=mse,
            ci_coverage=0.95  # 简化
        )


# =============================================================================
# 常用因果推断方法（简化实现）
# =============================================================================

class SimpleCausalMethods:
    """简化的因果推断方法集合"""

    @staticmethod
    def naive_ate(dataset: CausalDataset) -> float:
        """朴素ATE估计（不考虑混淆）"""
        treated_mask = dataset.treatment_vector == 1
        control_mask = dataset.treatment_vector == 0

        y1_mean = np.mean(dataset.outcome_vector[treated_mask])
        y0_mean = np.mean(dataset.outcome_vector[control_mask])

        return y1_mean - y0_mean

    @staticmethod
    def stratification_ate(dataset: CausalDataset, n_strata: int = 5) -> float:
        """
        分层估计ATE

        按协变量分层，控制混淆
        """
        X = dataset.covariate_matrix

        # 按第一个协变量分层
        strata_edges = np.linspace(X[:, 0].min(), X[:, 0].max(), n_strata + 1)
        ate_strata = []
        weights = []

        for i in range(n_strata):
            mask = (X[:, 0] >= strata_edges[i]) & (X[:, 0] < strata_edges[i + 1])
            if mask.sum() < 10:
                continue

            stratum_data = CausalDataset(
                name="stratum",
                treatment=dataset.treatment,
                outcome=dataset.outcome,
                covariates=dataset.covariates,
                treatment_vector=dataset.treatment_vector[mask],
                outcome_vector=dataset.outcome_vector[mask],
                true_ate=dataset.true_ate
            )

            ate_i = SimpleCausalMethods.naive_ate(stratum_data)
            ate_strata.append(ate_i)
            weights.append(mask.sum())

        weights = np.array(weights) / sum(weights)
        return np.sum(np.array(ate_strata) * weights)

    @staticmethod
    def ipw_ate(dataset: CausalDataset) -> float:
        """
        逆概率加权估计（IPW）

        估计倾向得分，然后加权
        """
        T = dataset.treatment_vector
        Y = dataset.outcome_vector
        X = dataset.covariate_matrix

        # 简化：使用logistic回归估计倾向得分
        from sklearn.linear_model import LogisticRegression

        lr = LogisticRegression(solver='lbfgs', max_iter=200)
        lr.fit(X, T)
        prop_score = lr.predict_proba(X)[:, 1]

        # 倾向得分裁剪
        prop_score = np.clip(prop_score, 0.1, 0.9)

        # IPW估计
        ate = (np.mean((T * Y) / prop_score) -
               np.mean(((1 - T) * Y) / (1 - prop_score)))

        return ate


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("因果推断基准数据集测试")
    print("=" * 60)

    # 测试1：合成数据生成
    print("\n【测试1：合成数据生成】")
    dataset = SyntheticDataGenerator.generate_linear_scm(1000)
    print(f"数据集: {dataset.name}")
    print(f"样本数: {len(dataset.treatment_vector)}")
    print(f"协变量: {dataset.covariates}")
    print(f"真实ATE: {dataset.true_ate}")
    print(f"观察到的ATE: {SimpleCausalMethods.naive_ate(dataset):.4f}")

    # 测试2：IHDP数据集
    print("\n【测试2：IHDP数据集】")
    ihdp = BenchmarkLoader.load_ihdp(500)
    print(f"数据集: {ihdp.name}")
    print(f"处理组均值: {np.mean(ihdp.outcome_vector[ihdp.treatment_vector == 1]):.4f}")
    print(f"对照组均值: {np.mean(ihdp.outcome_vector[ihdp.treatment_vector == 0]):.4f}")

    # 测试3：Jobs数据集
    print("\n【测试3：Jobs数据集】")
    jobs = BenchmarkLoader.load_jobs(500)
    print(f"数据集: {jobs.name}")
    print(f"处理组就业率: {np.mean(jobs.outcome_vector[jobs.treatment_vector == 1]):.4f}")
    print(f"对照组就业率: {np.mean(jobs.outcome_vector[jobs.treatment_vector == 0]):.4f}")

    # 测试4：评估不同方法
    print("\n【测试4：方法评估】")
    test_datasets = [
        SyntheticDataGenerator.generate_linear_scm(500, seed=i)
        for i in range(3)
    ]

    methods = {
        "Naive": SimpleCausalMethods.naive_ate,
        "Stratification": SimpleCausalMethods.stratification_ate,
        "IPW": SimpleCausalMethods.ipw_ate
    }

    print(f"{'方法':<20} {'估计ATE':<12} {'偏差':<12} {'MSE':<12}")
    print("-" * 60)

    for method_name, method_fn in methods.items():
        estimates = []
        for ds in test_datasets:
            ate_est = method_fn(ds)
            estimates.append(ate_est)

        mean_ate = np.mean(estimates)
        bias = mean_ate - test_datasets[0].true_ate if test_datasets[0].true_ate else 0
        mse = np.var(estimates)

        print(f"{method_name:<20} {mean_ate:<12.4f} {bias:<12.4f} {mse:<12.4f}")

    # 测试5：异质处理效应
    print("\n【测试5：异质处理效应数据】")
    hte_dataset = SyntheticDataGenerator.generate_interaction_scm(1000)
    print(f"数据集: {hte_dataset.name}")
    print(f"真实平均ATE: {hte_dataset.true_ate:.4f}")
    print(f"异质效应范围: [{hte_dataset.potential_outcomes['y1'].min() - hte_dataset.potential_outcomes['y0'].min():.2f}, "
          f"{hte_dataset.potential_outcomes['y1'].max() - hte_dataset.potential_outcomes['y0'].max():.2f}]")
