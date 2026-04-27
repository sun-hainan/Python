# -*- coding: utf-8 -*-

"""

算法实现：04_图算法 / breadth_first_search



本文件实现 breadth_first_search 相关的算法功能。

"""



#!/usr/bin/python



"""

广度优先搜索 (Breadth-First Search, BFS) - 中文注释版

==========================================



算法原理：

    BFS 是一种图/树的遍历算法，从根节点开始，按层次逐层遍历。

    使用队列（FIFO）来保证先访问的节点先被扩展。



与 DFS 的核心区别：

    - BFS：用队列，层层扩展，先访问近的节点

    - DFS：用栈（或递归），一条路走到黑，先访问远的节点



核心概念：

    - visited 集合：记录已访问的节点，避免重复访问

    - queue 队列：待访问的节点，按入队顺序访问



时间复杂度：O(V + E)，V 为顶点数，E 为边数

空间复杂度：O(V)



应用场景：

    - 最短路径（无权图）

    - 层次遍历

    - 查找所有可达节点

"""



from __future__ import annotations

from queue import Queue





class Graph:

    def __init__(self) -> None:

        # 邻接表：顶点 -> 邻接顶点列表

        self.vertices: dict[int, list[int]] = {}



    def print_graph(self) -> None:

        """打印邻接表"""

        for i in self.vertices:

            print(i, " : ", " -> ".join([str(j) for j in self.vertices[i]]))



    def add_edge(self, from_vertex: int, to_vertex: int) -> None:

        """添加有向边"""

        if from_vertex in self.vertices:

            self.vertices[from_vertex].append(to_vertex)

        else:

            self.vertices[from_vertex] = [to_vertex]



    def bfs(self, start_vertex: int) -> set[int]:

        """

        广度优先搜索



        算法步骤：

            1. 将起始顶点加入队列并标记为已访问

            2. 从队列取出一个顶点，访问它

            3. 将该顶点的所有未访问邻接顶点加入队列并标记

            4. 重复直到队列为空



        参数:

            start_vertex: 起始顶点



        返回:

            所有可达顶点的集合



        示例:

            >>> g = Graph()

            >>> g.add_edge(0, 1)

            >>> g.add_edge(0, 2)

            >>> g.add_edge(1, 2)

            >>> g.add_edge(2, 0)

            >>> g.add_edge(2, 3)

            >>> g.add_edge(3, 3)

            >>> sorted(g.bfs(2))

            [0, 1, 2, 3]

        """

        visited = set()  # 已访问顶点集合

        queue: Queue = Queue()  # BFS 用队列



        # 起点入队并标记已访问

        visited.add(start_vertex)

        queue.put(start_vertex)



        while not queue.empty():

            vertex = queue.get()  # 出队



            # 检查所有邻接顶点

            for adjacent_vertex in self.vertices[vertex]:

                if adjacent_vertex not in visited:

                    queue.put(adjacent_vertex)  # 入队

                    visited.add(adjacent_vertex)  # 标记



        return visited





if __name__ == "__main__":

    from doctest import testmod

    testmod(verbose=True)



    g = Graph()

    g.add_edge(0, 1)

    g.add_edge(0, 2)

    g.add_edge(1, 2)

    g.add_edge(2, 0)

    g.add_edge(2, 3)

    g.add_edge(3, 3)



    g.print_graph()

    # 0  :  1 -> 2

    # 1  :  2

    # 2  :  0 -> 3

    # 3  :  3



    print(f"BFS 从顶点 2 开始: {sorted(g.bfs(2))}")

