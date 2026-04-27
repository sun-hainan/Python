# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / greedy_coloring

本文件实现 greedy_coloring 相关的算法功能。
"""

import random
from typing import List, Dict, Set


class GreedyColoring:
    """贪婪着色算法"""

    def __init__(self, n_vertices: int):
        """
        参数：
            n_vertices: 顶点数
        """
        self.n = n_vertices
        self.graph = [[] for _ in range(n_vertices)]
        self.colors = [None] * n_vertices

    def add_edge(self, u: int, v: int) -> None:
        """
        添加边

        参数：
            u, v: 边的两端点
        """
        if u < self.n and v < self.n:
            self.graph[u].append(v)
            self.graph[v].append(u)

    def greedy_color(self) -> int:
        """
        贪婪着色

        返回：使用的颜色数
        """
        used_colors = set()

        for v in range(self.n):
            # 找相邻顶点使用的颜色
            forbidden = set()
            for neighbor in self.graph[v]:
                if self.colors[neighbor] is not None:
                    forbidden.add(self.colors[neighbor])

            # 用最小的可用颜色
            color = 0
            while color in forbidden:
                color += 1

            self.colors[v] = color
            used_colors.add(color)

        return len(used_colors)

    def analyze_coloring(self) -> dict:
        """
        分析着色结果

        返回：分析结果
        """
        color_counts = {}
        for c in self.colors:
            color_counts[c] = color_counts.get(c, 0) + 1

        return {
            'n_colors': len(color_counts),
            'color_distribution': color_counts,
            'max_degree': max(len(self.graph[i]) for i in range(self.n)),
            'colors': self.colors
        }


class BrooksAlgorithm:
    """Brooks算法（最坏情况着色）"""

    def __init__(self, graph: List[List[int]]):
        """
        参数：
            graph: 邻接表
        """
        self.graph = graph
        self.n = len(graph)

    def worst_case_coloring(self) -> int:
        """
        找出最坏情况的着色上界

        返回：上界（Δ 或 Δ+1）
        """
        max_degree = max(len(self.graph[i]) for i in range(self.n))

        # 检查是否是完全图或奇环
        is_complete = all(len(self.graph[i]) == self.n - 1 for i in range(self.n))
        is_odd_cycle = self._is_odd_cycle()

        if is_complete:
            return self.n  # 完全图需要 n 种颜色
        elif is_odd_cycle:
            return max_degree + 1  # 奇环需要 Δ+1
        else:
            return max_degree  # 其他图最多 Δ 种颜色

    def _is_odd_cycle(self) -> bool:
        """检查是否是奇环"""
        if self.n < 3:
            return False

        # 简化：只检查简单的环
        degree_two = sum(1 for i in range(self.n) if len(self.graph[i]) == 2)
        return degree_two == self.n


def coloring_complexity():
    """着色复杂度"""
    print("=== 图着色复杂度 ===")
    print()
    print("问题：")
    print("  - 确定图着色数是 NP-完全")
    print("  - 贪婪着色 O(V+E)")
    print()
    print("Brooks定理：")
    print("  - 除了完全图和奇环")
    print("  - 着色数 ≤ 最大度 Δ")
    print()
    print("应用：")
    print("  - 编译器寄存器分配")
    print("  - 航班调度")
    print("  - 数独求解")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 贪婪着色测试 ===\n")

    # 创建简单图
    n = 10
    coloring = GreedyColoring(n)

    # 添加边（构造一个接近二分图的图）
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5),
             (5, 0), (0, 6), (1, 7), (2, 8), (3, 9)]

    for u, v in edges:
        coloring.add_edge(u, v)

    print(f"顶点数: {n}")
    print(f"边数: {len(edges)}")
    print()

    # 贪婪着色
    n_colors = coloring.greedy_color()

    print(f"使用的颜色数: {n_colors}")
    print()

    # 分析
    analysis = coloring.analyze_coloring()

    print("着色分析：")
    print(f"  颜色数: {analysis['n_colors']}")
    print(f"  最大度: {analysis['max_degree']}")
    print(f"  着色结果: {analysis['colors']}")

    print()
    print("说明：")
    print("  - 贪婪着色是快速的近似算法")
    print("  - Brooks给出上界")
    print("  - 实际颜色数可能更少")
