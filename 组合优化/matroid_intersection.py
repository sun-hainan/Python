# -*- coding: utf-8 -*-
"""
算法实现：组合优化 / matroid_intersection

本文件实现 matroid_intersection 相关的算法功能。
"""

from typing import List, Set, Optional, Tuple
import random


class GraphicMatroid:
    """图拟阵（生成森林）"""

    def __init__(self, edges: List[Tuple[int, int]]):
        self.edges = edges
        self.n_vertices = max(max(e) for e in edges) + 1 if edges else 0

    def is_independent(self, edge_set: Set[int]) -> bool:
        """检查边集是否独立（无环）"""
        parent = list(range(self.n_vertices))

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px == py:
                return False  # 会形成环
            parent[px] = py
            return True

        for idx in edge_set:
            u, v = self.edges[idx]
            if not union(u, v):
                return False

        return True


class LinearMatroid:
    """线性拟阵（向量组线性无关）"""

    def __init__(self, vectors: List[List[float]]):
        self.vectors = vectors
        self.n_dims = len(vectors[0]) if vectors else 0

    def is_independent(self, indices: Set[int]) -> bool:
        """检查向量组是否线性无关"""
        if not indices:
            return True

        import numpy as np
        selected = [self.vectors[i] for i in indices]
        matrix = np.array(selected)

        rank = np.linalg.matrix_rank(matrix)
        return rank == len(selected)


class MatroidIntersection:
    """拟阵交算法"""

    def __init__(self, matroid1, matroid2):
        self.M1 = matroid1
        self.M2 = matroid2

    def find_max_intersection(self) -> Tuple[Set[int], int]:
        """
        找到最大交集

        返回：(最大公共独立集, 大小)
        """
        I = set()

        # 贪心算法（近似最优）
        elements = range(getattr(self.M1, 'n_edges', 100) or getattr(self.M2, 'n_vectors', 100))

        for e in elements:
            I_with_e = I | {e}

            if self.M1.is_independent(I_with_e) and self.M2.is_independent(I_with_e):
                I.add(e)

        return I, len(I)


def matroid_applications():
    """拟阵应用"""
    print("=== 拟阵交应用 ===")
    print()
    print("1. 生成森林问题")
    print("   - M1: 无向图的生成森林（无环）")
    print("   - M2: 有向图的分支（无冲突）")
    print()
    print("2. 约束生成树")
    print("   - 要求生成树包含某些边")
    print("   - 同时排除某些边")
    print()
    print("3. 调度问题")
    print("   - M1: 任务间独立性约束")
    print("   - M2: 时间窗口约束")


def greedy_algorithm():
    """贪心算法"""
    print()
    print("=== 拟阵上的贪心算法 ===")
    print()
    print("对于单个拟阵，贪心算法最优：")
    print("  按权重降序考虑元素")
    print("  如果加入后仍独立，保留")
    print()
    print("对于拟阵交：")
    print("  - 不直接适用")
    print("  - 需要更复杂的交换算法")
    print()
    print("复杂度：O(n² · f)")
    print("  n = 元素数")
    print("  f = 独立性检查时间")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 拟阵交测试 ===\n")

    # 创建图拟阵
    edges = [(0, 1), (1, 2), (2, 3), (0, 3), (1, 3)]
    gm = GraphicMatroid(edges)

    # 检查独立集
    test_sets = [
        {0, 1},      # 边0-1, 1-2，无环
        {0, 1, 2},    # 边0-1, 1-2, 2-3，无环
        {0, 1, 3},    # 有环
    ]

    print("图拟阵（生成森林）测试：")
    for idx_set in test_sets:
        is_ind = gm.is_independent(idx_set)
        edge_names = [f"e{i}" for i in idx_set]
        print(f"  边集 {edge_names}: {'独立' if is_ind else '不独立'}")

    print()
    matroid_applications()
    greedy_algorithm()

    print()
    print("说明：")
    print("  - 拟阵交是组合优化的基本问题")
    print("  - 有多项式时间算法")
    print("  - 应用于调度、编码、网络流")
