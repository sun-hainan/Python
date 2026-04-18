Prim - 最小生成树

原理: 贪心, O(V^2)

def prim(g):
    n = len(g)
    visited = [False]*n
    min_dist = [float("inf")]*n
    min_dist[0] = 0
    result = 0
    for _ in range(n):
        u = -1
        for v in range(n):
            if not visited[v] and (u==-1 or min_dist[v]<min_dist[u]):
                u = v
        if min_dist[u] == float("inf"): break
        visited[u] = True
        result += min_dist[u]
        for v in range(n):
            if g[u][v] > 0 and not visited[v]:
                min_dist[v] = min(min_dist[v], g[u][v])
    return result
