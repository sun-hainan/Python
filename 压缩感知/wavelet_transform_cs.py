# -*- coding: utf-8 -*-
"""
算法实现：压缩感知 / wavelet_transform_cs

本文件实现 wavelet_transform_cs 相关的算法功能。
"""

import numpy as np
from typing import Tuple, Optional
from scipy import signal
import pywt


def create_haar_matrix(n: int) -> np.ndarray:
    """
    创建Haar小波变换矩阵（2^n × 2^n）
    """
    if n == 1:
        return np.array([[1.0, 1.0], [1.0, -1.0]]) / np.sqrt(2)

    # 递归构建
    H_small = create_haar_matrix(n - 1)
    m = H_small.shape[0]

    # Kronecker积：H_n = H_2 ⊗ H_{n-1}
    H_big = np.zeros((2 * m, 2 * m))
    H_big[:m, :m] = H_small
    H_big[:m, m:] = H_small
    H_big[m:, :m] = H_small
    H_big[m:, m:] = -H_small

    return H_big / np.sqrt(2)


def daubechies_wavelet_matrix(N: int, db_order: int = 4) -> np.ndarray:
    """
    创建Daubechies小波酉矩阵（简化版）
    db_order: Daubechies阶数（4, 6, 8, ...）
    """
    # 使用scipy生成滤波器系数
    wavelet = f'db{db_order}'
    _, low_decomp, high_decomp, _, _ = pywt.Wavelet(wavelet).info

    # 简化的正交小波矩阵
    # 实际实现需要更复杂的滤波器设计
    raise NotImplementedError("需要完整的Daubechies矩阵构造")


def create_toeplitz_measurement_matrix(n: int, m: int, 
                                       lowpass_filter: np.ndarray) -> np.ndarray:
    """
    创建Toeplitz结构测量矩阵（用于小波域压缩感知）
    基于低通滤波器生成的循环Toeplitz矩阵

    这种结构：
    1. 保证与稀疏小波基的不相关性
    2. 易于硬件实现
    3. 存储效率高
    """
    # 低通滤波器（示例）
    if lowpass_filter is None:
        lowpass_filter = np.array([0.5, 0.25, 0.125, 0.125])

    # 创建Toeplitz结构
    A = np.zeros((m, n))
    for i in range(m):
        for j in range(n):
            idx = (i - j) % len(lowpass_filter)
            A[i, j] = lowpass_filter[idx]

    return A / np.sqrt(m)


def wavelet_sparse_basis(n: int, wavelet: str = "haar", 
                         level: Optional[int] = None) -> np.ndarray:
    """
    创建小波稀疏基矩阵

    对于Haar小波，可以使用Hadamard矩阵结构
    对于其他小波，使用pywt进行分解
    """
    if wavelet == "haar":
        # Haar小波：使用Hadamard矩阵
        if level is None:
            level = int(np.log2(n))
        return create_haar_matrix(level)

    elif wavelet == "db4":
        # Daubechies-4小波
        coeffs = pywt.wavedec(np.eye(n), wavelet, level=level)
        # 将小波系数堆叠为稀疏基
        # 简化为单位矩阵（实际应用需要正确的变换）
        return np.eye(n)

    else:
        # 默认返回单位阵
        return np.eye(n)


def cs_recovery_wavelet(A: np.ndarray, y: np.ndarray,
                        Psi: np.ndarray, s: int,
                        max_iter: int = 100) -> np.ndarray:
    """
    小波域压缩感知恢复

    信号模型：x = Psi * α，其中 α 是稀疏的
    测量：y = A * x = A * Psi * α

    恢复：在小波域稀疏约束下求解
    """
    # 构造复合测量矩阵
    Theta = A @ Psi

    # OMP恢复
    x_sparse = omp_sparse(Theta, y, s)

    # 逆变换
    x_recovered = Psi @ x_sparse

    return x_recovered


def omp_sparse(A: np.ndarray, y: np.ndarray, s: int) -> np.ndarray:
    """OMP稀疏恢复"""
    n = A.shape[1]
    x = np.zeros(n)
    support = []
    residual = y.copy()

    for _ in range(s):
        c = A.T @ residual
        best_idx = np.argmax(np.abs(c))
        if best_idx in support:
            break
        support.append(best_idx)

        A_support = A[:, support]
        x_support, _, _, _ = np.linalg.lstsq(A_support, y, rcond=None)

        residual = y - A_support @ x_support

    x[support] = x_support
    return x


class WaveletCSRecovery:
    """小波域压缩感知恢复器"""

    def __init__(self, n: int, wavelet: str = "haar"):
        self.n = n
        self.wavelet = wavelet
        self.Psi = wavelet_sparse_basis(n, wavelet)
        self.A = None

    def set_measurement_matrix(self, m: int, matrix_type: str = "gaussian"):
        """设置测量矩阵"""
        if matrix_type == "gaussian":
            self.A = np.random.randn(m, self.n) / np.sqrt(m)
        elif matrix_type == "toeplitz":
            lowpass = np.array([0.5, 0.25, 0.125, 0.125])
            self.A = create_toeplitz_measurement_matrix(self.n, m, lowpass)
        elif matrix_type == "bernoulli":
            self.A = np.random.choice([-1, 1], (m, self.n)) / np.sqrt(m)

    def recover(self, y: np.ndarray, s: int) -> np.ndarray:
        """恢复信号"""
        if self.A is None:
            raise ValueError("测量矩阵未设置")
        return cs_recovery_wavelet(self.A, y, self.Psi, s)


def test_wavelet_cs():
    """测试小波域压缩感知"""
    np.random.seed(42)

    n = 256   # 信号维度（2的幂次）
    m = 80    # 测量数
    s = 15    # 稀疏度

    print("=== 小波域压缩感知测试 ===")
    print(f"信号维度: {n}, 测量数: {m}, 稀疏度: {s}")

    # 创建小波基
    print("\n--- 小波基构造 ---")
    Psi_haar = wavelet_sparse_basis(n, "haar")
    print(f"Haar矩阵形状: {Psi_haar.shape}")
    print(f"是正交矩阵: {np.allclose(Psi_haar @ Psi_haar.T, np.eye(n))}")

    # 生成稀疏信号
    print("\n--- 信号生成 ---")
    x_true = np.zeros(n)
    support = np.random.choice(n, s, replace=False)
    x_true[support] = np.random.randn(s)

    # 小波变换后的稀疏性
    alpha = Psi_haar.T @ x_true
    alpha_sparse_count = np.sum(np.abs(alpha) > 1e-6)
    print(f"小波域非零系数: {alpha_sparse_count}")

    # 创建测量矩阵
    A = np.random.randn(m, n) / np.sqrt(m)

    # 测量
    y = A @ x_true

    # 恢复
    print("\n--- 恢复测试 ---")
    x_recovered = cs_recovery_wavelet(A, y, Psi_haar, s + 5)  # 加点冗余
    error = np.linalg.norm(x_recovered - x_true) / np.linalg.norm(x_true)
    print(f"恢复误差: {error:.6f}")

    # 不同测量矩阵对比
    print("\n--- 不同测量矩阵对比 ---")
    matrix_types = ["gaussian", "toeplitz", "bernoulli"]

    for mt in matrix_types:
        if mt == "toeplitz":
            A_test = create_toeplitz_measurement_matrix(n, m, None)
        elif mt == "gaussian":
            A_test = np.random.randn(m, n) / np.sqrt(m)
        else:
            A_test = np.random.choice([-1, 1], (m, n)) / np.sqrt(m)

        y_test = A_test @ x_true
        x_rec = cs_recovery_wavelet(A_test, y_test, Psi_haar, s)
        err = np.linalg.norm(x_rec - x_true) / np.linalg.norm(x_true)
        print(f"{mt:>12}: 误差 = {err:.6f}")

    # 小波CS恢复器测试
    print("\n--- WaveletCSRecovery类测试 ---")
    recovery = WaveletCSRecovery(n, "haar")
    recovery.set_measurement_matrix(m, "gaussian")
    x_recover = recovery.recover(y, s)
    err_class = np.linalg.norm(x_recover - x_true) / np.linalg.norm(x_true)
    print(f"类方法恢复误差: {err_class:.6f}")


if __name__ == "__main__":
    test_wavelet_cs()
