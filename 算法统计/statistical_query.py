# -*- coding: utf-8 -*-
"""
算法实现：算法统计 / statistical_query

本文件实现 statistical_query 相关的算法功能。
"""

import random
from typing import List, Callable, Tuple


class SQOracle:
    """统计查询Oracle"""

    def __init__(self, data: List[float]):
        """
        参数：
            data: 数据集
        """
        self.data = data
        self.n = len(data)

    def query_mean(self, weights: List[float] = None) -> float:
        """
        加权平均查询

        参数：
            weights: 可选权重向量

        返回：加权平均
        """
        if weights is None:
            return sum(self.data) / self.n

        weighted_sum = sum(w * x for w, x in zip(weights, self.data))
        weight_sum = sum(abs(w) for w in weights)

        return weighted_sum / weight_sum if weight_sum > 0 else 0

    def query_variance(self) -> float:
        """方差查询"""
        mean = self.query_mean()
        return sum((x - mean) ** 2 for x in self.data) / self.n

    def query_correlation(self, x_indices: List[int], y_indices: List[int]) -> float:
        """
        相关性查询

        参数：
            x_indices: 第一个变量的索引
            y_indices: 第二个变量的索引

        返回：相关系数
        """
        if len(x_indices) != len(y_indices):
            return 0

        n = len(x_indices)
        x_vals = [self.data[i] for i in x_indices]
        y_vals = [self.data[i] for i in y_indices]

        mean_x = sum(x_vals) / n
        mean_y = sum(y_vals) / n

        cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals)) / n
        std_x = (sum((x - mean_x) ** 2 for x in x_vals) / n) ** 0.5
        std_y = (sum((y - mean_y) ** 2 for y in y_vals) / n) ** 0.5

        return cov / (std_x * std_y) if std_x > 0 and std_y > 0 else 0


class SQTolerance:
    """SQ容差"""

    def __init__(self, tau: float):
        """
        参数：
            tau: 容差参数
        """
        self.tau = tau

    def is_learnable(self, concept_class_size: int) -> bool:
        """
        检查概念类是否在此容差下可学习

        参数：
            concept_class_size: 概念类大小

        返回：是否可学习
        """
        # 简化的可学习性判断
        # 真实条件需要更复杂的分析

        return concept_class_size < 1 / (self.tau ** 2)


def sq_vs_membership():
    """SQ vs 成员查询"""
    print("=== SQ模型 vs 成员查询模型 ===")
    print()
    print("成员查询（PAC）：")
    print("  - 可以访问任意数据点")
    print("  - 强大但需要完整数据")
    print()
    print("统计查询（SQ）：")
    print("  - 只能访问统计信息")
    print("  - 更弱但更实际")
    print()
    print("关系：")
    print("  - SQ ⊆ PAC（SQ更严格）")
    print("  - 但很多问题在SQ中仍然困难")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 统计查询模型测试 ===\n")

    random.seed(42)

    # 创建数据集
    data = [random.gauss(5, 2) for _ in range(100)]

    oracle = SQOracle(data)

    # 查询
    mean = oracle.query_mean()
    var = oracle.query_variance()

    print(f"数据统计：")
    print(f"  均值: {mean:.4f}")
    print(f"  方差: {var:.4f}")

    print()
    sq_vs_membership()

    print()
    print("SQ模型的应用：")
    print("  - 隐私保护机器学习")
    print("  - 差分隐私（SQ是DP的宽松版本）")
    print("  - 样本复杂度分析")
