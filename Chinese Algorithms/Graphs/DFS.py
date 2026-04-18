DFS - 深度优先搜索

原理: 栈或递归, O(V+E)

def dfs(g, s, visited=None):
    if visited is None: visited = set()
    visited.add(s)
    r = [s]
    for n in g.get(s, []):
        if n not in visited:
            r.extend(dfs(g, n, visited))
    return r
