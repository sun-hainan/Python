# -*- coding: utf-8 -*-
"""
算法实现：06_网络流与匹配 / ford_fulkerson

本文件实现 ford_fulkerson 相关的算法功能。
"""

from __future__ import annotations
from collections import deque


# 示例网络：
# 0 -> 1 (容量16), 0 -> 2 (容量13)
# 1 -> 2 (容量10), 1 -> 3 (容量12)
# 2 -> 1 (容量4),  2 -> 4 (容量14)
# 3 -> 2 (容量9),  3 -> 5 (容量20)
# 4 -> 3 (容量7),  4 -> 5 (容量4)
# 最大流 = 23
graph = [
    [0, 16, 13, 0, 0, 0],
    [0, 0, 10, 12, 0, 0],
    [0, 4, 0, 0, 14, 0],
    [0, 0, 9, 0, 0, 20],
    [0, 0, 0, 7, 0, 4],
    [0, 0, 0, 0, 0, 0],
]


def breadth_first_search(graph: list, source: int, sink: int, parents: list) -> bool:
    """
    BFS 找增广路径

    返回:
        True 如果找到从 source 到 sink 的路径
    """
    visited = [False] * len(graph)
    queue = deque([source])
    visited[source] = True

    while queue:
        u = queue.popleft()
        # 遍历所有邻居
        for ind, capacity in enumerate(graph[u]):
            if not visited[ind] and capacity > 0:
                queue.append(ind)
                visited[ind] = True
                parents[ind] = u

    return visited[sink]


def ford_fulkerson(graph: list, source: int, sink: int) -> int:
    """
    Ford-Fulkerson 最大流算法

    参数:
        graph: 邻接矩阵，graph[u][v] = 边(u,v)的容量
        source: 源点索引
        sink: 汇点索引

    返回:
        最大流值

    示例:
        >>> test_graph = [
        ...     [0, 16, 13, 0, 0, 0],
        ...     [0, 0, 10, 12, 0, 0],
        ...     [0, 4, 0, 0, 14, 0],
        ...     [0, 0, 9, 0, 0, 20],
        ...     [0, 0, 0, 7, 0, 4],
        ...     [0, 0, 0, 0, 0, 0],
        ... ]
        >>> ford_fulkerson(test_graph, 0, 5)
        23
    """
    parent = [-1] * len(graph)
    max_flow = 0

    # 持续找增广路径
    while breadth_first_search(graph, source, sink, parent):
        # 1. 找路径上最小残余容量
        path_flow = float('inf')
        s = sink
        while s != source:
            path_flow = min(path_flow, graph[parent[s]][s])
            s = parent[s]

        # 2. 增加流
        max_flow += path_flow

        # 3. 更新残余网络（正向边减少，反向边增加）
        v = sink
        while v != source:
            u = parent[v]
            graph[u][v] -= path_flow  # 正向边容量减少
            graph[v][u] += path_flow  # 反向边容量增加（允许撤销）
            v = parent[v]

        # 重置 parent 数组
        parent = [-1] * len(graph)

    return max_flow


if __name__ == "__main__":
    from doctest import testmod
    testmod()
    print(f"最大流: {ford_fulkerson(graph, source=0, sink=5)}")  # 23
