# -*- coding: utf-8 -*-
"""
算法实现：Graphs / 01_BFS

本文件实现 01_BFS 相关的算法功能。
"""

from collections import deque

def bfs(graph, start):
    """
    广度优先搜索
    """
    visited = {start}
    queue = deque([start])
    result = []
    while queue:
        vertex = queue.popleft()
        result.append(vertex)
        for neighbor in graph.get(vertex, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return result


if __name__ == "__main__":
    # 测试: bfs
    result = bfs()
    print(result)
