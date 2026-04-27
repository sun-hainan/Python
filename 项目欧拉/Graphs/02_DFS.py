# -*- coding: utf-8 -*-
"""
算法实现：Graphs / 02_DFS

本文件实现 02_DFS 相关的算法功能。
"""

def dfs(graph, start, visited=None):
    """
    深度优先搜索
    """
    if visited is None:
        visited = set()
    visited.add(start)
    result = [start]
    for neighbor in graph.get(start, []):
        if neighbor not in visited:
            result.extend(dfs(graph, neighbor, visited))
    return result


if __name__ == "__main__":
    # 测试: dfs
    result = dfs()
    print(result)
