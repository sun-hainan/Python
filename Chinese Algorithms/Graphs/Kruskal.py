Kruskal - 最小生成树

原理: 贪心+并查集, O(ElogE)

def kruskal(n, edges):
    edges = sorted(edges, key=lambda x: x[2])
    parent = list(range(n))
    def find(x):
        return x if parent[x]==x else find(parent[x])
    res = 0
    for u, v, w in edges:
        pu, pv = find(u), find(v)
        if pu != pv:
            parent[pu] = pv
            res += w
    return res
