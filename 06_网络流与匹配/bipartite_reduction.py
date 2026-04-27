# -*- coding: utf-8 -*-
"""
算法实现：06_网络流与匹配 / bipartite_reduction

本文件实现 bipartite_reduction 相关的算法功能。
"""

from typing import List, Dict, Tuple, Optional, Set


class BipartiteToFlow:
    """
    将二分图最大匹配规约到网络最大流的转换器。

    Attributes:
        n_left: 左侧顶点数
        n_right: 右侧顶点数
        edges: 二分图边集合 {(u, v), ...}，u∈[0,n_left), v∈[0,n_right)
        source: 超源编号（= n_left + n_right）
        sink: 超汇编号（= n_left + n_right + 1）
        n_total: 构造后网络的总顶点数
        adj: 网络的邻接表，格式: (to, capacity)
    """

    def __init__(self, n_left: int, n_right: int):
        """
        初始化规约器。

        Args:
            n_left: 左侧（U）顶点数
            n_right: 右侧（V）顶点数
        """
        self.n_left = n_left
        self.n_right = n_right
        self.edges: Set[Tuple[int, int]] = set()
        # 超源 = n_left + n_right，超汇 = n_left + n_right + 1
        self.source = n_left + n_right
        self.sink = n_left + n_right + 1
        self.n_total = n_left + n_right + 2

    def add_edge(self, u: int, v: int):
        """
        添加二分图中的一条边 (u, v)。

        Args:
            u: 左侧顶点编号 [0, n_left)
            v: 右侧顶点编号 [0, n_right)
        """
        if 0 <= u < self.n_left and 0 <= v < self.n_right:
            self.edges.add((u, v))

    def build_network(self) -> Tuple[int, List[List[Tuple[int, int]]]]:
        """
        构建等价的最大流网络。

        Returns:
            (n_total, adjacency_list):
                n_total: 网络总顶点数（含 s, t）
                adjacency_list: 邻接表，每条记录 (to, capacity)
                               包含正向边和反向边（各占一条记录）
        """
        n = self.n_total
        adj: List[List[Tuple[int, int]]] = [[] for _ in range(n)]

        def add_directed_edge(frm: int, to: int, cap: int):
            """添加一条有向边（含反向容量=0的边）"""
            adj[frm].append((to, cap))
            adj[to].append((frm, 0))  # 反向边，容量 0

        # 从超源到每个左侧顶点：容量 1
        for u in range(self.n_left):
            add_directed_edge(self.source, u, 1)

        # 从每个左侧顶点到右侧顶点：容量 1（每条二分边一条）
        for (u, v) in self.edges:
            add_directed_edge(u, self.n_left + v, 1)

        # 从每个右侧顶点到超汇：容量 1
        for v in range(self.n_right):
            add_directed_edge(self.n_left + v, self.sink, 1)

        return n, adj

    def ford_fulkerson(self, adj: List[List[Tuple[int, int]]]) -> Tuple[int, List[int]]:
        """
        在构造的网络上执行 Ford-Fulkerson（DFS 版）求最大流。

        Args:
            adj: 邻接表（已构造）

        Returns:
            (max_flow_value, flow_matrix): 最大流值和流矩阵
        """
        n = self.n_total
        flow = [[0] * n for _ in range(n)]

        def dfs_augment(u: int, pushed: int) -> int:
            """DFS 寻找增广路径"""
            if u == self.sink:
                return pushed
            for i, (to, cap) in enumerate(adj[u]):
                residual = cap - flow[u][to]
                if residual > 0:
                    sent = dfs_augment(to, min(pushed, residual))
                    if sent > 0:
                        flow[u][to] += sent
                        flow[to][u] -= sent
                        return sent
            return 0

        max_flow = 0
        while True:
            pushed = dfs_augment(self.source, float('inf'))
            if pushed == 0:
                break
            max_flow += pushed

        return max_flow, flow

    def extract_matching(self, flow: List[List[int]]) -> List[Tuple[int, int]]:
        """
        从计算出的流矩阵中提取匹配。

        流矩阵中，饱和的 u→v 边（u 在左侧，v 在右侧）即为匹配边。

        Args:
            flow: n x n 流矩阵

        Returns:
            匹配列表 [(u, v), ...]
        """
        matching = []
        for (u, v) in self.edges:
            # 检查 u→v 这条边的流量是否达到容量 1（饱和）
            if flow[u][self.n_left + v] >= 1:
                matching.append((u, v))
        return matching

    def max_matching(self) -> Tuple[int, List[Tuple[int, int]]]:
        """
        完整流程：规约 → 求最大流 → 提取匹配。

        Returns:
            (max_matching_size, matching_pairs)
        """
        n, adj = self.build_network()
        max_flow, flow = self.ford_fulkerson(adj)
        matching = self.extract_matching(flow)
        return max_flow, matching


def bipartite_matching_via_network_flow(
    n_left: int,
    n_right: int,
    edges: List[Tuple[int, int]]
) -> Tuple[int, List[Tuple[int, int]]]:
    """
    便捷接口：将二分图匹配规约到网络流并求解。

    Args:
        n_left: 左侧顶点数
        n_right: 右侧顶点数
        edges: 二分图边列表

    Returns:
        (最大匹配大小, 匹配对列表)
    """
    reducer = BipartiteToFlow(n_left, n_right)
    for u, v in edges:
        reducer.add_edge(u, v)
    return reducer.max_matching()


if __name__ == "__main__":
    import sys

    # ----------------- 测试 1: 经典示例 -----------------
    # 左侧: {0,1,2}，右侧: {0,1,2}
    # 边: 0-0, 0-1, 1-1, 1-2, 2-0, 2-2
    # 最大匹配: 3（完美匹配）
    edges1 = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 2)]
    size1, match1 = bipartite_matching_via_network_flow(3, 3, edges1)
    print(f"[测试1] 二分图最大匹配 = {size1} (期望: 3)")
    print(f"  匹配: {match1}")
    assert size1 == 3, f"期望 3，实际 {size1}"

    # ----------------- 测试 2: 无法完美匹配 -----------------
    # 左侧: {0,1}，右侧: {0,1,2}
    # 边: 0-0, 0-2, 1-0, 1-1
    # 最大匹配: 2
    edges2 = [(0, 0), (0, 2), (1, 0), (1, 1)]
    size2, match2 = bipartite_matching_via_network_flow(2, 3, edges2)
    print(f"[测试2] 非完美匹配 = {size2} (期望: 2)")
    print(f"  匹配: {match2}")
    assert size2 == 2

    # ----------------- 测试 3: 无边 -----------------
    edges3 = []
    size3, match3 = bipartite_matching_via_network_flow(3, 3, edges3)
    print(f"[测试3] 空图 = {size3} (期望: 0)")
    assert size3 == 0 and match3 == []

    # ----------------- 测试 4: 星形图 -----------------
    # 左侧: {0}，右侧: {0,1,2,3}
    # 边: 0-0, 0-1, 0-2, 0-3
    # 最大匹配: 1
    edges4 = [(0, 0), (0, 1), (0, 2), (0, 3)]
    size4, match4 = bipartite_matching_via_network_flow(1, 4, edges4)
    print(f"[测试4] 星形图 = {size4} (期望: 1)")
    assert size4 == 1

    # ----------------- 测试 5: 链式图 -----------------
    # 左侧: {0,1,2,3}，右侧: {0,1,2,3}
    # 边: 0-0, 1-1, 2-2, 3-3, 还加 0-1, 1-2, 2-3
    edges5 = [(0, 0), (1, 1), (2, 2), (3, 3), (0, 1), (1, 2), (2, 3)]
    size5, match5 = bipartite_matching_via_network_flow(4, 4, edges5)
    print(f"[测试5] 链式图 = {size5} (期望: 4)")
    assert size5 == 4

    # ----------------- 测试 6: 大小不对称的图 -----------------
    # 左侧: 5 个，右侧: 3 个，边较多
    # 最大匹配 <= 3
    n_left6, n_right6 = 5, 3
    edges6 = [
        (0, 0), (0, 1), (0, 2),
        (1, 0), (1, 1),
        (2, 1), (2, 2),
        (3, 0), (3, 2),
        (4, 1),
    ]
    size6, match6 = bipartite_matching_via_network_flow(n_left6, n_right6, edges6)
    print(f"[测试6] 5x3 不对称图 = {size6} (期望: 3)")
    assert size6 == 3

    print("\n所有二分图→网络流规约测试通过！")
