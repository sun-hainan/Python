"""
Topological Sort - 拓扑排序
==========================================

【问题定义】
对有向无环图(DAG)进行线性排序，
使得所有有向边(u,v)中，u都在v之前。

【应用场景】
- 课程先修关系
- 项目任务调度
- Makefile依赖解析
"""

from collections import deque

def topological_sort(graph):
    """
    拓扑排序 - Kahn算法(BFS)
    
    Args:
        graph: 邻接表 {顶点: [邻接顶点]}
        
    Returns:
        拓扑排序结果
    """
    in_degree = {v: 0 for v in graph}
    for v in graph:
        for neighbor in graph[v]:
            in_degree[neighbor] += 1
    
    queue = deque([v for v in graph if in_degree[v] == 0])
    result = []
    
    while queue:
        vertex = queue.popleft()
        result.append(vertex)
        
        for neighbor in graph[vertex]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return result
