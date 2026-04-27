# -*- coding: utf-8 -*-

"""

算法实现：参数算法 / parameterized_backtracking



本文件实现 parameterized_backtracking 相关的算法功能。

"""



from typing import List, Optional, Tuple





class ParameterizedBacktracking:

    """参数化回溯算法"""



    def __init__(self, k: int):

        """

        参数：

            k: 参数（时间/深度限制）

        """

        self.k = k

        self.solutions = []

        self.nodes_visited = 0



    def solve_vertex_cover(self, graph: List[List[int]], k: int) -> List[List[int]]:

        """

        参数化顶点覆盖求解



        参数：

            graph: 邻接表

            k: 允许的顶点数



        返回：所有大小 ≤ k 的顶点覆盖

        """

        self.solutions = []

        self.nodes_visited = 0



        vertices = list(range(len(graph)))



        # 从空覆盖开始

        current_cover = []



        self._backtrack_vc(graph, vertices, current_cover, k, 0)



        return self.solutions



    def _backtrack_vc(self, graph: List[List[int]],

                    vertices: List[int],

                    current: List[int],

                    k: int,

                    start_idx: int) -> None:

        """回溯搜索"""

        self.nodes_visited += 1



        # 如果已经有k个顶点，检查是否覆盖所有边

        if len(current) == k:

            if self._is_cover(graph, current):

                self.solutions.append(current.copy())

            return



        # 剪枝：如果剩余顶点数不够

        remaining = k - len(current)

        if remaining <= 0:

            return



        # 尝试添加顶点

        for i in range(start_idx, len(vertices)):

            if len(current) < k:

                current.append(vertices[i])

                self._backtrack_vc(graph, vertices, current, k, i + 1)

                current.pop()  # 撤销



    def _is_cover(self, graph: List[List[int]], cover: List[int]) -> bool:

        """检查是否覆盖所有边"""

        n = len(graph)

        covered = set(cover)



        for u in range(n):

            for v in graph[u]:

                if u not in covered and v not in covered:

                    return False



        return True



    def solve_k_path(self, graph: List[List[int]], k: int) -> List[int]:

        """

        找长度 ≤ k 的路径



        返回：路径或None

        """

        n = len(graph)

        self.nodes_visited = 0



        for start in range(n):

            path = [start]

            visited = {start}



            if self._dfs_path(graph, start, k - 1, visited, path):

                return path



        return []



    def _dfs_path(self, graph: List[List[int]],

                 u: int,

                 remaining: int,

                 visited: set,

                 path: List[int]) -> bool:

        """DFS寻找路径"""

        self.nodes_visited += 1



        if remaining == 0:

            return True



        for v in graph[u]:

            if v not in visited:

                visited.add(v)

                path.append(v)



                if self._dfs_path(graph, v, remaining - 1, visited, path):

                    return True



                path.pop()

                visited.remove(v)



        return False





def parameterized_backtracking_analysis():

    """参数化回溯分析"""

    print("=== 参数化回溯分析 ===")

    print()

    print("技术：")

    print("  - 深度优先搜索")

    print("  - 剪枝减少搜索")

    print("  - Branch and bound")

    print()

    print("复杂度：")

    print("  - O(k! × n) 最坏情况")

    print("  - 实际更快（剪枝）")

    print()

    print("应用：")

    print("  - 顶点覆盖")

    print("  - 路径问题")

    print("  - 约束满足")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 参数化回溯测试 ===\n")



    # 测试顶点覆盖

    graph = [[1, 2], [0, 2], [0, 1, 3], [2]]

    k = 2



    solver = ParameterizedBacktracking(k)



    covers = solver.solve_vertex_cover(graph, k)



    print(f"图: {graph}")

    print(f"k = {k}")

    print(f"找到覆盖: {covers}")

    print(f"访问节点数: {solver.nodes_visited}")

    print()



    # 测试路径

    k_path = 3

    path = solver.solve_k_path(graph, k_path)



    print(f"找长度≤{k_path}的路径:")

    print(f"  结果: {path}")



    print()

    parameterized_backtracking_analysis()



    print()

    print("说明：")

    print("  - 参数化回溯是FPT的基础")

    print("  - 适合小k的情况")

    print("  - 剪枝关键")

