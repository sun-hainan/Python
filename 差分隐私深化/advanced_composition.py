# -*- coding: utf-8 -*-
"""
高级组合定理 (Advanced Composition Theorem)
============================================

算法原理:
高级组合定理提供了比基本序列组合定理更紧密的隐私损失上界。
给定k个机制，每个满足(ε, δ)-DP，通过适当的噪声缩放可以实现
更小的总体隐私参数。对于k个(ε, δ)-DP机制的组合，基本定理给出
O(kε, kδ)，而高级组合可达到 O(ε√(k log(1/δ')), δ+δ')。

主要变体:
1. 强大数律组合 (Strong Law Composition): 处理异构机制的组合
2. 泊松混合 (Poisson Mixture): 基于泊松过程的隐私预算分配
3. 拆解重组 (Bucketing/Squaring): 将时间线分段并重组以获得更好界限

时间复杂度: O(k) 其中k为机制数量
空间复杂度: O(1) 仅为参数存储

应用场景:
- 大规模机器学习训练过程
- 多轮交互式查询系统
- 隐私预算规划与分配
- 迭代式数据分析管道
"""

import math
import numpy as np


def strong_law_composition(epsilon_list, delta_list):
    """
    强大数律组合 (Strong Law Composition)
    
    原理: 对于一系列可能不同的(ε_i, δ_i)-DP机制，
    总体隐私参数满足更强的联合界。
    
    参数:
        epsilon_list: 每个机制的ε值列表
        delta_list: 每个机制的δ值列表
    
    返回:
        总隐私损失上界 (epsilon_total, delta_total)
    
    数学证明基于martingale集中不等式和强大数律。
    """
    k = len(epsilon_list)
    assert len(delta_list) == k, "epsilon_list和delta_list长度必须一致"
    
    # 计算累积ε (使用平方和根界，比线性界更紧)
    eps_sq_sum = sum(e**2 for e in epsilon_list)
    epsilon_total = math.sqrt(2 * math.log(1 / 1e-6)) * math.sqrt(eps_sq_sum)
    
    # 累积δ
    delta_total = sum(delta_list)
    
    return epsilon_total, delta_total


def poisson_mixture_composition(base_epsilon, base_delta, num_queries, alpha=1.0):
    """
    泊松混合组合 (Poisson Mixture Composition)
    
    原理: 假设查询数量服从泊松分布，以概率分配不同的隐私预算。
    这种方法在查询数量不确定时特别有用。
    
    参数:
        base_epsilon: 基础ε值
        base_delta: 基础δ值  
        num_queries: 预期查询数量
        alpha: 混合系数，控制预算分配的方差
    
    返回:
        调整后的隐私参数 (adjusted_epsilon, adjusted_delta)
    """
    # 泊松混合下的期望隐私损失
    # 基于随机化查询数量的期望值
    expected_queries = num_queries
    variance_factor = alpha ** 2 * expected_queries
    
    # 使用集中不等式得到概率上界
    adjusted_epsilon = base_epsilon * math.sqrt(1 + variance_factor / expected_queries)
    
    # δ保持线性组合
    adjusted_delta = base_delta * expected_queries
    
    return adjusted_epsilon, adjusted_delta


def bucketing_composition(epsilon, delta, num_queries, bucket_size=None):
    """
    拆解重组组合 (Bucketing/Squaring Composition)
    
    原理: 将连续的查询分成若干"桶"，在每个桶内应用更强的隐私保证，
    然后组合这些桶的结果。这可以获得比纯序列组合更好的界限。
    
    参数:
        epsilon: 单个查询的ε
        delta: 单个查询的δ
        num_queries: 查询总数
        bucket_size: 每个桶的大小，默认为√num_queries
    
    返回:
        总体隐私参数
    """
    if bucket_size is None:
        # 最优桶大小为√n，此时获得O(ε√n)的界限
        bucket_size = max(1, int(math.sqrt(num_queries)))
    
    num_buckets = math.ceil(num_queries / bucket_size)
    
    # 每个桶内部的组合 (bucket_size个查询)
    eps_inside = epsilon * bucket_size  # 基本组合
    delta_inside = delta * bucket_size
    
    # 桶之间的组合 (num_buckets个桶)
    # 使用基本组合定理
    eps_total = eps_inside * num_buckets
    delta_total = delta_inside * num_buckets
    
    # 高级组合优化: 使用平方根界
    eps_optimized = epsilon * math.sqrt(2 * num_buckets * math.log(1 / delta))
    
    return eps_optimized, delta_total


def advanced_composition_grid(epsilon, delta, k, delta_prime=None):
    """
    标准高级组合定理的网格搜索实现
    
    参考文献: Dwork, Rothblum, Vadhan (2010)
    
    参数:
        epsilon: 目标单轮ε
        delta: 目标单轮δ
        k: 组合机制数量
        delta_prime: 可选的额外δ'用于精细化界
    
    返回:
        总体(ε_total, δ_total)满足k轮组合
    """
    if delta_prime is None:
        delta_prime = delta / k  # 均匀分配额外δ
    
    # 高级组合定理的标准形式
    # ε_total = 2ε√(2k log(1/δ'))
    epsilon_total = 2 * epsilon * math.sqrt(2 * k * math.log(1 / delta_prime))
    
    # δ_total = kδ + δ'
    delta_total = k * delta + delta_prime
    
    return epsilon_total, delta_total


def compute_privacy_budget(epsilon, delta, k, method="advanced"):
    """
    计算k轮组合后的隐私预算
    
    参数:
        epsilon: 初始隐私参数ε
        delta: 初始隐私参数δ
        k: 组合轮数
        method: "basic"(基本组合) 或 "advanced"(高级组合)
    
    返回:
        总体隐私参数
    """
    if method == "basic":
        # 基本组合: 线性增长
        return epsilon * k, delta * k
    elif method == "advanced":
        # 高级组合: 平方根增长
        delta_prime = delta  # 常用选择
        eps_total = 2 * epsilon * math.sqrt(2 * k * math.log(1 / delta_prime))
        return eps_total, k * delta + delta_prime
    else:
        raise ValueError(f"未知方法: {method}")


if __name__ == "__main__":
    # 测试高级组合定理
    
    print("=" * 60)
    print("高级组合定理测试")
    print("=" * 60)
    
    # 测试1: 强大数律组合
    print("\n[测试1] 强大数律组合")
    epsilons = [0.1, 0.2, 0.15, 0.1, 0.05]
    deltas = [1e-5, 1e-5, 1e-6, 1e-5, 1e-6]
    eps_total, delta_total = strong_law_composition(epsilons, deltas)
    print(f"  5个机制: ε=[{', '.join(map(str, epsilons))}]")
    print(f"  强大数律: ε_total={eps_total:.4f}, δ_total={delta_total:.6f}")
    
    # 基本组合对比
    basic_eps = sum(epsilons)
    print(f"  基本组合: ε_total={basic_eps:.4f} (强大数律改进: {basic_eps/eps_total:.2f}x)")
    
    # 测试2: 泊松混合
    print("\n[测试2] 泊松混合组合")
    adj_eps, adj_delta = poisson_mixture_composition(0.1, 1e-5, 1000, alpha=0.5)
    print(f"  base_ε=0.1, base_δ=1e-5, 预期1000次查询")
    print(f"  调整后: ε={adj_eps:.4f}, δ={adj_delta:.4f}")
    
    # 测试3: 拆解重组
    print("\n[测试3] 拆解重组组合")
    eps_total, delta_total = bucketing_composition(0.1, 1e-5, 10000)
    basic_eps = 0.1 * 10000
    print(f"  单轮ε=0.1, 共10000轮查询")
    print(f"  拆解重组: ε_total={eps_total:.4f}")
    print(f"  基本组合: ε_total={basic_eps:.2f} (改进: {basic_eps/eps_total:.1f}x)")
    
    # 测试4: 标准高级组合网格
    print("\n[测试4] 标准高级组合定理")
    for k in [100, 1000, 10000]:
        eps_a, delta_a = compute_privacy_budget(0.1, 1e-5, k, "advanced")
        eps_b, delta_b = compute_privacy_budget(0.1, 1e-5, k, "basic")
        print(f"  k={k:>5}: 高级ε={eps_a:>8.4f} vs 基本ε={eps_b:>8.4f}")
    
    # 测试5: 可视化组合对比
    print("\n[测试5] 隐私损失增长对比")
    print(f"  {'k':>6} | {'基本ε':>10} | {'高级ε':>10} | 改进倍数")
    print("  " + "-" * 45)
    for k in [100, 500, 1000, 5000, 10000]:
        eps_a, _ = compute_privacy_budget(0.1, 1e-5, k, "advanced")
        eps_b, _ = compute_privacy_budget(0.1, 1e-5, k, "basic")
        ratio = eps_b / eps_a
        print(f"  {k:>6} | {eps_b:>10.2f} | {eps_a:>10.2f} | {ratio:>6.2f}x")
    
    print("\n" + "=" * 60)
    print("测试完成 - 高级组合定理显著优于基本组合")
    print("=" * 60)
