"""
二分图检测 (Bipartite Graph Check)
===================================
检测一个无向图是否为二分图。

二分图：图的顶点可以分成两个不相交的集合，使得每条边都连接两个不同集合的顶点。

算法：二分图等价于图不包含奇环。使用BFS/DFS着色算法检测。

参考：
    - König, D. (1931). Über Graphen und ihre Anwendung auf Determinantentheorie.
"""

from typing import List, Set, Optional
from collections import deque


class Graph:
    """无向图"""
    def __init__(self, n: int = 0):
        self.n = n
        self.adj = [set() for _ in range(n)]
    
    def add_edge(self, u: int, v: int):
        self.adj[u].add(v)
        self.adj[v].add(u)
    
    def neighbors(self, u: int) -> Set[int]:
        return self.adj[u]


def is_bipartite_bfs(graph: Graph) -> tuple[bool, Optional[List[int]]]:
    """
    使用BFS着色检测二分图
    
    参数:
        graph: 输入图
    
    返回:
        (是否为二分图, 分区方案或None)
    """
    n = graph.n
    
    if n == 0:
        return True, []
    
    # color[i] = 0 或 1 表示颜色，-1表示未着色
    color = [-1] * n
    
    # 可能存在多个连通分量，需要分别检测
    for start in range(n):
        if color[start] != -1:
            continue
        
        # BFS着色
        queue = deque([start])
        color[start] = 0
        
        while queue:
            u = queue.popleft()
            
            for v in graph.neighbors(u):
                if color[v] == -1:
                    # 邻居着不同颜色
                    color[v] = 1 - color[u]
                    queue.append(v)
                elif color[v] == color[u]:
                    # 同色邻居 -> 存在奇环，不是二分图
                    return False, None
    
    return True, color


def is_bipartite_dfs(graph: Graph) -> tuple[bool, Optional[List[int]]]:
    """
    使用DFS着色检测二分图
    
    参数:
        graph: 输入图
    
    返回:
        (是否为二分图, 分区方案或None)
    """
    n = graph.n
    color = [-1] * n
    
    def dfs(u: int, c: int) -> bool:
        """递归DFS着色"""
        color[u] = c
        
        for v in graph.neighbors(u):
            if color[v] == -1:
                if not dfs(v, 1 - c):
                    return False
            elif color[v] == c:
                return False
        
        return True
    
    for start in range(n):
        if color[start] == -1:
            if not dfs(start, 0):
                return False, None
    
    return True, color


def is_bipartite_union_find(graph: Graph) -> tuple[bool, Optional[List[int]]]:
    """
    使用并查集检测二分图
    
    每个节点维护两个"角色"：属于集合A或集合B
    对于边(u,v)，u和v不能属于同一集合
    
    参数:
        graph: 输入图
    
   返回:
        (是否为二分图, 分区方案)
    """
    n = graph.n
    
    # 并查集父节点
    parent = list(range(2 * n))  # 节点i的两个版本: i (集合A) 和 i+n (集合B)
    
    def find(x: int) -> int:
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x: int, y: int):
        px, py = find(x), find(y)
        if px == py:
            return False  # 冲突
        parent[px] = py
        return True
    
    # 遍历所有边
    for u in range(n):
        for v in graph.neighbors(u):
            if u >= v:  # 每条边只处理一次
                continue
            
            # u和v不能在同一集合
            # 即 u(A) 与 v(B) 不能相连，且 u(B) 与 v(A) 不能相连
            # 合并: u(A) 与 v(B)
            if not union(u, v + n):
                return False, None
            # 合并: u(B) 与 v(A)
            if not union(u + n, v):
                return False, None
    
    # 恢复分区方案
    partition = [-1] * n
    for i in range(n):
        if find(i) == find(i):  # i在集合A
            partition[i] = 0 if find(i) < find(i + n) else 1
    
    # 重新计算正确的分区
    color = [-1] * n
    for i in range(n):
        if color[i] == -1:
            # 确定颜色
            root = find(i)
            c = 0 if find(i) < find(i + n) else 1
            # BFS设置颜色
            queue = deque([i])
            color[i] = c
            while queue:
                u = queue.popleft()
                for v in graph.neighbors(u):
                    if color[v] == -1:
                        color[v] = 1 - color[u]
                        queue.append(v)
    
    return True, color


def find_bipartite_components(graph: Graph) -> List[Tuple[Set[int], Set[int]]]:
    """
    找出所有二分分量及其两个集合
    
    参数:
        graph: 输入图
    
    返回:
        [(集合A, 集合B), ...] 每个连通分量的分区
    """
    n = graph.n
    visited = [False] * n
    components = []
    
    for start in range(n):
        if visited[start]:
            continue
        
        # BFS遍历一个连通分量
        set_a = set()
        set_b = set()
        queue = deque([(start, 0)])  # (节点, 集合)
        visited[start] = True
        
        while queue:
            u, s = queue.popleft()
            
            if s == 0:
                set_a.add(u)
            else:
                set_b.add(u)
            
            for v in graph.neighbors(u):
                if not visited[v]:
                    visited[v] = True
                    queue.append((v, 1 - s))
        
        components.append((set_a, set_b))
    
    return components


def maximum_matching_bipartite(graph: Graph, 
                               partition_a: Set[int], 
                               partition_b: Set[int]) -> int:
    """
    二分图最大匹配（霍普克罗夫特-卡普算法简化版）
    
    参数:
        graph: 输入图
        partition_a: 集合A
        partition_b: 集合B
    
    返回:
        最大匹配数
    """
    # 简化实现：DFS增广路径（匈牙利算法）
    n = graph.n
    match_to = [-1] * n  # match_to[v] = 匹配的A中节点
    
    def bpm(u: int, visited: Set[int]) -> bool:
        """尝试为节点u找到增广路径"""
        for v in graph.neighbors(u):
            if v not in visited:
                visited.add(v)
                if match_to[v] == -1 or bpm(match_to[v], visited):
                    match_to[v] = u
                    return True
        return False
    
    result = 0
    for u in partition_a:
        visited = set()
        if bpm(u, visited):
            result += 1
    
    return result


def is_complete_bipartite(graph: Graph) -> tuple[bool, Optional[Tuple[Set[int], Set[int]]]]:
    """
    检测图是否为完全二分图 K_{m,n}
    
    参数:
        graph: 输入图
    
    返回:
        (是否为完全二分图, (集合A, 集合B))
    """
    is_bip, partition = is_bipartite_bfs(graph)
    
    if not is_bip or partition is None:
        return False, None
    
    # 分离两个集合
    set_a = {i for i in range(graph.n) if partition[i] == 0}
    set_b = {i for i in range(graph.n) if partition[i] == 1}
    
    # 检查：集合A中任意节点与集合B中任意节点都有边
    # 且集合内无边
    for a in set_a:
        for b in set_b:
            if b not in graph.neighbors(a):
                return False, None
    
    for a1 in set_a:
        for a2 in set_a:
            if a1 != a2 and a2 in graph.neighbors(a1):
                return False, None
    
    for b1 in set_b:
        for b2 in set_b:
            if b1 != b2 and b2 in graph.neighbors(b1):
                return False, None
    
    return True, (set_a, set_b)


if __name__ == "__main__":
    print("=== 二分图检测测试 ===")
    
    # 测试1: 简单二分图（偶环）
    g1 = Graph(6)
    g1.add_edge(0, 1)
    g1.add_edge(1, 2)
    g1.add_edge(2, 3)
    g1.add_edge(3, 4)
    g1.add_edge(4, 5)
    g1.add_edge(5, 0)
    
    is_bip, part = is_bipartite_bfs(g1)
    print(f"\n六边形 (偶环): 二分图? {is_bip}")
    if part:
        print(f"  集合A: {[i for i, c in enumerate(part) if c == 0]}")
        print(f"  集合B: {[i for i, c in enumerate(part) if c == 1]}")
    
    # 测试2: 非二分图（奇环）
    g2 = Graph(5)
    g2.add_edge(0, 1)
    g2.add_edge(1, 2)
    g2.add_edge(2, 3)
    g2.add_edge(3, 4)
    g2.add_edge(4, 0)
    g2.add_edge(0, 2)  # 形成三角形
    
    is_bip2, _ = is_bipartite_bfs(g2)
    print(f"\n五边形+对角线 (含奇环): 二分图? {is_bip2}")
    
    # 测试3: 完全二分图 K_{2,3}
    g3 = Graph(5)
    # A = {0, 1}, B = {2, 3, 4}
    for a in [0, 1]:
        for b in [2, 3, 4]:
            g3.add_edge(a, b)
    
    is_kmn, parts = is_complete_bipartite(g3)
    print(f"\n完全二分图 K_{{2,3}}: {is_kmn}")
    if parts:
        print(f"  集合A: {parts[0]}, 集合B: {parts[1]}")
    
    # 测试4: 非连通二分图
    g4 = Graph(8)
    # 分量1: 0-1-2
    g4.add_edge(0, 1)
    g4.add_edge(1, 2)
    # 分量2: 3-4-5-6 (树)
    g4.add_edge(3, 4)
    g4.add_edge(4, 5)
    g4.add_edge(5, 6)
    # 分量3: 单独节点 7
    
    is_bip4, _ = is_bipartite_bfs(g4)
    print(f"\n非连通图: 二分图? {is_bip4}")
    
    components = find_bipartite_components(g4)
    print(f"找到 {len(components)} 个连通分量:")
    for i, (set_a, set_b) in enumerate(components):
        print(f"  分量{i+1}: A={set_a}, B={set_b}")
    
    # 测试5: 并查集方法
    g5 = Graph(4)
    g5.add_edge(0, 2)
    g5.add_edge(1, 3)
    g5.add_edge(0, 3)
    
    is_bip5, part5 = is_bipartite_union_find(g5)
    print(f"\n并查集方法测试: 二分图? {is_bip5}")
    if part5:
        print(f"  着色: {part5}")
    
    print("\n=== 测试完成 ===")
