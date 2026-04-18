"""
BFS - 广度优先搜索
==========================================

【算法原理】
使用队列，按层次遍历。先访问近的节点，再访问远的节点。

【时间复杂度】O(V + E)
【空间复杂度】O(V)

【应用场景】
- 最短路径(无权图)
- 层次遍历
- 社交网络好友推荐
"""

from collections import deque

def bfs(graph, start):
    """
    广度优先搜索
    
    Args:
        graph: 邻接表 {顶点: [邻接顶点]}
        start: 起始顶点
        
    Returns:
        从start可达的所有顶点
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
