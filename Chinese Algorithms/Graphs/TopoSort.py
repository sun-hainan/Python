Topological Sort - 拓扑排序

原理: Kahn算法, BFS, O(V+E)

from collections import deque

def topo(g):
    in_deg = {v:0 for v in g}
    for v in g:
        for n in g[v]:
            in_deg[n] += 1
    q = deque([v for v in g if in_deg[v]==0])
    r = []
    while q:
        v = q.popleft()
        r.append(v)
        for n in g[v]:
            in_deg[n] -= 1
            if in_deg[n]==0:
                q.append(n)
    return r
