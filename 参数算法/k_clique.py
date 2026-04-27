# -*- coding: utf-8 -*-
"""
算法实现：参数算法 / k_clique

本文件实现 k_clique 相关的算法功能。
"""

import random


def color_coding_clique(graph, k, trials=1000):
    """
    使用颜色编码检测 k-团。

    思想：对顶点随机着色到 k 种颜色。如果存在大小为 k 的团，
    则该团的所有顶点颜色恰好各出现一次（彩虹 k-团）。
    通过动态规划检测彩虹 k-团。

    参数:
        graph: 邻接表
        k: 团的规模
        trials: 随机试验次数

    返回:
        找到的团的顶点列表，或 None
    """
    vertices = list(graph.keys())
    n = len(vertices)
    if n < k:
        return None

    for _ in range(trials):
        # 随机着色：每种颜色分配给多个顶点
        colors = [random.randint(0, k - 1) for _ in range(n)]
        color_to_vertices = [[] for _ in range(k)]
        for i, v in enumerate(vertices):
            color_to_vertices[colors[i]].append(v)

        # 检查每种颜色的顶点是否构成团（实际上需要不同颜色的顶点构成团）
        # DP 方案：枚举子集，检查是否两两相连
        result = _dp_rainbow_clique(graph, vertices, colors, k)
        if result is not None:
            return result

    return None


def _dp_rainbow_clique(graph, vertices, colors, k):
    """
    动态规划检测彩虹 k-团。

    状态 dp[S][v] = 顶点集合 S（颜色集合的子集）是否能形成以 v 结尾的团
    """
    n = len(vertices)
    # 简化：直接检查所有 k 元子集是否构成团
    vertex_list = vertices

    # 枚举所有 k 元子集
    for subset in _k_subsets(vertex_list, k):
        # 检查子集是否两两相连
        all_connected = True
        for i in range(k):
            for j in range(i + 1, k):
                u, v = subset[i], subset[j]
                # 检查无向边
                neighbors = graph.get(u, [])
                if v not in neighbors:
                    all_connected = False
                    break
            if not all_connected:
                break
        if all_connected:
            return list(subset)

    return None


def _k_subsets(vertices, k):
    """生成所有 k 元子集（迭代版本）。"""
    n = len(vertices)
    if k > n or k < 0:
        return
    indices = list(range(k))
    while True:
        yield [vertices[i] for i in indices]
        # 寻找下一个组合
        i = k - 1
        while i >= 0 and indices[i] == n - k + i:
            i -= 1
        if i < 0:
            return
        indices[i] += 1
        for j in range(i + 1, k):
            indices[j] = indices[j - 1] + 1


def bron_kerbosch_clique(graph, r=None, p=None, x=None):
    """
    Bron-Kerbosch 算法（回溯），求所有极大团。

    参数:
        graph: 邻接表
        r: 当前已在团中的顶点集合
        p: 可能扩展的顶点集合
        x: 已排除的顶点集合

    返回:
        所有极大团的列表
    """
    if r is None:
        r = set()
    if p is None:
        p = set(graph.keys())
    if x is None:
        x = set()

    if not p and not x:
        yield r.copy()

    # 支化：选择透视顶点（pivot）
    pivot = max(p.union(x), key=lambda v: len(p.intersection(graph.get(v, []))))
    neighbors = set(graph.get(pivot, []))

    for v in p - neighbors:
        neighbors_v = set(graph.get(v, []))
        yield from bron_kerbosch_clique(
            graph,
            r.union({v}),
            p.intersection(neighbors_v),
            x.intersection(neighbors_v)
        )
        p = p - {v}
        x = x.union({v})


def max_clique_size(graph):
    """求最大团的大小（使用 Bron-Kerbosch）。"""
    max_size = 0
    for clique in bron_kerbosch_clique(graph):
        max_size = max(max_size, len(clique))
    return max_size


if __name__ == "__main__":
    # 测试图：一个 5-团和一些额外边
    test_graph = {
        0: [1, 2, 3, 4],
        1: [0, 2, 3, 4],
        2: [0, 1, 3, 4],
        3: [0, 1, 2, 4],
        4: [0, 1, 2, 3],
        5: [1, 2],
        6: []
    }

    print("=== k-团检测测试 ===")
    print(f"测试图: {test_graph}")

    for k in [3, 4, 5]:
        found = color_coding_clique(test_graph, k, trials=5000)
        print(f"\nk={k}: 找到团 = {found}")

    print("\n=== Bron-Kerbosch 所有极大团 ===")
    cliques = list(bron_kerbosch_clique(test_graph))
    print(f"极大团数量: {len(cliques)}")
    for c in cliques:
        print(f"  {sorted(c)} (大小={len(c)})")

    print(f"\n最大团大小: {max_clique_size(test_graph)}")
