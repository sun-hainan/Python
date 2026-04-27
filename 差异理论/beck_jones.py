# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / beck_jones

本文件实现 beck_jones 相关的算法功能。
"""

import math
import random
from typing import List, Tuple, Dict


def initialize_coloring(n):
    """
    初始化 n 个元素的着色方案。
    
    参数:
        n: int - 元素的数量
    
    返回:
        List[int] - 初始着色向量，每个元素为 +1 或 -1
    """
    coloring = []
    for i in range(n):
        val = 1 if random.random() < 0.5 else -1  # 每个元素随机赋值为 +1 或 -1
        coloring.append(val)
    return coloring


def compute_discrepancy(coloring, sets):
    """
    计算给定着色方案下，所有集合的差异值。
    
    参数:
        coloring: List[int] - 着色向量
        sets: List[List[int]] - 集合族，每个集合是元素索引的列表
    
    返回:
        float - 最大差异值（所有集合加权和绝对值的最大值）
    """
    max_discrepancy = 0.0
    for s in sets:
        # 计算该集合的加权和
        weighted_sum = sum(coloring[i] for i in s)
        discrepancy = abs(weighted_sum)
        max_discrepancy = max(max_discrepancy, discrepancy)
    return max_discrepancy


def beck_jones_bound(n, m, min_set_size):
    """
    计算 Beck-Jones 定理给出的差异上界。
    
    参数:
        n: int - 元素总数
        m: int - 集合数量
        min_set_size: int - 每个集合的最小大小
    
    返回:
        float - 差异的理论上界
    """
    # Beck-Jones 定理的基本上界: O(sqrt(n * log(m/n)))
    # 当集合较大时，差异可以控制在较小范围内
    if min_set_size == 0:
        return float('inf')
    bound = 2.0 * math.sqrt(n * math.log(max(m, 1)) / min_set_size)
    return bound


def partial_coloring_iteration(coloring, sets, alpha=0.5):
    """
    部分着色迭代算法，用于改进当前着色方案。
    
    参数:
        coloring: List[int] - 当前着色向量
        sets: List[List[int]] - 集合族
        alpha: float - 步长参数，控制每次迭代的调整幅度
    
    返回:
        List[int] - 更新后的着色向量
    """
    n = len(coloring)
    new_coloring = coloring.copy()
    
    # 计算每个元素对各集合的边际贡献
    marginal_contributions = []
    for i in range(n):
        contribution = 0.0
        for s in sets:
            if i in s:
                # 计算元素 i 在集合 s 中的边际影响
                sum_other = sum(coloring[j] for j in s if j != i)
                contribution += sum_other
        marginal_contributions.append(contribution)
    
    # 找出边际贡献最大的元素，优先调整
    max_idx = 0
    max_val = marginal_contributions[0]
    for i in range(1, n):
        if marginal_contributions[i] > max_val:
            max_val = marginal_contributions[i]
            max_idx = i
    
    # 对边际贡献最大的元素进行翻转
    if max_val > 0:
        new_coloring[max_idx] = -new_coloring[max_idx]
    
    return new_coloring


def iterative_improvement(coloring, sets, max_iterations=1000, tolerance=1e-6):
    """
    迭代改进算法，逐步优化着色方案以降低差异。
    
    参数:
        coloring: List[int] - 初始着色向量
        sets: List[List[int]] - 集合族
        max_iterations: int - 最大迭代次数
        tolerance: float - 收敛容忍度
    
    返回:
        Tuple[List[int], float] - (最优着色方案, 最终差异值)
    """
    current_coloring = coloring.copy()
    current_discrepancy = compute_discrepancy(current_coloring, sets)
    
    for iteration in range(max_iterations):
        improved_coloring = partial_coloring_iteration(current_coloring, sets)
        improved_discrepancy = compute_discrepancy(improved_coloring, sets)
        
        # 如果改进幅度小于容忍度，提前停止
        if abs(current_discrepancy - improved_discrepancy) < tolerance:
            break
        
        current_coloring = improved_coloring
        current_discrepancy = improved_discrepancy
    
    return current_coloring, current_discrepancy


def beck_jones_algorithm(n, sets, delta=0.5):
    """
    Beck-Jones 定理的核心算法实现。
    
    该算法基于概率方法和条件期望构造一个具有较小差异的着色方案。
    
    参数:
        n: int - 元素总数
        sets: List[List[int]] - 集合族
        delta: float - 精度参数，控制差异上界
    
    返回:
        Tuple[List[int], float] - (着色方案, 差异值)
    """
    # 初始化随机着色
    coloring = initialize_coloring(n)
    
    # 迭代改进
    final_coloring, final_discrepancy = iterative_improvement(coloring, sets)
    
    return final_coloring, final_discrepancy


def verify_beck_jones_property(coloring, sets, bound):
    """
    验证着色方案是否满足 Beck-Jones 性质。
    
    参数:
        coloring: List[int] - 着色向量
        sets: List[List[int]] - 集合族
        bound: float - 理论上界
    
    返回:
        bool - 是否满足性质
    """
    for s in sets:
        weighted_sum = sum(coloring[i] for i in s)
        if abs(weighted_sum) > bound:
            return False
    return True


def generate_random_sets(n, m, avg_size=5):
    """
    生成随机的集合族，用于测试算法。
    
    参数:
        n: int - 元素总数
        m: int - 集合数量
        avg_size: float - 平均集合大小
    
    返回:
        List[List[int]] - 随机生成的集合族
    """
    sets = []
    for _ in range(m):
        # 使用泊松分布确定集合大小
        size = max(1, int(random.gauss(avg_size, avg_size / 2)))
        size = min(size, n)
        # 随机选择 size 个元素
        elements = random.sample(range(n), size)
        sets.append(sorted(elements))
    return sets


def analyze_set_system(n, sets):
    """
    分析 set system 的性质，计算相关统计量。
    
    参数:
        n: int - 元素总数
        sets: List[List[int]] - 集合族
    
    返回:
        Dict - 包含统计信息的字典
    """
    set_sizes = [len(s) for s in sets]
    min_size = min(set_sizes) if set_sizes else 0
    max_size = max(set_sizes) if set_sizes else 0
    avg_size = sum(set_sizes) / len(set_sizes) if set_sizes else 0
    
    # 计算元素出现频率
    frequency = [0] * n
    for s in sets:
        for i in s:
            frequency[i] += 1
    
    analysis = {
        'num_sets': len(sets),
        'min_set_size': min_size,
        'max_set_size': max_size,
        'avg_set_size': avg_size,
        'element_frequencies': frequency,
        'max_frequency': max(frequency) if frequency else 0,
        'min_frequency': min(frequency) if frequency else 0
    }
    return analysis


def compare_random_vs_beck_jones(n=50, m=20, num_trials=10):
    """
    比较随机着色与 Beck-Jones 算法的性能差异。
    
    参数:
        n: int - 元素数量
        m: int - 集合数量
        num_trials: int - 试验次数
    
    返回:
        Dict - 比较结果统计
    """
    random_discrepancies = []
    beck_jones_discrepancies = []
    
    for trial in range(num_trials):
        # 生成随机集合
        random.seed(trial * 42)
        sets = generate_random_sets(n, m, avg_size=n // 4)
        
        # 随机着色
        random_coloring = initialize_coloring(n)
        random_disc = compute_discrepancy(random_coloring, sets)
        random_discrepancies.append(random_disc)
        
        # Beck-Jones 算法
        bj_coloring, bj_disc = beck_jones_algorithm(n, sets)
        beck_jones_discrepancies.append(bj_disc)
    
    results = {
        'avg_random_discrepancy': sum(random_discrepancies) / len(random_discrepancies),
        'avg_beck_jones_discrepancy': sum(beck_jones_discrepancies) / len(beck_jones_discrepancies),
        'improvement_ratio': sum(random_discrepancies) / max(sum(beck_jones_discrepancies), 0.001)
    }
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("Beck-Jones 定理实现测试")
    print("=" * 60)
    
    # 测试基本功能
    print("\n1. 基本功能测试")
    n = 20  # 元素数量
    m = 10  # 集合数量
    sets = generate_random_sets(n, m, avg_size=5)
    
    print(f"元素数量 n = {n}")
    print(f"集合数量 m = {m}")
    
    # 分析集合系统
    analysis = analyze_set_system(n, sets)
    print(f"集合大小范围: [{analysis['min_set_size']}, {analysis['max_set_size']}]")
    print(f"平均集合大小: {analysis['avg_set_size']:.2f}")
    print(f"元素最大出现频率: {analysis['max_frequency']}")
    
    # 计算理论界
    bound = beck_jones_bound(n, m, analysis['min_set_size'])
    print(f"\nBeck-Jones 上界: {bound:.4f}")
    
    # 测试随机着色
    random_coloring = initialize_coloring(n)
    random_disc = compute_discrepancy(random_coloring, sets)
    print(f"随机着色差异: {random_disc}")
    
    # 测试 Beck-Jones 算法
    bj_coloring, bj_disc = beck_jones_algorithm(n, sets)
    print(f"Beck-Jones 算法差异: {bj_disc}")
    
    # 验证性质
    satisfies = verify_beck_jones_property(bj_coloring, sets, bound * 2)
    print(f"是否满足扩展 Beck-Jones 性质: {satisfies}")
    
    # 性能比较
    print("\n2. 性能比较测试")
    comparison = compare_random_vs_beck_jones(n=30, m=15, num_trials=5)
    print(f"随机着色平均差异: {comparison['avg_random_discrepancy']:.4f}")
    print(f"Beck-Jones 平均差异: {comparison['avg_beck_jones_discrepancy']:.4f}")
    print(f"改进比: {comparison['improvement_ratio']:.2f}x")
    
    # 不同参数规模测试
    print("\n3. 不同规模测试")
    test_cases = [
        (10, 5, 3),
        (50, 25, 5),
        (100, 50, 10),
    ]
    
    for n_t, m_t, avg_t in test_cases:
        sets_t = generate_random_sets(n_t, m_t, avg_size=avg_t)
        analysis_t = analyze_set_system(n_t, sets_t)
        bound_t = beck_jones_bound(n_t, m_t, analysis_t['min_set_size'])
        bj_coloring_t, bj_disc_t = beck_jones_algorithm(n_t, sets_t)
        
        print(f"n={n_t}, m={m_t}: 理论界={bound_t:.2f}, 实际差异={bj_disc_t}, "
              f"比值={bj_disc_t/max(bound_t, 0.001):.2f}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print("\n复杂度分析:")
    print("  - initialize_coloring: O(n)")
    print("  - compute_discrepancy: O(n * m * avg_size)")
    print("  - iterative_improvement: O(max_iterations * n * m * avg_size)")
    print("  - beck_jones_algorithm: O(n * m * avg_size * max_iterations)")
    print("  - 总体空间复杂度: O(n + m * avg_size)")
