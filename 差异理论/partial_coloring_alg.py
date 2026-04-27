# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / partial_coloring_alg

本文件实现 partial_coloring_alg 相关的算法功能。
"""

import math
import random
from typing import List, Tuple, Dict, Optional
import numpy as np


def partial_coloring_lemma(A, target_discrepancy=None):
    """
    部分着色引理的算法实现。
    
    目标：找到向量 x ∈ {-1,0,1}^n 使得 ||Ax||_∞ 最小化。
    
    参数:
        A: numpy.ndarray - 关联矩阵 (m x n)
        target_discrepancy: float - 目标差异值
    
    返回:
        Tuple[numpy.ndarray, float] - (着色向量, 达到的差异)
    """
    m, n = A.shape
    
    if target_discrepancy is None:
        # 使用标准界
        target_discrepancy = 2 * math.sqrt(n * math.log(m + 1))
    
    # 初始化
    x = np.zeros(n)
    remaining = set(range(n))
    
    iteration = 0
    max_iterations = n * 10
    
    while remaining and iteration < max_iterations:
        # 选择最需要着色的元素
        best_idx = None
        best_score = -float('inf')
        
        for idx in remaining:
            # 计算该元素设为 +1 和 -1 时的差异
            current_diff = max(np.abs(A @ x))
            
            # 设为 +1 的情况
            x_plus = x.copy()
            x_plus[idx] = 1
            diff_plus = max(np.abs(A @ x_plus)) if np.any(x_plus) else float('inf')
            
            # 设为 -1 的情况
            x_minus = x.copy()
            x_minus[idx] = -1
            diff_minus = max(np.abs(A @ x_minus)) if np.any(x_minus) else float('inf')
            
            # 选择使差异减小的方向
            improvement = min(diff_plus, diff_minus) - current_diff
            if improvement > best_score:
                best_score = improvement
                best_idx = idx
                best_value = 1 if diff_plus <= diff_minus else -1
        
        if best_idx is None or best_score >= 0:
            # 没有改进，随机选择
            best_idx = random.choice(list(remaining))
            best_value = 1 if random.random() < 0.5 else -1
        
        x[best_idx] = best_value
        remaining.remove(best_idx)
        iteration += 1
    
    # 计算最终差异
    final_discrepancy = max(np.abs(A @ x)) if np.any(x) else 0.0
    
    return x, final_discrepancy


def sdp_relaxation_coloring(A, gamma=1.0):
    """
    基于半正定规划（SDP）松弛的着色算法。
    
    将离散的 ±1 变量松弛到单位球面上的连续变量，
    求解 SDP 后将结果round到 ±1。
    
    参数:
        A: numpy.ndarray - 关联矩阵
        gamma: float - 目标界参数
    
    返回:
        numpy.ndarray - 着色向量
    """
    m, n = A.shape
    
    # 简化的 SDP：直接使用谱方法
    # 计算 A^T A 的特征向量
    M = A.T @ A
    
    try:
        eigenvalues, eigenvectors = np.linalg.eigh(M)
        # 选择最大特征值对应的特征向量
        principal_eigenvector = eigenvectors[:, -1]
    except:
        principal_eigenvector = np.ones(n) / math.sqrt(n)
    
    # 将连续值 round 到 ±1
    coloring = np.sign(principal_eigenvector)
    
    # 确保没有零分量
    coloring[coloring == 0] = 1
    
    return coloring


def greedy_partial_coloring(A, alpha=0.5):
    """
    贪心部分着色算法。
    
    每一步选择使当前差异最小的元素进行着色。
    
    参数:
        A: numpy.ndarray - 关联矩阵
        alpha: float - 平衡参数
    
    返回:
        Tuple[numpy.ndarray, float] - (着色向量, 差异)
    """
    m, n = A.shape
    
    # 初始化
    x = np.zeros(n)
    current_values = np.zeros(m)
    remaining = set(range(n))
    
    while remaining:
        best_idx = None
        best_value = None
        best_max_discrepancy = float('inf')
        
        # 尝试每个剩余元素
        for idx in remaining:
            for val in [1, -1]:
                # 模拟赋值
                trial_x = x.copy()
                trial_x[idx] = val
                trial_values = A @ trial_x
                max_disc = np.max(np.abs(trial_values))
                
                if max_disc < best_max_discrepancy:
                    best_max_discrepancy = max_disc
                    best_idx = idx
                    best_value = val
        
        if best_idx is not None:
            x[best_idx] = best_value
            remaining.remove(best_idx)
        else:
            # 没有改进，随机处理
            best_idx = random.choice(list(remaining))
            x[best_idx] = 1 if random.random() < 0.5 else -1
            remaining.remove(best_idx)
    
    final_discrepancy = np.max(np.abs(A @ x))
    
    return x, final_discrepancy


def metropolis_partial_coloring(A, temperature=1.0, iterations=1000):
    """
    基于 Metropolis-Hastings 的随机部分着色算法。
    
    参数:
        A: numpy.ndarray - 关联矩阵
        temperature: float - 温度参数
        iterations: int - 迭代次数
    
    返回:
        Tuple[numpy.ndarray, float] - (着色向量, 差异)
    """
    m, n = A.shape
    
    # 初始化随机着色
    x = np.array([1 if random.random() < 0.5 else -1 for _ in range(n)])
    current_disc = np.max(np.abs(A @ x))
    
    best_x = x.copy()
    best_disc = current_disc
    
    for _ in range(iterations):
        # 随机选择一个位置翻转
        idx = random.randint(0, n - 1)
        trial_x = x.copy()
        trial_x[idx] = -trial_x[idx]
        
        trial_disc = np.max(np.abs(A @ trial_x))
        delta = trial_disc - current_disc
        
        # Metropolis 准则
        if delta < 0 or random.random() < math.exp(-delta / temperature):
            x = trial_x
            current_disc = trial_disc
            
            if current_disc < best_disc:
                best_x = x.copy()
                best_disc = current_disc
        
        # 降温
        temperature *= 0.995
    
    return best_x, best_disc


def las_vegas_coloring(A, time_limit=5.0):
    """
    拉斯维加斯风格的随机算法。
    
    持续随机搜索，直到找到满足条件的着色或超时。
    
    参数:
        A: numpy.ndarray - 关联矩阵
        time_limit: float - 时间限制（秒）
    
    返回:
        Tuple[numpy.ndarray, float, bool] - (着色, 差异, 是否成功)
    """
    m, n = A.shape
    
    import time
    start_time = time.time()
    
    target_disc = 2 * math.sqrt(n * math.log(m + 1))
    best_x = None
    best_disc = float('inf')
    
    while time.time() - start_time < time_limit:
        # 生成随机着色
        x = np.array([1 if random.random() < 0.5 else -1 for _ in range(n)])
        disc = np.max(np.abs(A @ x))
        
        if disc < best_disc:
            best_x = x.copy()
            best_disc = disc
        
        if disc <= target_disc:
            return x, disc, True
    
    return best_x, best_disc, False


def matrix_sampling_algorithm(A, num_samples=100):
    """
    矩阵采样算法。
    
    基于列采样和概率权重分配。
    
    参数:
        A: numpy.ndarray - 关联矩阵
        num_samples: int - 采样数量
    
    返回:
        Tuple[numpy.ndarray, float] - (着色向量, 差异)
    """
    m, n = A.shape
    
    # 计算列范数
    col_norms = np.linalg.norm(A, axis=0)
    
    # 采样概率与列范数成正比
    probabilities = col_norms / np.sum(col_norms)
    
    # 多次采样
    best_x = None
    best_disc = float('inf')
    
    for _ in range(num_samples):
        # 按概率选择若干列
        selected = np.where(np.random.random(len(probabilities)) < probabilities * 3)[0]
        
        # 初始化
        x = np.zeros(n)
        
        for idx in selected:
            # 使用贪心策略赋值
            val_plus = 0
            val_minus = 0
            
            for j in range(m):
                if A[j, idx] != 0:
                    sum_other = sum(x[k] * A[j, k] for k in range(n) if k != idx)
                    val_plus += abs(sum_other + A[j, idx])
                    val_minus += abs(sum_other - A[j, idx])
            
            x[idx] = 1 if val_plus <= val_minus else -1
        
        # 随机赋值未选中列
        for idx in range(n):
            if idx not in selected:
                x[idx] = 1 if random.random() < 0.5 else -1
        
        disc = np.max(np.abs(A @ x))
        
        if disc < best_disc:
            best_x = x.copy()
            best_disc = disc
    
    return best_x, best_disc


def incremental_coloring(A, batch_size=5):
    """
    增量着色算法。
    
    每次处理一小批元素，使用 SDP 进行优化。
    
    参数:
        A: numpy.ndarray - 关联矩阵
        batch_size: int - 每批处理元素数量
    
    返回:
        Tuple[numpy.ndarray, float] - (着色向量, 差异)
    """
    m, n = A.shape
    
    x = np.zeros(n)
    processed = set()
    
    while len(processed) < n:
        # 选择下一批元素
        remaining = [i for i in range(n) if i not in processed]
        batch = remaining[:batch_size]
        
        # 对当前批次应用 SDP
        A_batch = A[:, batch]
        x_batch = sdp_relaxation_coloring(A_batch)
        
        for idx, val in zip(batch, x_batch):
            x[idx] = val
            processed.add(idx)
    
    disc = np.max(np.abs(A @ x))
    
    return x, disc


def verify_algorithmic_discrepancy(x, A, bound):
    """
    验证算法差异性质。
    
    参数:
        x: numpy.ndarray - 着色向量
        A: numpy.ndarray - 关联矩阵
        bound: float - 上界
    
    返回:
        Tuple[bool, float] - (是否满足, 实际差异)
    """
    disc = np.max(np.abs(A @ x))
    return disc <= bound, disc


def generate_incidence_matrix(n, m, density=0.2):
    """
    生成随机关联矩阵。
    
    参数:
        n: int - 行数（集合数）
        m: int - 列数（元素数）
        density: float - 1的比例
    
    返回:
        numpy.ndarray - 稀疏关联矩阵
    """
    A = np.zeros((n, m))
    for i in range(n):
        for j in range(m):
            if random.random() < density:
                A[i, j] = 1
    return A


def compare_algorithmic_methods(n=50, m=30):
    """
    比较各种算法实现的效果。
    
    参数:
        n: int - 元素数量
        m: int - 集合数量
    
    返回:
        Dict[str, float] - 各方法性能比较
    """
    A = generate_incidence_matrix(m, n, density=0.3)
    bound = 2 * math.sqrt(n * math.log(m + 1))
    
    results = {}
    
    # Partial Coloring Lemma
    x_pcl, disc_pcl = partial_coloring_lemma(A, bound)
    results['partial_coloring_lemma'] = disc_pcl
    
    # Greedy
    x_greedy, disc_greedy = greedy_partial_coloring(A)
    results['greedy'] = disc_greedy
    
    # Metropolis
    x_metro, disc_metro = metropolis_partial_coloring(A, iterations=500)
    results['metropolis'] = disc_metro
    
    # Matrix Sampling
    x_ms, disc_ms = matrix_sampling_algorithm(A, num_samples=50)
    results['matrix_sampling'] = disc_ms
    
    # SDP Relaxation
    x_sdp = sdp_relaxation_coloring(A)
    disc_sdp = np.max(np.abs(A @ x_sdp))
    results['sdp_relaxation'] = disc_sdp
    
    results['theoretical_bound'] = bound
    
    return results


if __name__ == "__main__":
    print("=" * 70)
    print("算法差异部分着色测试 - Algorithmic Partial Coloring")
    print("=" * 70)
    
    # 基本测试
    print("\n1. 基本功能测试")
    n = 40  # 元素数
    m = 25  # 集合数
    A = generate_incidence_matrix(m, n, density=0.25)
    
    print(f"矩阵形状: {A.shape}")
    print(f"非零元素比例: {np.count_nonzero(A) / (n * m):.2%}")
    print(f"理论目标界: {2 * math.sqrt(n * math.log(m + 1)):.4f}")
    
    # 各算法测试
    print("\n2. 各算法性能比较")
    comparison = compare_algorithmic_methods(n, m)
    
    for method, disc in comparison.items():
        if method != 'theoretical_bound':
            bound = comparison['theoretical_bound']
            ratio = disc / bound if bound > 0 else 0
            status = "✓" if disc <= bound else "✗"
            print(f"  {method}: {disc:.4f} ({ratio:.2f}x 界) {status}")
    
    print(f"\n  理论界: {comparison['theoretical_bound']:.4f}")
    
    # Partial Coloring Lemma 详细测试
    print("\n3. Partial Coloring Lemma 详细测试")
    x_pcl, disc_pcl = partial_coloring_lemma(A)
    satisfies, actual = verify_algorithmic_discrepancy(x_pcl, A, 2 * math.sqrt(n * math.log(m + 1)))
    print(f"差异值: {actual:.4f}")
    print(f"满足界: {satisfies}")
    print(f"非零分量: {np.count_nonzero(x_pcl)}/{n}")
    
    # Metropolis 算法测试
    print("\n4. Metropolis 算法测试")
    for temp in [0.5, 1.0, 2.0]:
        x_m, disc_m = metropolis_partial_coloring(A, temperature=temp, iterations=300)
        print(f"  温度={temp}: 差异={disc_m:.4f}")
    
    # 拉斯维加斯算法测试
    print("\n5. 拉斯维加斯算法测试")
    x_lv, disc_lv, success = las_vegas_coloring(A, time_limit=2.0)
    print(f"成功找到解: {success}")
    print(f"差异: {disc_lv:.4f}")
    
    # 矩阵采样算法测试
    print("\n6. 矩阵采样算法测试")
    x_ms, disc_ms = matrix_sampling_algorithm(A, num_samples=100)
    print(f"差异: {disc_ms:.4f}")
    
    # 不同规模测试
    print("\n7. 不同规模测试")
    test_cases = [
        (30, 20),
        (50, 30),
        (80, 50),
        (120, 80),
    ]
    
    print(f"{'n':>4} {'m':>4} {'贪心':>8} {'Metropolis':>10} {'采样':>8} {'界':>8}")
    print("-" * 60)
    
    for n_t, m_t in test_cases:
        A_t = generate_incidence_matrix(m_t, n_t, density=0.25)
        bound_t = 2 * math.sqrt(n_t * math.log(m_t + 1))
        
        x_g, d_g = greedy_partial_coloring(A_t)
        x_m, d_m = metropolis_partial_coloring(A_t, iterations=200)
        x_s, d_s = matrix_sampling_algorithm(A_t, num_samples=50)
        
        print(f"{n_t:4d} {m_t:4d} {d_g:8.2f} {d_m:10.2f} {d_s:8.2f} {bound_t:8.2f}")
    
    # 增量着色测试
    print("\n8. 增量着色算法测试")
    for batch in [3, 5, 10]:
        x_inc, disc_inc = incremental_coloring(A, batch_size=batch)
        print(f"  批次大小={batch}: 差异={disc_inc:.4f}")
    
    # 收敛性分析
    print("\n9. Metropolis 收敛性分析")
    temperatures = [0.1, 0.5, 1.0, 2.0, 5.0]
    
    for temp in temperatures:
        all_discs = []
        for _ in range(10):
            x_m, disc_m = metropolis_partial_coloring(A, temperature=temp, iterations=100)
            all_discs.append(disc_m)
        
        avg = sum(all_discs) / len(all_discs)
        var = sum((d - avg) ** 2 for d in all_discs) / len(all_discs)
        print(f"  温度={temp}: 平均差异={avg:.4f}, 方差={var:.4f}")
    
    print("\n" + "=" * 70)
    print("复杂度分析:")
    print("  - partial_coloring_lemma: O(n^2 * m)")
    print("  - greedy_partial_coloring: O(n^2 * m)")
    print("  - metropolis_partial_coloring: O(iterations * n * m)")
    print("  - matrix_sampling_algorithm: O(num_samples * n^2 * m)")
    print("  - sdp_relaxation_coloring: O(n^3) [特征分解]")
    print("  - incremental_coloring: O(num_batches * n^3)")
    print("  - 总体空间复杂度: O(n * m)")
    print("=" * 70)
