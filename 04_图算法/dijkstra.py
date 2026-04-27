# -*- coding: utf-8 -*-
"""
算法实现：04_图算法 / dijkstra

本文件实现 dijkstra 相关的算法功能。
"""

import heapq


def dijkstra(graph, start, end):
    """
    Dijkstra 最短路径算法

    参数:
        graph: 邻接表，格式 {顶点: [[邻居, 权重], ...]}
        start: 起始顶点
        end: 目标顶点

    返回:
        从 start 到 end 的最短路径长度，未找到返回 -1

    示例:
        >>> dijkstra(G, "E", "C")
        6
        >>> dijkstra(G2, "E", "F")
        3
    """
    # (从源点到该顶点的总距离, 顶点)
    heap = [(0, start)]
    visited = set()

    while heap:
        (cost, u) = heapq.heappop(heap)  # 弹出最短距离的顶点

        if u in visited:
            continue  # 已访问过，跳过
        visited.add(u)

        # 找到目标顶点
        if u == end:
            return cost

        # 遍历所有邻居
        for v, c in graph[u]:
            if v in visited:
                continue
            next_item = cost + c
            heapq.heappush(heap, (next_item, v))

    return -1  # 不可达


# ============== 示例图 ==============
#     A -- 2 --> B
#     |          |
#     5          1
#     |          v
#     C <-- 3 -- F
#
# G 的邻接表表示：
G = {
    "A": [["B", 2], ["C", 5]],
    "B": [["A", 2], ["D", 3], ["E", 1], ["F", 1]],
    "C": [["A", 5], ["F", 3]],
    "D": [["B", 3]],
    "E": [["B", 4], ["F", 3]],
    "F": [["C", 3], ["E", 3]],
}

if __name__ == "__main__":
    import doctest
    doctest.testmod()

    print(f"E 到 C 的最短距离: {dijkstra(G, 'E', 'C')}")  # 输出: 6
