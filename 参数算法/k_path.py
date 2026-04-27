# -*- coding: utf-8 -*-
"""
算法实现：参数算法 / k_path

本文件实现 k_path 相关的算法功能。
"""

import random


def color_coding_path(graph, k, trials=1000):
    """
    使用颜色编码求解 k-路径问题。

    颜色编码的核心思想：
    - 随机将图顶点着色为 k+1 种颜色
    - 如果存在一条长度 k 的路径，其顶点颜色互不相同（完美哈希）
    - 检测是否存在彩虹色的 k-路径

    参数:
        graph: 邻接表
        k: 路径长度（边数）
        trials: 随机试验次数

    返回:
        True 如果找到 k-路径，否则 False
    """
    n = len(graph)
    if n < k + 1:
        return False

    for _ in range(trials):
        # 步骤1：随机着色
        colors = _random_coloring(list(graph.keys()), k + 1)

        # 步骤2：动态规划检测彩虹 k-路径
        if _has_rainbow_k_path(graph, colors, k):
            return True

    return False


def _random_coloring(vertices, num_colors):
    """为每个顶点随机分配 0..num_colors-1 的颜色。"""
    return {v: random.randint(0, num_colors - 1) for v in vertices}


def _has_rainbow_k_path(graph, colors, k):
    """
    检查是否存在彩虹色的长度 k 路径。

    DP 状态：dp[v][c] = 从某个起点到 v 且以颜色 c 结束的路径的最大长度
    """
    # 初始化：每个顶点可以成为长度为 0 的路径的终点
    dp = {v: {colors[v]: 0} for v in graph}

    for length in range(k):
        new_dp = {v: {} for v in graph}
        for v in graph:
            for u in graph[v]:
                # 从 u 扩展到 v
                for cu, lu in dp[u].items():
                    cv = colors[v]
                    # 如果颜色不冲突
                    if cu != cv:
                        new_len = lu + 1
                        if cv not in new_dp[v] or new_len > new_dp[v][cv]:
                            new_dp[v][cv] = new_len
        dp = new_dp

    # 检查是否存在长度 k 的路径
    for v in dp:
        for c, length in dp[v].items():
            if length >= k:
                return True
    return False


def exhaustive_k_path(graph, k):
    """
    暴力枚举验证（用于对比，指数复杂度）。
    """
    vertices = list(graph.keys())

    def dfs(path, visited):
        if len(path) - 1 == k:
            return True
        last = path[-1]
        for neighbor in graph.get(last, []):
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                if dfs(path, visited):
                    return True
                path.pop()
                visited.remove(neighbor)
        return False

    for start in vertices:
        visited = {start}
        if dfs([start], visited):
            return True
    return False


if __name__ == "__main__":
    # 测试图
    test_graph = {
        'A': ['B', 'C'],
        'B': ['A', 'C', 'D'],
        'C': ['A', 'B', 'D'],
        'D': ['B', 'C', 'E'],
        'E': ['D', 'F'],
        'F': ['E']
    }

    print("=== 颜色编码 k-路径测试 ===")
    print(f"测试图: {test_graph}")

    for k in [3, 4, 5]:
        # 颜色编码（10000次试验）
        found_cc = color_coding_path(test_graph, k, trials=10000)
        # 暴力验证
        found_ex = exhaustive_k_path(test_graph, k)

        print(f"\nk={k}:")
        print(f"  颜色编码找到: {found_cc}")
        print(f"  暴力验证:     {found_ex}")

    # 随机图测试
    print("\n=== 随机图测试 ===")
    random.seed(42)
    vertices = list(range(20))
    random_graph = {v: [] for v in vertices}
    for i in range(30):
        u = random.choice(vertices)
        v = random.choice(vertices)
        if u != v and v not in random_graph[u]:
            random_graph[u].append(v)
            random_graph.setdefault(v, []).append(u)

    for k in [5, 7]:
        found = color_coding_path(random_graph, k, trials=5000)
        print(f"随机图 n=20, k={k}: 找到 = {found}")
