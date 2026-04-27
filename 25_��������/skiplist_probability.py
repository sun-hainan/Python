# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / skiplist_probability

本文件实现 skiplist_probability 相关的算法功能。
"""

import random
import math
from typing import List, Tuple
import matplotlib.pyplot as plt


class SkipListProbability:
    """
    跳表概率分析
    """
    
    def __init__(self, p: float = 0.5):
        """
        初始化
        
        Args:
            p: 每层晋升概率
        """
        self.p = p
    
    def level_distribution(self, n_elements: int) -> List[int]:
        """
        分析元素的层级分布
        
        Args:
            n_elements: 元素数量
        
        Returns:
            每层元素数量列表
        """
        levels = [0]  # 假设最大100层
        max_level = 100
        
        for _ in range(n_elements):
            # 计算元素的层级
            level = 0
            while random.random() < self.p and level < max_level:
                level += 1
            
            while len(levels) <= level:
                levels.append(0)
            
            levels[level] += 1
        
        return levels
    
    def expected_level(self) -> float:
        """
        计算单元素的期望层级
        
        Returns:
            期望层级
        """
        # 几何分布的期望: 1/(1-p) - 1 = p/(1-p)
        return self.p / (1 - self.p)
    
    def probability_of_level(self, level: int) -> float:
        """
        计算元素达到某层级的概率
        
        P(Level >= k) = p^k
        
        Args:
            level: 层级
        
        Returns:
            概率
        """
        return self.p ** level
    
    def expected_height(self, n_elements: int) -> float:
        """
        计算n个元素的期望高度
        
        近似: log_{1/p}(n)
        
        Args:
            n_elements: 元素数量
        
        Returns:
            期望高度
        """
        return math.log(n_elements, 1 / self.p)
    
    def space_complexity(self, n_elements: int) -> Tuple[float, float]:
        """
        计算空间复杂度
        
        Returns:
            (期望指针数, 每元素指针数)
        """
        # 每元素期望指针数 = E(level) + 1 = p/(1-p) + 1
        pointers_per_element = self.expected_level() + 1
        total_pointers = n_elements * pointers_per_element
        
        return total_pointers, pointers_per_element
    
    def search_complexity(self, n_elements: int) -> Tuple[float, float]:
        """
        搜索复杂度分析
        
        Returns:
            (期望比较次数, 高度)
        """
        height = self.expected_height(n_elements)
        
        # 每层平均比较次数约2-3
        comparisons_per_level = 2
        
        expected_comparisons = height * comparisons_per_level
        
        return expected_comparisons, height


def demo_level_distribution():
    """演示层级分布"""
    print("=== 跳表层级分布 ===\n")
    
    slp = SkipListProbability(p=0.5)
    
    print("理论分析 (p=0.5):")
    print(f"  单元素期望层级: {slp.expected_level():.2f}")
    
    for n in [100, 1000, 10000]:
        h = slp.expected_height(n)
        print(f"  {n:6d} 元素期望高度: {h:.1f}")
    
    print()
    
    # 模拟
    print("模拟统计 (10000元素):")
    
    trials = 10
    all_heights = []
    all_level_dists = []
    
    for _ in range(trials):
        dist = slp.level_distribution(10000)
        height = len(dist) - 1
        all_heights.append(height)
        all_level_dists.append(dist)
    
    avg_height = sum(all_heights) / trials
    max_height = max(all_heights)
    
    print(f"  平均高度: {avg_height:.1f}")
    print(f"  最大高度: {max_height}")
    
    # 平均层级分布
    avg_dist = [0] * max(len(d) for d in all_level_dists)
    for d in all_level_dists:
        for i, v in enumerate(d):
            avg_dist[i] += v / trials
    
    print("\n  平均层级分布:")
    for i in range(min(10, len(avg_dist))):
        count = avg_dist[i]
        pct = count / 10000 * 100
        bar = '█' * int(pct / 2)
        print(f"    Level {i}: {count:8.1f} ({pct:5.1f}%) {bar}")


def demo_probability_calculation():
    """演示概率计算"""
    print("\n=== 概率计算 ===\n")
    
    slp = SkipListProbability(p=0.5)
    
    print("达到各层级的概率 (p=0.5):")
    print("| Level | P(Level >= k) | P(Level = k) |")
    print("|-------|---------------|--------------|")
    
    cumulative = 0.0
    for k in range(8):
        p_ge = slp.probability_of_level(k)
        p_eq = p_ge * (1 - 0.5) if k > 0 else p_ge
        if k > 0:
            p_eq = p_ge * 0.5
        else:
            p_eq = 1 - 0.5
        
        print(f"| {k:6d} | {p_ge:12.6f} | {p_eq:11.6f} |")
    
    print()
    
    print("解释:")
    print("  - Level 0: 100% 元素")
    print("  - Level 1: 50% 元素")
    print("  - Level 2: 25% 元素")
    print("  - Level k: (0.5)^k 元素")


def demo_complexity_analysis():
    """演示复杂度分析"""
    print("\n=== 复杂度分析 ===\n")
    
    slp = SkipListProbability(p=0.5)
    
    print("搜索复杂度 (期望比较次数):")
    print("| 元素数 | 期望高度 | 期望比较 |")
    print("|--------|---------|----------|")
    
    for n in [100, 1000, 10000, 100000]:
        comps, height = slp.search_complexity(n)
        print(f"| {n:7,d} | {height:8.1f} | {comps:8.1f} |")
    
    print()
    
    print("空间复杂度 (p=0.5):")
    print("| 元素数 | 总指针 | 每元素 |")
    print("|--------|--------|--------|")
    
    for n in [100, 1000, 10000]:
        total, per_elem = slp.space_complexity(n)
        print(f"| {n:7,d} | {total:7.0f} | {per_elem:6.1f} |")


def demo_p_parameter_effect():
    """演示p参数影响"""
    print("\n=== P参数影响 ===\n")
    
    print("p (晋升概率) 对性能的影响:")
    print()
    
    print("| p     | E(Level) | 期望高度(10K) | 每元素指针 |")
    print("|-------|----------|---------------|------------|")
    
    for p in [0.25, 0.5, 0.75, 0.9]:
        slp = SkipListProbability(p=p)
        
        e_level = slp.expected_level()
        e_height = slp.expected_height(10000)
        _, per_elem = slp.space_complexity(100)
        
        print(f"| {p:.2f}   | {e_level:8.2f} | {e_height:13.1f} | {per_elem:10.2f} |")
    
    print()
    
    print("结论:")
    print("  - p 越小，空间效率越高")
    print("  - p 越大，高度越低，搜索越快")
    print("  - Redis使用 p=0.25 平衡两者")


def demo_height_tail():
    """演示高度尾部概率"""
    print("\n=== 高度尾部概率 ===\n")
    
    slp = SkipListProbability(p=0.5)
    
    print("n=10000 时高度超过k的概率:")
    print("| k   | P(Height > k) |")
    print("|-----|---------------|")
    
    for k in [10, 15, 20, 25, 30]:
        # P(Height > k) ≈ 1 - (1 - p^k)^n
        # 但更准确的是上界: n * p^k
        upper_bound = 10000 * (0.5 ** k)
        upper_bound = min(upper_bound, 1.0)
        print(f"| {k:3d} | {upper_bound:12.6f} |")
    
    print()
    
    print("分析:")
    print("  - 高度超过30的概率极低")
    print("  - 实际上高度通常在 O(log n)")


def plot_level_distribution():
    """绘制层级分布图"""
    print("\n=== 绘制层级分布图 ===\n")
    
    slp = SkipListProbability(p=0.5)
    
    n_elements = 10000
    trials = 5
    
    all_dists = []
    for _ in range(trials):
        dist = slp.level_distribution(n_elements)
        all_dists.append(dist)
    
    # 计算平均值
    max_len = max(len(d) for d in all_dists)
    avg_dist = [0.0] * max_len
    for d in all_dists:
        for i in range(len(d)):
            avg_dist[i] += d[i] / trials
    
    # 绘制
    plt.figure(figsize=(10, 6))
    
    levels = list(range(len(avg_dist)))
    counts = avg_dist
    
    plt.bar(levels, counts, alpha=0.7)
    plt.xlabel('Level')
    plt.ylabel('Number of Elements')
    plt.title('Skip List Level Distribution (n=10000, p=0.5)')
    plt.grid(True, alpha=0.3)
    
    plt.savefig('skiplist_levels.png', dpi=150)
    print("已保存到 skiplist_levels.png")
    plt.show()


def demo_theoretical_bounds():
    """演示理论界"""
    print("\n=== 理论界分析 ===\n")
    
    print("跳表高度的高概率界:")
    print()
    
    print("对于n个元素，跳表高度h满足:")
    print("  h > (1+ε)log_{1/p}(n) 的概率 < 1/n^ε")
    print()
    
    print("具体例子 (n=1000000, p=0.5):")
    n = 1000000
    
    h0 = math.log(n, 2)  # ≈ 20
    h_2 = 2 * h0  # ≈ 40
    
    p_h_gt_20 = n * (0.5 ** 20)
    p_h_gt_40 = n * (0.5 ** 40)
    
    print(f"  log_2(n) = {h0:.1f}")
    print(f"  P(h > {h0:.0f}) < {p_h_gt_20:.6f}")
    print(f"  P(h > {h_2:.0f}) < {p_h_gt_40:.10f}")
    
    print()
    
    print("Chernoff界分析:")
    print("  高度由独立几何分布决定")
    print("  可以用Chernoff界精确分析尾部概率")


if __name__ == "__main__":
    print("=" * 60)
    print("跳表层次概率分析")
    print("=" * 60)
    
    # 层级分布
    demo_level_distribution()
    
    # 概率计算
    demo_probability_calculation()
    
    # 复杂度分析
    demo_complexity_analysis()
    
    # p参数影响
    demo_p_parameter_effect()
    
    # 尾部概率
    demo_height_tail()
    
    # 理论界
    demo_theoretical_bounds()
    
    # 绘图
    plot_level_distribution()
    
    print("\n" + "=" * 60)
    print("核心结论:")
    print("=" * 60)
    print("""
1. 层级分布:
   - Level k 有 n * p^k * (1-p) 元素
   - 大部分元素在低层

2. 高度分析:
   - 期望高度: O(log n)
   - 尾部概率极小

3. 搜索复杂度:
   - 期望: O(log n)
   - 每层平均2-3次比较

4. 空间复杂度:
   - 每元素平均 1/(1-p) 个指针
   - p=0.25: 1.33 指针/元素
   - p=0.5: 2.00 指针/元素

5. Redis选择 p=0.25:
   - 平衡空间和搜索时间
   - 空间效率高
   - 高度仍为 O(log n)
""")
