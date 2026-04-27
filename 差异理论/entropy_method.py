# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / entropy_method

本文件实现 entropy_method 相关的算法功能。
"""

import math
import random
from typing import List, Tuple, Dict, Set
from collections import defaultdict
import numpy as np


def binary_entropy(p):
    """
    计算二进制熵函数 H(p) = -p*log(p) - (1-p)*log(1-p)。
    
    参数:
        p: float - 概率值，0 < p < 1
    
    返回:
        float - 熵值（以 2 为底）
    """
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def joint_entropy(prob_matrix):
    """
    计算联合熵 H(X_1, X_2, ..., X_n)。
    
    参数:
        prob_matrix: numpy.ndarray - 概率分布矩阵
    
    返回:
        float - 联合熵值
    """
    entropy = 0.0
    for row in prob_matrix:
        for p in row:
            if p > 0:
                entropy -= p * math.log2(p)
    return entropy


def conditional_entropy(prob_joint, prob_marginal):
    """
    计算条件熵 H(X|Y) = H(X,Y) - H(Y)。
    
    参数:
        prob_joint: numpy.ndarray - 联合分布
        prob_marginal: numpy.ndarray - 边缘分布
    
    返回:
        float - 条件熵值
    """
    h_xy = joint_entropy(prob_joint)
    h_y = joint_entropy(prob_marginal)
    return max(0.0, h_xy - h_y)


def expected_discrepancy(n, m, set_list):
    """
    计算随机着色下差异的期望值。
    
    设每个元素独立以概率 1/2 着为 +1 或 -1，
    计算每个集合加权和的期望平方。
    
    参数:
        n: int - 元素数量
        m: int - 集合数量
        set_list: List[Set[int]] - 集合列表
    
    返回:
        float - 期望最大差异的估计
    """
    expected_squared_sum = 0.0
    
    for s in set_list:
        size = len(s)
        # 每个集合加权和的平方期望等于集合大小
        expected_squared_sum += size
    
    # 期望最大差异约为 sqrt(2 * sum_i E[S_i^2] * log(m))
    expected_max = math.sqrt(2 * expected_squared_sum * math.log(m))
    
    return expected_max


def entropy_bound_for_discrepancy(n, m, set_list):
    """
    利用熵方法推导差异上界。
    
    定理（基于Baber-Lovasz-Matousek）：
    对于任意 n 元素和 m 个集合的 set system，
    存在着色使得每个集合的加权和满足 |S_i| ≤ C√n。
    
    参数:
        n: int - 元素数量
        m: int - 集合数量
        set_list: List[Set[int]] - 集合列表
    
    返回:
        float - 熵方法给出的上界
    """
    # 计算总权重
    total_weight = sum(len(s) for s in set_list)
    
    # 每个元素的平均出现次数
    avg_frequency = total_weight / n if n > 0 else 0
    
    # 熵方法界: O(sqrt(n * log(m/n)))
    if m <= n:
        bound = math.sqrt(2 * n * math.log(2 * n / m)) if m > 0 else math.sqrt(2 * n)
    else:
        bound = math.sqrt(2 * n * math.log(2 * m))
    
    return bound


def lovasz_local_lemma_condition(prob, num_bad_events):
    """
    Lovasz Local Lemma 的条件检查。
    
    如果存在 p 使得 e * p * (2d + 1) ≤ 1，
    则存在避免所有坏事件的着色方案。
    
    参数:
        prob: float - 单个坏事件发生的概率
        num_bad_events: int - 与单个事件相关的坏事件数量
    
    返回:
        bool - 是否满足 LLL 条件
    """
    threshold = 1.0 / (math.e * (2 * num_bad_events + 1))
    return prob <= threshold


def entropy_optimized_coloring(n, sets, target_discrepancy=None):
    """
    基于熵优化的着色算法。
    
    参数:
        n: int - 元素数量
        sets: List[List[int]] - 集合族
        target_discrepancy: float - 目标差异值
    
    返回:
        Tuple[List[int], float] - (着色方案, 实际差异)
    """
    if target_discrepancy is None:
        target_discrepancy = 2 * math.sqrt(n * math.log(len(sets)))
    
    # 初始化
    coloring = [0] * n
    remaining = list(range(n))
    
    while remaining:
        # 选择边际熵最大的元素
        best_element = None
        best_entropy_gain = -float('inf')
        
        for e in remaining:
            # 计算翻转该元素的熵增益
            current_contributions = []
            for s in sets:
                if e in s:
                    sum_other = sum(coloring[i] for i in s if i != e)
                    current_contributions.append((sum_other, len(s)))
            
            # 熵增益估计
            entropy_gain = sum(
                abs(current_contributions[i][0] + 1) - abs(current_contributions[i][0] - 1)
                for i in range(len(current_contributions))
            )
            
            if entropy_gain > best_entropy_gain:
                best_entropy_gain = entropy_gain
                best_element = e
        
        # 确定该元素的最佳值
        value_plus = 0
        value_minus = 0
        
        for s in sets:
            if best_element in s:
                sum_other = sum(coloring[i] for i in s if i != best_element)
                value_plus += sum_other + 1
                value_minus += sum_other - 1
        
        # 选择使差异更小的值
        coloring[best_element] = 1 if abs(value_plus) < abs(value_minus) else -1
        remaining.remove(best_element)
    
    # 计算最终差异
    max_discrepancy = 0
    for s in sets:
        disc = abs(sum(coloring[i] for i in s))
        max_discrepancy = max(max_discrepancy, disc)
    
    return coloring, max_discrepancy


def randomized_entropy_algorithm(n, sets, num_samples=1000):
    """
    基于随机采样的熵优化算法。
    
    参数:
        n: int - 元素数量
        sets: List[List[int]] - 集合族
        num_samples: int - 采样数量
    
    返回:
        Tuple[List[int], float] - (最优着色, 最小差异)
    """
    best_coloring = None
    best_discrepancy = float('inf')
    
    for _ in range(num_samples):
        # 生成随机着色
        coloring = [1 if random.random() < 0.5 else -1 for _ in range(n)]
        
        # 计算差异
        max_disc = 0
        for s in sets:
            disc = abs(sum(coloring[i] for i in s))
            max_disc = max(max_disc, disc)
        
        if max_disc < best_discrepancy:
            best_discrepancy = max_disc
            best_coloring = coloring
    
    return best_coloring, best_discrepancy


def mollified_entropy_bound(sets, n):
    """
    计算平滑熵界（Mollified Entropy Bound）。
    
    参数:
        sets: List[Set[int]] - 集合族
        n: int - 元素数量
    
    返回:
        float - 平滑后的上界
    """
    set_sizes = [len(s) for s in sets]
    max_size = max(set_sizes) if set_sizes else 0
    min_size = min(set_sizes) if set_sizes else 0
    
    # 基础界
    base_bound = math.sqrt(n * math.log(len(sets)))
    
    # 平滑因子
    if max_size > 0:
        smoothing_factor = math.sqrt(max_size / min_size) if min_size > 0 else 1.0
    else:
        smoothing_factor = 1.0
    
    return base_bound * smoothing_factor


def entropy_method_iteration(coloring, sets, temperature=1.0):
    """
    模拟退火风格的熵优化迭代。
    
    参数:
        coloring: List[int] - 当前着色
        sets: List[List[int]] - 集合族
        temperature: float - 温度参数
    
    返回:
        Tuple[List[int], float] - (改进的着色, 差异)
    """
    n = len(coloring)
    new_coloring = coloring.copy()
    
    # 随机选择要翻转的元素
    idx = random.randint(0, n - 1)
    current_value = coloring[idx]
    new_value = -current_value
    
    # 计算翻转前后的差异变化
    old_contribution = 0
    new_contribution = 0
    
    for s in sets:
        if idx in s:
            sum_other = sum(new_coloring[i] for i in s if i != idx)
            old_contribution += abs(sum_other + current_value)
            new_contribution += abs(sum_other + new_value)
    
    # Metropolis 准则
    delta = new_contribution - old_contribution
    if delta < 0 or random.random() < math.exp(-delta / temperature):
        new_coloring[idx] = new_value
    
    # 计算新差异
    max_disc = 0
    for s in sets:
        disc = abs(sum(new_coloring[i] for i in s))
        max_disc = max(max_disc, disc)
    
    return new_coloring, max_disc


def annealed_entropy_coloring(n, sets, cooling_rate=0.995, min_temp=0.01):
    """
    退火熵着色算法。
    
    参数:
        n: int - 元素数量
        sets: List[List[int]] - 集合族
        cooling_rate: float - 冷却率
        min_temp: float - 最低温度
    
    返回:
        List[int] - 最终着色
    """
    # 初始化随机着色
    coloring = [1 if random.random() < 0.5 else -1 for _ in range(n)]
    temperature = 10.0
    
    while temperature > min_temp:
        coloring, disc = entropy_method_iteration(coloring, sets, temperature)
        temperature *= cooling_rate
    
    return coloring


def compute_shannon_entropy(coloring, sets):
    """
    计算当前着色方案的信息熵。
    
    参数:
        coloring: List[int] - 着色向量
        sets: List[List[int]] - 集合族
    
    返回:
        float - 加权熵
    """
    total_entropy = 0.0
    
    for s in sets:
        # 计算集合中 +1 和 -1 的比例
        values = [coloring[i] for i in s]
        count_plus = values.count(1)
        count_minus = len(values) - count_plus
        
        if count_plus > 0 and count_minus > 0:
            p = count_plus / len(values)
            ent = binary_entropy(p)
            total_entropy += ent * len(s)
    
    return total_entropy


def baber_lovasz_bound(n, sets):
    """
    Baber-Lovasz-Matousek 熵界。
    
    参数:
        n: int - 元素数量
        sets: List[List[int]] - 集合族
    
    返回:
        float - 差异上界
    """
    m = len(sets)
    if m == 0:
        return 0.0
    
    # 计算权重分布
    weights = [len(s) for s in sets]
    avg_weight = sum(weights) / m
    
    # Baber-Lovasz 界
    bound = math.sqrt(2 * n * math.log(2 * m / avg_weight))
    
    return bound


def compare_entropy_bounds(n, sets):
    """
    比较不同熵界的松紧程度。
    
    参数:
        n: int - 元素数量
        sets: List[List[int]] - 集合族
    
    返回:
        Dict[str, float] - 各界值
    """
    set_list = [set(s) for s in sets]
    
    return {
        'expected': expected_discrepancy(n, len(sets), set_list),
        'entropy_bound': entropy_bound_for_discrepancy(n, len(sets), set_list),
        'mollified': mollified_entropy_bound(set_list, n),
        'baber_lovasz': baber_lovasz_bound(n, sets)
    }


if __name__ == "__main__":
    print("=" * 70)
    print("熵方法测试 - Entropy Method in Discrepancy")
    print("=" * 70)
    
    # 基本测试
    print("\n1. 基本熵函数测试")
    test_probs = [0.1, 0.25, 0.5, 0.75, 0.9]
    for p in test_probs:
        h = binary_entropy(p)
        print(f"  H({p}) = {h:.4f} bits")
    
    # 集合系统测试
    print("\n2. 集合系统测试")
    n = 50  # 元素数量
    m = 25  # 集合数量
    sets = [random.sample(range(n), random.randint(3, 10)) for _ in range(m)]
    
    print(f"元素数量: {n}")
    print(f"集合数量: {m}")
    
    # 比较不同界
    print("\n3. 差异界比较")
    bounds = compare_entropy_bounds(n, sets)
    for bound_name, bound_value in bounds.items():
        print(f"  {bound_name}: {bound_value:.4f}")
    
    # 随机采样算法
    print("\n4. 随机采样算法测试")
    best_coloring, best_disc = randomized_entropy_algorithm(n, sets, num_samples=500)
    print(f"最优差异（500次采样）: {best_disc}")
    
    # 退火算法
    print("\n5. 退火熵着色算法测试")
    annealed_coloring = annealed_entropy_coloring(n, sets, cooling_rate=0.99)
    max_disc_annealed = max(abs(sum(annealed_coloring[i] for i in s)) for s in sets)
    print(f"退火算法最终差异: {max_disc_annealed}")
    
    # 熵优化算法
    print("\n6. 熵优化着色算法测试")
    opt_coloring, opt_disc = entropy_optimized_coloring(n, sets)
    print(f"熵优化算法差异: {opt_disc}")
    
    # 信息熵分析
    print("\n7. 信息熵分析")
    shannon_ent = compute_shannon_entropy(opt_coloring, sets)
    print(f"最优着色加权熵: {shannon_ent:.4f}")
    
    # 不同规模测试
    print("\n8. 不同规模性能测试")
    test_sizes = [(20, 10), (50, 25), (100, 50), (200, 100)]
    
    for n_t, m_t in test_sizes:
        sets_t = [random.sample(range(n_t), random.randint(3, 10)) for _ in range(m_t)]
        
        # 熵界
        ent_bound = entropy_bound_for_discrepancy(n_t, m_t, [set(s) for s in sets_t])
        
        # 退火算法
        ann_coloring = annealed_entropy_coloring(n_t, sets_t, cooling_rate=0.99, min_temp=0.1)
        ann_disc = max(abs(sum(ann_coloring[i] for i in s)) for s in sets_t)
        
        # 熵优化
        opt_coloring_t, opt_disc_t = entropy_optimized_coloring(n_t, sets_t)
        
        print(f"n={n_t:3d}, m={m_t:3d}: 界={ent_bound:7.2f}, "
              f"退火={ann_disc:7.2f}, 优化={opt_disc_t:7.2f}")
    
    # LLL 条件检查
    print("\n9. Lovasz Local Lemma 条件检查")
    for trial in range(3):
        n_t = 30
        m_t = 15
        sets_t = [random.sample(range(n_t), random.randint(3, 8)) for _ in range(m_t)]
        
        # 估计单个坏事件概率（差异超过界的事件）
        p_bad = 0.1  # 简化估计
        degree = 10  # 每个事件与其他事件的依赖数
        
        satisfies_lll = lovasz_local_lemma_condition(p_bad, degree)
        print(f"  测试 {trial + 1}: LLL条件 = {satisfies_lll}")
    
    print("\n" + "=" * 70)
    print("复杂度分析:")
    print("  - binary_entropy: O(1)")
    print("  - entropy_bound_for_discrepancy: O(n + m)")
    print("  - lovasz_local_lemma_condition: O(1)")
    print("  - entropy_optimized_coloring: O(n^2 * m)")
    print("  - randomized_entropy_algorithm: O(num_samples * n * m * avg_size)")
    print("  - annealed_entropy_coloring: O( iterations * n * m)")
    print("  - 总体空间复杂度: O(n + m * avg_size)")
    print("=" * 70)
