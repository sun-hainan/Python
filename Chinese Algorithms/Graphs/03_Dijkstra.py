"""
Dijkstra - 最短路径算法
==========================================

【算法原理】
贪心 + 最小堆，从源点开始逐步扩展。
每次选择距离最短的未访问顶点。

【时间复杂度】O((V + E) log V)
【空间复杂度】O(V)

【应用场景】
- GPS导航最短路径
- 网络路由
- 航班中转规划

【限制】不能处理负权边
"""

import heapq

def dijkstra(graph, start, end):
    """
    Dijkstra单源最短路径
    
    Args:
        graph: 邻接表 {顶点: [(邻居, 权重)]}
        start: 起始顶点
        end: 目标顶点
        
    Returns:
        start到end的最短距离，找不到返回-1
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
