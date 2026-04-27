# -*- coding: utf-8 -*-

"""

算法实现：04_图算法 / minimum_spanning_tree_kruskal



本文件实现 minimum_spanning_tree_kruskal 相关的算法功能。

"""



from typing import List, Tuple





def kruskal(

    num_nodes: int, edges: List[Tuple[int, int, int]]

) -> List[Tuple[int, int, int]]:

    """

    Kruskal 最小生成树算法



    参数:

        num_nodes: 顶点数

        edges: 边列表，格式 [(起点, 终点, 权重), ...]



    返回:

        最小生成树的边列表



    示例:

        >>> kruskal(4, [(0, 1, 3), (1, 2, 5), (2, 3, 1)])

        [(2, 3, 1), (0, 1, 3), (1, 2, 5)]



        >>> kruskal(4, [(0, 1, 3), (1, 2, 5), (2, 3, 1), (0, 2, 1), (0, 3, 2)])

        [(2, 3, 1), (0, 2, 1), (0, 1, 3)]

    """

    # 1. 按权重排序所有边

    edges = sorted(edges, key=lambda edge: edge[2])



    # 2. 初始化并查集（每个顶点是自己的父节点）

    parent = list(range(num_nodes))



    def find_parent(i):

        """路径压缩：查找根节点"""

        if i != parent[i]:

            parent[i] = find_parent(parent[i])

        return parent[i]



    minimum_spanning_tree_cost = 0

    minimum_spanning_tree = []



    # 3. 依次选择最小边

    for edge in edges:

        parent_a = find_parent(edge[0])

        parent_b = find_parent(edge[1])



        # 如果两个顶点不在同一个集合（不成环）

        if parent_a != parent_b:

            minimum_spanning_tree_cost += edge[2]

            minimum_spanning_tree.append(edge)

            # 合并两个集合

            parent[parent_a] = parent_b



    return minimum_spanning_tree





if __name__ == "__main__":

    num_nodes, num_edges = map(int, input("输入顶点数和边数: ").strip().split())

    edges = []

    for _ in range(num_edges):

        node1, node2, cost = map(int, input().strip().split())

        edges.append((node1, node2, cost))



    mst = kruskal(num_nodes, edges)

    print(f"最小生成树边: {mst}")

