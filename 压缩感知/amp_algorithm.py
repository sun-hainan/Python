# -*- coding: utf-8 -*-
"""
算法实现：压缩感知 / amp_algorithm

本文件实现 amp_algorithm 相关的算法功能。
"""

import numpy as np
from typing import Tuple, Optional


def amp(A: np.ndarray, y: np.ndarray, s: int,
        max_iter: int = 100, tol: float = 1e-6,
        lambda_0: float = 0.0) -> Tuple[np.ndarray, int, list[float]]:
    """
    近似消息传递算法（AMP）用于稀疏恢复
    输入：
        A: 测量矩阵 (m × n)
        y: 测量向量 (m,)
        s: 稀疏度
        lambda_0: 噪声标准差估计
    输出：
        x: 恢复信号
        iterations: 迭代次数
        residual_history: 残差历史
    """
    m, n = A.shape

    # 计算A的谱范数
    sigma_A = np.linalg.norm(A, ord=2)

    # 初始化
    x = np.zeros(n)
    z = y.copy()  # 残差（有效噪声）
    r_history = []

    for iteration in range(max_iter):
        # 1. 信道估计（去噪）
        # 硬阈值或软阈值
        theta = A.T @ z  # 伪域
        x_new = hard_threshold_sparsity(theta, s)

        # 2. 计算残差
        # AMP特有的"去相关"项：基于上次迭代的x
        if iteration > 0:
            # 修正项：(||x_new||² / m) * (某些量)
            pass

        # 标准AMP残差更新
        Ax_new = A @ x_new
        z_new = y - Ax_new + (n / m) * z * np.mean(np.abs(x_new) > 0)

        # 3. 计算残差范数
        residual_norm = np.linalg.norm(z_new)
        r_history.append(residual_norm)

        # 4. 收敛检查
        if iteration > 0 and abs(r_history[-1] - r_history[-2]) < tol:
            break

        x = x_new
        z = z_new

    return x, iteration + 1, r_history


def hard_threshold_sparsity(x: np.ndarray, s: int) -> np.ndarray:
    """保留s个最大绝对值"""
    n = len(x)
    x_thresh = np.zeros(n)
    indices = np.argsort(np.abs(x))[-s:]
    x_thresh[indices] = x[indices]
    return x_thresh


def soft_threshold(x: np.ndarray, threshold: float) -> np.ndarray:
    """软阈值：sign(x) * max(|x| - threshold, 0)"""
    return np.sign(x) * np.maximum(np.abs(x) - threshold, 0)


def wave_shrink(x: np.ndarray, threshold: float, wavelet: str = "soft") -> np.ndarray:
    """小波收缩（用于信号去噪）"""
    if wavelet == "soft":
        return soft_threshold(x, threshold)
    else:
        return hard_threshold_sparsity(x, int(len(x) * threshold))


def gated_amp(A: np.ndarray, y: np.ndarray, s: int,
              max_iter: int = 100, tol: float = 1e-6) -> Tuple[np.ndarray, int]:
    """
    门控AMP：自适应调整阈值
    思想：根据残差动态调整稀疏约束
    """
    m, n = A.shape

    x = np.zeros(n)
    z = y.copy()
    alpha_history = []  # 门控参数历史

    for iteration in range(max_iter):
        # 计算当前残差能量
        r_norm = np.linalg.norm(z)

        # 门控参数（根据残差调整）
        alpha = min(1.0, r_norm / np.sqrt(m))
        alpha_history.append(alpha)

        # 伪域计算
        theta = A.T @ z

        # 门控阈值
        threshold = alpha * np.median(np.abs(theta)) * 1.4826

        # 去噪（软阈值）
        x_new = soft_threshold(theta, threshold)

        # 更新残差
        Ax_new = A @ x_new
        z_new = y - Ax_new + (n / m) * z * np.mean(np.abs(x_new) > 0)

        # 收敛检查
        if np.linalg.norm(z_new - z) < tol:
            break

        x = x_new
        z = z_new

    return x, iteration + 1


def em_gamp(A: np.ndarray, y: np.ndarray,
            max_iter: int = 100, tol: float = 1e-6) -> Tuple[np.ndarray, int]:
    """
    EM-AMP：期望最大化自适应AMP
    自动估计噪声方差和信号先验参数
    """
    m, n = A.shape

    # 初始化参数估计
    sigma_w_sq = np.var(y) * 0.1  # 噪声方差初始估计
    lambda_param = 0.1  # 稀疏参数

    x = np.zeros(n)
    z = y.copy()

    sigma_x_sq = np.var(A.T @ y) * 0.5  # 信号方差估计

    for iteration in range(max_iter):
        # E步：根据当前参数估计信号后验
        # M步：更新噪声方差和信号方差

        # 伪域
        theta = A.T @ z + sigma_w_sq / sigma_x_sq * x

        # 稀疏先验下的估计
        x_new = np.sign(theta) * np.maximum(np.abs(theta) - lambda_param, 0)

        # 更新方差估计
        sigma_x_sq_new = np.mean(x_new ** 2) + 1e-6

        # 残差更新
        Ax_new = A @ x_new
        z_new = y - Ax_new + (n / m) * z * (sigma_w_sq / sigma_x_sq_new)

        # 更新噪声方差
        sigma_w_sq_new = np.mean(z_new ** 2)

        # 收敛检查
        if abs(sigma_w_sq_new - sigma_w_sq) < tol:
            break

        sigma_x_sq = sigma_x_sq_new
        sigma_w_sq = sigma_w_sq_new
        x = x_new
        z = z_new

    return x, iteration + 1


def test_amp():
    """测试AMP算法"""
    np.random.seed(42)

    n, m, s = 500, 150, 20

    # 生成稀疏信号
    x_true = np.zeros(n)
    support = np.random.choice(n, s, replace=False)
    x_true[support] = np.random.randn(s)
    x_true = x_true / np.linalg.norm(x_true)

    # 测量矩阵
    A = np.random.randn(m, n) / np.sqrt(m)

    # 测量
    y = A @ x_true + 0.001 * np.random.randn(m)

    print("=== AMP算法演示 ===")
    print(f"信号维度: {n}, 测量数: {m}, 稀疏度: {s}")

    # 标准AMP
    x_amp, it_amp, history = amp(A, y, s)
    err_amp = np.linalg.norm(x_amp - x_true) / np.linalg.norm(x_true)
    print(f"\n标准AMP: 迭代={it_amp}, 误差={err_amp:.6f}")

    # 门控AMP
    x_gamp, it_gamp = gated_amp(A, y, s)
    err_gamp = np.linalg.norm(x_gamp - x_true) / np.linalg.norm(x_true)
    print(f"门控AMP: 迭代={it_gamp}, 误差={err_gamp:.6f}")

    # EM-AMP
    x_em, it_em = em_gamp(A, y)
    err_em = np.linalg.norm(x_em - x_true) / np.linalg.norm(x_true)
    print(f"EM-AMP: 迭代={it_em}, 误差={err_em:.6f}")

    print("\n--- 收敛历史（标准AMP）---")
    print(f"初始残差: {history[0]:.4f}")
    print(f"最终残差: {history[-1]:.4f}")
    print(f"收敛速度: {len(history)} 次迭代")


if __name__ == "__main__":
    test_amp()
