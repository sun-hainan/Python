Dijkstra - 最短路径

原理: 贪心+最小堆, O((V+E)logV)

import heapq

def dijkstra(g, s, e):
    h = [(0, s)]
    visited = set()
    while h:
        c, v = heapq.heappop(h)
        if v in visited: continue
        visited.add(v)
        if v == e: return c
        for n, w in g.get(v, []):
            if n not in visited:
                heapq.heappush(h, (c+w, n))
    return -1
