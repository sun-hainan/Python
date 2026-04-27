# -*- coding: utf-8 -*-
"""
算法实现：在线算法 / online_binning

本文件实现 online_binning 相关的算法功能。
"""

import random
import math


class Bin:
    """箱子"""

    def __init__(self, capacity=1.0):
        self.capacity = capacity
        self.items = []         # [(size, item_id), ...]
        self.remaining = capacity

    def can_fit(self, size):
        return self.remaining >= size

    def add_item(self, item_id, size):
        """放入物品"""
        if not self.can_fit(size):
            return False
        self.items.append((item_id, size))
        self.remaining -= size
        return True

    def __repr__(self):
        return f"Bin(items={len(self.items)}, remaining={self.remaining:.3f})"


class NextFit:
    """
    Next-Fit 算法：当前箱满即开新箱
    优点：O(1) 时间，O(1) 空间
    缺点：A/OPT ≤ 2（差）
    """

    def __init__(self, capacity=1.0):
        self.capacity = capacity
        self.bins = [Bin(capacity)]
        self.total_items = 0

    def add_item(self, size):
        """放入物品"""
        self.total_items += 1
        current_bin = self.bins[-1]
        if current_bin.can_fit(size):
            current_bin.add_item(self.total_items, size)
        else:
            new_bin = Bin(self.capacity)
            new_bin.add_item(self.total_items, size)
            self.bins.append(new_bin)
        return len(self.bins)


class FirstFit:
    """
    First-Fit 算法：放入编号最小的、能容纳物品的箱子
    时间复杂度：O(n^2)，空间 O(n)
    A/OPT ≤ 1.7（任意序列）
    """

    def __init__(self, capacity=1.0):
        self.capacity = capacity
        self.bins = [Bin(capacity)]
        self.total_items = 0

    def add_item(self, size):
        """放入物品"""
        self.total_items += 1

        # 找到第一个能容纳的箱子
        for bin_idx, b in enumerate(self.bins):
            if b.can_fit(size):
                b.add_item(self.total_items, size)
                return bin_idx + 1

        # 没有能容纳的箱子，开新箱
        new_bin = Bin(self.capacity)
        new_bin.add_item(self.total_items, size)
        self.bins.append(new_bin)
        return len(self.bins)

    def get_bin_count(self):
        return len(self.bins)


class BestFit:
    """
    Best-Fit 算法：放入剩余空间最小（但能容纳物品）的箱子
    优点：更好地利用空间
    """

    def __init__(self, capacity=1.0):
        self.capacity = capacity
        self.bins = [Bin(capacity)]
        self.total_items = 0

    def add_item(self, size):
        self.total_items += 1

        # 找剩余空间最小但能容纳的箱子
        best_bin = None
        best_remaining = float('inf')

        for b in self.bins:
            if b.can_fit(size):
                if b.remaining < best_remaining:
                    best_remaining = b.remaining
                    best_bin = b

        if best_bin:
            best_bin.add_item(self.total_items, size)
        else:
            new_bin = Bin(self.capacity)
            new_bin.add_item(self.total_items, size)
            self.bins.append(new_bin)
            best_bin = new_bin

        return len(self.bins)


class HarmonicFit:
    """
    Harmonic-Fit 算法：按物品大小分类处理
    将物品按大小分为 k 类，每类使用专门的箱子
    A/OPT ≤ 1.5
    """

    def __init__(self, k=2, capacity=1.0):
        self.capacity = capacity
        self.k = k  # 分类数
        # 每个类别的物品大小范围
        self.categories = []  # [(lower, upper), ...]
        for i in range(1, k + 1):
            lower = 1.0 / (i + 1)
            upper = 1.0 / i
            self.categories.append((lower, upper))
        self.categories.append((0, 1.0 / (k + 1)))

        # 每个类别维护一组箱子
        self.category_bins = [[] for _ in range(k + 1)]
        self.total_items = 0

    def _get_category(self, size):
        """获取物品所属类别"""
        for i, (lower, upper) in enumerate(self.categories):
            if lower < size <= upper:
                return i
        return len(self.categories) - 1

    def add_item(self, size):
        self.total_items += 1
        cat_idx = self._get_category(size)

        if cat_idx == len(self.categories) - 1:
            # 小物品类：每个箱子最多放 k 个
            bin_size = self.k
            for b in self.category_bins[cat_idx]:
                if b.remaining >= size:
                    b.add_item(self.total_items, size)
                    return
            # 没有能容纳的箱子
            new_bin = Bin(self.capacity)
            new_bin._k_limit = self.k
            new_bin.add_item(self.total_items, size)
            self.category_bins[cat_idx].append(new_bin)
        else:
            # 大物品：每个物品独占一个箱子
            new_bin = Bin(self.capacity)
            new_bin.add_item(self.total_items, size)
            self.category_bins[cat_idx].append(new_bin)

        return

    def get_bin_count(self):
        return sum(len(bins) for bins in self.category_bins)


class FirstFitDecreasing:
    """
    First-Fit Decreasing（FFD）：离线算法，先降序排列再 FF
    A/OPT ≤ 11/9 ≈ 1.222（最好的近似保证）
    """

    def __init__(self, capacity=1.0):
        self.capacity = capacity
        self.bins = []

    def solve(self, items):
        """
        离线求解
        items: [(item_id, size), ...]
        返回: 使用的箱子数
        """
        # 降序排列
        sorted_items = sorted(items, key=lambda x: x[1], reverse=True)
        ff = FirstFit(self.capacity)
        for item_id, size in sorted_items:
            ff.add_item(size)
        return ff.get_bin_count()


def compute_lower_bound(items):
    """
    计算最优装箱的下界
    LB = max(total_size, max_item_size)
    """
    total_size = sum(size for _, size in items)
    max_item = max(size for _, size in items)
    return max(math.ceil(total_size), max_item)


if __name__ == '__main__':
    print("在线装箱（Online Bin Packing）算法演示")
    print("=" * 60)

    # 随机物品序列
    import random
    random.seed(42)

    n_items = 50
    sizes = [(i, random.uniform(0.05, 0.95)) for i in range(n_items)]
    total_size = sum(s for _, s in sizes)
    lb = compute_lower_bound(sizes)

    print(f"\n物品数量: {n_items}")
    print(f"总大小: {total_size:.2f} / 箱子容量 1.0")
    print(f"理论最优下界 LB = {lb} 箱")
    print(f"理论最优上界: ≥ {math.ceil(total_size)} 箱")

    # 各算法结果
    algorithms = [
        ('Next-Fit', NextFit()),
        ('First-Fit', FirstFit()),
        ('Best-Fit', BestFit()),
        ('Harmonic-Fit', HarmonicFit(k=3)),
    ]

    print(f"\n{'算法':<15} {'箱数':<10} {'浪费空间':<15} {'A/OPT 下界'}")
    print("  " + "-" * 60)

    for name, alg in algorithms:
        for item_id, size in sizes:
            alg.add_item(size)

        bin_count = alg.get_bin_count()
        wasted = bin_count - total_size
        approx_ratio = bin_count / lb
        print(f"  {name:<15} {bin_count:<10} {wasted:<15.2f} {approx_ratio:<10.2f}")

    # FFD（离线）
    ffd = FirstFitDecreasing()
    ffd_count = ffd.solve(sizes)
    print(f"  {'FFD (离线)':<15} {ffd_count:<10} {ffd_count - total_size:<15.2f} {ffd_count/lb:<10.2f}")

    print("\n" + "=" * 60)
    print("在线装箱算法竞争比分析：")
    print(f"  Next-Fit:   A/OPT ≤ 2.0（最差，最简单）")
    print(f"  First-Fit:  A/OPT ≤ 1.7（经典）")
    print(f"  Best-Fit:   A/OPT ≤ 1.7（与 FF 类似）")
    print(f"  Harmonic:   A/OPT ≤ 1.5（最优在线）")
    print(f"  FFD:        A/OPT ≤ 11/9 ≈ 1.222（离线最优）")
    print(f"\n  已知最优在线算法竞争比下界: 1.5（Harmonic 达到）")
    print(f"  即：没有任何确定性在线算法能保证 A/OPT < 1.5")
    print(f"\n实际意义：对于任意序列，最坏情况下需要多浪费 50% 的箱子空间")
