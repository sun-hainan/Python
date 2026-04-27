# -*- coding: utf-8 -*-
"""
算法实现：次线性算法 / sparse_recovery

本文件实现 sparse_recovery 相关的算法功能。
"""

import numpy as np
import random


def orthogonal_matching_pursuit(y, A, k, tolerance=1e-6):
    """
    正交匹配追踪 (OMP)
    
    贪婪算法:
    1. 找到与残差最相关的列
    2. 添加到支撑集
    3. 最小二乘更新
    4. 重复直到达到 k 个原子或残差足够小
    
    时间复杂度: O(k * n * m)
    
    Parameters
    ----------
    y : np.ndarray
        测量向量,形状 (m,)
    A : np.ndarray
        测量矩阵,形状 (m, n)
    k : int
        稀疏度
    tolerance : float
        收敛容差
    
    Returns
    -------
    np.ndarray
        恢复的稀疏向量 x,形状 (n,)
    """
    m, n = A.shape
    
    # 初始化
    residual = y.copy()
    x_hat = np.zeros(n)
    support = []
    
    for iteration in range(k):
        # 计算相关度
        correlations = np.abs(A.T @ residual)
        
        # 选择最大相关的索引 (不在支撑集中)
        for idx in support:
            correlations[idx] = 0
        
        max_corr_idx = np.argmax(correlations)
        
        if correlations[max_corr_idx] < tolerance:
            break
        
        support.append(max_corr_idx)
        
        # 最小二乘更新
        A_support = A[:, support]
        x_support, _, _, _ = np.linalg.lstsq(A_support, y, rcond=None)
        
        # 更新残差
        residual = y - A_support @ x_support
        
        # 更新 x_hat
        x_hat[support] = x_support
    
    return x_hat


def iterative_hard_thresholding(y, A, k, max_iter=100, tolerance=1e-6):
    """
    迭代硬阈值 (IHT)
    
    算法:
    x_{t+1} = H_k(x_t + A^T(y - Ax_t))
    
    其中 H_k 是硬阈值算子,保留 k 个最大元素
    
    时间复杂度: O(k * n * m) per iteration
    
    Parameters
    ----------
    y : np.ndarray
        测量向量
    A : np.ndarray
        测量矩阵
    k : int
        稀疏度
    max_iter : int
        最大迭代次数
    tolerance : float
        收敛容差
    
    Returns
    -------
    np.ndarray
        恢复的稀疏向量
    """
    m, n = A.shape
    
    # 初始化
    x = np.zeros(n)
    
    for iteration in range(max_iter):
        # 梯度步骤
        gradient = A.T @ (y - A @ x)
        x_new = x + gradient
        
        # 硬阈值
        # 保留 k 个最大元素
        threshold = np.sort(np.abs(x_new))[-k] if k < n else np.abs(x_new).min()
        x_new[np.abs(x_new) < threshold] = 0
        
        # 检查收敛
        if np.linalg.norm(x_new - x) < tolerance:
            x = x_new
            break
        
        x = x_new
    
    return x


def cosamp(A, y, k, max_iter=100, tolerance=1e-6):
    """
    CoSaMP (Compressive Sampling Matching Pursuit)
    
    算法:
    1. 找到残差最相关的 2k 列
    2. 合并到候选集
    3. 最小二乘估计
    4. 硬阈值保留 k 个最大
    5. 更新残差
    
    时间复杂度: O(k * n * m)
    
    Parameters
    ----------
    A : np.ndarray
        测量矩阵
    y : np.ndarray
        测量向量
    k : int
        稀疏度
    max_iter : int
        最大迭代次数
    tolerance : float
        收敛容差
    
    Returns
    -------
    np.ndarray
        恢复的稀疏向量
    """
    m, n = A.shape
    
    x_hat = np.zeros(n)
    residual = y.copy()
    
    for iteration in range(max_iter):
        # 找到残差最相关的 2k 列
        correlations = np.abs(A.T @ residual)
        
        # 候选集
        candidates = set(np.argsort(correlations)[-2 * k:])
        
        # 合并当前支撑集
        current_support = set(np.where(np.abs(x_hat) > 1e-10)[0])
        support = list(candidates | current_support)
        
        # 最小二乘估计
        A_support = A[:, support]
        x_support, _, _, _ = np.linalg.lstsq(A_support, y, rcond=None)
        
        # 硬阈值保留 k 个最大
        if len(x_support) > k:
            threshold = np.sort(np.abs(x_support))[-k]
            x_support[np.abs(x_support) < threshold] = 0
        
        # 更新支撑集
        new_support = [support[i] for i in range(len(support)) if np.abs(x_support[i]) > 1e-10]
        
        # 重构信号
        x_hat = np.zeros(n)
        for i, idx in enumerate(new_support):
            x_hat[idx] = x_support[i]
        
        # 更新残差
        residual = y - A @ x_hat
        
        # 检查收敛
        residual_norm = np.linalg.norm(residual)
        if residual_norm < tolerance:
            break
    
    return x_hat


def basis_pursuit(y, A, lambda_reg=0.01, max_iter=1000, tolerance=1e-6):
    """
    基追踪 (Basis Pursuit)
    
    求解: min ||x||_1 s.t. Ax = y
    
    使用近端梯度法 (ISTA)
    
    Parameters
    ----------
    y : np.ndarray
        测量向量
    A : np.ndarray
        测量矩阵
    lambda_reg : float
        正则化参数
    max_iter : int
        最大迭代次数
    tolerance : float
        收敛容差
    
    Returns
    -------
    np.ndarray
        恢复的稀疏向量
    """
    m, n = A.shape
    
    # Lipschitz 常数
    L = np.linalg.norm(A, ord=2) ** 2
    
    # 初始化
    x = np.zeros(n)
    
    for iteration in range(max_iter):
        # 梯度步骤
        gradient = A.T @ (A @ x - y)
        x_temp = x - gradient / L
        
        # 软阈值
        x_new = np.sign(x_temp) * np.maximum(np.abs(x_temp) - lambda_reg / L, 0)
        
        # 检查收敛
        if np.linalg.norm(x_new - x) < tolerance:
            x = x_new
            break
        
        x = x_new
    
    return x


def thresholding_operator(x, k):
    """
    硬阈值算子
    
    保留 x 中 k 个最大元素,其余设为 0
    
    Parameters
    ----------
    x : np.ndarray
        输入向量
    k : int
        保留的元素数量
    
    Returns
    -------
    np.ndarray
        稀疏向量
    """
    result = np.zeros_like(x)
    
    if k >= len(x):
        return x.copy()
    
    # 找到 k 个最大元素的索引
    indices = np.argsort(np.abs(x))[-k:]
    
    for idx in indices:
        result[idx] = x[idx]
    
    return result


def soft_thresholding(x, threshold):
    """
    软阈值算子 (Shrinkage)
    
    S_τ(x) = sign(x) * max(|x| - τ, 0)
    
    Parameters
    ----------
    x : np.ndarray
        输入向量
    threshold : float
        阈值
    
    Returns
    -------
    np.ndarray
        收缩后的向量
    """
    return np.sign(x) * np.maximum(np.abs(x) - threshold, 0)


def compressive_sampling_matrix(m, n, type='gaussian'):
    """
    生成压缩采样测量矩阵
    
    类型:
    - gaussian: i.i.d. N(0, 1/m)
    - bernoulli: ±1/√m
    - partial_dct: 随机选择的 DCT 基
    
    Parameters
    ----------
    m : int
        测量数量
    n : int
        信号长度
    type : str
        矩阵类型
    
    Returns
    -------
    np.ndarray
        测量矩阵
    """
    if type == 'gaussian':
        A = np.random.randn(m, n) / np.sqrt(m)
    
    elif type == 'bernoulli':
        A = (np.random.randint(0, 2, size=(m, n)) * 2 - 1) / np.sqrt(m)
    
    elif type == 'partial_dct':
        # 随机选择 m 行 DCT 矩阵
        dct_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dct_matrix[i, j] = np.cos(np.pi * i * (j + 0.5) / n)
        
        rows = np.random.choice(n, m, replace=False)
        A = dct_matrix[rows] / np.sqrt(m)
    
    else:
        raise ValueError(f"未知类型: {type}")
    
    return A


def verify_rip(A, s, delta):
    """
    验证 RIP (Restricted Isometry Property) 条件
    
    RIP(s, δ): 对所有 s-稀疏向量 x,
    (1-δ)||x||_2^2 <= ||Ax||_2^2 <= (1+δ)||x||_2^2
    
    这里使用随机测试估计
    
    Parameters
    ----------
    A : np.ndarray
        测量矩阵
    s : int
        稀疏度
    delta : float
        RIP 常数
    num_tests : int
        测试次数
    
    Returns
    -------
    float
        估计的 RIP 常数
    """
    m, n = A.shape
    num_tests = 100
    
    max_delta = 0
    
    for _ in range(num_tests):
        # 生成随机 s-稀疏向量
        x = np.zeros(n)
        support = np.random.choice(n, s, replace=False)
        x[support] = np.random.randn(s)
        
        # 测量
        y = A @ x
        
        # 计算范数比
        norm_x = np.linalg.norm(x)
        norm_y = np.linalg.norm(y)
        
        if norm_x > 1e-10:
            ratio = (norm_y ** 2) / (norm_x ** 2)
            delta_est = max(abs(1 - ratio))
            max_delta = max(max_delta, delta_est)
    
    return max_delta


def sparse_signal_recovery_comparison(y, A, k, methods=None):
    """
    比较多种稀疏恢复方法
    
    Parameters
    ----------
    y : np.ndarray
        测量向量
    A : np.ndarray
        测量矩阵
    k : int
        稀疏度
    methods : list
        要比较的方法列表
    
    Returns
    -------
    dict
        各方法的恢复结果
    """
    if methods is None:
        methods = ['omp', 'iht', 'cosamp', 'bp']
    
    results = {}
    
    if 'omp' in methods:
        x_omp = orthogonal_matching_pursuit(y, A, k)
        results['omp'] = {
            'x': x_omp,
            'error': np.linalg.norm(x_omp - true_x) if 'true_x' in dir() else None
        }
    
    if 'iht' in methods:
        x_iht = iterative_hard_thresholding(y, A, k)
        results['iht'] = {'x': x_iht}
    
    if 'cosamp' in methods:
        x_cosamp = cosamp(A, y, k)
        results['cosamp'] = {'x': x_cosamp}
    
    if 'bp' in methods:
        x_bp = basis_pursuit(y, A, lambda_reg=0.01)
        results['bp'] = {'x': x_bp}
    
    return results


def stable_sparse_recovery(A, k, noise_level=0.1):
    """
    稳定稀疏恢复测试
    
    验证算法在噪声存在时的鲁棒性
    
    Parameters
    ----------
    A : np.ndarray
        测量矩阵
    k : int
        稀疏度
    noise_level : float
        噪声水平
    
    Returns
    -------
    dict
        各算法的恢复误差
    """
    m, n = A.shape
    
    # 生成随机稀疏信号
    x_true = np.zeros(n)
    support = np.random.choice(n, k, replace=False)
    x_true[support] = np.random.randn(k)
    
    # 添加噪声的测量
    y = A @ x_true + noise_level * np.random.randn(m)
    
    # 各算法恢复
    errors = {}
    
    x_omp = orthogonal_matching_pursuit(y, A, k)
    errors['omp'] = np.linalg.norm(x_omp - x_true) / np.linalg.norm(x_true)
    
    x_iht = iterative_hard_thresholding(y, A, k)
    errors['iht'] = np.linalg.norm(x_iht - x_true) / np.linalg.norm(x_true)
    
    x_cosamp = cosamp(A, y, k)
    errors['cosamp'] = np.linalg.norm(x_cosamp - x_true) / np.linalg.norm(x_true)
    
    x_bp = basis_pursuit(y, A, lambda_reg=0.01)
    errors['bp'] = np.linalg.norm(x_bp - x_true) / np.linalg.norm(x_true)
    
    return errors


if __name__ == "__main__":
    # 测试: 稀疏恢复
    
    print("=" * 60)
    print("稀疏恢复算法测试")
    print("=" * 60)
    
    np.random.seed(42)
    random.seed(42)
    
    # 设置参数
    n = 200  # 信号长度
    m = 50   # 测量数量 (远小于 n)
    k = 5    # 稀疏度
    
    print(f"\n信号长度: {n}")
    print(f"测量数量: {m}")
    print(f"稀疏度: {k}")
    
    # 生成测量矩阵
    A = compressive_sampling_matrix(m, n, type='gaussian')
    
    print(f"测量矩阵形状: {A.shape}")
    
    # 生成稀疏信号
    x_true = np.zeros(n)
    support = np.random.choice(n, k, replace=False)
    x_true[support] = np.random.randn(k)
    
    print(f"真实稀疏向量非零位置: {sorted(support)}")
    print(f"真实向量非零值: {x_true[support]}")
    
    # 测量
    y = A @ x_true
    
    print(f"测量向量形状: {y.shape}")
    
    # OMP
    print("\n--- OMP ---")
    x_omp = orthogonal_matching_pursuit(y, A, k)
    omp_error = np.linalg.norm(x_omp - x_true) / np.linalg.norm(x_true)
    print(f"恢复误差 (相对): {omp_error:.6f}")
    print(f"恢复的非零位置: {np.where(np.abs(x_omp) > 1e-6)[0]}")
    
    # IHT
    print("\n--- IHT ---")
    x_iht = iterative_hard_thresholding(y, A, k, max_iter=50)
    iht_error = np.linalg.norm(x_iht - x_true) / np.linalg.norm(x_true)
    print(f"恢复误差 (相对): {iht_error:.6f}")
    
    # CoSaMP
    print("\n--- CoSaMP ---")
    x_cosamp = cosamp(A, y, k, max_iter=20)
    cosamp_error = np.linalg.norm(x_cosamp - x_true) / np.linalg.norm(x_true)
    print(f"恢复误差 (相对): {cosamp_error:.6f}")
    
    # Basis Pursuit
    print("\n--- Basis Pursuit ---")
    x_bp = basis_pursuit(y, A, lambda_reg=0.001)
    bp_error = np.linalg.norm(x_bp - x_true) / np.linalg.norm(x_true)
    print(f"恢复误差 (相对): {bp_error:.6f}")
    
    # 比较
    print("\n--- 算法比较 ---")
    print(f"OMP:     {omp_error:.6f}")
    print(f"IHT:     {iht_error:.6f}")
    print(f"CoSaMP:  {cosamp_error:.6f}")
    print(f"BP:      {bp_error:.6f}")
    
    # 噪声鲁棒性测试
    print("\n--- 噪声鲁棒性测试 ---")
    
    for noise in [0.01, 0.1, 0.5]:
        y_noisy = y + noise * np.random.randn(m)
        
        x_omp_noisy = orthogonal_matching_pursuit(y_noisy, A, k)
        error = np.linalg.norm(x_omp_noisy - x_true) / np.linalg.norm(x_true)
        
        x_cosamp_noisy = cosamp(A, y_noisy, k)
        error_cosamp = np.linalg.norm(x_cosamp_noisy - x_true) / np.linalg.norm(x_true)
        
        print(f"噪声水平={noise}: OMP误差={error:.4f}, CoSaMP误差={error_cosamp:.4f}")
    
    # RIP 验证
    print("\n--- RIP 常数估计 ---")
    
    for s in [5, 10, 15]:
        delta_est = verify_rip(A, s, delta=0.5)
        print(f"k={s} 时估计的 RIP δ: {delta_est:.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
