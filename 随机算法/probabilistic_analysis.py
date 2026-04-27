# -*- coding: utf-8 -*-
"""
算法实现：随机算法 / probabilistic_analysis

本文件实现 probabilistic_analysis 相关的算法功能。
"""

import random
from typing import List


def hire_assistant(n: int, k: int) -> bool:
    """
    雇佣问题模拟

    参数：
        n: 候选人总数
        k: 观察期长度

    返回：是否选到了最好的
    """
    candidates = list(range(n))
    random.shuffle(candidates)

    # 观察前k个
    best_of_k = max(candidates[:k]) if k > 0 else -1

    # 从k+1开始，遇到比前面都好的就录用
    for i in range(k, n):
        if candidates[i] > best_of_k:
            # 录用
            return candidates[i] == n - 1  # n-1是最好的

    # 没遇到更好的，录用最后一个
    return candidates[-1] == n - 1


def probability_best_candidate(n: int, k: int, trials: int = 10000) -> float:
    """
    估计选到最优候选人的概率

    参数：
        n: 候选人总数
        k: 观察期长度
        trials: 试验次数
    """
    successes = 0
    for _ in range(trials):
        if hire_assistant(n, k):
            successes += 1
    return successes / trials


def hire_assistant_analysis():
    """
    理论分析

    选到最优候选人的概率 ≈ k/n * (1 + 1/2 + 1/3 + ... + 1/(n-k))

    最优k ≈ n/e
    """
    print("雇佣问题理论分析")
    print("=" * 50)

    n = 100

    print(f"\nn = {n} 候选人")
    print(f"最优观察期 k ≈ n/e ≈ {n/2.718:.0f}")
    print()

    for k in [10, 20, 30, 37, 50]:
        prob = probability_best_candidate(n, k, trials=5000)
        print(f"k = {k:2d}: 选到最优的概率 ≈ {prob:.3f} ({prob*100:.1f}%)")

    print()

    # 期望成本分析
    print("期望面试人数分析:")
    print("-" * 50)

    def expected_interviews(n: int, k: int) -> float:
        """期望面试人数"""
        return k + (n - k) * (k + 1) / (k + 1)

    for k in [10, 37, 50]:
        expected = k + (n - k) * (1.0 / (k + 1))
        print(f"k = {k:2d}: 期望面试 {expected:.1f} 人")


def coupon_collector_analysis():
    """
    Coupon Collector（集齐卡片问题）

    随机拿卡片，集齐所有n种需要多少次？
    """
    print("\n\n集齐卡片问题分析")
    print("=" * 50)

    n = 10  # n种卡片

    def simulate(n: int, trials: int = 1000) -> float:
        """模拟"""
        total_steps = []
        for _ in range(trials):
            collected = set()
            steps = 0
            while len(collected) < n:
                card = random.randint(0, n - 1)
                collected.add(card)
                steps += 1
            total_steps.append(steps)

        return sum(total_steps) / trials

    mean = simulate(n)
    theoretical = n * (1 + 1/2 + 1/3 + ... + 1/n)  # 近似

    print(f"n = {n} 种卡片")
    print(f"模拟均值: {mean:.1f}")
    print(f"理论均值 ≈ n * H_n = {n * sum(1/i for i in range(1, n+1)):.1f}")


def average_case_quicksort():
    """
    快排的平均情况分析

    使用概率分析证明平均时间复杂度
    """
    print("\n\n快速排序平均情况分析")
    print("=" * 50)

    print("假设：所有排列等概率")
    print()

    def analyze_depth(arr: List) -> int:
        """分析递归深度"""
        if len(arr) <= 1:
            return 0

        pivot = arr[0]
        left = [x for x in arr[1:] if x < pivot]
        right = [x for x in arr[1:] if x >= pivot]

        return 1 + max(analyze_depth(left), analyze_depth(right))

    trials = 100
    total_depth = 0

    for _ in range(trials):
        arr = list(range(100))
        random.shuffle(arr)
        depth = analyze_depth(arr)
        total_depth += depth

    avg_depth = total_depth / trials
    print(f"n=100, {trials}次随机排列的平均递归深度: {avg_depth:.1f}")
    print(f"理论值: ~2 ln n ≈ {2 * 2.718 * 100:.1f}")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 概率分析：雇佣问题 ===\n")

    random.seed(42)

    hire_assistant_analysis()
    coupon_collector_analysis()
    average_case_quicksort()

    print("\n说明：")
    print("  - 概率分析是设计随机算法的基础")
    print("  - 期望 vs 最坏情况分析")
    print("  - 随机算法通常有很好的期望性能")
