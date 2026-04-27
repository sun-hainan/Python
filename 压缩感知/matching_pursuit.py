# -*- coding: utf-8 -*-
"""
算法实现：压缩感知 / matching_pursuit

本文件实现 matching_pursuit 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple


class MatchingPursuit:
    """匹配追踪算法"""

    def __init__(self, dictionary: np.ndarray, max_iter: int = 100):
        """
        参数：
            dictionary: 字典矩阵（列是原子）
            max_iter: 最大迭代次数
        """
        self.D = dictionary  # n_atoms x n_features
        self.n_atoms, self.n_features = dictionary.shape
        self.max_iter = max_iter

    def sparse_decompose(self, signal: np.ndarray, sparsity: int) -> Tuple[np.ndarray, List[int]]:
        """
        稀疏分解

        参数：
            signal: 输入信号
            sparsity: 稀疏度（非零系数数量）

        返回：(稀疏系数, 使用的原子索引)
        """
        residual = signal.copy()
        indices = []
        coefficients = np.zeros(self.n_atoms)

        for _ in range(sparsity):
            # 找与残差最相关的原子
            correlations = self.D.T @ residual
            idx = np.argmax(np.abs(correlations))

            if np.abs(correlations[idx]) < 1e-10:
                break

            indices.append(idx)

            # 更新系数（最小二乘）
            selected = np.array(indices)
            D_subset = self.D[:, selected]

            try:
                coeff = np.linalg.lstsq(D_subset, signal, rcond=None)[0]
            except:
                coeff = np.zeros(len(indices))

            # 更新残差
            approximation = D_subset @ coeff
            residual = signal - approximation

            # 更新系数
            for i, idx_i in enumerate(indices):
                coefficients[idx_i] = coeff[i]

        return coefficients, indices


class OrthogonalMP:
    """正交匹配追踪（OMP）"""

    def __init__(self, dictionary: np.ndarray, tolerance: float = 1e-6):
        self.D = dictionary
        self.tolerance = tolerance

    def omp_decompose(self, signal: np.ndarray, sparsity: int) -> Tuple[np.ndarray, List[int]]:
        """
        OMP稀疏分解

        与MP的区别：每次迭代对所有选中原子做正交化
        """
        residual = signal.copy()
        indices = []
        coefficients = np.zeros(self.D.shape[1])

        for _ in range(sparsity):
            # 相关性
            correlations = np.abs(self.D.T @ residual)
            correlations[indices] = -np.inf  # 已选原子不再选

            # 选最相关原子
            idx = np.argmax(correlations)
            indices.append(idx)

            # 最小二乘更新（所有选中原子正交）
            D_used = self.D[:, indices]
            coeff = np.linalg.lstsq(D_used, signal, rcond=None)[0]

            # 更新残差
            approximation = D_used @ coeff
            residual = signal - approximation

            # 残差足够小则停止
            if np.linalg.norm(residual) < self.tolerance:
                break

        for i, idx in enumerate(indices):
            coefficients[idx] = coeff[i]

        return coefficients, indices


def create_gaussian_dictionary(n_atoms: int, n_features: int) -> np.ndarray:
    """
    创建高斯字典

    参数：
        n_atoms: 原子数
        n_features: 特征维数

    返回：归一化的字典矩阵
    """
    D = np.random.randn(n_features, n_atoms)
    # 归一化每个原子
    for i in range(n_atoms):
        D[:, i] /= np.linalg.norm(D[:, i])
    return D


def signal_reconstruction():
    """信号重建示例"""
    print("=== 匹配追踪信号重建 ===\n")

    # 创建字典
    n_features = 100
    n_atoms = 200
    D = create_gaussian_dictionary(n_atoms, n_features)

    # 创建稀疏信号
    sparsity = 5
    true_indices = np.random.choice(n_atoms, sparsity, replace=False)
    true_coeff = np.zeros(n_atoms)
    true_coeff[true_indices] = np.random.randn(sparsity)

    signal = D @ true_coeff

    print(f"信号维度: {signal.shape}")
    print(f"字典大小: {D.shape}")
    print(f"真实稀疏度: {sparsity}")
    print(f"真实非零位置: {sorted(true_indices)}")
    print()

    # MP分解
    mp = MatchingPursuit(D)
    recovered_coeff, used_indices = mp.sparse_decompose(signal, sparsity)

    print("MP结果：")
    print(f"  恢复稀疏度: {np.sum(np.abs(recovered_coeff) > 0.1)}")
    print(f"  恢复原子: {sorted(used_indices)}")
    print(f"  重建误差: {np.linalg.norm(signal - D @ recovered_coeff):.4f}")

    print()

    # OMP分解
    omp = OrthogonalMP(D)
    omp_coeff, omp_indices = omp.omp_decompose(signal, sparsity)

    print("OMP结果：")
    print(f"  恢复稀疏度: {np.sum(np.abs(omp_coeff) > 0.1)}")
    print(f"  恢复原子: {sorted(omp_indices)}")
    print(f"  重建误差: {np.linalg.norm(signal - D @ omp_coeff):.4f}")


def compressive_sensing():
    """压缩感知应用"""
    print()
    print("=== 压缩感知 ===")
    print()
    print("场景：从少量测量中恢复稀疏信号")
    print()
    print("步骤：")
    print("  1. 采样：y = Φx")
    print("  2. 恢复：通过OMP等算法恢复x")
    print()
    print("条件：")
    print("  - 信号是稀疏的（在某字典下）")
    print("  - 测量矩阵满足RIP")
    print()
    print("应用：")
    print("  - MRI成像")
    print("  - 天文图像")
    print("  - 无线通信")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    np.random.seed(42)
    signal_reconstruction()
    compressive_sensing()

    print()
    print("算法对比：")
    print("  MP：贪心，简单但可能不收敛")
    print("  OMP：每次正交化，收敛更快")
    print("  CoSaMP：更鲁棒，处理噪声更好")
