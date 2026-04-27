# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / discrepancy_bounding

本文件实现 discrepancy_bounding 相关的算法功能。
"""

import math
import random
from typing import List, Tuple, Dict
import numpy as np


def simple_random_bound(n, m, avg_size):
    """
    简单随机着色界。
    
    设每个元素独立以概率 1/2 着为 ±1，
    则对于任意固定集合 S，|S| 服从二项分布。
    
    P(|S| > t) ≤ exp(-2t^2/|S|)
    
    参数:
        n: int - 元素数量
        m: int - 集合数量
        avg_size: float - 平均集合大小
    
    返回:
        float - 高概率下的差异界
    """
    # Chernoff 界: 差异以高概率不超过 O(sqrt(n log m))
    t = math.sqrt(2 * avg_size * math.log(m))
    return t


def chernoff_bound(n, delta=0.5):
    """
    Chernoff-Hoeffding 界。
    
    参数:
        n: int - 独立随机变量的数量
        delta: float - 偏离均值的比例
    
    返回:
        float - 尾部概率上界
    """
    # P(X > (1 + delta) * μ) ≤ exp(-δ^2 * μ / 3)
    mu = n / 2
    if delta > 0:
        return math.exp(-delta * delta * mu / 3)
    return 1.0


def kolmogorov_bound(n, confidence=0.99):
    """
    柯尔莫戈洛夫（正态近似）界。
    
    中心极限定理表明，标准化的二项分布趋近于正态分布。
    
    参数:
        n: int - 试验次数
        confidence: float - 置信水平
    
    返回:
        float - 差异上界
    """
    # 正态分布的分位数
    from scipy.special import erfinv
    z = math.sqrt(2) * erfinv(2 * confidence - 1)
    
    # 差异界: z * sqrt(n) / 2
    bound = z * math.sqrt(n) / 2
    return bound


def spencer_six_deviations(n, sets):
    """
    Spencer 的六标准差定理实现。
    
    定理：在任意 n 元素和 n 个集合的 set system 中，
    存在着色使得每个集合的差异不超过 6√n。
    
    这是"六标准差定理"的核心形式。
    
    参数:
        n: int - 元素数量
        sets: List[List[int]] - 集合族
    
    返回:
        Tuple[float, float] - (理论界, 实际界)
    """
    # Spencer 定理界
    theoretical_bound = 6 * math.sqrt(n)
    
    # 实际可达到的界（可能更紧）
    # 使用核心引理（Six Standard Deviations lemma）
    actual_bound = six_standard_deviations_lemma(sets)
    
    return theoretical_bound, actual_bound


def six_standard_deviations_lemma(sets):
    """
    六标准差引理（Core Lemma）的实现。
    
    该引理证明：对于平衡的 set system，
    存在着色使得差异不超过 6√n。
    
    参数:
        sets: List[List[int]] - 集合族
    
    返回:
        float - 差异上界
    """
    n_elements = set()
    for s in sets:
        n_elements.update(s)
    
    n = len(n_elements)
    
    if n == 0:
        return 0.0
    
    # 平衡因子：每个元素出现在相近数量的集合中
    # 在最优情况下，差异界可以改进为 O(sqrt(n log(n/m)))
    if len(sets) > 0:
        avg_size = sum(len(s) for s in sets) / len(sets)
        bound = min(6 * math.sqrt(n), 2 * math.sqrt(n * math.log(len(sets) / avg_size)))
    else:
        bound = 0.0
    
    return bound


def beck_fiala_bound(n, sets):
    """
    Beck-Fiala 定理实现。
    
    定理：如果每个元素最多出现在 t 个集合中，
    则差异上界为 2t - 1。
    
    参数:
        n: int - 元素数量
        sets: List[List[int]] - 集合族
    
    返回:
        Tuple[float, int] - (上界, 最大频率)
    """
    # 计算每个元素的出现频率
    frequency = {}
    for s in sets:
        for element in s:
            frequency[element] = frequency.get(element, 0) + 1
    
    max_frequency = max(frequency.values()) if frequency else 0
    t = max_frequency
    
    # Beck-Fiala 界
    if t == 0:
        bound = 0.0
    elif t == 1:
        bound = 1.0
    else:
        bound = 2 * t - 1
    
    return bound, t


def partial_coloring_bound(n, m):
    """
    部分着色方法的差异界。
    
    参数:
        n: int - 元素数量
        m: int - 集合数量
    
    返回:
        float - 基于部分着色的上界
    """
    # 当 m ≤ n 时，界为 O(sqrt(n))
    # 当 m > n 时，界为 O(sqrt(n log(m/n)))
    if m <= n:
        return math.sqrt(n)
    else:
        return math.sqrt(n * math.log(m / n))


def discrepancy_upper_bound(n, sets, method="auto"):
    """
    综合多种方法的统一上界接口。
    
    参数:
        n: int - 元素数量
        sets: List[List[int]] - 集合族
        method: str - 选择的方法
    
    返回:
        float - 综合上界
    """
    m = len(sets)
    
    if method == "auto":
        # 根据参数自动选择最优界
        if m <= n:
            bound1 = math.sqrt(n)
        else:
            bound1 = math.sqrt(n * math.log(m / n))
        
        bound2, t = beck_fiala_bound(n, sets)
        bound3 = six_standard_deviations_lemma(sets)
        
        return min(bound1, bound2, bound3)
    
    elif method == "chernoff":
        avg_size = sum(len(s) for s in sets) / m if m > 0 else 0
        return simple_random_bound(n, m, avg_size)
    
    elif method == "spencer":
        theoretical, _ = spencer_six_deviations(n, sets)
        return theoretical
    
    elif method == "beck-fiala":
        bound, _ = beck_fiala_bound(n, sets)
        return bound
    
    elif method == "partial":
        return partial_coloring_bound(n, m)
    
    else:
        return math.sqrt(n)


def tariff_method(n, sets, max_iterations=100):
    """
    关税法（Tariff Method）着色算法。
    
    这是一种构造性方法，通过迭代调整权重
    来达到目标差异界。
    
    参数:
        n: int - 元素数量
        sets: List[List[int]] - 集合族
        max_iterations: int - 最大迭代次数
    
    返回:
        Tuple[List[int], float] - (着色方案, 最终差异)
    """
    # 初始化
    weights = [0.0] * n
    coloring = [0] * n
    
    for iteration in range(max_iterations):
        # 目标差异
        target = 2.0 * math.sqrt(n * math.log(len(sets)))
        
        # 调整每个元素
        for i in range(n):
            sum_positive = 0
            sum_negative = 0
            
            for s_idx, s in enumerate(sets):
                if i in s:
                    other_sum = sum(weights[j] for j in s if j != i)
                    sum_positive += abs(other_sum + 1)
                    sum_negative += abs(other_sum - 1)
            
            # 选择使集合加权和更平衡的值
            if sum_positive <= sum_negative:
                weights[i] = 1.0
            else:
                weights[i] = -1.0
        
        # 检查是否达到目标
        max_discrepancy = 0
        for s in sets:
            disc = abs(sum(weights[i] for i in s))
            max_discrepancy = max(max_discrepancy, disc)
        
        if max_discrepancy <= target:
            break
    
    # 将权重转换为着色
    coloring = [1 if w > 0 else -1 for w in weights]
    
    return coloring, max_discrepancy


def iterative_weighting(n, sets, target_bound=None):
    """
    迭代权重调整算法。
    
    参数:
        n: int - 元素数量
        sets: List[List[int]] - 集合族
        target_bound: float - 目标差异界
    
    返回:
        List[int] - 最终着色
    """
    if target_bound is None:
        target_bound = 6 * math.sqrt(n)
    
    # 初始化着色
    coloring = [0] * n
    active = set(range(n))
    
    iteration = 0
    while active and iteration < n:
        # 选择最需要着色的元素
        best_element = None
        best_score = -float('inf')
        
        for e in active:
            # 计算该元素对各集合的影响
            score = 0
            for s in sets:
                if e in s:
                    sum_other = sum(coloring[i] for i in s if i != e)
                    score += sum_other ** 2
            if score > best_score:
                best_score = score
                best_element = e
        
        # 贪心选择最佳值
        if best_element is not None:
            val_plus = 0
            val_minus = 0
            
            for s in sets:
                if best_element in s:
                    sum_other = sum(coloring[i] for i in s if i != best_element)
                    val_plus += abs(sum_other + 1)
                    val_minus += abs(sum_other - 1)
            
            coloring[best_element] = 1 if val_plus <= val_minus else -1
            active.remove(best_element)
        
        iteration += 1
    
    # 对于未着色的元素，随机赋值
    for i in range(n):
        if coloring[i] == 0:
            coloring[i] = 1 if random.random() < 0.5 else -1
    
    return coloring


def harmonic_coin_flipping(n, sets, num_players=3):
    """
    谐波抛硬币游戏算法。
    
    参数:
        n: int - 元素数量
        sets: List[List[int]] - 集合族
        num_players: int - 玩家数量
    
    返回:
        List[int] - 着色结果
    """
    # 简化的多玩家抛硬币过程
    coloring = [0] * n
    
    # 每个玩家依次决定部分元素的着色
    elements_per_player = n // num_players
    remaining = list(range(n))
    
    for player in range(num_players):
        # 玩家选择要处理的元素
        if remaining:
            player_elements = remaining[:elements_per_player]
            
            for e in player_elements:
                # 计算该元素的期望贡献
                contribution = 0
                for s in sets:
                    if e in s:
                        sum_other = sum(coloring[i] for i in s if i != e)
                        contribution += sum_other
                
                # 基于期望贡献决定着色
                if contribution >= 0:
                    coloring[e] = 1
                else:
                    coloring[e] = -1
            
            # 从剩余列表中移除已处理的元素
            remaining = remaining[elements_per_player:]
    
    # 处理剩余元素
    for e in remaining:
        coloring[e] = 1 if random.random() < 0.5 else -1
    
    return coloring


def verify_discrepancy_bound(coloring, sets, bound):
    """
    验证着色方案是否满足指定的差异界。
    
    参数:
        coloring: List[int] - 着色向量
        sets: List[List[int]] - 集合族
        bound: float - 上界
    
    返回:
        Tuple[bool, float] - (是否满足, 最大差异)
    """
    max_disc = 0.0
    for s in sets:
        disc = abs(sum(coloring[i] for i in s))
        max_disc = max(max_disc, disc)
    
    return max_disc <= bound, max_disc


def generate_balanced_set_system(n, m, max_freq=3):
    """
    生成平衡的 set system，其中每个元素出现次数不超过 max_freq。
    
    参数:
        n: int - 元素数量
        m: int - 集合数量
        max_freq: int - 元素最大出现频率
    
    返回:
        List[List[int]] - 平衡的集合族
    """
    # 每个元素的当前使用次数
    usage_count = [0] * n
    sets = []
    
    for _ in range(m):
        # 优先选择使用较少的元素
        available = [i for i in range(n) if usage_count[i] < max_freq]
        
        if len(available) < 3:
            available = list(range(n))
        
        # 随机选择集合大小
        size = random.randint(3, min(8, len(available)))
        selected = random.sample(available, size)
        
        for e in selected:
            usage_count[e] += 1
        
        sets.append(selected)
    
    return sets


if __name__ == "__main__":
    print("=" * 70)
    print("差异上界技术测试 - Discrepancy Bounding Techniques")
    print("=" * 70)
    
    # 测试不同上界
    print("\n1. 理论界比较测试")
    n = 100
    m = 100
    sets = generate_balanced_set_system(n, m, max_freq=5)
    
    print(f"元素数量: {n}")
    print(f"集合数量: {m}")
    
    bounds = {
        '简单随机界': simple_random_bound(n, m, sum(len(s) for s in sets) / m),
        'Spencer六标准差': spencer_six_deviations(n, sets)[0],
        'Beck-Fiala界': beck_fiala_bound(n, sets)[0],
        '部分着色界': partial_coloring_bound(n, m),
        '综合界': discrepancy_upper_bound(n, sets, method="auto")
    }
    
    for name, bound_val in bounds.items():
        print(f"  {name}: {bound_val:.4f}")
    
    # 实际算法测试
    print("\n2. 构造算法测试")
    
    # 关税法
    tariff_coloring, tariff_disc = tariff_method(n, sets)
    print(f"关税法差异: {tariff_disc:.4f}")
    
    # 迭代权重法
    iter_coloring = iterative_weighting(n, sets)
    iter_disc = max(abs(sum(iter_coloring[i] for i in s)) for s in sets)
    print(f"迭代权重法差异: {iter_disc:.4f}")
    
    # 谐波抛硬币
    harmonic_coloring = harmonic_coin_flipping(n, sets)
    harmonic_disc = max(abs(sum(harmonic_coloring[i] for i in s)) for s in sets)
    print(f"谐波抛硬币差异: {harmonic_disc:.4f}")
    
    # 不同规模测试
    print("\n3. 不同规模测试")
    test_cases = [
        (20, 20),
        (50, 50),
        (100, 100),
        (200, 200),
    ]
    
    for n_t, m_t in test_cases:
        sets_t = generate_balanced_set_system(n_t, m_t, max_freq=5)
        
        # 各界计算
        spencer_b, actual_spencer = spencer_six_deviations(n_t, sets_t)
        beck_b, t = beck_fiala_bound(n_t, sets_t)
        auto_b = discrepancy_upper_bound(n_t, sets_t, method="auto")
        
        # 实际算法
        tariff_c, tariff_d = tariff_method(n_t, sets_t)
        iter_c = iterative_weighting(n_t, sets_t)
        iter_d = max(abs(sum(iter_c[i] for i in s)) for s in sets_t)
        
        print(f"\n  n={n_t:3d}, m={m_t:3d}, t={t:2d}:")
        print(f"    Spencer界: {spencer_b:7.2f}, Beck-Fiala: {beck_b:7.2f}, 自动: {auto_b:7.2f}")
        print(f"    关税法: {tariff_d:7.2f}, 迭代权重: {iter_d:7.2f}")
    
    # Chernoff 界分析
    print("\n4. Chernoff 界分析")
    for n_t in [50, 100, 200, 500]:
        for delta in [0.1, 0.5, 1.0]:
            prob = chernoff_bound(n_t, delta)
            print(f"  n={n_t:3d}, δ={delta:.1f}: P > (1+δ)μ ≤ {prob:.6f}")
    
    # Beck-Fiala 特定测试
    print("\n5. Beck-Fiala 定理详细测试")
    for trial in range(5):
        n_t = 50
        m_t = 30
        sets_t = generate_balanced_set_system(n_t, m_t, max_freq=4)
        
        bound, t = beck_fiala_bound(n_t, sets_t)
        
        # 验证着色
        coloring = iterative_weighting(n_t, sets_t, target_bound=bound)
        satisfies, actual_disc = verify_discrepancy_bound(coloring, sets_t, bound)
        
        print(f"  测试 {trial + 1}: t={t:2d}, 界={bound:5.2f}, "
              f"实际差异={actual_disc:5.2f}, 满足={satisfies}")
    
    print("\n" + "=" * 70)
    print("复杂度分析:")
    print("  - simple_random_bound: O(1)")
    print("  - beck_fiala_bound: O(n + m * avg_size)")
    print("  - spencer_six_deviations: O(n * m * avg_size)")
    print("  - tariff_method: O(n * m * avg_size * iterations)")
    print("  - iterative_weighting: O(n^2 * m * avg_size)")
    print("  - harmonic_coin_flipping: O(n * m * avg_size)")
    print("  - 总体空间复杂度: O(n + m * avg_size)")
    print("=" * 70)
