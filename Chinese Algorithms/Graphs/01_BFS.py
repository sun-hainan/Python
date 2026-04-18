"""
BFS - 广度优先搜索
==========================================

【算法原理】
使用队列，按层次遍历。先访问近的节点，再访问远的节点。

【时间复杂度】O(V + E)
【空间复杂度】O(V)

【应用场景】
- 社交网络好友推荐（2度人脉）
- GPS无权图最短路径
- 迷宫最短路径
- 层次遍历文件系统

【何时使用】
- 无权图最短路径
- 层次遍历
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
