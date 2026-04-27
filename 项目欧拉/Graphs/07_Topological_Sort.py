# -*- coding: utf-8 -*-
"""
算法实现：Graphs / 07_Topological_Sort

本文件实现 07_Topological_Sort 相关的算法功能。
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


if __name__ == "__main__":
    # 测试: topological_sort
    result = topological_sort()
    print(result)
