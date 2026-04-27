# -*- coding: utf-8 -*-

"""

算法实现：Graphs / 05_Kruskal



本文件实现 05_Kruskal 相关的算法功能。

"""



def kruskal(num_nodes, edges):

    """

    Kruskal最小生成树

    """

    edges = sorted(edges, key=lambda x: x[2])

    parent = list(range(num_nodes))

    def find(x):

        if parent[x] != x:

            parent[x] = find(parent[x])

        return parent[x]

    result = 0

    for u, v, w in edges:

        pu, pv = find(u), find(v)

        if pu != pv:

            parent[pu] = pv

            result += w

    return result





if __name__ == "__main__":

    # 测试: find

    result = find()

    print(result)

