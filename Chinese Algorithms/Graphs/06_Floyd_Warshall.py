"""
Floyd-Warshall - 全源最短路径
==========================================

【算法原理】
动态规划：
逐步引入中间顶点，更新所有顶点对之间的距离。
dist[i][j][k] = 经过顶点k时i到j的最短距离

【时间复杂度】O(V^3)
【空间复杂度】O(V^2)

【应用场景】
- 需要查询任意两点间距离
- 传递闭包
-  detecting negative cycles
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
    dist = [row[:] for row in graph]  # 复制
    
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    
    return dist


# ---------- Topo Sort ----------
FILES['Chinese Algorithms/Graphs/07_Topological_Sort.py'] = 
Topological Sort - 拓扑排序
==========================================

【问题定义】
对有向无环图(DAG)进行线性排序，
使得所有有向边(u,v)中，u都在v之前。

【应用场景】
- 课程先修关系
- 项目任务调度
- Makefile依赖解析
- 编译器符号表构建
