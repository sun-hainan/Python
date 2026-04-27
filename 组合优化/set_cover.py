# -*- coding: utf-8 -*-
"""
算法实现：组合优化 / set_cover

本文件实现 set_cover 相关的算法功能。
"""

from typing import List, Set, Tuple, Optional
import random


class SetCoverSolver:
    """
    集合覆盖问题求解器
    给定一组元素和子集集合,找到覆盖所有元素的最小子集
    """
    
    def __init__(self, elements: Set[int], subsets: List[Set[int]]):
        """
        初始化
        
        Args:
            elements: 需要覆盖的元素集合
            subsets: 子集列表,每个子集是一组元素
        """
        self.elements = elements
        self.subsets = subsets
        self.n = len(subsets)
    
    def greedy_set_cover(self) -> Tuple[List[int], float]:
        """
        贪心算法:每步选择覆盖最多未覆盖元素的子集
        
        Returns:
            (选择的子集索引列表, 选择的子集数量)
        """
        uncovered = self.elements.copy()
        selected = []
        
        while uncovered:
            # 找覆盖最多未覆盖元素的子集
            best_idx = -1
            best_coverage = set()
            
            for i, subset in enumerate(self.subsets):
                if i in selected:
                    continue
                
                coverage = uncovered & subset
                if len(coverage) > len(best_coverage):
                    best_coverage = coverage
                    best_idx = i
            
            if best_idx == -1 or not best_coverage:
                # 无法覆盖所有元素
                break
            
            selected.append(best_idx)
            uncovered -= best_coverage
        
        return selected, len(selected)
    
    def greedy_by_ratio(self) -> Tuple[List[int], float]:
        """
        改进贪心算法:按性价比(覆盖元素数/成本)选择
        
        Returns:
            (选择的子集索引列表, 选择的子集数量)
        """
        uncovered = self.elements.copy()
        selected = []
        costs = [1.0] * self.n  # 假设每个子集成本为1
        
        while uncovered:
            best_idx = -1
            best_ratio = -1
            
            for i, subset in enumerate(self.subsets):
                if i in selected:
                    continue
                
                coverage = len(uncovered & subset)
                if coverage == 0:
                    continue
                
                ratio = coverage / costs[i]
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_idx = i
            
            if best_idx == -1:
                break
            
            selected.append(best_idx)
            uncovered -= self.subsets[best_idx] & uncovered
        
        return selected, len(selected)
    
    def lp_relaxation(self) -> List[float]:
        """
        线性规划松弛求解
        
        Returns:
            每个子集的选择分数(0-1之间)
        """
        # 简化实现:使用朴素方法
        # 实际应该用单纯形法或内点法
        # 这里只是演示概念
        
        # 计算每个元素被多少个子集覆盖
        element_coverage = {e: 0 for e in self.elements}
        for subset in self.subsets:
            for e in subset:
                if e in element_coverage:
                    element_coverage[e] += 1
        
        # 每个子集的分数 = min(1, 该子集覆盖的元素中coverage最小的)
        scores = []
        for subset in self.subsets:
            min_cov = min(element_coverage.get(e, 1) for e in subset)
            scores.append(min(1.0, 1.0 / min_cov if min_cov > 0 else 1.0))
        
        return scores
    
    def round_lp_solution(self, scores: List[float], threshold: float = 0.5) -> List[int]:
        """
        将LP分数舍入为离散解
        
        Args:
            scores: LP解的分数
            threshold: 阈值
        
        Returns:
            选择的子集索引
        """
        return [i for i, s in enumerate(scores) if s >= threshold]


def solve_set_cover(elements: Set[int], subsets: List[Set[int]],
                   method: str = 'greedy') -> Optional[List[int]]:
    """
    集合覆盖求解便捷函数
    
    Args:
        elements: 元素集合
        subsets: 子集列表
        method: 'greedy', 'ratio', 'lp'
    
    Returns:
        选择的子集索引列表
    """
    solver = SetCoverSolver(elements, subsets)
    
    if method == 'greedy':
        selected, _ = solver.greedy_set_cover()
        return selected
    elif method == 'ratio':
        selected, _ = solver.greedy_by_ratio()
        return selected
    else:
        scores = solver.lp_relaxation()
        return solver.round_lp_solution(scores)


# 测试代码
if __name__ == "__main__":
    # 测试1: 简单实例
    print("测试1 - 简单实例:")
    elements = {1, 2, 3, 4, 5}
    subsets = [
        {1, 2, 3},   # 子集0
        {3, 4},      # 子集1
        {4, 5},      # 子集2
        {1, 5},      # 子集3
        {2, 3, 4, 5} # 子集4
    ]
    
    solver = SetCoverSolver(elements, subsets)
    
    selected, count = solver.greedy_set_cover()
    print(f"  元素: {elements}")
    print(f"  子集: {subsets}")
    print(f"  贪心选择: {selected}")
    print(f"  选择的子集: {[subsets[i] for i in selected]}")
    
    # 验证覆盖
    covered = set()
    for i in selected:
        covered |= subsets[i]
    print(f"  覆盖的元素: {covered}")
    print(f"  完全覆盖: {covered == elements}")
    
    # 测试2: 改进贪心
    print("\n测试2 - 改进贪心:")
    selected2, count2 = solver.greedy_by_ratio()
    print(f"  按性价比选择: {selected2}")
    
    # 测试3: LP松弛
    print("\n测试3 - LP松弛:")
    scores = solver.lp_relaxation()
    print(f"  LP分数: {scores}")
    
    rounded = solver.round_lp_solution(scores, 0.3)
    print(f"  舍入结果(threshold=0.3): {rounded}")
    
    # 测试4: 随机实例
    print("\n测试4 - 随机实例:")
    random.seed(42)
    
    n_elements = 20
    n_subsets = 50
    elements4 = set(range(n_elements))
    
    subsets4 = []
    for _ in range(n_subsets):
        # 每个子集随机包含若干元素
        size = random.randint(1, n_elements)
        subset = set(random.sample(range(n_elements), size))
        subsets4.append(subset)
    
    solver4 = SetCoverSolver(elements4, subsets4)
    
    selected4, count4 = solver4.greedy_set_cover()
    print(f"  贪心算法: 选择{count4}个子集")
    
    selected4b, count4b = solver4.greedy_by_ratio()
    print(f"  性价比算法: 选择{count4b}个子集")
    
    # 验证覆盖
    covered4 = set()
    for i in selected4:
        covered4 |= subsets4[i]
    print(f"  完全覆盖: {covered4 == elements4}")
    
    # 测试5: 近似比分析
    print("\n测试5 - 近似比分析:")
    # 集合覆盖的贪心算法有 O(log n) 的近似比
    
    sizes = [len(s) for s in subsets4]
    print(f"  子集大小统计: min={min(sizes)}, max={max(sizes)}, avg={sum(sizes)/len(sizes):.1f}")
    
    # 计算LP下界
    scores4 = solver4.lp_relaxation()
    lp_sum = sum(scores4)
    print(f"  LP解的和: {lp_sum:.2f}")
    print(f"  贪心/LP比值: {count4/lp_sum:.2f}")
    
    print("\n所有测试完成!")
