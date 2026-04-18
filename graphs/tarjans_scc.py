"""
Tarjan 算法 - 强连通分量 - 中文注释版
==========================================

强连通分量定义：
    在有向图中，如果两个顶点 u 和 v 可以互相到达，
    则称 u 和 v 属于同一个强连通分量（SCC）。

Tarjan 算法核心思想：
    1. 使用 DFS 遍历图
    2. 每个顶点有两个属性：
       - index[v]：顶点 v 首次被访问的时间戳
       - lowlink[v]：从 v 出发能回溯到的最小时间戳
    3. 当 lowlink[v] == index[v] 时，v 是某个 SCC 的根

算法步骤：
    1. DFS 中将顶点入栈
    2. 更新 lowlink
    3. 如果 lowlink[v] == index[v]，弹出栈得到一个 SCC

时间复杂度：O(V + E)
空间复杂度：O(V)
"""

from collections import deque
from typing import List


def tarjan(g: List[List[int]]) -> List[List[int]]:
    """
    Tarjan 算法求强连通分量

    参数:
        g: 邻接表，格式 [顶点0的邻居列表, 顶点1的邻居列表, ...]

    返回:
        强连通分量列表，每个 SCC 是顶点索引的列表

    示例:
        >>> tarjan([[2, 3, 4], [2, 3, 4], [0, 1, 3], [0, 1, 2], [1]])
        [[4, 3, 1, 2, 0]]
        >>> tarjan([[], [], [], []])
        [[0], [1], [2], [3]]
    """
    n = len(g)
    stack: deque[int] = deque()
    on_stack = [False] * n
    index_of = [-1] * n          # 每个节点的访问次序（时间戳）
    lowlink_of = [-1] * n        # 每个节点能回溯到的最小时间戳

    def strong_connect(v: int, idx: int, components: List[List[int]]) -> int:
        """
        DFS 递归求强连通分量
        返回下一个可用的时间戳
        """
        index_of[v] = idx        # 记录访问时间戳
        lowlink_of[v] = idx      # 初始化为自己的时间戳
        idx += 1

        stack.append(v)
        on_stack[v] = True

        # 遍历所有邻居
        for w in g[v]:
            if index_of[w] == -1:
                # w 未访问，递归 DFS
                idx = strong_connect(w, idx, components)
                lowlink_of[v] = min(lowlink_of[w], lowlink_of[v])
            elif on_stack[w]:
                # w 在栈中，说明 w 是 v 的祖先，更新 lowlink
                lowlink_of[v] = min(lowlink_of[w], lowlink_of[v])

        # 如果 v 是 SCC 的根，弹出栈得到一个 SCC
        if lowlink_of[v] == index_of[v]:
            component = []
            w = stack.pop()
            on_stack[w] = False
            component.append(w)
            while w != v:
                w = stack.pop()
                on_stack[w] = False
                component.append(w)
            components.append(component)

        return idx

    components: List[List[int]] = []
    for v in range(n):
        if index_of[v] == -1:
            strong_connect(v, 0, components)

    return components


def create_graph(n: int, edges: List[tuple[int, int]]) -> List[List[int]]:
    """
    根据边列表创建邻接表

    示例:
        >>> create_graph(7, [(0,1), (0,3), (1,2), (2,0), (3,4), (4,5), (4,6)])
        [[1, 3], [2], [0], [4], [5, 6], [], []]
    """
    g: List[List[int]] = [[] for _ in range(n)]
    for u, v in edges:
        g[u].append(v)
    return g


if __name__ == "__main__":
    n_vertices = 7
    source = [0, 0, 1, 2, 3, 3, 4, 4, 6]
    target = [1, 3, 2, 0, 1, 4, 5, 6, 5]
    edges = list(zip(source, target))
    g = create_graph(n_vertices, edges)

    print(f"强连通分量: {tarjan(g)}")
    # 预期: [[5], [6], [4], [3, 2, 1, 0]]
