# -*- coding: utf-8 -*-

"""

算法实现：04_图算法 / check_bipatrite



本文件实现 check_bipatrite 相关的算法功能。

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

