"""
深度优先搜索 (Depth-First Search, DFS) - 中文注释版
==========================================

算法原理：
    DFS 是一种图/树的遍历算法，沿着一条路径尽可能深入，直到不能再深入为止，
    然后回溯到上一个节点，继续探索其他路径。

与 BFS 的核心区别：
    - BFS：用队列，层层扩展，先访问近的节点（像水波扩散）
    - DFS：用栈（或递归），一条路走到黑（像走迷宫）

实现方式：
    - 递归实现：代码简洁，但递归深度受限于系统栈大小
    - 迭代实现（栈）：避免递归深度限制

核心概念：
    - explored 集合：记录已访问的节点
    - stack 栈：待访问的节点，后进先出

时间复杂度：O(V + E)，V 为顶点数，E 为边数
空间复杂度：O(V)

应用场景：
    - 拓扑排序
    - 连通分量
    - 路径搜索
    - 回溯算法基础
"""

from __future__ import annotations


def depth_first_search(graph: dict, start: str) -> set[str]:
    """
    深度优先搜索（非递归实现，使用栈）

    算法步骤：
        1. 将起始顶点加入栈并标记已访问
        2. 从栈弹出一个顶点（后进先出）
        3. 访问该顶点，将未访问的邻接顶点入栈
        4. 重复直到栈为空

    与 BFS 的区别：
        1. 用栈（pop）代替队列（pop(0)）
        2. 将邻接顶点直接加入栈，而不是按顺序探索

    参数:
        graph: 有向图，以字典表示（key=顶点，value=邻接顶点列表）
        start: 起始顶点

    返回:
        所有可达顶点的集合

    示例:
        >>> input_G = {
        ...     "A": ["B", "C", "D"], "B": ["A", "D", "E"],
        ...     "C": ["A", "F"], "D": ["B", "D"], "E": ["B", "F"],
        ...     "F": ["C", "E", "G"], "G": ["F"]
        ... }
        >>> sorted(depth_first_search(input_G, "A"))
        ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    """
    explored, stack = set([start]), [start]

    while stack:
        v = stack.pop()  # 弹出栈顶元素（后进先出）
        explored.add(v)

        # 逆序添加邻接顶点，使结果顺序与递归版一致
        for adj in reversed(graph[v]):
            if adj not in explored:
                stack.append(adj)

    return explored


# 示例图
G = {
    "A": ["B", "C", "D"],
    "B": ["A", "D", "E"],
    "C": ["A", "F"],
    "D": ["B", "D"],
    "E": ["B", "F"],
    "F": ["C", "E", "G"],
    "G": ["F"],
}


if __name__ == "__main__":
    import doctest
    doctest.testmod()
    print(f"DFS 从 A 开始: {sorted(depth_first_search(G, 'A'))}")
