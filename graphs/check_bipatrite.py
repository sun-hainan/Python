"""
二分图判定 (Bipartite Graph Check) - 中文注释版
==========================================

二分图定义：
    一个图可以分成两个互不相交的顶点集合 U 和 V，
    使得图中每条边都连接 U 中的一个顶点和 V 中的一个顶点。
    换句话说：图中不存在奇环。

判断方法：
    图 G 是二分图 ⟺ 图 G 中所有环的长度都是偶数

核心思想：图的二染色
    - 用 BFS 或 DFS 遍历图
    - 相邻顶点必须染不同颜色
    - 如果发现相邻顶点颜色相同，则不是二分图

应用场景：
    - 稳定婚姻匹配
    - 任务分配（二分图匹配）
    - 平面地图着色
    - 二分网络
"""

from __future__ import annotations
from collections import defaultdict, deque


def is_bipartite_dfs(graph: dict) -> bool:
    """
    二分图判定 - DFS 版本

    参数:
        graph: 邻接表，格式 {顶点: [邻居列表]}

    返回:
        True 如果是二分图，False 否则

    示例:
        >>> is_bipartite_dfs({0: [1, 2], 1: [0, 3], 2: [0, 4]})
        True
        >>> is_bipartite_dfs({0: [1, 2], 1: [0, 3], 2: [0, 1]})
        False
    """
    visited = defaultdict(lambda: -1)  # -1=未访问, 0=颜色A, 1=颜色B

    def depth_first_search(node: int, color: int) -> bool:
        if visited[node] == -1:
            visited[node] = color
            if node not in graph:
                return True
            for neighbor in graph[node]:
                if not depth_first_search(neighbor, 1 - color):
                    return False
            return visited[node] == color
        return True

    for node in graph:
        if visited[node] == -1:
            if not depth_first_search(node, 0):
                return False
    return True


def is_bipartite_bfs(graph: dict) -> bool:
    """
    二分图判定 - BFS 版本

    BFS 思路：
        1. 从任意未访问顶点开始，染成颜色 0
        2. 将其所有邻居染成颜色 1
        3. 将邻居的邻居染成颜色 0
        4. 重复...
        5. 如果发现邻居已被染成相同颜色，则不是二分图

    示例:
        >>> is_bipartite_bfs({0: [1, 2], 1: [0, 3], 2: [0, 4]})
        True
        >>> is_bipartite_bfs({0: [1, 2], 1: [0, 2], 2: [0, 1]})
        False
    """
    visited = defaultdict(lambda: -1)

    for node in graph:
        if visited[node] == -1:
            queue = deque([node])
            visited[node] = 0

            while queue:
                curr = queue.popleft()
                if curr not in graph:
                    continue
                for neighbor in graph[curr]:
                    if visited[neighbor] == -1:
                        visited[neighbor] = 1 - visited[curr]
                        queue.append(neighbor)
                    elif visited[neighbor] == visited[curr]:
                        return False

    return True


if __name__ == "__main__":
    import doctest

    # 测试用例
    print("=== 二分图测试 ===")

    # 示例 1：奇环
    g1 = {0: [1, 2], 1: [0, 2], 2: [0, 1]}  # 三角形，有奇环
    print(f"三角形图 (有奇环): 二分图? {is_bipartite_dfs(g1)}")  # False

    # 示例 2：偶环
    g2 = {0: [1, 2], 1: [0, 3], 2: [0, 4], 3: [1, 4], 4: [2, 3]}  # 四边形
    print(f"四边形图 (偶环): 二分图? {is_bipartite_dfs(g2)}")  # True

    # 示例 3：链
    g3 = {0: [1], 1: [0, 2], 2: [1]}
    print(f"链式图: 二分图? {is_bipartite_dfs(g3)}")  # True

    doctest.testmod()
