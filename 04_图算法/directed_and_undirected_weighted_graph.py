# -*- coding: utf-8 -*-

"""

算法实现：04_图算法 / directed_and_undirected_weighted_graph



本文件实现 directed_and_undirected_weighted_graph 相关的算法功能。

"""



from __future__ import annotations



# 导入所需标准库

from collections import deque  # 双端队列，用于 BFS

from math import floor        # 向下取整，用于随机图生成

from random import random    # 随机数生成

from time import time        # 时间测量





# ==========================================================

# 有向图类（DirectedGraph）

# ==========================================================

class DirectedGraph:

    """

    有向图数据结构，使用邻接表存储。

    

    支持的操作：添加顶点/边、DFS、BFS、拓扑排序、环检测等。

    """



    def __init__(self):

        # graph: 字典，键为顶点，值为该顶点指向的所有邻接点（带权重）

        self.graph = {}



    def add_pair(self, u, v, w=1):

        """

        添加一条从 u 指向 v 的有向边，权重为 w（默认1）。

        自动创建不存在的顶点，自动去重。

        """

        if self.graph.get(u):

            if self.graph[u].count([w, v]) == 0:

                self.graph[u].append([w, v])

        else:

            self.graph[u] = [[w, v]]

        if not self.graph.get(v):

            self.graph[v] = []



    def all_nodes(self):

        """返回图中所有顶点列表。"""

        return list(self.graph)



    def remove_pair(self, u, v):

        """删除从 u 指向 v 的边（如果存在）。"""

        if self.graph.get(u):

            for _ in self.graph[u]:

                if _[1] == v:

                    self.graph[u].remove(_)



    def dfs(self, s=-2, d=-1):

        """

        深度优先搜索（DFS）。

        

        Args:

            s: 起始顶点（默认-2表示自动选择第一个顶点）

            d: 目标顶点（默认-1表示遍历全部）

        

        Returns:

            从 s 到 d 的路径顶点列表，若无法到达则返回完整遍历序列

        """

        if s == d:

            return []

        stack = []        # 模拟递归栈

        visited = []      # 已访问顶点记录

        if s == -2:

            s = next(iter(self.graph))

        stack.append(s)

        visited.append(s)

        ss = s



        while True:

            # 检查当前顶点是否有未访问的邻接点

            if len(self.graph[s]) != 0:

                ss = s

                for node in self.graph[s]:

                    if visited.count(node[1]) < 1:

                        if node[1] == d:

                            visited.append(d)

                            return visited

                        else:

                            stack.append(node[1])

                            visited.append(node[1])

                            ss = node[1]

                            break



            # 检查是否所有邻接点均已访问

            if s == ss:

                stack.pop()

                if len(stack) != 0:

                    s = stack[len(stack) - 1]

            else:

                s = ss



            # 检查是否已回到起点

            if len(stack) == 0:

                return visited



    def fill_graph_randomly(self, c=-1):

        """

        随机生成图。

        

        Args:

            c: 顶点数（默认-1表示随机10~10000之间）

        """

        if c == -1:

            c = floor(random() * 10000) + 10

        for i in range(c):

            # 每个顶点最多有100条出边

            for _ in range(floor(random() * 102) + 1):

                n = floor(random() * c) + 1

                if n != i:

                    self.add_pair(i, n, 1)



    def bfs(self, s=-2):

        """

        广度优先搜索（BFS）。

        

        Args:

            s: 起始顶点（默认-2表示自动选择第一个顶点）

        

        Returns:

            从 s 可达的所有顶点列表

        """

        d = deque()

        visited = []

        if s == -2:

            s = next(iter(self.graph))

        d.append(s)

        visited.append(s)

        while d:

            s = d.popleft()

            if len(self.graph[s]) != 0:

                for node in self.graph[s]:

                    if visited.count(node[1]) < 1:

                        d.append(node[1])

                        visited.append(node[1])

        return visited



    def in_degree(self, u):

        """计算顶点 u 的入度。"""

        count = 0

        for x in self.graph:

            for y in self.graph[x]:

                if y[1] == u:

                    count += 1

        return count



    def out_degree(self, u):

        """计算顶点 u 的出度。"""

        return len(self.graph[u])



    def topological_sort(self, s=-2):

        """

        拓扑排序（DFS实现）。

        

        Returns:

            拓扑排序后的顶点序列

        """

        stack = []

        visited = []

        if s == -2:

            s = next(iter(self.graph))

        stack.append(s)

        visited.append(s)

        ss = s

        sorted_nodes = []



        while True:

            # 检查是否有未访问的邻接点

            if len(self.graph[s]) != 0:

                ss = s

                for node in self.graph[s]:

                    if visited.count(node[1]) < 1:

                        stack.append(node[1])

                        visited.append(node[1])

                        ss = node[1]

                        break



            # 检查是否所有邻接点均已访问

            if s == ss:

                sorted_nodes.append(stack.pop())

                if len(stack) != 0:

                    s = stack[len(stack) - 1]

            else:

                s = ss



            # 检查是否已回到起点

            if len(stack) == 0:

                return sorted_nodes



    def cycle_nodes(self):

        """检测图中所有处于环中的顶点。"""

        stack = []

        visited = []

        s = next(iter(self.graph))

        stack.append(s)

        visited.append(s)

        parent = -2

        indirect_parents = []

        ss = s

        on_the_way_back = False

        anticipating_nodes = set()



        while True:

            if len(self.graph[s]) != 0:

                ss = s

                for node in self.graph[s]:

                    # 检测回边形成的环

                    if (visited.count(node[1]) > 0 and node[1] != parent

                            and indirect_parents.count(node[1]) > 0

                            and not on_the_way_back):

                        len_stack = len(stack) - 1

                        while len_stack >= 0:

                            if stack[len_stack] == node[1]:

                                anticipating_nodes.add(node[1])

                                break

                            else:

                                anticipating_nodes.add(stack[len_stack])

                                len_stack -= 1

                    if visited.count(node[1]) < 1:

                        stack.append(node[1])

                        visited.append(node[1])

                        ss = node[1]

                        break



            if s == ss:

                stack.pop()

                on_the_way_back = True

                if len(stack) != 0:

                    s = stack[len(stack) - 1]

            else:

                on_the_way_back = False

                indirect_parents.append(parent)

                parent = s

                s = ss



            if len(stack) == 0:

                return list(anticipating_nodes)



    def has_cycle(self):

        """检测图中是否存在环。"""

        stack = []

        visited = []

        s = next(iter(self.graph))

        stack.append(s)

        visited.append(s)

        parent = -2

        indirect_parents = []

        ss = s

        on_the_way_back = False



        while True:

            if len(self.graph[s]) != 0:

                ss = s

                for node in self.graph[s]:

                    if (visited.count(node[1]) > 0 and node[1] != parent

                            and indirect_parents.count(node[1]) > 0

                            and not on_the_way_back):

                        len_stack_minus_one = len(stack) - 1

                        while len_stack_minus_one >= 0:

                            if stack[len_stack_minus_one] == node[1]:

                                break

                            else:

                                return True

                    if visited.count(node[1]) < 1:

                        stack.append(node[1])

                        visited.append(node[1])

                        ss = node[1]

                        break



            if s == ss:

                stack.pop()

                on_the_way_back = True

                if len(stack) != 0:

                    s = stack[len(stack) - 1]

            else:

                on_the_way_back = False

                indirect_parents.append(parent)

                parent = s

                s = ss



            if len(stack) == 0:

                return False



    def dfs_time(self, s=-2, e=-1):

        """测量从 s 到 e 的 DFS 执行时间（秒）。"""

        begin = time()

        self.dfs(s, e)

        end = time()

        return end - begin



    def bfs_time(self, s=-2):

        """测量从 s 出发的 BFS 执行时间（秒）。"""

        begin = time()

        self.bfs(s)

        end = time()

        return end - begin





# ==========================================================

# 无向图类（Graph）

# ==========================================================

class Graph:

    """

    无向图数据结构，使用邻接表存储。

    

    支持的操作：添加顶点/边、DFS、BFS、环检测等。

    """



    def __init__(self):

        self.graph = {}



    def add_pair(self, u, v, w=1):

        """

        添加一条连接 u 和 v 的无向边，权重为 w（默认1）。

        自动创建不存在的顶点，自动去重。

        """

        # 检查 u 是否存在

        if self.graph.get(u):

            # 如果边已存在则不添加

            if self.graph[u].count([w, v]) == 0:

                self.graph[u].append([w, v])

        else:

            self.graph[u] = [[w, v]]

        # 添加反向边

        if self.graph.get(v):

            if self.graph[v].count([w, u]) == 0:

                self.graph[v].append([w, u])

        else:

            self.graph[v] = [[w, u]]



    def remove_pair(self, u, v):

        """删除连接 u 和 v 的边（如果存在）。"""

        if self.graph.get(u):

            for _ in self.graph[u]:

                if _[1] == v:

                    self.graph[u].remove(_)

        if self.graph.get(v):

            for _ in self.graph[v]:

                if _[1] == u:

                    self.graph[v].remove(_)



    def dfs(self, s=-2, d=-1):

        """

        深度优先搜索（DFS）。

        

        Args:

            s: 起始顶点（默认-2表示自动选择第一个顶点）

            d: 目标顶点（默认-1表示遍历全部）

        

        Returns:

            从 s 到 d 的路径顶点列表

        """

        if s == d:

            return []

        stack = []

        visited = []

        if s == -2:

            s = next(iter(self.graph))

        stack.append(s)

        visited.append(s)

        ss = s



        while True:

            if len(self.graph[s]) != 0:

                ss = s

                for node in self.graph[s]:

                    if visited.count(node[1]) < 1:

                        if node[1] == d:

                            visited.append(d)

                            return visited

                        else:

                            stack.append(node[1])

                            visited.append(node[1])

                            ss = node[1]

                            break



            if s == ss:

                stack.pop()

                if len(stack) != 0:

                    s = stack[len(stack) - 1]

            else:

                s = ss



            if len(stack) == 0:

                return visited



    def fill_graph_randomly(self, c=-1):

        """

        随机生成无向图。

        

        Args:

            c: 顶点数（默认-1表示随机10~10000之间）

        """

        if c == -1:

            c = floor(random() * 10000) + 10

        for i in range(c):

            for _ in range(floor(random() * 102) + 1):

                n = floor(random() * c) + 1

                if n != i:

                    self.add_pair(i, n, 1)



    def bfs(self, s=-2):

        """

        广度优先搜索（BFS）。

        

        Args:

            s: 起始顶点（默认-2表示自动选择第一个顶点）

        

        Returns:

            从 s 可达的所有顶点列表

        """

        d = deque()

        visited = []

        if s == -2:

            s = next(iter(self.graph))

        d.append(s)

        visited.append(s)

        while d:

            s = d.popleft()

            if len(self.graph[s]) != 0:

                for node in self.graph[s]:

                    if visited.count(node[1]) < 1:

                        d.append(node[1])

                        visited.append(node[1])

        return visited



    def degree(self, u):

        """计算顶点 u 的度数（无向图中出度=入度=度数）。"""

        return len(self.graph[u])



    def cycle_nodes(self):

        """检测图中所有处于环中的顶点。"""

        stack = []

        visited = []

        s = next(iter(self.graph))

        stack.append(s)

        visited.append(s)

        parent = -2

        indirect_parents = []

        ss = s

        on_the_way_back = False

        anticipating_nodes = set()



        while True:

            if len(self.graph[s]) != 0:

                ss = s

                for node in self.graph[s]:

                    if (visited.count(node[1]) > 0 and node[1] != parent

                            and indirect_parents.count(node[1]) > 0

                            and not on_the_way_back):

                        len_stack = len(stack) - 1

                        while len_stack >= 0:

                            if stack[len_stack] == node[1]:

                                anticipating_nodes.add(node[1])

                                break

                            else:

                                anticipating_nodes.add(stack[len_stack])

                                len_stack -= 1

                    if visited.count(node[1]) < 1:

                        stack.append(node[1])

                        visited.append(node[1])

                        ss = node[1]

                        break



            if s == ss:

                stack.pop()

                on_the_way_back = True

                if len(stack) != 0:

                    s = stack[len(stack) - 1]

            else:

                on_the_way_back = False

                indirect_parents.append(parent)

                parent = s

                s = ss



            if len(stack) == 0:

                return list(anticipating_nodes)



    def has_cycle(self):

        """检测无向图中是否存在环。"""

        stack = []

        visited = []

        s = next(iter(self.graph))

        stack.append(s)

        visited.append(s)

        parent = -2

        indirect_parents = []

        ss = s

        on_the_way_back = False



        while True:

            if len(self.graph[s]) != 0:

                ss = s

                for node in self.graph[s]:

                    if (visited.count(node[1]) > 0 and node[1] != parent

                            and indirect_parents.count(node[1]) > 0

                            and not on_the_way_back):

                        len_stack_minus_one = len(stack) - 1

                        while len_stack_minus_one >= 0:

                            if stack[len_stack_minus_one] == node[1]:

                                break

                            else:

                                return True

                    if visited.count(node[1]) < 1:

                        stack.append(node[1])

                        visited.append(node[1])

                        ss = node[1]

                        break



            if s == ss:

                stack.pop()

                on_the_way_back = True

                if len(stack) != 0:

                    s = stack[len(stack) - 1]

            else:

                on_the_way_back = False

                indirect_parents.append(parent)

                parent = s

                s = ss



            if len(stack) == 0:

                return False



    def all_nodes(self):

        """返回图中所有顶点列表。"""

        return list(self.graph)



    def dfs_time(self, s=-2, e=-1):

        """测量从 s 到 e 的 DFS 执行时间（秒）。"""

        begin = time()

        self.dfs(s, e)

        end = time()

        return end - begin



    def bfs_time(self, s=-2):

        """测量从 s 出发的 BFS 执行时间（秒）。"""

        begin = time()

        self.bfs(s)

        end = time()

        return end - begin





if __name__ == "__main__":

    # 测试用例：创建有向图

    dg = DirectedGraph()

    for i in range(5):

        dg.add_pair(i, i + 1)

    print("有向图 DFS 遍历结果:", dg.dfs(0))

    print("有向图 BFS 遍历结果:", dg.bfs(0))

    

    # 测试用例：创建无向图

    g = Graph()

    g.add_pair(0, 1)

    g.add_pair(1, 2)

    g.add_pair(2, 0)  # 形成一个环

    print("无向图环检测结果:", g.has_cycle())

    print("无向图 DFS 遍历结果:", g.dfs(0))

