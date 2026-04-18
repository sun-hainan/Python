"""
Floyd-Warshall - 全源最短路径
==========================================

【算法原理】
动态规划，逐步引入中间顶点更新所有顶点对距离。

【时间复杂度】O(V^3)
【空间复杂度】O(V^2)

【应用场景】
- 任意两点间距离查询
- 社交网络关系分析
- 传递闭包检测

【何时使用】
- 需要频繁查询任意两点间距离
- V <= 500
"""

def floyd_warshall(graph):
    """
    Floyd-Warshall全源最短路径
    """
    n = len(graph)
    dist = [row[:] for row in graph]
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    return dist
