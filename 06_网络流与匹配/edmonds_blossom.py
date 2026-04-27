# -*- coding: utf-8 -*-

"""

算法实现：06_网络流与匹配 / edmonds_blossom



本文件实现 edmonds_blossom 相关的算法功能。

"""



from collections import deque





class BlossomAlgorithm:

    """Edmonds Blossom 一般图最大匹配算法"""

    

    def __init__(self, n):

        self.n = n  # 顶点数

        self.adj = [[] for _ in range(n)]  # 邻接表

        self.match = [-1] * n  # 匹配：match[v] = u 或 -1

        self.base = list(range(n))  # 每个顶点的花基

        self.p = [-1] * n  # BFS树中的父节点

        self.used = [False] * n  # 标记是否访问

        self.qq = []  # BFS队列

        self.qhead = 0

    

    def add_edge(self, u, v):

        """添加无向边"""

        self.adj[u].append(v)

        self.adj[v].append(u)

    

    def lca(self, a, b):

        """找两个顶点的最低公共祖先（沿匹配交替树的路径）"""

        used = [False] * self.n

        

        while True:

            a = self.base[a]

            used[a] = True

            if self.match[a] == -1:

                break

            a = self.p[self.match[a]]

        

        while True:

            b = self.base[b]

            if used[b]:

                return b

            b = self.p[self.match[b]]

    

    def mark_path(self, v, b, child):

        """标记从 v 到 base b 的路径上的顶点（用于花收缩）"""

        while self.base[v] != b:

            self.p[v] = child

            child = self.base[self.match[v]]

            used_v = self.used[v] = True

            used_child = self.used[child] = True

            

            # 沿着交替树向上

            v = self.p[self.match[v]]

            

            while self.base[v] != b:

                self.p[v] = child

                child = self.base[v]

                v = self.p[self.match[v]]

            

            self.base[v] = self.base[child] = b

    

    def find_path(self, root):

        """从根节点开始找增广路"""

        self.used = [False] * self.n

        self.p = [-1] * self.n

        for i in range(self.n):

            self.base[i] = i

        

        self.qq = [root]

        self.qhead = 0

        self.used[root] = True

        

        while self.qhead < len(self.qq):

            v = self.qq[self.qhead]

            self.qhead += 1

            

            for u in self.adj[v]:

                # 跳过自环和已匹配的边

                if self.base[v] == self.base[u] or self.match[v] == u:

                    continue

                

                # 发现增广路

                if u == root or (self.match[u] != -1 and self.p[self.match[u]] != -1):

                    # 找到奇环（花），收缩它

                    b = self.lca(v, u)

                    

                    used_uv = [False] * self.n

                    self.mark_path(v, b, u)

                    self.mark_path(u, b, v)

                    

                    for i in range(self.n):

                        if used_uv[i]:

                            used_uv[i] = False

                            if self.base[i] == b:

                                self.base[i] = b

                                self.qq.append(i)

                                self.used[i] = True

                

                elif self.p[u] == -1:

                    self.p[u] = v

                    if self.match[u] == -1:

                        # 找到自由顶点，增广成功

                        self.qhead = len(self.qq)  # 终止BFS

                        return self.extend_path(u)

                    else:

                        # 继续BFS

                        u_match = self.match[u]

                        self.used[u_match] = True

                        self.qq.append(u_match)

        

        return False

    

    def extend_path(self, u):

        """沿 p 数组回溯，扩展匹配"""

        v = u

        while v != -1:

            pv = self.p[v]

            nv = self.match[pv] if pv != -1 else -1

            self.match[v] = pv

            self.match[pv] = v

            v = nv

        return True

    

    def max_matching(self, start_node=0):

        """

        计算最大匹配

        

        返回匹配对列表

        """

        result = []

        for i in range(self.n):

            if self.match[i] == -1:

                if self.find_path(i):

                    result = [(v, self.match[v]) 

                             for v in range(self.n) if v < self.match[v]]

        return result





def build_general_graph():

    """构建一个一般图示例（包含奇环）"""

    #     0

    #    /|\

    #   1 | 2

    #   |\|

    #   4-3

    # 斜线表示一个奇环：1-3-4-1（3个顶点）

    n = 5

    edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (1, 4), (3, 4)]

    return n, edges





if __name__ == "__main__":

    print("=" * 55)

    print("Edmonds Blossom 一般图最大匹配算法")

    print("=" * 55)

    

    n, edges = build_general_graph()

    

    blossom = BlossomAlgorithm(n)

    for u, v in edges:

        blossom.add_edge(u, v)

    

    print(f"\n图：{n} 个顶点")

    print("边：", edges)

    print("\n邻接表：")

    for i in range(n):

        print(f"  顶点{i}: {blossom.adj[i]}")

    

    print("\n算法执行：")

    matching = blossom.max_matching()

    

    print("\n最大匹配结果：")

    for u, v in matching:

        print(f"  顶点{u} <-> 顶点{v}")

    

    print(f"\n匹配大小 = {len(matching)}")

    

    # 验证：匹配边的端点不重复

    all_vertices = set()

    for u, v in matching:

        all_vertices.add(u)

        all_vertices.add(v)

    print(f"覆盖顶点数 = {len(all_vertices)}",

          "✓" if len(all_vertices) == 2 * len(matching) else "✗")

