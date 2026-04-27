# -*- coding: utf-8 -*-
"""
算法实现：参数算法 / bounded_treewidth

本文件实现 bounded_treewidth 相关的算法功能。
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict, deque


class TreeDecomposition:
    """树分解"""

    def __init__(self, graph: Dict[int, List[int]]):
        """
        参数：
            graph: 邻接表表示的图
        """
        self.graph = graph
        self.nodes = list(graph.keys())
        self.n = len(self.nodes)
        self.bags = []  # 树分解的bags
        self.tree = defaultdict(list)  # 树结构
        self.node_to_bags = defaultdict(list)  # 节点到bag的映射

    def find_nice_tree_decomposition(self) -> List[Set[int]]:
        """
        找到nice树分解（简化版）

        返回：bags列表
        """
        # 简化：使用染色算法的思想
        # 实际需要更复杂的PEA算法

        # 这里是概念性演示
        bags = []

        # 对于树宽为1的图（树），找到所有节点的树分解
        # 使用BFS中心作为根
        if self.n <= 2:
            bags = [{v} for v in self.nodes]
            bags.append({self.nodes[0], self.nodes[-1]}) if self.n > 1 else None
            return bags

        # 启发式：使用最大度节点作为根
        root = max(self.nodes, key=lambda v: len(self.graph[v]))

        # BFS分层
        visited = {root}
        level = {root: 0}
        parent = {}
        queue = deque([root])

        while queue:
            u = queue.popleft()
            for v in self.graph[u]:
                if v not in visited:
                    visited.add(v)
                    parent[v] = u
                    level[v] = level[u] + 1
                    queue.append(v)

        # 为每条边创建bag
        for v in self.nodes:
            if v in parent:
                bags.append({v, parent[v]})

        # 根节点单独一个bag
        bags.append({root})

        self.bags = bags
        return bags

    def compute_treewidth(self) -> int:
        """
        估计树宽（下界）

        返回：树宽估计
        """
        if not self.bags:
            self.find_nice_tree_decomposition()

        if not self.bags:
            return 0

        # 树宽 = max(|bag|) - 1
        max_bag_size = max(len(bag) for bag in self.bags) if self.bags else 0
        return max(0, max_bag_size - 1)


class CourcellesTheorem:
    """Courcelle定理：树宽有界的图上的一阶逻辑可解"""

    @staticmethod
    def solve_independent_set(graph: Dict[int, List[int]], k: int) -> bool:
        """
        用树分解求解独立集（动态规划）

        参数：
            graph: 图
            k: 目标大小

        返回：是否存在大小为k的独立集
        """
        # 简化实现
        # 实际需要完整的树分解

        td = TreeDecomposition(graph)
        bags = td.find_nice_tree_decomposition()

        # 动态规划：对于每个bag，计算最大独立集大小
        dp = {}

        for bag in bags:
            # 这个bag内的独立集大小 = min(k, |bag|)
            size = min(k, len(bag))
            dp[frozenset(bag)] = size

        return any(v >= k for v in dp.values())

    @staticmethod
    def solve_vertex_cover(tree: Dict[int, List[int]], k: int) -> bool:
        """
        树图上的顶点覆盖（多项式时间）

        树宽=1，可用更简单的方法
        """
        visited = set()
        result = True

        def dfs(u, parent):
            nonlocal result

            children = [v for v in tree[u] if v != parent]

            # 如果子树中的边数 > k，无法覆盖
            total_edges = sum(len(tree[v]) for v in children) // 2
            if total_edges > k:
                result = False
                return False

            # 简单贪心：选父节点或子节点
            return True

        dfs(0, -1)
        return result


def pathwidth_approximation(graph: Dict[int, List[int]]) -> int:
    """
    路径宽近似

    路径宽是树宽的特殊情况
    """
    n = len(graph)

    # 简单下界：最小顶点覆盖的大小
    # 对于一般图，这是NP-hard
    # 这里返回简单的启发式下界

    if n == 0:
        return 0

    # 使用最大匹配大小的下界
    matched = set()
    match_size = 0

    for u in graph:
        if u not in matched:
            matched.add(u)
            for v in graph[u]:
                if v not in matched:
                    matched.add(v)
                    match_size += 1
                    break

    # 最小顶点覆盖 >= 最大匹配（König定理对二分图成立）
    # 一般图这是一个下界
    return match_size


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 树宽有界图的算法测试 ===\n")

    # 树（图宽=1）
    tree = {
        0: [1, 2],
        1: [0, 3],
        2: [0],
        3: [1]
    }

    print("测试图1（树）:")
    print(f"  邻接表: {tree}")

    td = TreeDecomposition(tree)
    bags = td.find_nice_tree_decomposition()
    tw = td.compute_treewidth()

    print(f"  树宽: {tw}")
    print(f"  Bags数: {len(bags)}")
    for i, bag in enumerate(bags):
        print(f"    Bag{i}: {bag}")

    print()

    # 系列-并行图（树宽=2）
    sp_graph = {
        0: [1, 2],
        1: [0, 2],
        2: [0, 1, 3],
        3: [2]
    }

    print("测试图2（系列-并行图）:")
    print(f"  邻接表: {sp_graph}")

    td2 = TreeDecomposition(sp_graph)
    bags2 = td2.find_nice_tree_decomposition()
    tw2 = td2.compute_treewidth()

    print(f"  树宽估计: {tw2}")

    print()
    print("树宽应用：")
    print("  1. 电路设计：晶体管布局")
    print("  2. 数据库： join顺序优化")
    print("  3. 生物：蛋白质折叠")
    print("  4. NLP：依存句法树")
    print()
    print("算法复杂度：")
    print("  树宽固定：很多NP难问题变为多项式")
    print("  独立集：O(n * 2^k)")
    print("  支配集：O(n * 3^k)")
