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
        # 选择未访问的最小距离顶点
        u = -1
        for v in range(n):
            if not visited[v]:
                if u == -1 or min_dist[v] < min_dist[u]:
                    u = v
        
        if min_dist[u] == float('inf'):
            break
        
        visited[u] = True
        result += min_dist[u]
        
        # 更新邻居顶点的距离
        for v in range(n):
            if graph[u][v] > 0 and not visited[v]:
                min_dist[v] = min(min_dist[v], graph[u][v])
    
    return result


# ---------- Kruskal ----------
FILES['Chinese Algorithms/Graphs/05_Kruskal.py'] = 
Kruskal - 最小生成树
==========================================

【算法原理】
贪心 + 并查集：
1. 将所有边按权重排序
2. 依次选择最小边(不成环)
3. 直到选中V-1条边

【时间复杂度】O(E log E)
【空间复杂度】O(V)

【应用场景】与Prim相同
