"""
Prim - 最小生成树
==========================================

【算法原理】
贪心算法，每次选择连接已选和未选集合的最小权边。

【时间复杂度】O(V^2) 或 O(E log V)
【空间复杂度】O(V)

【应用场景】
- 城市光钎网络铺设
- 电路板布线
- 道路网络规划

【何时使用】
- 需要连接所有节点成本最低
"""

def prim(graph):
    """
    Prim最小生成树
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
