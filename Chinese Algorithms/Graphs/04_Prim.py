"""
Prim - 最小生成树
==========================================

【算法原理】
贪心算法：
1. 从一个顶点开始
2. 每次选择连接已选集合和未选集合的最小权边
3. 直到所有顶点都被选中

【时间复杂度】O(V^2) 或 O(E log V)
【空间复杂度】O(V)

【应用场景】
- 城市光钎网络铺设
- 电路板布线
- 道路网络规划
- 电网建设

【何时使用】
- 需要连接所有节点成本最低
- 网络/交通规划
- 聚类分析

【实际案例】
# 村庄光钎网络建设
# 6个村庄，如何铺设光钎总长度最短？
villages = [
    [0, 6, 1, 5, 0, 0],  # 村庄0到各村的距离
    [6, 0, 5, 0, 3, 0],
    [1, 5, 0, 5, 6, 4],
    [5, 0, 5, 0, 2, 0],
    [0, 3, 6, 2, 0, 6],
    [0, 0, 4, 0, 6, 0]
]
prim(villages)  # 输出最小铺设长度

# 分布式数据库连接
# 如何用最少的光钎连接所有数据中心
"""

def prim(graph):
    """
    Prim最小生成树
    
    Args:
        graph: 邻接矩阵
        
    Returns:
        最小生成树的总权重
    """
    n = len(graph)
    visited = [False] * n
    min_dist = [float('inf')] * n
    min_dist[0] = 0
    result = 0
    
    for _ in range(n):
        u = -1
        for v in range(n):
            if not visited[v]:
                if u == -1 or min_dist[v] < min_dist[u]:
                    u = v
        
        if min_dist[u] == float('inf'):
            break
        
        visited[u] = True
        result += min_dist[u]
        
        for v in range(n):
            if graph[u][v] > 0 and not visited[v]:
                min_dist[v] = min(min_dist[v], graph[u][v])
    
    return result
