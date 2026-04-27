# -*- coding: utf-8 -*-
"""
算法实现：组合优化 / bin_packing

本文件实现 bin_packing 相关的算法功能。
"""

from typing import List, Tuple


class BinPackingSolver:
    """
    装箱问题求解器
    使用First Fit Decreasing算法
    """
    
    def __init__(self, bin_capacity: float):
        """
        初始化求解器
        
        Args:
            bin_capacity: 箱子容量
        """
        self.capacity = bin_capacity
    
    def first_fit_decreasing(self, items: List[float]) -> Tuple[List[List[float]], int]:
        """
        First Fit Decreasing算法
        
        Args:
            items: 物品尺寸列表
        
        Returns:
            (箱子列表, 箱子数量)
        """
        # 降序排序
        items_sorted = sorted(items, reverse=True)
        
        bins = []  # 每个箱子剩余空间
        
        for item in items_sorted:
            placed = False
            
            # 扫描所有箱子,找第一个能放下的
            for i, remaining in enumerate(bins):
                if remaining >= item:
                    bins[i] = remaining - item
                    placed = True
                    break
            
            # 没有能放下的箱子,创建新的
            if not placed:
                bins.append(self.capacity - item)
        
        return [[self.capacity - r for r in bins]], len(bins)
    
    def best_fit_decreasing(self, items: List[float]) -> Tuple[List[List[float]], int]:
        """
        Best Fit Decreasing算法:放入最合适(剩余空间最小)的箱子
        
        Args:
            items: 物品尺寸列表
        
        Returns:
            (箱子列表, 箱子数量)
        """
        items_sorted = sorted(items, reverse=True)
        
        bins = []  # 每个箱子剩余空间
        
        for item in items_sorted:
            best_idx = -1
            best_remaining = float('inf')
            
            for i, remaining in enumerate(bins):
                if remaining >= item and remaining - item < best_remaining:
                    best_remaining = remaining - item
                    best_idx = i
            
            if best_idx >= 0:
                bins[best_idx] -= item
            else:
                bins.append(self.capacity - item)
        
        return [[self.capacity - r for r in bins]], len(bins)
    
    def worst_fit_decreasing(self, items: List[float]) -> Tuple[List[List[float]], int]:
        """
        Worst Fit Decreasing算法:放入剩余空间最大的箱子
        
        Args:
            items: 物品尺寸列表
        
        Returns:
            (箱子列表, 箱子数量)
        """
        items_sorted = sorted(items, reverse=True)
        
        bins = []  # 每个箱子剩余空间
        
        for item in items_sorted:
            worst_idx = -1
            worst_remaining = -1
            
            for i, remaining in enumerate(bins):
                if remaining >= item and remaining > worst_remaining:
                    worst_remaining = remaining
                    worst_idx = i
            
            if worst_idx >= 0:
                bins[worst_idx] -= item
            else:
                bins.append(self.capacity - item)
        
        return [[self.capacity - r for r in bins]], len(bins)
    
    def first_fit(self, items: List[float]) -> Tuple[List[List[float]], int]:
        """
        First Fit算法(不排序)
        
        Args:
            items: 物品尺寸列表
        
        Returns:
            (箱子列表, 箱子数量)
        """
        bins = []  # 每个箱子剩余空间
        bin_contents = []  # 每个箱子的物品
        
        for item in items:
            placed = False
            
            for i, remaining in enumerate(bins):
                if remaining >= item:
                    bins[i] -= item
                    bin_contents[i].append(item)
                    placed = True
                    break
            
            if not placed:
                bins.append(self.capacity - item)
                bin_contents.append([item])
        
        return bin_contents, len(bins)
    
    def next_fit(self, items: List[float]) -> Tuple[List[List[float]], int]:
        """
        Next Fit算法:只检查当前箱子
        
        Args:
            items: 物品尺寸列表
        
        Returns:
            (箱子列表, 箱子数量)
        """
        bins = []
        bin_contents = []
        current_remaining = self.capacity
        current_items = []
        
        for item in items:
            if current_remaining >= item:
                current_remaining -= item
                current_items.append(item)
            else:
                bins.append(current_remaining)
                bin_contents.append(current_items)
                current_remaining = self.capacity - item
                current_items = [item]
        
        if current_items:
            bins.append(current_remaining)
            bin_contents.append(current_items)
        
        return bin_contents, len(bins)
    
    def get_utilization(self, bins: List[List[float]]) -> float:
        """
        计算箱子利用率
        
        Args:
            bins: 箱子内容
        
        Returns:
            平均利用率
        """
        total_used = sum(sum(bin) for bin in bins)
        total_capacity = len(bins) * self.capacity
        return total_used / total_capacity if total_capacity > 0 else 0


def solve_bin_packing(items: List[float], capacity: float,
                     method: str = 'ffd') -> Tuple[List[List[float]], int]:
    """
    装箱问题求解便捷函数
    
    Args:
        items: 物品尺寸
        capacity: 箱子容量
        method: 'ffd', 'bfd', 'wfd', 'ff', 'nf'
    
    Returns:
        (箱子列表, 箱子数量)
    """
    solver = BinPackingSolver(capacity)
    
    if method == 'ffd':
        return solver.first_fit_decreasing(items)
    elif method == 'bfd':
        return solver.best_fit_decreasing(items)
    elif method == 'wfd':
        return solver.worst_fit_decreasing(items)
    elif method == 'ff':
        return solver.first_fit(items)
    elif method == 'nf':
        return solver.next_fit(items)
    else:
        return solver.first_fit_decreasing(items)


# 测试代码
if __name__ == "__main__":
    import random
    random.seed(42)
    
    # 测试1: 简单实例
    print("测试1 - 简单实例:")
    items1 = [0.8, 0.4, 0.7, 0.5, 0.3, 0.6, 0.9, 0.2]
    capacity = 1.0
    
    solver = BinPackingSolver(capacity)
    
    bins, count = solver.first_fit_decreasing(items1)
    print(f"  FFD: {count}个箱子")
    for i, bin_items in enumerate(bins):
        print(f"    箱子{i}: {bin_items}, 利用率={sum(bin_items)/capacity:.2%}")
    
    print(f"  总利用率: {solver.get_utilization(bins):.2%}")
    
    # 测试2: 不同算法对比
    print("\n测试2 - 算法对比:")
    items2 = [0.5, 0.7, 0.3, 0.9, 0.2, 0.6, 0.4, 0.8, 0.1, 0.75]
    
    print(f"  物品: {items2}")
    
    for method in ['ffd', 'bfd', 'wfd', 'ff', 'nf']:
        if method == 'ffd':
            bins, count = solver.first_fit_decreasing(items2)
        elif method == 'bfd':
            bins, count = solver.best_fit_decreasing(items2)
        elif method == 'wfd':
            bins, count = solver.worst_fit_decreasing(items2)
        elif method == 'ff':
            bins, count = solver.first_fit(items2)
        else:
            bins, count = solver.next_fit(items2)
        
        util = solver.get_utilization(bins)
        print(f"    {method.upper()}: {count}个箱子, 利用率={util:.2%}")
    
    # 测试3: 大规模实例
    print("\n测试3 - 大规模实例(100物品):")
    items_large = [random.uniform(0.1, 0.9) for _ in range(100)]
    
    bins, count = solver.first_fit_decreasing(items_large)
    print(f"  FFD: {count}个箱子")
    print(f"  总利用率: {solver.get_utilization(bins):.2%}")
    
    # 测试4: 已知最优(简单实例)
    print("\n测试4 - 已知最优实例:")
    # 容量1.0,物品[0.5, 0.5, 0.3, 0.3, 0.3, 0.3, 0.3]
    # 最优需要3个箱子
    items_opt = [0.5, 0.5, 0.3, 0.3, 0.3, 0.3, 0.3]
    bins_opt, count_opt = solver.first_fit_decreasing(items_opt)
    print(f"  物品: {items_opt}")
    print(f"  FFD结果: {count_opt}个箱子")
    
    # 测试5: 随机生成并验证
    print("\n测试5 - 随机实例验证:")
    for trial in range(3):
        items = [random.uniform(0.1, 0.9) for _ in range(20)]
        bins, count = solver.first_fit_decreasing(items)
        
        # 验证:所有物品都被放置
        total_placed = sum(sum(bin) for bin in bins)
        total_items = sum(items)
        valid = abs(total_placed - total_items) < 1e-9
        
        # 验证:没有箱子溢出
        overflow = any(sum(bin) > capacity + 1e-9 for bin in bins)
        
        print(f"  试用{trial+1}: {count}箱, 放置正确={valid}, 无溢出={not overflow}")
    
    print("\n所有测试完成!")
