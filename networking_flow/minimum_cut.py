"""
最小割 (Minimum Cut) - 中文注释版
==========================================

割（Cut）的定义：
    在网络流中，"割"是将图的顶点分成两个集合 S 和 T，
    其中源点 s 在 S 集合，汇点 t 在 T 集合。
    割的容量 = 所有从 S 到 T 的边的容量之和。

最小割定理（Max-Flow Min-Cut Theorem）：
    最大流的流量 = 最小割的容量

最小割的实际意义：
    - 找到网络中"最薄弱"的环节
    - 删除这些边就能切断源点到汇点的所有路径

如何找最小割：
    1. 先用 Ford-Fulkerson 求最大流
    2. 最大流算法结束后，在残余网络中
    3. 从源点出发，沿残余网络中还有正向容量的边可达的所有顶点 -> 集合 S
    4. 所有从 S 指向 T 的边（原始边有容量但现在残余容量为0）就是最小割边

应用场景：
    - 网络可靠性分析
    - 交通运输瓶颈识别
    - 金融风险传播
    - 图像分割（计算机视觉）
"""

from __future__ import annotations
from collections import deque


test_graph = [
    [0, 16, 13, 0, 0, 0],
    [0, 0, 10, 12, 0, 0],
    [0, 4, 0, 0, 14, 0],
    [0, 0, 9, 0, 0, 20],
    [0, 0, 0, 7, 0, 4],
    [0, 0, 0, 0, 0, 0],
]


def bfs(graph, s, t, parent):
    """
    BFS 找增广路径

    返回:
        True 如果从 s 可以到达 t
    """
    visited = [False] * len(graph)
    queue = deque([s])
    visited[s] = True

    while queue:
        u = queue.popleft()
        for ind in range(len(graph[u])):
            if not visited[ind] and graph[u][ind] > 0:
                queue.append(ind)
                visited[ind] = True
                parent[ind] = u

    return visited[t]


def mincut(graph, source, sink):
    """
    求最小割边

    参数:
        graph: 邻接矩阵
        source: 源点
        sink: 汇点

    返回:
        最小割边的列表 [(起点, 终点), ...]

    示例:
        >>> mincut(test_graph, source=0, sink=5)
        [(1, 3), (4, 3), (4, 5)]
    """
    parent = [-1] * len(graph)
    max_flow = 0
    res = []
    temp = [row[:] for row in graph]  # 保存原始图

    # 1. 先求最大流（使用 Ford-Fulkerson）
    while bfs(graph, source, sink, parent):
        path_flow = float("inf")
        s = sink

        # 找路径上最小容量
        while s != source:
            path_flow = min(path_flow, graph[parent[s]][s])
            s = parent[s]

        max_flow += path_flow
        v = sink

        # 更新残余网络
        while v != source:
            u = parent[v]
            graph[u][v] -= path_flow
            graph[v][u] += path_flow
            v = parent[v]

    # 2. 在残余网络中找从源可达的顶点 -> 集合 S
    # 残余网络中 graph[i][j] > 0 表示从 i 到 j 还有容量
    visited = [False] * len(graph)
    queue = deque([source])
    visited[source] = True

    while queue:
        u = queue.popleft()
        for v in range(len(graph)):
            if not visited[v] and graph[u][v] > 0:
                visited[v] = True
                queue.append(v)

    # 3. 找所有从 S 到 T 的边（即最小割边）
    # 条件：u 在 S (visited[u]=True)，v 在 T (visited[v]=False)
    # 且原始边 temp[u][v] > 0，当前残余容量 graph[u][v] == 0
    for i in range(len(graph)):
        for j in range(len(graph[0])):
            if graph[i][j] == 0 and temp[i][j] > 0 and visited[i] and not visited[j]:
                res.append((i, j))

    print(f"最大流 = {max_flow}")
    return res


if __name__ == "__main__":
    result = mincut(test_graph, source=0, sink=5)
    print(f"最小割边: {result}")
    # 预期: [(1, 3), (4, 3), (4, 5)]
