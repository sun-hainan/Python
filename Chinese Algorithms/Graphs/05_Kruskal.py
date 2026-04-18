"""
Kruskal - 最小生成树
==========================================

【算法原理】
贪心+并查集，按边权重排序，依次选择不成环的最小边。

【时间复杂度】O(E log E)
【空间复杂度】O(V)

【应用场景】
- 航空公司航线规划
- 电网建设
- 边稀疏图的MST

【何时使用】
- 边稀疏的图
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
