# -*- coding: utf-8 -*-
"""
算法实现：压缩感知 / rip_measurement

本文件实现 rip_measurement 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple


class RIPMatrix:
    """RIP测量矩阵"""

    def __init__(self, n: int, m: int):
        """
        参数：
            n: 信号维度
            m: 测量数
        """
        self.n = n
        self.m = m
        self.matrix = self._generate_matrix()

    def _generate_matrix(self) -> np.ndarray:
        """
        生成高斯随机矩阵

        返回：m × n 矩阵
        """
        # 生成高斯随机矩阵并归一化
        A = np.random.randn(self.m, self.n)
        A = A / np.sqrt(self.m)  # 列归一化

        return A

    def compute_rip_constant(self, k: int, n_trials: int = 100) -> float:
        """
        计算RIP常数δ

        参数：
            k: 稀疏度
            n_trials: 试验次数

        返回：估计的RIP常数
        """
        max_ratio = 0
        min_ratio = float('inf')

        for _ in range(n_trials):
            # 生成随机k-稀疏向量
            x = np.zeros(self.n)
            support = np.random.choice(self.n, k, replace=False)
            x[support] = np.random.randn(k)

            x_norm_sq = np.linalg.norm(x) ** 2

            if x_norm_sq < 1e-10:
                continue

            # 测量
            y = self.matrix @ x
            y_norm_sq = np.linalg.norm(y) ** 2

            # 比例
            ratio = y_norm_sq / x_norm_sq

            max_ratio = max(max_ratio, ratio)
            min_ratio = min(min_ratio, ratio)

        # RIP常数
        delta = max(max_ratio - 1, 1 - min_ratio)

        return delta

    def verify_rip(self, k: int, delta_threshold: float = 0.5) -> dict:
        """
        验证RIP条件

        返回：验证结果
        """
        delta = self.compute_rip_constant(k)

        return {
            'rip_constant': delta,
            'satisfies_rip': delta < delta_threshold,
            'k': k,
            'm': self.m,
            'n': self.n
        }

    def sensing_matrix_properties(self) -> dict:
        """
        分析传感矩阵属性

        返回：属性字典
        """
        # 奇异值分解
        U, s, Vt = np.linalg.svd(self.matrix, full_matrices=False)

        return {
            'rank': len([sv for sv in s if sv > 1e-10]),
            'condition_number': s[0] / s[-1] if s[-1] > 1e-10 else float('inf'),
            'singular_values': s.tolist()[:10]  # 前10个
        }


def rip_theory():
    """RIP理论"""
    print("=== RIP理论 ===")
    print()
    print("RIP条件：")
    print("  (1-δ)||x||² ≤ ||Ax||² ≤ (1+δ)||x||²")
    print("  对所有k-稀疏向量x成立")
    print()
    print("RIP常数要求：")
    print("  - δ < sqrt(2) - 1 ≈ 0.414 用于精确恢复")
    print("  - 常见的是 δ < 0.5")
    print()
    print("RIP的应用：")
    print("  - 保证稀疏信号恢复")
    print("  - 分析测量矩阵质量")
    print("  - 压缩感知理论核心")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== RIP测量矩阵测试 ===\n")

    np.random.seed(42)

    # 创建传感矩阵
    n = 100  # 信号维度
    m = 30   # 测量数

    rip_matrix = RIPMatrix(n, m)

    print(f"信号维度 n: {n}")
    print(f"测量数 m: {m}")
    print(f"压缩比: {m/n:.2f}")
    print()

    # 验证RIP
    k = 5  # 稀疏度

    print(f"验证RIP (k={k}):")
    result = rip_matrix.verify_rip(k, delta_threshold=0.5)

    print(f"  RIP常数 δ: {result['rip_constant']:.4f}")
    print(f"  满足RIP (δ<0.5): {'是' if result['satisfies_rip'] else '否'}")
    print()

    # 矩阵属性
    props = rip_matrix.sensing_matrix_properties()

    print("传感矩阵属性：")
    print(f"  秩: {props['rank']}")
    print(f"  条件数: {props['condition_number']:.2f}")
    print(f"  奇异值（前5）: {[f'{sv:.2f}' for sv in props['singular_values'][:5]]}")

    print()
    rip_theory()

    print()
    print("说明：")
    print("  - RIP是压缩感知的核心性质")
    print("  - 高斯矩阵大概率满足RIP")
    print("  - RIP常数越小恢复越精确")
