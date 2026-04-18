"""
BFS - 广度优先搜索
==========================================

【算法原理】
使用队列，按层次遍历。先访问近的节点，再访问远的节点。

【时间复杂度】O(V + E)
【空间复杂度】O(V)

【应用场景】
- 社交网络好友推荐（共同好友）
- GPS最短路径（无权图）
- 迷宫最短路径
- 层次遍历（文件系统）

【何时使用】
- 求最短路径（无权图）
- 层次遍历
- 找所有可达节点
- 社交网络关系分析

【实际案例】
# 朋友圈好友推荐
# 你认识A，A认识B，B认识C
# BFS找到你所有2度好友（朋友的朋友）
network = {
    "你": ["A", "B"],
    "A": ["你", "C", "D"],
    "B": ["你", "E", "F"],
    "C": ["A", "G"],
    "D": ["A"],
    "E": ["B", "H"]
}
bfs(network, "你")  # 逐层扩展，找到所有认识的人

# 拼写检查（编辑距离的BFS应用）
# 找出所有与目标词距离1的词
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
