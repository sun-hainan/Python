# -*- coding: utf-8 -*-
"""
算法实现：04_图算法 / minimum_spanning_tree_boruvka

本文件实现 minimum_spanning_tree_boruvka 相关的算法功能。
"""

class Graph:
    """
    基于邻接表存储的图数据结构。
    
    提供添加顶点/边、获取边列表、构建 MST 等功能。
    """

    def __init__(self):
        self.num_vertices = 0  # 顶点数量
        self.num_edges = 0    # 边数量
        self.adjacency = {}   # 邻接表：{顶点: {邻接顶点: 权重}}

    def add_vertex(self, vertex):
        """
        添加单个顶点。
        
        Args:
            vertex: 顶点标识符
        """
        if vertex not in self.adjacency:
            self.adjacency[vertex] = {}
            self.num_vertices += 1

    def add_edge(self, head, tail, weight):
        """
        添加一条无向边。
        
        Args:
            head: 顶点1
            tail: 顶点2
            weight: 边权重
        """
        self.add_vertex(head)
        self.add_vertex(tail)

        if head == tail:
            return

        # 双向添加（无向图）
        self.adjacency[head][tail] = weight
        self.adjacency[tail][head] = weight

    def distinct_weight(self):
        """
        将边权重转换为互不相同（用于 Boruvka 算法）。
        
        原理：按权重排序后，相等的边权重递增1。
        """
        edges = self.get_edges()
        # 去除重复边（双向存储）
        for edge in edges:
            head, tail, weight = edge
            edges.remove((tail, head, weight))
        for i in range(len(edges)):
            edges[i] = list(edges[i])

        # 按权重排序
        edges.sort(key=lambda e: e[2])
        # 使权重互不相同
        for i in range(len(edges) - 1):
            if edges[i][2] >= edges[i + 1][2]:
                edges[i + 1][2] = edges[i][2] + 1
        # 更新图中权重
        for edge in edges:
            head, tail, weight = edge
            self.adjacency[head][tail] = weight
            self.adjacency[tail][head] = weight

    def __str__(self):
        """
        返回图的字符串表示。
        
        格式：head -> tail == weight
        """
        string = ""
        for tail in self.adjacency:
            for head in self.adjacency[tail]:
                weight = self.adjacency[head][tail]
                string += f"{head} -> {tail} == {weight}\n"
        return string.rstrip("\n")

    def get_edges(self):
        """
        返回图中所有边。
        
        Returns:
            边列表：[(tail, head, weight), ...]
        """
        output = []
        for tail in self.adjacency:
            for head in self.adjacency[tail]:
                output.append((tail, head, self.adjacency[head][tail]))
        return output

    def get_vertices(self):
        """返回图中所有顶点。"""
        return self.adjacency.keys()

    @staticmethod
    def build(vertices=None, edges=None):
        """
        从顶点和边列表构建图。
        
        Args:
            vertices: 顶点列表（可选）
            edges: 边列表，每条边为 (head, tail, weight)
        
        Returns:
            新建的 Graph 实例
        """
        g = Graph()
        if vertices is None:
            vertices = []
        if edges is None:
            edge = []
        for vertex in vertices:
            g.add_vertex(vertex)
        for edge in edges:
            g.add_edge(*edge)
        return g

    class UnionFind:
        """
        并查集（Disjoint Set Union）数据结构。
        
        用于 Boruvka 算法中判断两个顶点是否在同一连通分量。
        """

        def __init__(self):
            self.parent = {}  # 父节点映射
            self.rank = {}    # 秩（用于路径压缩优化）

        def __len__(self):
            return len(self.parent)

        def make_set(self, item):
            """创建新集合。"""
            if item in self.parent:
                return self.find(item)
            self.parent[item] = item
            self.rank[item] = 0
            return item

        def find(self, item):
            """
            查找 item 所属集合的代表元素（带路径压缩）。
            
            Returns:
                集合代表元素
            """
            if item not in self.parent:
                return self.make_set(item)
            if item != self.parent[item]:
                self.parent[item] = self.find(self.parent[item])
            return self.parent[item]

        def union(self, item1, item2):
            """
            合并两个集合（按秩合并）。
            
            Returns:
                合并后的集合代表元素
            """
            root1 = self.find(item1)
            root2 = self.find(item2)

            if root1 == root2:
                return root1

            # 秩大的作为父节点
            if self.rank[root1] > self.rank[root2]:
                self.parent[root2] = root1
                return root1

            if self.rank[root1] < self.rank[root2]:
                self.parent[root1] = root2
                return root2

            # 秩相等时，root2 作为父节点，root1 秩+1
            if self.rank[root1] == self.rank[root2]:
                self.rank[root1] += 1
                self.parent[root2] = root1
                return root1
            return None

    @staticmethod
    def boruvka_mst(graph):
        """
        Boruvka 算法求最小生成树（MST）。
        
        Args:
            graph: Graph 实例
        
        Returns:
            包含 MST 边的新 Graph 实例
        
        示例:
        >>> g = Graph()
        >>> g = Graph.build([0, 1, 2, 3], [[0, 1, 1], [0, 2, 1],[2, 3, 1]])
        >>> g.distinct_weight()
        >>> bg = Graph.boruvka_mst(g)
        >>> print(bg)  # 显示 MST 的边
        """
        num_components = graph.num_vertices

        union_find = Graph.UnionFind()
        mst_edges = []
        
        # 迭代直到只剩一个连通分量
        while num_components > 1:
            # 每个连通分量的最小边
            cheap_edge = {}
            for vertex in graph.get_vertices():
                cheap_edge[vertex] = -1

            # 获取所有边
            edges = graph.get_edges()
            # 去除重复边
            for edge in edges:
                head, tail, weight = edge
                edges.remove((tail, head, weight))
            
            # 为每个连通分量找最小边
            for edge in edges:
                head, tail, weight = edge
                set1 = union_find.find(head)
                set2 = union_find.find(tail)
                if set1 != set2:
                    # 更新 set1 的最小边
                    if cheap_edge[set1] == -1 or cheap_edge[set1][2] > weight:
                        cheap_edge[set1] = [head, tail, weight]
                    # 更新 set2 的最小边
                    if cheap_edge[set2] == -1 or cheap_edge[set2][2] > weight:
                        cheap_edge[set2] = [head, tail, weight]
            
            # 将最小边加入 MST
            for head_tail_weight in cheap_edge.values():
                if head_tail_weight != -1:
                    head, tail, weight = head_tail_weight
                    if union_find.find(head) != union_find.find(tail):
                        union_find.union(head, tail)
                        mst_edges.append(head_tail_weight)
                        num_components = num_components - 1
        
        # 构建 MST 图
        mst = Graph.build(edges=mst_edges)
        return mst


# ==========================================================
# 测试代码
# ==========================================================
if __name__ == "__main__":
    # 创建示例图
    #     0
    #    /|\
    #   1 | 2
    #   |/  \
    #   3----4
    g = Graph.build(
        vertices=[0, 1, 2, 3, 4],
        edges=[
            [0, 1, 1],
            [0, 2, 2],
            [0, 3, 3],
            [1, 3, 4],
            [2, 4, 5],
            [3, 4, 6]
        ]
    )
    # 使边权重互不相同
    g.distinct_weight()
    # 计算 MST
    mst = Graph.boruvka_mst(g)
    print("MST 边:")
    print(mst)
