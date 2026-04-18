"""
Dijkstra 最短路径算法 - 中文注释版
==========================================

算法原理：
    Dijkstra 算法用于在带权图中找到从单个源点到所有其他顶点的最短路径。
    核心思想：贪心 + 优先队列（最小堆）

    每一步都选择当前已知最短距离最小的未访问顶点，
    然后更新该顶点的邻居的最短距离。

算法步骤：
    1. 初始化：源点距离为 0，其他顶点距离为无穷大
    2. 使用最小堆存储 (距离, 顶点) 对
    3. 弹出距离最小的未访问顶点
    4. 如果该顶点是目标顶点，返回距离
    5. 更新该顶点所有邻居的距离（如果通过它更近）
    6. 重复直到堆为空或找到目标

时间复杂度：O((V + E) * log V)，使用最小堆
空间复杂度：O(V)

适用条件：
    - 正权边图（必须！负权边会导致错误结果）
    - 单源最短路径

对比 Bellman-Ford：
    - Dijkstra：O((V+E) log V)，但不能处理负权边
    - Bellman-Ford：O(VE)，可以处理负权边，能检测负环
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
