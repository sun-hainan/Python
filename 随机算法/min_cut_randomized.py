# -*- coding: utf-8 -*-
"""
算法实现：随机算法 / min_cut_randomized

本文件实现 min_cut_randomized 相关的算法功能。
"""

import random
from typing import List, Tuple, Set, Dict
from collections import defaultdict


class KargerMinCut:
    """Karger随机最小割"""

    def __init__(self, n: int):
        self.n = n
        self.edges = []
        self.super_vertices = list(range(n))
        self.vertex_map = {i: i for i in range(n)}

    def reset(self, edges: List[Tuple[int, int, float]]):
        """重置"""
        self.edges = [(u, v, w) for u, v, w in edges]
        self.super_vertices = list(range(self.n))
        self.vertex_map = {i: i for i in range(self.n)}

    def contract_edge(self, edge_idx: int) -> bool:
        """
        收缩一条边

        返回：是否成功收缩
        """
        if edge_idx >= len(self.edges):
            return False

        u, v, w = self.edges[edge_idx]

        # 找到两个顶点所属的super-vertex
        super_u = self.vertex_map[u]
        super_v = self.vertex_map[v]

        if super_u == super_v:
            return False

        # 删除所有连接u,v的边
        new_edges = []
        for eu, ev, ew in self.edges:
            su = self.vertex_map[eu]
            sv = self.vertex_map[ev]
            # 跳过自环和被收缩的边
            if su == super_u and sv == super_v:
                continue
            if su == super_v and sv == super_u:
                continue
            # 更新顶点映射
            if su == super_v:
                su = super_u
            if sv == super_v:
                sv = super_u
            new_edges.append((su, sv, ew))

        # 更新顶点映射
        for i in self.vertex_map:
            if self.vertex_map[i] == super_v:
                self.vertex_map[i] = super_u

        self.edges = new_edges
        return True

    def find_min_cut(self) -> Tuple[Set[Tuple[int, int]], float]:
        """
        找最小割

        返回：(割的边集合, 总权重)
        """
        # 收缩到只剩2个super-vertex
        while len(set(self.vertex_map.values())) > 2:
            if not self.edges:
                break
            edge_idx = random.randint(0, len(self.edges) - 1)
            self.contract_edge(edge_idx)

        # 剩余的边就是割
        cut_edges = set()
        cut_weight = 0.0

        for u, v, w in self.edges:
            su, sv = self.vertex_map[u], self.vertex_map[v]
            if su != sv:
                cut_edges.add((min(su, sv), max(su, sv), w))
                cut_weight += w

        return cut_edges, cut_weight


def repeated_karger(n: int, edges: List[Tuple[int, int, float]],
                    iterations: int = None) -> Tuple[Set[Tuple[int, int]], float]:
    """
    重复Karger算法提高成功率

    成功率：1 - 1/n²
    重复n²次：成功率 > 63%

    参数：
        iterations: 迭代次数（默认n²）
    """
    if iterations is None:
        iterations = n * n

    best_cut = None
    best_weight = float('inf')

    for _ in range(iterations):
        karger = KargerMinCut(n)
        karger.reset(edges)
        cut_edges, cut_weight = karger.find_min_cut()

        if cut_weight < best_weight:
            best_weight = cut_weight
            best_cut = cut_edges

    return best_cut, best_weight


def stoer_wagner_min_cut(n: int, edges: List[Tuple[int, int, float]]) -> Tuple[float, Set[int]]:
    """
    Stoer-Wagner算法（确定性O(nm log n)）

    参数：
        返回：(最小割权重, 一个割的顶点集合)
    """
    # 构建邻接表
    adj = defaultdict(list)
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))

    # 初始化
    best_cut = float('inf')
    best_set = set(range(n))

    # 当前活跃顶点
    active = list(range(n))
    W = defaultdict(lambda: 0)  # 顶点到已知集合的边权重和

    for _ in range(n - 1):
        # 选择最远的顶点（使用A循环）
        seen = set()
        W = defaultdict(lambda: 0)
        last = None

        for v in active:
            if v not in seen:
                # BFS/扩展
                queue = [v]
                seen.add(v)

                while queue:
                    curr = queue.pop(0)
                    for neighbor, weight in adj[curr]:
                        if neighbor not in seen and neighbor in active:
                            W[neighbor] += weight
                            queue.append(neighbor)

                last = v  # 最后添加的顶点

        # 更新最小割
        if W[last] < best_cut:
            best_cut = W[last]
            best_set = seen.copy()

        # 合并last和其他顶点
        for neighbor, weight in adj[last]:
            if neighbor in active and neighbor != last:
                adj[neighbor].append((last, weight))
                adj[last].append((neighbor, weight))

        active.remove(last)

    return best_cut, best_set


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Karger最小割测试 ===\n")

    random.seed(42)

    # 创建简单图
    n = 6
    edges = [
        (0, 1, 1), (0, 2, 2), (0, 3, 3),
        (1, 2, 1), (1, 4, 4),
        (2, 3, 1), (2, 5, 5),
        (3, 5, 2),
        (4, 5, 1),
    ]

    print(f"节点数: {n}, 边数: {len(edges)}")

    # Karger
    print("\n--- 重复Karger ---")
    cut_edges, cut_weight = repeated_karger(n, edges, iterations=50)
    print(f"最小割权重: {cut_weight}")
    print(f"割的边: {[e[:2] for e in cut_edges]}")

    # 确定性算法对比
    print("\n--- Stoer-Wagner (确定性) ---")
    sw_cut, sw_set = stoer_wagner_min_cut(n, edges)
    print(f"最小割权重: {sw_cut}")
    print(f"割的顶点集合: {sw_set}")

    # 概率分析
    print("\n概率分析:")
    success_count = 0
    trials = 100

    for _ in range(trials):
        karger = KargerMinCut(n)
        karger.reset(edges)
        _, weight = karger.find_min_cut()
        if abs(weight - sw_cut) < 0.01:
            success_count += 1

    print(f"  {trials}次尝试中找到最优解: {success_count}次 ({success_count/trials*100:.1f}%)")

    print("\n说明：")
    print("  - Karger: 简单但成功率低")
    print("  - 重复n²次: 成功概率>63%")
    print("  - Stoer-Wagner: 确定性O(nm log n)")
