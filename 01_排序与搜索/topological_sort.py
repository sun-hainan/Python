# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / topological_sort

本文件实现 topological_sort 相关的算法功能。
"""

#     a
#    / \
#   b  c
#  / \
# d  e
edges: dict[str, list[str]] = {
    "a": ["c", "b"],
    "b": ["d", "e"],
    "c": [],
    "d": [],
    "e": [],
}
vertices: list[str] = ["a", "b", "c", "d", "e"]



# topological_sort 函数实现
def topological_sort(start: str, visited: list[str], sort: list[str]) -> list[str]:
    """Perform topological sort on a directed acyclic graph."""
    current = start
    # add current to visited
    visited.append(current)
    neighbors = edges[current]
    for neighbor in neighbors:
    # 遍历循环
        # if neighbor not in visited, visit
        if neighbor not in visited:
    # 条件判断
            sort = topological_sort(neighbor, visited, sort)
    # if all neighbors visited add current to sort
    sort.append(current)
    # if all vertices haven't been visited select a new one to visit
    if len(visited) != len(vertices):
    # 条件判断
        for vertice in vertices:
    # 遍历循环
            if vertice not in visited:
    # 条件判断
                sort = topological_sort(vertice, visited, sort)
    # return sort
    return sort
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    sort = topological_sort("a", [], [])
    print(sort)
