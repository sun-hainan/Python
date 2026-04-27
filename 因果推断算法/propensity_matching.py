# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / propensity_matching

本文件实现 propensity_matching 相关的算法功能。
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbor
from sklearn.neighbors import KDTree
from scipy.spatial.distance import cdist


@dataclass
class MatchedPair:
    """匹配对"""
    treated_index: int  # 处理组索引
    control_index: int  # 对照组索引
    propensity_diff: float  # 倾向性评分差异
    treated_outcome: float  # 处理组结果
    control_outcome: float  # 对照组结果
    ite: float  # 个体处理效应估计


class PropensityScoreMatcher:
    """
    倾向性评分匹配器

    方法:
    1. 估计倾向性评分 e(x) = P(T=1 | X)
    2. 基于评分进行匹配
    3. 估计处理效应

    匹配策略:
    - 最近邻匹配
    - 卡尺匹配(限定评分差异)
    - 分层匹配
    - 核匹配
    """

    def __init__(self, caliper: float = 0.1, replacement: bool = True,
                 matching_method: str = "nearest_neighbor"):
        """
        参数:
            caliper: 卡尺半径,超过该差异的不匹配
            replacement: 是否放回匹配
            matching_method: 匹配方法
        """
        self.caliper = caliper
        self.replacement = replacement
        self.matching_method = matching_method
        self.propensity_scores: Optional[np.ndarray] = None
        self.matched_pairs: List[MatchedPair] = []
        self.model = None

    def fit(self, X: pd.DataFrame, T: np.ndarray, Y: np.ndarray) -> 'PropensityScoreMatcher':
        """
        拟合匹配器

        参数:
            X: 特征矩阵
            T: 处理指示器 (0/1)
            Y: 观测结果
        """
        # 1. 估计倾向性评分
        self.propensity_scores = self._estimate_propensity(X, T)

        # 2. 执行匹配
        self.matched_pairs = self._match(X, T, Y)

        return self

    def _estimate_propensity(self, X: pd.DataFrame, T: np.ndarray) -> np.ndarray:
        """估计倾向性评分"""
        self.model = LogisticRegression(max_iter=1000)
        self.model.fit(X, T)
        self.propensity_scores = self.model.predict_proba(X)[:, 1]
        return self.propensity_scores

    def _match(self, X: pd.DataFrame, T: np.ndarray, Y: np.ndarray) -> List[MatchedPair]:
        """执行匹配"""
        if self.matching_method == "nearest_neighbor":
            return self._nearest_neighbor_match(T, Y)
        elif self.matching_method == "caliper":
            return self._caliper_match(T, Y)
        elif self.matching_method == "stratification":
            return self._stratification_match(T, Y)
        else:
            return self._nearest_neighbor_match(T, Y)

    def _nearest_neighbor_match(self, T: np.ndarray, Y: np.ndarray) -> List[MatchedPair]:
        """
        最近邻匹配

        对每个处理组单位,找到倾向性评分最接近的对照组单位
        """
        treated_mask = T == 1
        control_mask = T == 0

        treated_indices = np.where(treated_mask)[0]
        control_indices = np.where(control_mask)[0]
        treated_scores = self.propensity_scores[treated_mask]
        control_scores = self.propensity_scores[control_mask]

        pairs = []
        used_control = set()

        for t_idx in treated_indices:
            t_score = self.propensity_scores[t_idx]

            # 找最近的对照组
            best_control = None
            best_diff = float('inf')

            for c_idx in control_indices:
                if c_idx in used_control and not self.replacement:
                    continue

                c_score = self.propensity_scores[c_idx]
                diff = abs(t_score - c_score)

                if diff < best_diff:
                    best_diff = diff
                    best_control = c_idx

            if best_control is not None:
                # 检查卡尺
                if best_diff <= self.caliper:
                    pairs.append(MatchedPair(
                        treated_index=t_idx,
                        control_index=best_control,
                        propensity_diff=best_diff,
                        treated_outcome=Y[t_idx],
                        control_outcome=Y[best_control],
                        ite=Y[t_idx] - Y[best_control]
                    ))

                    if not self.replacement:
                        used_control.add(best_control)

        return pairs

    def _caliper_match(self, T: np.ndarray, Y: np.ndarray) -> List[MatchedPair]:
        """
        卡尺匹配

        对每个处理组单位,找到卡尺范围内的最近对照组
        """
        return self._nearest_neighbor_match(T, Y)  # 已在上面实现卡尺检查

    def _stratification_match(self, T: np.ndarray, Y: np.ndarray, n_strata: int = 5) -> List[MatchedPair]:
        """
        分层匹配

        按倾向性评分分位数分层,在每层内进行匹配
        """
        treated_mask = T == 1
        control_mask = T == 0

        treated_scores = self.propensity_scores[treated_mask]
        control_scores = self.propensity_scores[control_mask]

        # 计算分位数边界
        quantiles = np.linspace(0, 1, n_strata + 1)
        boundaries = np.quantile(np.concatenate([treated_scores, control_scores]), quantiles)

        pairs = []

        for i in range(n_strata):
            lower = boundaries[i]
            upper = boundaries[i + 1]

            # 获取该层内的单位
            t_in_stratum = (treated_scores >= lower) & (treated_scores < upper)
            c_in_stratum = (control_scores >= lower) & (control_scores < upper)

            if not np.any(t_in_stratum) or not np.any(c_in_stratum):
                continue

            # 层内最近邻匹配
            t_indices = np.where(treated_mask)[0][t_in_stratum]
            c_indices = np.where(control_mask)[0][c_in_stratum]
            t_scores = treated_scores[t_in_stratum]
            c_scores = control_scores[c_in_stratum]

            for j, t_idx in enumerate(t_indices):
                t_score = t_scores[j]
                best_c = None
                best_diff = float('inf')

                for k, c_idx in enumerate(c_indices):
                    diff = abs(t_score - c_scores[k])
                    if diff < best_diff:
                        best_diff = diff
                        best_c = c_idx

                if best_c is not None and best_diff <= self.caliper:
                    pairs.append(MatchedPair(
                        treated_index=t_idx,
                        control_index=best_c,
                        propensity_diff=best_diff,
                        treated_outcome=Y[t_idx],
                        control_outcome=Y[best_c],
                        ite=Y[t_idx] - Y[best_c]
                    ))

        return pairs

    def estimate_ate(self) -> Tuple[float, float]:
        """
        估计平均处理效应(ATE)及标准误

        返回:
            (ATE估计, 标准误)
        """
        if not self.matched_pairs:
            raise ValueError("没有匹配对")

        ites = np.array([p.ite for p in self.matched_pairs])
        ate = np.mean(ites)
        se = np.std(ites) / np.sqrt(len(ites))

        return ate, se

    def estimate_ate_with_ci(self, confidence_level: float = 0.95) -> Tuple[float, float, float]:
        """
        带置信区间的ATE估计

        返回:
            (ATE估计, 下界, 上界)
        """
        ate, se = self.estimate_ate()
        alpha = 1 - confidence_level

        from scipy.stats import t as t_dist
        df = len(self.matched_pairs) - 1
        t_val = t_dist.ppf(1 - alpha / 2, df)

        lower = ate - t_val * se
        upper = ate + t_val * se

        return ate, lower, upper

    def get_matched_data(self, X: pd.DataFrame, T: np.ndarray, Y: np.ndarray) -> Tuple:
        """
        获取匹配后的数据(用于后续分析)

        返回:
            (X_matched, T_matched, Y_matched)
        """
        treated_idx = [p.treated_index for p in self.matched_pairs]
        control_idx = [p.control_index for p in self.matched_pairs]
        matched_idx = treated_idx + control_idx

        return X.iloc[matched_idx], T[matched_idx], Y[matched_idx]

    def get_balance_statistics(self, X: pd.DataFrame, T: np.ndarray) -> Dict:
        """
        获取平衡性统计

        评估匹配后协变量分布的平衡性
        """
        X_matched, T_matched, _ = self.get_matched_data(X, T, np.zeros(len(T)))

        results = {}
        for col in X.columns:
            # 计算标准化均值差异
            t_mean = X_matched[T_matched == 1][col].mean()
            c_mean = X_matched[T_matched == 0][col].mean()
            t_std = X_matched[T_matched == 1][col].std()
            c_std = X_matched[T_matched == 0][col].std()
            pooled_std = np.sqrt((t_std**2 + c_std**2) / 2)

            smd = abs(t_mean - c_mean) / pooled_std if pooled_std > 0 else 0

            results[col] = {
                "treated_mean": t_mean,
                "control_mean": c_mean,
                "standardized_mean_diff": smd
            }

        return results


def print_match_summary(matcher: PropensityScoreMatcher, Y_true: np.ndarray = None):
    """打印匹配摘要"""
    n_treated = len([p for p in matcher.matched_pairs])
    n_total_treated = np.sum(matcher.propensity_scores > 0.5) if matcher.propensity_scores is not None else 0

    print("=== 倾向性评分匹配摘要 ===")
    print(f"匹配方法: {matcher.matching_method}")
    print(f"卡尺: {matcher.caliper}")
    print(f"总匹配对数: {len(matcher.matched_pairs)}")
    print(f"处理组匹配率: {n_treated / max(n_total_treated, 1) * 100:.1f}%")

    if matcher.matched_pairs:
        ate, se = matcher.estimate_ate()
        ate, lower, upper = matcher.estimate_ate_with_ci()

        print(f"\n处理效应估计:")
        print(f"  ATE: {ate:.4f}")
        print(f"  SE: {se:.4f}")
        print(f"  95% CI: [{lower:.4f}, {upper:.4f}]")

        # 平均倾向性差异
        avg_prop_diff = np.mean([p.propensity_diff for p in matcher.matched_pairs])
        print(f"  平均倾向性差异: {avg_prop_diff:.4f}")


if __name__ == "__main__":
    np.random.seed(42)
    n = 500

    # 生成协变量
    X = pd.DataFrame({
        "age": np.random.normal(40, 10, n),
        "education": np.random.randint(12, 20, n),
        "income": np.random.normal(50000, 15000, n),
        "severity": np.random.normal(5, 2, n)
    })

    # 处理分配机制(混杂)
    logit_p = -2 + 0.05 * (X["age"] - 40) + 0.1 * (X["severity"] - 5)
    p = 1 / (1 + np.exp(-logit_p))
    T = np.random.binomial(1, p, n)

    # 潜在结果
    Y0 = 10000 + 100 * X["age"] + 0.2 * X["income"] + np.random.normal(0, 1000, n)
    treatment_effect = 2000 + 500 * (X["severity"] - 5)  # 异质效应
    Y1 = Y0 + treatment_effect + np.random.normal(0, 1000, n)

    # 观测结果
    Y = np.where(T == 1, Y1, Y0)

    print("=== 倾向性评分匹配示例 ===")
    print(f"样本数: {n}")
    print(f"处理组: {np.sum(T)}, 对照组: {n - np.sum(T)}")
    print(f"真实ATE: {np.mean(treatment_effect):.2f}")

    # 执行匹配
    matcher = PropensityScoreMatcher(caliper=0.1, replacement=False)
    matcher.fit(X, T, Y)

    print_match_summary(matcher)

    # 平衡性统计
    print("\n=== 平衡性统计 ===")
    balance = matcher.get_balance_statistics(X, T)
    for var, stats in balance.items():
        print(f"  {var}: SMD = {stats['standardized_mean_diff']:.4f}")
