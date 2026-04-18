"""
DFS - 深度优先搜索
==========================================

【算法原理】
使用栈(或递归)，一条路走到黑，再回溯探索其他路径。

【时间复杂度】O(V + E)
【空间复杂度】O(V)

【应用场景】
- 走迷宫求解
- 全排列枚举
- 连通分量检测
- 拓扑排序

【何时使用】
- 找所有可能路径
- 连通分量分析
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
