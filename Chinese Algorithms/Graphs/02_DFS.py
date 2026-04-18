"""
DFS - 深度优先搜索
==========================================

【算法原理】
使用栈(或递归)，一条路走到黑，再回溯探索其他路径。

【时间复杂度】O(V + E)
【空间复杂度】O(V)

【应用场景】
- 路径搜索
- 连通分量
- 拓扑排序
- 迷宫求解
"""

def dfs(graph, start, visited=None):
    """
    深度优先搜索(递归版)
    
    Args:
        graph: 邻接表 {顶点: [邻接顶点]}
        start: 起始顶点
        visited: 已访问顶点集合
        
    Returns:
        从start可达的所有顶点
    """
    if visited is None:
        visited = set()
    
    visited.add(start)
    result = [start]
    
    for neighbor in graph.get(start, []):
        if neighbor not in visited:
            result.extend(dfs(graph, neighbor, visited))
    
    return result


# ---------- Dijkstra ----------
FILES['Chinese Algorithms/Graphs/03_Dijkstra.py'] = 
Dijkstra - 最短路径算法
==========================================

【算法原理】
贪心 + 最小堆，从源点开始逐步扩展，
每次选择距离最短的未访问顶点。

【时间复杂度】O((V + E) log V)
【空间复杂度】O(V)

【应用场景】
- GPS导航最短路径
- 网络路由
- 航班中转规划

【限制】不能处理负权边
