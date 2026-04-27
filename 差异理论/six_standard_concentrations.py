# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / six_standard_concentrations

本文件实现 six_standard_concentrations 相关的算法功能。
"""

import math
import random
from typing import List, Tuple, Dict, Set
from collections import defaultdict
import numpy as np


def estimate_variance_of_sum(n, set_list):
    """
    估计随机着色下集合加权和的方差。
    
    对于独立均匀的 ±1 着色，
    每个集合 S 的加权和 X_S = Σ_{i∈S} X_i 的方差为 |S|。
    
    参数:
        n: int - 元素数量
        set_list: List[Set[int]] - 集合列表
    
    返回:
        float - 最大方差估计
    """
    max_variance = 0.0
    for s in set_list:
        # 独立 ±1 变量的方差为1
        variance = len(s)
        max_variance = max(max_variance, variance)
    return max_variance


def gauss_approximation_bound(n, confidence=0.95):
    """
    高斯近似的差异界。
    
    对于 n 个独立 ±1 变量的和，
    使用正态分布近似：
    P(|S| > t) ≈ 2 * (1 - Φ(t/√n))
    
    参数:
        n: int - 变量数量
        confidence: float - 置信水平
    
    返回:
        float - 对应的阈值 t
    """
    # 逆误差函数近似
    z = math.sqrt(2) * self_inverse_erf(2 * confidence - 1)
    return z * math.sqrt(n)


def self_inverse_erf(x):
    """
    误差函数的近似逆函数。
    
    参数:
        x: float - 输入值 (-1, 1)
    
    返回:
        float - 逆误差函数值
    """
    # 简化的近似公式
    return math.sqrt(math.pi) / 2 * x


def core_lemma_implementation(sets, delta=0.01):
    """
    核心引理（Core Lemma）的实现。
    
    核心引理：对于平衡的 set system，
    存在一个非零向量 x ∈ {-1,0,1}^n 使得
    ||A x||_∞ ≤ 6√n。
    
    参数:
        sets: List[List[int]] - 集合族
        delta: float - 控制参数
    
    返回:
        Tuple[numpy.ndarray, float] - (着色向量, 差异值)
    """
    n_elements = set()
    for s in sets:
        n_elements.update(s)
    
    n = len(n_elements)
    m = len(sets)
    
    if n == 0:
        return np.array([]), 0.0
    
    # 初始化
    x = np.zeros(n)
    remaining = set(range(n))
    
    # 迭代过程
    while remaining:
        # 计算每个剩余元素的边际贡献
        marginal_scores = []
        
        for i in remaining:
            score_plus = 0
            score_minus = 0
            
            for s_idx, s in enumerate(sets):
                if i in s:
                    sum_other = sum(x[j] for j in s if j in remaining and j != i)
                    score_plus += abs(sum_other + 1)
                    score_minus += abs(sum_other - 1)
            
            marginal_scores.append((i, score_plus, score_minus))
        
        # 选择边际贡献最大的元素
        best_i = None
        best_improvement = -float('inf')
        
        for i, sp, sm in marginal_scores:
            improvement = min(sp, sm)
            if improvement > best_improvement:
                best_improvement = improvement
                best_i = i
        
        if best_i is None:
            break
        
        # 计算最佳赋值
        val_plus = 0
        val_minus = 0
        
        for s in sets:
            if best_i in s:
                sum_other = sum(x[j] for j in s if j in remaining and j != best_i)
                val_plus += abs(sum_other + 1)
                val_minus += abs(sum_other - 1)
        
        # 选择使差异最小的值
        x[best_i] = 1 if val_plus <= val_minus else -1
        remaining.remove(best_i)
        
        # 提前停止条件：差异已达到目标
        current_max = max(
            abs(sum(x[j] for j in s if not remaining or j not in remaining))
            for s in sets
        )
        if current_max <= 6 * math.sqrt(n):
            break
    
    # 计算最终差异
    final_discrepancy = 0.0
    for s in sets:
        disc = abs(sum(x[j] for j in s))
        final_discrepancy = max(final_discrepancy, disc)
    
    return x, final_discrepancy


def six_deviation_random_walk(n_steps, target_bound):
    """
    六标准差随机游动算法。
    
    模拟一个随机过程，逐步构造具有小差异的着色方案。
    
    参数:
        n_steps: int - 游动步数
        target_bound: float - 目标差异界
    
    返回:
        Tuple[List[int], float] - (着色序列, 最终值)
    """
    path = []
    current = 0.0
    
    for step in range(n_steps):
        # 步长控制
        if step < n_steps / 2:
            step_size = 1.0
        else:
            step_size = 0.5
        
        # 以概率偏移选择方向
        bias = 0.1 * (1 - 2 * step / n_steps)
        direction = 1 if random.random() < 0.5 + bias else -1
        
        new_value = current + direction * step_size
        
        # 反弹机制
        if abs(new_value) > target_bound:
            new_value = 2 * target_bound * (direction > 0) - new_value
        
        path.append(new_value)
        current = new_value
    
    return path, current


def partial_coloring_recursion(n, sets, depth=0, max_depth=5):
    """
    递归部分着色算法。
    
    将问题分解为更小的子问题，递归应用核心引理。
    
    参数:
        n: int - 元素数量
        sets: List[List[int]] - 集合族
        depth: int - 当前递归深度
        max_depth: int - 最大递归深度
    
    返回:
        List[int] - 着色向量
    """
    if depth >= max_depth or n <= 1:
        # 基本情况：随机着色
        return [1 if random.random() < 0.5 else -1 for _ in range(n)]
    
    # 应用核心引理得到部分着色
    x, disc = core_lemma_implementation(sets)
    
    # 递归处理未着色部分
    uncolored = [i for i in range(n) if x[i] == 0]
    
    if uncolored:
        # 构造子问题
        sub_n = len(uncolored)
        sub_sets = []
        
        for s in sets:
            sub_s = [i for i in s if x[i] == 0]
            if sub_s:
                sub_sets.append(sub_s)
        
        # 递归求解
        sub_coloring = partial_coloring_recursion(sub_n, sub_sets, depth + 1, max_depth)
        
        # 合并结果
        for idx, i in enumerate(uncolored):
            x[i] = sub_coloring[idx]
    
    return x.tolist() if isinstance(x, np.ndarray) else x


def iterative_six_deviation(n, sets, num_iterations=50):
    """
    迭代六标准差优化算法。
    
    多次运行部分着色，选择最优结果。
    
    参数:
        n: int - 元素数量
        sets: List[List[int]] - 集合族
        num_iterations: int - 迭代次数
    
    返回:
        Tuple[List[int], float] - (最优着色, 最小差异)
    """
    best_coloring = None
    best_discrepancy = float('inf')
    
    for _ in range(num_iterations):
        # 随机化部分着色
        x = partial_coloring_recursion(n, sets, max_depth=3)
        
        # 计算差异
        max_disc = 0.0
        for s in sets:
            disc = abs(sum(x[i] for i in s))
            max_disc = max(max_disc, disc)
        
        if max_disc < best_discrepancy:
            best_discrepancy = max_disc
            best_coloring = x
    
    return best_coloring, best_discrepancy


def verify_six_deviation_bound(coloring, sets):
    """
    验证着色是否满足六标准差界。
    
    参数:
        coloring: List[int] - 着色向量
        sets: List[List[int]] - 集合族
    
    返回:
        Tuple[bool, float, float] - (是否满足, 实际差异, 理论界)
    """
    n = len(coloring)
    theoretical_bound = 6 * math.sqrt(n)
    
    max_disc = 0.0
    for s in sets:
        disc = abs(sum(coloring[i] for i in s))
        max_disc = max(max_disc, disc)
    
    return max_disc <= theoretical_bound, max_disc, theoretical_bound


def gauss_elimination_step(matrix, target_vector):
    """
    高斯消元步骤，用于线性代数方法。
    
    参数:
        matrix: numpy.ndarray - 系数矩阵
        target_vector: numpy.ndarray - 目标向量
    
    返回:
        numpy.ndarray - 解向量
    """
    n = matrix.shape[0]
    augmented = np.column_stack([matrix, target_vector])
    
    # 前向消元
    for i in range(n):
        # 找主元
        max_row = np.argmax(np.abs(augmented[i:, i])) + i
        augmented[[i, max_row]] = augmented[[max_row, i]]
        
        # 消元
        if abs(augmented[i, i]) > 1e-10:
            augmented[i + 1:] -= augmented[i + 1:, i:i + 1] * augmented[i + 1:, i] / augmented[i, i]
    
    # 回代
    x = np.zeros(n)
    for i in range(n - 1, -1, -1):
        if abs(augmented[i, i]) > 1e-10:
            x[i] = (augmented[i, -1] - np.dot(augmented[i, :-1], x)) / augmented[i, i]
    
    return x


def linear_algebraic_coloring(n, sets):
    """
    基于线性代数的着色方法。
    
    构造关联矩阵并求解线性方程组。
    
    参数:
        n: int - 元素数量
        sets: List[List[int]] - 集合族
    
    返回:
        List[int] - 着色向量
    """
    m = len(sets)
    
    # 构造关联矩阵
    A = np.zeros((m, n))
    for i, s in enumerate(sets):
        for j in s:
            A[i, j] = 1.0
    
    # 目标：使每行和接近零
    target = np.zeros(m)
    
    # 求解最小二乘问题
    try:
        # 简化为 A x ≈ target
        x = np.linalg.lstsq(A, target, rcond=None)[0]
    except:
        x = np.zeros(n)
    
    # 将实数值转换为 ±1
    coloring = [1 if x[i] >= 0 else -1 for i in range(n)]
    
    return coloring


def probabilistic_method_analysis(n, m):
    """
    概率方法分析框架。
    
    参数:
        n: int - 元素数量
        m: int - 集合数量
    
    返回:
        Dict[str, float] - 分析结果
    """
    # 随机着色下，单个集合偏离期望的概率
    # 使用 Chernoff 界
    expected = 0
    variance = 1  # 每个元素贡献的方差
    
    # 差异超过 t 的概率上界
    t_values = [2, 4, 6]
    probs = {}
    
    for t in t_values:
        # P(|X| > t) ≤ 2 exp(-t^2 / (2n))
        prob = 2 * math.exp(-t * t / (2 * n))
        probs[f't={t}'] = prob
    
    # 并集界：至少一个集合超过 t 的概率
    union_probs = {}
    for t, p in probs.items():
        union_prob = min(1.0, m * p)
        union_probs[t] = union_prob
    
    # 期望最大差异
    # E[max_i |X_i|] 的近似估计
    expected_max = math.sqrt(2 * n * math.log(m))
    
    return {
        'expected_max': expected_max,
        'individual_probs': probs,
        'union_probs': union_probs
    }


def generate_test_sets(n, m, constraint='unconstrained'):
    """
    生成测试用集合族。
    
    参数:
        n: int - 元素数量
        m: int - 集合数量
        constraint: str - 约束类型
    
    返回:
        List[List[int]] - 集合族
    """
    sets = []
    
    if constraint == 'balanced':
        # 平衡集合：每个元素出现相近次数
        frequency = [0] * n
        
        for _ in range(m):
            size = random.randint(3, min(8, n))
            available = list(range(n))
            
            # 优先选择使用较少的元素
            available.sort(key=lambda x: frequency[x])
            selected = available[:size]
            
            for e in selected:
                frequency[e] += 1
            
            sets.append(selected)
    
    else:
        # 无约束随机集合
        for _ in range(m):
            size = random.randint(3, min(10, n))
            sets.append(random.sample(range(n), size))
    
    return sets


def numerical_verification(n, num_trials=100):
    """
    数值验证六标准差定理。
    
    参数:
        n: int - 元素数量
        num_trials: int - 试验次数
    
    返回:
        Dict[str, float] - 验证结果
    """
    m = n  # 确保是方阵
    max_deviations = []
    bound = 6 * math.sqrt(n)
    
    for _ in range(num_trials):
        sets = generate_test_sets(n, m, constraint='balanced')
        
        # 迭代优化
        coloring, disc = iterative_six_deviation(n, sets, num_iterations=20)
        
        max_deviations.append(disc)
    
    # 统计结果
    avg_deviation = sum(max_deviations) / len(max_deviations)
    max_observed = max(max_deviations)
    ratio = max_observed / bound
    
    return {
        'theoretical_bound': bound,
        'average_observed': avg_deviation,
        'max_observed': max_observed,
        'max_ratio': ratio,
        'bound_satisfaction_rate': sum(1 for d in max_deviations if d <= bound) / num_trials
    }


if __name__ == "__main__":
    print("=" * 70)
    print("六标准差定理实现测试 - Six Standard Deviations Theorem")
    print("=" * 70)
    
    # 基本测试
    print("\n1. 核心引理测试")
    n = 50
    m = 50
    sets = generate_test_sets(n, m, constraint='balanced')
    
    print(f"元素数量: {n}, 集合数量: {m}")
    print(f"理论界 (6√n): {6 * math.sqrt(n):.4f}")
    
    # 核心引理
    x, disc = core_lemma_implementation(sets)
    print(f"核心引理差异: {disc:.4f}")
    print(f"非零分量比例: {np.count_nonzero(x) / n:.2%}")
    
    # 递归部分着色
    print("\n2. 递归部分着色测试")
    recursive_coloring = partial_coloring_recursion(n, sets, max_depth=3)
    recursive_disc = max(abs(sum(recursive_coloring[i] for i in s)) for s in sets)
    print(f"递归方法差异: {recursive_disc:.4f}")
    
    # 迭代优化
    print("\n3. 迭代优化测试")
    best_coloring, best_disc = iterative_six_deviation(n, sets, num_iterations=30)
    satisfies, actual, theoretical = verify_six_deviation_bound(best_coloring, sets)
    print(f"最优差异: {actual:.4f}")
    print(f"理论界: {theoretical:.4f}")
    print(f"满足六标准差界: {satisfies}")
    
    # 线性代数方法
    print("\n4. 线性代数方法测试")
    la_coloring = linear_algebraic_coloring(n, sets)
    la_disc = max(abs(sum(la_coloring[i] for i in s)) for s in sets)
    print(f"线性代数方法差异: {la_disc:.4f}")
    
    # 概率方法分析
    print("\n5. 概率方法分析")
    prob_analysis = probabilistic_method_analysis(n, m)
    print(f"期望最大差异: {prob_analysis['expected_max']:.4f}")
    for t, p in prob_analysis['individual_probs'].items():
        print(f"  P(|X| > {t[2:]}): {p:.6f}")
    for t, p in prob_analysis['union_probs'].items():
        print(f"  P(∃S: |S| > {t[2:]}): {p:.6f}")
    
    # 不同规模验证
    print("\n6. 不同规模数值验证")
    test_sizes = [20, 50, 100, 150]
    
    for n_t in test_sizes:
        m_t = n_t
        result = numerical_verification(n_t, num_trials=20)
        print(f"\n  n={n_t:3d}:")
        print(f"    理论界: {result['theoretical_bound']:.2f}")
        print(f"    平均差异: {result['average_observed']:.2f}")
        print(f"    最大观察: {result['max_observed']:.2f}")
        print(f"    满足率: {result['bound_satisfaction_rate']:.2%}")
    
    # 六标准差随机游动演示
    print("\n7. 六标准差随机游动演示")
    path, final = six_deviation_random_walk(100, target_bound=6 * math.sqrt(100))
    print(f"步数: 100, 最终值: {final:.4f}")
    print(f"路径范围: [{min(path):.2f}, {max(path):.2f}]")
    
    # 综合比较
    print("\n8. 方法比较")
    methods = ['核心引理', '递归部分着色', '迭代优化', '线性代数']
    discrepancies = [disc, recursive_disc, best_disc, la_disc]
    
    theoretical = 6 * math.sqrt(n)
    for method, disc_val in zip(methods, discrepancies):
        ratio = disc_val / theoretical
        status = "✓" if disc_val <= theoretical else "✗"
        print(f"  {method}: {disc_val:.4f} ({ratio:.2f} * 理论界) {status}")
    
    print("\n" + "=" * 70)
    print("复杂度分析:")
    print("  - core_lemma_implementation: O(n^2 * m)")
    print("  - partial_coloring_recursion: O(n * m * avg_size * 2^max_depth)")
    print("  - iterative_six_deviation: O(num_iterations * n^2 * m)")
    print("  - linear_algebraic_coloring: O(n^3) [SVD/最小二乘]")
    print("  - 总体空间复杂度: O(n * m)")
    print("=" * 70)
