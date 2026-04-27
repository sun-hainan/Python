# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / online_binning



本文件实现 online_binning 相关的算法功能。

"""



import random

import math

from typing import List, Tuple, Optional

from dataclasses import dataclass





@dataclass

class Bin:

    """箱子"""

    id: int

    capacity: float

    items: List[float]

    

    @property

    def remaining(self) -> float:

        """剩余容量"""

        return self.capacity - sum(self.items)

    

    @property

    def fullness(self) -> float:

        """满度"""

        return sum(self.items) / self.capacity

    

    def can_fit(self, item: float) -> bool:

        """是否能放入"""

        return self.remaining >= item

    

    def add_item(self, item: float) -> bool:

        """尝试添加物品"""

        if self.can_fit(item):

            self.items.append(item)

            return True

        return False





class NextFit:

    """

    Next Fit算法

    

    策略：

    - 只维护一个当前箱子

    - 当前箱子放不下则开新箱

    - 简单但效率较低

    """

    

    def __init__(self, bin_capacity: float = 1.0):

        self.bin_capacity = bin_capacity

        self.bins: List[Bin] = []

        self.current_bin: Optional[Bin] = None

        self.bin_count = 0

    

    def _new_bin(self) -> Bin:

        """创建新箱子"""

        self.bin_count += 1

        new_bin = Bin(self.bin_count, self.bin_capacity, [])

        self.bins.append(new_bin)

        return new_bin

    

    def _get_current_bin(self) -> Bin:

        """获取当前箱子"""

        if self.current_bin is None or not self.current_bin.can_fit(self.bin_capacity):

            self.current_bin = self._new_bin()

        return self.current_bin

    

    def pack(self, item: float) -> int:

        """

        放入物品

        

        Args:

            item: 物品大小

        

        Returns:

            使用的箱子数量

        """

        current = self._get_current_bin()

        

        if not current.can_fit(item):

            self.current_bin = self._new_bin()

            current = self.current_bin

        

        current.add_item(item)

        return len(self.bins)

    

    def reset(self):

        """重置"""

        self.bins = []

        self.current_bin = None

        self.bin_count = 0





class FirstFit:

    """

    First Fit算法

    

    策略：

    - 扫描所有箱子，找到第一个能容纳的

    - 比NF更优但需要查找

    """

    

    def __init__(self, bin_capacity: float = 1.0):

        self.bin_capacity = bin_capacity

        self.bins: List[Bin] = []

        self.bin_count = 0

    

    def _new_bin(self) -> Bin:

        """创建新箱子"""

        self.bin_count += 1

        new_bin = Bin(self.bin_count, self.bin_capacity, [])

        self.bins.append(new_bin)

        return new_bin

    

    def pack(self, item: float) -> int:

        """

        放入物品

        

        Returns:

            使用的箱子数量

        """

        # 找到第一个能容纳的箱子

        for bin in self.bins:

            if bin.can_fit(item):

                bin.add_item(item)

                return len(self.bins)

        

        # 没有能容纳的箱子，创建新的

        new_bin = self._new_bin()

        new_bin.add_item(item)

        return len(self.bins)





class BestFit:

    """

    Best Fit算法

    

    策略：

    - 放入最满但能容纳的箱子

    - 减少空间碎片

    """

    

    def __init__(self, bin_capacity: float = 1.0):

        self.bin_capacity = bin_capacity

        self.bins: List[Bin] = []

        self.bin_count = 0

    

    def _new_bin(self) -> Bin:

        """创建新箱子"""

        self.bin_count += 1

        new_bin = Bin(self.bin_count, self.bin_capacity, [])

        self.bins.append(new_bin)

        return new_bin

    

    def pack(self, item: float) -> int:

        """

        放入物品

        

        Returns:

            使用的箱子数量

        """

        best_bin = None

        best_remaining = float('inf')

        

        # 找到最满但能容纳的箱子

        for bin in self.bins:

            if bin.can_fit(item):

                remaining = bin.remaining

                if remaining < best_remaining:

                    best_remaining = remaining

                    best_bin = bin

        

        if best_bin is None:

            best_bin = self._new_bin()

        

        best_bin.add_item(item)

        return len(self.bins)





class WorstFit:

    """

    Worst Fit算法

    

    策略：

    - 放入最空的箱子

    - 避免小物品放入几乎满的箱子

    """

    

    def __init__(self, bin_capacity: float = 1.0):

        self.bin_capacity = bin_capacity

        self.bins: List[Bin] = []

        self.bin_count = 0

    

    def _new_bin(self) -> Bin:

        """创建新箱子"""

        self.bin_count += 1

        new_bin = Bin(self.bin_count, self.bin_capacity, [])

        self.bins.append(new_bin)

        return new_bin

    

    def pack(self, item: float) -> int:

        """

        放入物品

        

        Returns:

            使用的箱子数量

        """

        worst_bin = None

        max_remaining = -1

        

        # 找到最空的箱子

        for bin in self.bins:

            if bin.can_fit(item):

                remaining = bin.remaining

                if remaining > max_remaining:

                    max_remaining = remaining

                    worst_bin = bin

        

        if worst_bin is None:

            worst_bin = self._new_bin()

        

        worst_bin.add_item(item)

        return len(self.bins)





class RefinedFirstFit:

    """

    Refined First Fit (RFF) 算法

    

    策略：

    - 根据物品大小分类

    - 小物品用特定箱子

    - 大物品优先处理

    """

    

    def __init__(self, bin_capacity: float = 1.0):

        self.bin_capacity = bin_capacity

        self.bin_count = 0

        

        # 分类阈值

        self.small_threshold = 0.3

        self.medium_threshold = 0.6

        

        # 各类箱子

        self.small_bins: List[Bin] = []

        self.medium_bins: List[Bin] = []

        self.large_bins: List[Bin] = []

    

    def _classify(self, item: float) -> str:

        """分类物品"""

        ratio = item / self.bin_capacity

        if ratio <= self.small_threshold:

            return 'small'

        elif ratio <= self.medium_threshold:

            return 'medium'

        else:

            return 'large'

    

    def _new_bin(self) -> Bin:

        """创建新箱子"""

        self.bin_count += 1

        return Bin(self.bin_count, self.bin_capacity, [])

    

    def _pack_to_list(self, item: float, bins: List[Bin]) -> bool:

        """尝试放入箱子列表"""

        for bin in bins:

            if bin.can_fit(item):

                bin.add_item(item)

                return True

        return False

    

    def pack(self, item: float) -> int:

        """

        放入物品

        

        Returns:

            使用的箱子数量

        """

        category = self._classify(item)

        

        if category == 'small':

            # 小物品：优先放入小物品箱

            if not self._pack_to_list(item, self.small_bins):

                new_bin = self._new_bin()

                new_bin.add_item(item)

                self.small_bins.append(new_bin)

        

        elif category == 'medium':

            # 中物品：放入中物品箱或大物品箱

            if not self._pack_to_list(item, self.medium_bins):

                if not self._pack_to_list(item, self.large_bins):

                    new_bin = self._new_bin()

                    new_bin.add_item(item)

                    self.medium_bins.append(new_bin)

        

        else:  # large

            # 大物品：直接开新箱

            new_bin = self._new_bin()

            new_bin.add_item(item)

            self.large_bins.append(new_bin)

        

        return self.bin_count





def simulate_bin_packing(algorithm_class, items: List[float], 

                        capacity: float = 1.0) -> Tuple[int, List[Bin]]:

    """

    模拟装箱算法

    

    Args:

        algorithm_class: 算法类

        items: 物品列表

        capacity: 箱子容量

    

    Returns:

        (箱子数量, 箱子列表)

    """

    algo = algorithm_class(capacity)

    

    for item in items:

        algo.pack(item)

    

    return algo.bin_count, algo.bins





def analyze_competitive_ratio():

    """

    分析竞争比

    

    装箱问题的最优下界：

    - OPT >= sum(items) / capacity

    """

    print("=== 在线装箱竞争比分析 ===\n")

    

    print("竞争比上界:")

    print("| 算法        | 竞争比 | 备注              |")

    print("|-------------|--------|-------------------|")

    print("| Next Fit    | 2      | 最坏情况         |")

    print("| First Fit   | 1.7    | 渐进竞争比        |")

    print("| Best Fit    | 1.7    | 渐进竞争比        |")

    print("| Worst Fit   | 2      | 最坏情况较差     |")

    print("| Refined FF  | 1.5    | 分类方法          |")

    

    print("\n理论下界:")

    print("  - 任何在线算法: Ω(log n) 当物品大小均匀分布")

    print("  - 当物品很小(<1/3): Θ(1) 竞争比可达")

    print("  - 当物品任意: Ω(log n) 是下界")





def demo_uniform_items():

    """演示均匀分布物品"""

    print("\n=== 均匀分布物品演示 ===\n")

    

    random.seed(42)

    

    # 生成均匀分布的物品

    items = [random.uniform(0.1, 0.5) for _ in range(100)]

    

    capacity = 1.0

    lower_bound = math.ceil(sum(items) / capacity)

    

    print(f"物品数: {len(items)}")

    print(f"总大小: {sum(items):.2f}")

    print(f"理论下界: {lower_bound} 箱")

    print()

    

    algorithms = {

        'Next Fit': NextFit,

        'First Fit': FirstFit,

        'Best Fit': BestFit,

        'Worst Fit': WorstFit,

        'Refined First Fit': RefinedFirstFit,

    }

    

    print("| 算法               | 箱数 | 效率 |")

    print("|--------------------|------|------|")

    

    for name, algo_class in algorithms.items():

        count, bins = simulate_bin_packing(algo_class, items, capacity)

        efficiency = sum(items) / (count * capacity) * 100

        print(f"| {name:18s} | {count:4d} | {efficiency:4.1f}% |")





def demo_worst_case():

    """演示最坏情况"""

    print("\n=== 最坏情况演示 ===\n")

    

    capacity = 1.0

    

    # Next Fit的最坏情况：交替大小物品

    items = [0.6, 0.6, 0.6, 0.6] + [0.4, 0.4, 0.4, 0.4]

    

    print(f"物品序列: {items}")

    print()

    

    # NF会使用8箱（每对物品一箱）

    nf = NextFit(capacity)

    for item in items:

        nf.pack(item)

    

    print(f"Next Fit: {nf.bin_count} 箱")

    print(f"  理论最优: 3 箱 (6+0.4+0.4=1, 0.6+0.4=1, 0.6+0.4=1)")

    

    # Best Fit会更好

    bf = BestFit(capacity)

    for item in items:

        bf.pack(item)

    

    print(f"\nBest Fit: {bf.bin_count} 箱")





def demo_items_distribution():

    """演示物品大小分布影响"""

    print("\n=== 物品大小分布影响 ===\n")

    

    print("物品类型:")

    print("  - 很小 (<1/3): 容易装箱，接近最优")

    print("  - 中等 (1/3-2/3): 挑战较大")

    print("  - 很大 (>2/3): 每箱最多一个")

    print()

    

    scenarios = [

        ("全部很小", [0.1] * 20),

        ("全部很大", [0.7] * 10),

        ("混合大小", [random.uniform(0.1, 0.9) for _ in range(20)]),

        ("全部接近0.5", [0.49] * 20),

    ]

    

    print("| 场景       | NF  | FF  | BF  | 最优下界 |")

    print("|------------|-----|-----|-----|----------|")

    

    for name, items in scenarios:

        nf_count, _ = simulate_bin_packing(NextFit, items)

        ff_count, _ = simulate_bin_patching(FirstFit, items)

        bf_count, _ = simulate_bin_packing(BestFit, items)

        lower = math.ceil(sum(items))

        

        print(f"| {name:10s} | {nf_count:3d} | {ff_count:3d} | {bf_count:3d} | {lower:6d}     |")





def demo_skyline():

    """天际线问题（2D装箱）"""

    print("\n=== 天际线问题 ===\n")

    

    print("天际线问题:")

    print("  - 物品有宽度和高度")

    print("  - 箱子有最大宽度和高度")

    print("  - 目标是覆盖给定天际线")

    print()

    

    print("应用:")

    print("  - 城市规划")

    print("  - 内存布局")

    print("  - VLSI芯片设计")





if __name__ == "__main__":

    print("=" * 60)

    print("在线装箱算法")

    print("=" * 60)

    

    # 均匀物品

    demo_uniform_items()

    

    # 最坏情况

    demo_worst_case()

    

    # 物品分布影响

    demo_items_distribution()

    

    # 天际线

    demo_skyline()

    

    # 竞争比分析

    analyze_competitive_ratio()

    

    print("\n" + "=" * 60)

    print("关键结论:")

    print("=" * 60)

    print("""

1. 算法选择:

   - 小物品多: Refined First Fit 最好

   - 大物品多: First Fit 或 Best Fit

   - 均匀分布: 差异不大

   

2. 竞争比:

   - 任意物品: Ω(log n) 下界

   - Best Fit: O(log n) 上界

   

3. 实际建议:

   - First Fit 实现简单，效果不错

   - Best Fit 适合物品大小差异大的情况

   - Refined FF 适合有大小分类的场景

""")

