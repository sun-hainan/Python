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
- 网络路由（OSPF协议）
- 航班/铁路中转规划
- 游戏地图寻路

【何时使用】
- 带权图最短路径
- 正权边（非负权重）
- 单源最短路径
- 实时路径规划

【实际案例】
# 导航地图 - 从家到公司的最短路径
city_map = {
    "家": [("地铁站", 10), ("公交站", 5)],
    "地铁站": [("公司", 20), ("公交站", 3)],
    "公交站": [("公司", 15)],
    "公司": []
}
dijkstra(city_map, "家", "公司")  # 输出最短距离

# 网络延迟最小路径
# 服务器A到服务器F的最快路径
network = {
    "A": [("B", 4), ("C", 2)],
    "B": [("C", 1), ("D", 5)],
    "C": [("D", 8), ("E", 10)],
    "D": [("E", 2), ("F", 3)],
    "E": [("F", 6)]
}
dijkstra(network, "A", "F")  # 输出最小延迟
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
