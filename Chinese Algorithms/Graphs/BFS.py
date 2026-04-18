BFS - 广度优先搜索

原理: 队列, O(V+E)

from collections import deque

def bfs(g, s):
    visited = {s}
    q = deque([s])
    r = []
    while q:
        v = q.popleft()
        r.append(v)
        for n in g.get(v, []):
            if n not in visited:
                visited.add(n)
                q.append(n)
    return r
