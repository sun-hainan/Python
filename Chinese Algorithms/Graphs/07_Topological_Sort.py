"""
Topological Sort - 拓扑排序
==========================================

【问题定义】
对DAG进行线性排序，使得所有有向边(u,v)中u都在v之前。

【时间复杂度】O(V + E)
【空间复杂度】O(V)

【应用场景】
- 大学课程先修关系
- 项目任务调度
- Makefile依赖解析
- 做菜顺序安排

【何时使用】
- 有依赖关系的任务排序
"""

from collections import deque

def topological_sort(graph):
    """
    拓扑排序 - Kahn算法
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
