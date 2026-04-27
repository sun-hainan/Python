# -*- coding: utf-8 -*-
"""
算法实现：压缩感知 / cosamp_detailed

本文件实现 cosamp_detailed 相关的算法功能。
"""

import numpy as np
from typing import Tuple


class CoSaMPDetailed:
    """CoSaMP详细实现"""

    def __init__(self, A: np.ndarray):
        """
        参数：
            A: 测量矩阵
        """
        self.A = A
        self.m, self.n = A.shape

    def recover(self, y: np.ndarray, k: int,
              max_iter: int = 100,
              tolerance: float = 1e-6) -> np.ndarray:
        """
        恢复稀疏信号

        参数：
            y: 观测向量
            k: 稀疏度
            max_iter: 最大迭代
            tolerance: 收敛容差

        返回：恢复的信号
        """
        # 初始化
        residual = y.copy()
        support = set()
        x_hat = np.zeros(self.n)

        for iteration in range(max_iter):
            # Step 1: 关联 - 找到最大的2k个相关列
            correlations = np.abs(self.A.T @ residual)
            largest_indices = np.argsort(correlations)[-2*k:]

            # Step 2: 合并支持集
            support = support | set(largest_indices)

            # Step 3: 最小二乘求解
            support_list = list(support)
            A_support = self.A[:, support_list]

            # 最小二乘解
            x_temp = np.linalg.lstsq(A_support, y, rcond=None)[0]

            # Step 4: 修剪 - 只保留最大的k个
            x_full = np.zeros(self.n)
            for i, idx in enumerate(support_list):
                x_full[idx] = x_temp[i]

            # 找最大的k个
            k_largest = np.argsort(np.abs(x_full))[-k:]
            x_hat = np.zeros(self.n)
            for idx in k_largest:
                x_hat[idx] = x_full[idx]

            # 更新支持集
            support = set(k_largest)

            # Step 5: 更新残差
            residual = y - self.A @ x_hat

            # 检查收敛
            if np.linalg.norm(residual) < tolerance:
                print(f"在第{iteration+1}次迭代收敛")
                break

        return x_hat


def cosamp_analysis():
    """CoSaMP分析"""
    print("=== CoSaMP分析 ===")
    print()
    print("收敛性：")
    print("  - 在RIP条件下 O(k log n) 收敛")
    print("  - 通常10-20次迭代")
    print()
    print("复杂度：")
    print("  - 每次迭代 O(mn)")
    print("  - 总复杂度 O(k m n)")
    print()
    print("RIP条件：")
    print("  - 需要 2k 阶RIP")
    print("  - 矩阵需要特殊结构")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== CoSaMP详细测试 ===\n")

    np.random.seed(42)

    # 创建问题
    n = 200  # 信号维度
    k = 10   # 稀疏度
    m = 60   # 测量数

    # 测量矩阵
    A = np.random.randn(m, n)
    A = A / np.linalg.norm(A, axis=0)

    # 真实信号
    x_true = np.zeros(n)
    support = np.random.choice(n, k, replace=False)
    x_true[support] = np.random.randn(k)

    # 观测
    y = A @ x_true + 0.01 * np.random.randn(m)

    print(f"信号维度: {n}, 测量数: {m}, 稀疏度: {k}")
    print()

    # CoSaMP恢复
    cosamp = CoSaMPDetailed(A)
    x_rec = cosamp.recover(y, k)

    # 误差
    error = np.linalg.norm(x_rec - x_true) / np.linalg.norm(x_true)
    support_rec = set(np.where(np.abs(x_rec) > 0.1)[0])
    support_match = len(support & support_rec)

    print(f"相对误差: {error:.4f}")
    print(f"支持集匹配: {support_match}/{k}")
    print(f"恢复成功率: {support_match/k*100:.1f}%")

    print()
    cosamp_analysis()

    print()
    print("说明：")
    print("  - CoSaMP是贪婪算法的代表")
    print("  - 有RIP理论保证")
    print("  - 比OMP更好但计算量更大")
