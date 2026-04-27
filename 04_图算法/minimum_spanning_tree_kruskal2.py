# -*- coding: utf-8 -*-

"""

算法实现：04_图算法 / minimum_spanning_tree_kruskal2



本文件实现 minimum_spanning_tree_kruskal2 相关的算法功能。

"""



from __future__ import annotations



from typing import TypeVar



T = TypeVar("T")





# ==========================================================

# 并查集节点类（Disjoint Set Tree Node）

# ==========================================================

class DisjointSetTreeNode[T]:

    """

    并查集中的节点。

    

    Attributes:

        data: 节点存储的数据

        parent: 父节点指针

        rank: 节点的秩（用于合并优化）

    """



    def __init__(self, data: T) -> None:

        self.data = data

        self.parent = self  # 初始时父节点指向自己

        self.rank = 0       # 初始秩为0





# ==========================================================

# 并查集类（Disjoint Set Tree）

# ==========================================================

class DisjointSetTree[T]:

    """

    并查集数据结构（带路径压缩和按秩合并）。

    

    支持 make_set、find_set、union 操作。

    """



    def __init__(self) -> None:

        # map: 数据到节点对象的映射

        self.map: dict[T, DisjointSetTreeNode[T]] = {}



    def make_set(self, data: T) -> None:

        """创建包含 data 的新集合。"""

        self.map[data] = DisjointSetTreeNode(data)



    def find_set(self, data: T) -> DisjointSetTreeNode[T]:

        """

        查找 data 所属集合的代表元素（带路径压缩）。

        

        Args:

            data: 要查找的数据

        

        Returns:

            集合代表元素的节点对象

        """

        elem_ref = self.map[data]

        if elem_ref != elem_ref.parent:

            elem_ref.parent = self.find_set(elem_ref.parent.data)

        return elem_ref.parent



    def link(

        self, node1: DisjointSetTreeNode[T], node2: DisjointSetTreeNode[T]

    ) -> None:

        """

        合并两个集合（按秩合并）。

        

        Args:

            node1: 集合1的代表节点

            node2: 集合2的代表节点

        """

        # 秩大的作为父节点

        if node1.rank > node2.rank:

            node2.parent = node1

        else:

            node1.parent = node2

            if node1.rank == node2.rank:

                node2.rank += 1



    def union(self, data1: T, data2: T) -> None:

        """

        合并 data1 和 data2 所属的两个集合。

        

        Args:

            data1: 元素1

            data2: 元素2

        """

        self.link(self.find_set(data1), self.find_set(data2))





# ==========================================================

# 加权无向图类（Graph Undirected Weighted）

# ==========================================================

class GraphUndirectedWeighted[T]:

    """

    加权无向图，使用邻接表存储。

    

    提供 Kruskal 算法求解 MST 的功能。

    """



    def __init__(self) -> None:

        # connections: {节点: {邻接节点: 权重}}

        self.connections: dict[T, dict[T, int]] = {}



    def add_node(self, node: T) -> None:

        """

        添加节点（如果不存在）。

        

        Args:

            node: 节点标识符

        """

        if node not in self.connections:

            self.connections[node] = {}



    def add_edge(self, node1: T, node2: T, weight: int) -> None:

        """

        添加一条无向边。

        

        Args:

            node1: 顶点1

            node2: 顶点2

            weight: 边权重

        """

        self.add_node(node1)

        self.add_node(node2)

        self.connections[node1][node2] = weight

        self.connections[node2][node1] = weight



    def kruskal(self) -> GraphUndirectedWeighted[T]:

        """

        Kruskal 算法求解最小生成树（MST）。

        

        Returns:

            包含 MST 的新图

        

        算法步骤：

        1. 将所有边按权重升序排列

        2. 依次遍历每条边，若两端点不在同一集合，则加入 MST

        3. 直到 MST 包含 n-1 条边

        

        示例:

        >>> g1 = GraphUndirectedWeighted[int]()

        >>> g1.add_edge(1, 2, 1)

        >>> g1.add_edge(2, 3, 2)

        >>> g1.add_edge(3, 4, 1)

        >>> g1.add_edge(3, 5, 100)  # 不会出现在 MST 中

        >>> g1.add_edge(4, 5, 5)

        >>> mst = g1.kruskal()

        >>> assert 5 not in mst.connections[3]  # 边(3,5) 未被选中

        """

        # 步骤1: 获取所有边并按权重排序

        edges = []

        seen = set()

        for start in self.connections:

            for end in self.connections[start]:

                if (start, end) not in seen:

                    seen.add((end, start))  # 避免重复

                    edges.append((start, end, self.connections[start][end]))

        edges.sort(key=lambda x: x[2])



        # 步骤2: 创建并查集

        disjoint_set = DisjointSetTree[T]()

        for node in self.connections:

            disjoint_set.make_set(node)



        # 步骤3: 构建 MST

        num_edges = 0

        index = 0

        graph = GraphUndirectedWeighted[T]()

        

        while num_edges < len(self.connections) - 1:

            u, v, w = edges[index]

            index += 1

            # 检查两端点是否在同一集合

            parent_u = disjoint_set.find_set(u)

            parent_v = disjoint_set.find_set(v)

            if parent_u != parent_v:

                num_edges += 1

                graph.add_edge(u, v, w)

                disjoint_set.union(u, v)

        return graph





# ==========================================================

# 测试代码

# ==========================================================

if __name__ == "__main__":

    # 示例：整数类型图

    print("=== 整数图 MST 示例 ===")

    g1 = GraphUndirectedWeighted[int]()

    g1.add_edge(1, 2, 1)

    g1.add_edge(2, 3, 2)

    g1.add_edge(3, 4, 1)

    g1.add_edge(3, 5, 100)  # 高权重边

    g1.add_edge(4, 5, 5)

    

    mst1 = g1.kruskal()

    print("MST 边:", list(mst1.connections.items()))

    

    # 示例：字符串类型图

    print("\n=== 字符串图 MST 示例 ===")

    g2 = GraphUndirectedWeighted[str]()

    g2.add_edge('A', 'B', 1)

    g2.add_edge('B', 'C', 2)

    g2.add_edge('C', 'D', 1)

    g2.add_edge('C', 'E', 100)  # 高权重边

    g2.add_edge('D', 'E', 5)

    

    mst2 = g2.kruskal()

    print("MST 边:", list(mst2.connections.items()))

