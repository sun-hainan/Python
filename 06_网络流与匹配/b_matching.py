# -*- coding: utf-8 -*-
"""
算法实现：06_网络流与匹配 / b_matching

本文件实现 b_matching 相关的算法功能。
"""

from collections import defaultdict, deque


class BMatching:
    """b-匹配求解器"""
    
    def __init__(self, n):
        self.n = n  # 原始顶点数
        self.b = [1] * n  # 默认配额为1
        self.adj = defaultdict(list)  # 原始邻接表
        self.edges = []  # 边列表
    
    def set_quota(self, v, quota):
        """设置顶点 v 的配额"""
        self.b[v] = quota
    
    def add_edge(self, u, v):
        """添加无向边"""
        self.adj[u].append(v)
        self.adj[v].append(u)
        self.edges.append((u, v))
    
    def to_standard_matching(self):
        """
        将 b-匹配转换为普通匹配
        
        方法：
        - 创建 n' = sum(b(v)) 个顶点（每个顶点 v 有 b(v) 个副本）
        - 原图的边连接相应的副本
        - 同一顶点的不同副本之间连边（形成团）
        
        返回：(n', new_adj, copies) 
        copies[v] = [copy_id_1, copy_id_2, ...] 
        """
        # 为每个顶点创建副本
        copies = []
        total_vertices = 0
        
        for v in range(self.n):
            copies.append(list(range(total_vertices, total_vertices + self.b[v])))
            total_vertices += self.b[v]
        
        # 构建新图的邻接表
        new_adj = defaultdict(list)
        
        # Step 1: 添加原边（连接相应副本）
        for u, v in self.edges:
            # u 的第 i 个副本与 v 的第 i 个副本配对
            for i in range(min(self.b[u], self.b[v])):
                cu = copies[u][i]
                cv = copies[v][i]
                new_adj[cu].append(cv)
                new_adj[cv].append(cu)
        
        # Step 2: 添加内部边（同一顶点的副本之间）
        # 形成团，使得任意匹配都可以
        for v in range(self.n):
            for i in range(self.b[v]):
                for j in range(i + 1, self.b[v]):
                    ci = copies[v][i]
                    cj = copies[v][j]
                    new_adj[ci].append(cj)
                    new_adj[cj].append(ci)
        
        return total_vertices, new_adj, copies
    
    def max_b_matching(self):
        """
        求最大 b-匹配
        
        返回：匹配边列表 [(u, v), ...]
        """
        total_v, new_adj, copies = self.to_standard_matching()
        
        # 使用 Hopcroft-Karp 求最大匹配
        n_left = total_v
        n_right = total_v  # 实际上是无向图，需要处理
        
        # 这里简化：直接用 BFS/DFS 求最大匹配
        matching = [-1] * total_v  # matching[copy] = matched_copy
        visited = [False] * total_v
        
        def bfs_level():
            """BFS 构建层次图"""
            level = [-1] * total_v
            queue = deque()
            
            for v in range(total_v):
                if matching[v] == -1:
                    level[v] = 0
                    queue.append(v)
            
            found_augment = False
            while queue:
                u = queue.popleft()
                for v in new_adj[u]:
                    if level[v] == -1:
                        level[v] = level[u] + 1
                        if matching[v] == -1:
                            found_augment = True
                        elif matching[v] != u:
                            queue.append(matching[v])
            
            return level, found_augment
        
        def dfs(u, level, visited):
            """DFS 找增广路"""
            for v in new_adj[u]:
                if level[v] == level[u] + 1 and not visited[v]:
                    visited[v] = True
                    if matching[v] == -1 or dfs(matching[v], level, visited):
                        matching[u] = v
                        matching[v] = u
                        return True
            return False
        
        # 简化的最大匹配
        matched_pairs = set()
        for start in range(total_v):
            if matching[start] != -1:
                continue
            
            visited = [False] * total_v
            stack = [(start, [start])]
            
            while stack:
                u, path = stack.pop()
                if matching[u] == -1:
                    # 找到增广路
                    for i in range(0, len(path) - 1, 2):
                        v1, v2 = path[i], path[i+1]
                        matching[v1] = v2
                        matching[v2] = v1
                        pair = (min(v1, v2), max(v1, v2))
                        matched_pairs.add(pair)
                    break
                
                for v in new_adj[u]:
                    if v not in path and (matching[v] == -1 or matching[v] in path):
                        if matching[v] != -1:
                            next_idx = path.index(matching[v]) + 1
                            if next_idx < len(path):
                                new_path = path[:next_idx] + [v]
                            else:
                                new_path = path + [matching[v], v]
                        else:
                            new_path = path + [v]
                        stack.append((v, new_path))
        
        # 转换回原始顶点
        b_matching = []
        for cu, cv in matched_pairs:
            # 找到原始顶点
            orig_u = None
            orig_v = None
            for ov in range(self.n):
                if cu in copies[ov]:
                    orig_u = ov
                if cv in copies[ov]:
                    orig_v = ov
            
            if orig_u is not None and orig_v is not None and orig_u < orig_v:
                b_matching.append((orig_u, orig_v))
        
        return b_matching


def build_b_matching_example():
    """构建 b-匹配示例"""
    bm = BMatching(5)
    
    # 配额
    bm.set_quota(0, 2)
    bm.set_quota(1, 2)
    bm.set_quota(2, 2)
    bm.set_quota(3, 1)
    bm.set_quota(4, 1)
    
    # 边
    bm.add_edge(0, 1)
    bm.add_edge(0, 2)
    bm.add_edge(1, 2)
    bm.add_edge(1, 3)
    bm.add_edge(2, 3)
    bm.add_edge(2, 4)
    bm.add_edge(3, 4)
    
    return bm


if __name__ == "__main__":
    print("=" * 55)
    print("b-匹配（b-Matching）")
    print("=" * 55)
    
    bm = build_b_matching_example()
    
    print("\n原始图：5 节点")
    print("\n配额 b(v)：")
    for i in range(bm.n):
        print(f"  顶点 {i}: b({i}) = {bm.b[i]}")
    
    print("\n边：", bm.edges)
    
    print("\n转换到普通匹配...")
    total_v, new_adj, copies = bm.to_standard_matching()
    
    print(f"\n展开后顶点数: {total_v}")
    print("副本映射：")
    for v in range(bm.n):
        print(f"  原始顶点 {v} -> 副本 {copies[v]}")
    
    print("\n求最大 b-匹配...")
    matching = bm.max_b_matching()
    
    print("\n最大 b-匹配结果：")
    for u, v in matching:
        print(f"  ({u}, {v})")
    
    # 统计每个顶点的匹配次数
    match_count = [0] * bm.n
    for u, v in matching:
        match_count[u] += 1
        match_count[v] += 1
    
    print("\n各顶点的匹配次数：")
    for v in range(bm.n):
        status = "✓" if match_count[v] <= bm.b[v] else "✗"
        print(f"  顶点 {v}: {match_count[v]}/{bm.b[v]} {status}")
