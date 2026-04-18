"""
Floyd-Warshall - 全源最短路径
==========================================

【算法原理】
动态规划，逐步引入中间顶点，更新所有顶点对之间的距离。

【时间复杂度】O(V^3)
【空间复杂度】O(V^2)

【应用场景】
- 任意两点间最短距离查询
- 传递闭包检测
- 检测负环
- 地图导航（预计算所有距离）

【何时使用】
- 需要频繁查询任意两点间距离
- V <= 500（复杂度O(V^3)）
- 预计算所有路径距离

【实际案例】
# 城市间最短距离查询系统
# 预计算全国所有城市间的最短距离
city_dist = [
    [0, 30, 60, 100],
    [30, 0, 50, 40],
    [60, 50, 0, 20],
    [100, 40, 20, 0]
]
floyd_warshall(city_dist)  # 输出任意两城市最短距离

# 判断社交网络中的关系
# 任意两人是否连通？需要几度人脉？
social = [
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
    [1, 0, 0, 0]
]
floyd_warshall(social)  # 找出所有人脉距离
"""

def floyd_warshall(graph):
    """
    Floyd-Warshall全源最短路径
    
    Args:
        graph: 邻接矩阵
        
    Returns:
        所有顶点对之间的最短距离矩阵
    """
    n = len(graph)
    dist = [row[:] for row in graph]
    
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    
    return dist
