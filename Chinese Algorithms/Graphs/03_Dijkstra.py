"""
Dijkstra - 最短路径算法
==========================================

【算法原理】
贪心+最小堆，每次选择距离最短的未访问顶点。

【时间复杂度】O((V + E) log V)
【空间复杂度】O(V)

【应用场景】
- GPS导航最短路径
- 网络路由（OSPF协议）
- 航班/铁路中转规划
- 游戏地图寻路

【何时使用】
- 带权图最短路径
- 正权边
"""

import heapq

def dijkstra(graph, start, end):
    """
    Dijkstra最短路径
    """
    heap = [(0, start)]
    visited = set()
    while heap:
        dist, vertex = heapq.heappop(heap)
        if vertex in visited:
            continue
        visited.add(vertex)
        if vertex == end:
            return dist
        for neighbor, weight in graph.get(vertex, []):
            if neighbor not in visited:
                heapq.heappush(heap, (dist + weight, neighbor))
    return -1
